from PyQt5.QtCore import QTimer
from NodeGraphQt.constants import NodePropWidgetEnum
import math

from graph.db_spec_singleton import db_spec, effect_system_tables
from schema_generator import SQLValidator
from graph.custom_widgets import IntSpinNodeWidget, FloatSpinNodeWidget, ExpandingLineEdit, DropDownLineEdit
from graph.nodes.base_nodes import BasicDBNode, set_output_port_constraints


class BaseEffectNode(BasicDBNode):
    arg_setter_prop = None
    widget_props = []
    loaded_transient_widgets = False

    def set_property(self, name, value, push_undo=True):   # TODO on reload, try get this to trigger on setting effectType
        if name == self.arg_setter_prop:
            if self.graph is not None and self.get_property(self.arg_setter_prop) != value:
                self.graph.begin_undo("change mode")
                old = self.old_effect
                super().set_property(name=name, value=value, push_undo=True)
                QTimer.singleShot(0, lambda v=value, o=old: self._apply_mode(v, push_undo=True, old_mode=o))
                self.graph.end_undo()
                return
        elif name == 'arg_params' and self.graph is None and not self.loaded_transient_widgets:
                super().set_property(name=name, value=value, push_undo=True)
                self._apply_mode(value, push_undo=True)
                self.loaded_transient_widgets = True

        super().set_property(name, value, push_undo=push_undo)

    def update(self):
        super().update()
        self._apply_mode(self.get_property(self.arg_setter_prop), push_undo=False)

    def _apply_mode(self, mode, push_undo=False, old_mode=None):
        # show/hide arg_params on change in EffectType/RequirementType
        if old_mode == mode:
            return
        new_params = self.arg_prop_map().get(mode)
        if new_params is None:
            return
        self.view.setVisible(False)

        if old_mode is not None:
            old_params = self.arg_prop_map()[old_mode]
            turn_off_params = list(set(old_params) - set(new_params))
            new_param_list = list(set(new_params) - set(old_params))
            new_params = {k: v for k, v in new_params.items() if k in new_param_list}
            for arg in turn_off_params:
                self.hide_prop_widget(arg, push_undo)
        for arg, prop in new_params.items():
            self.show_or_make_prop_widget(arg, prop, mode, push_undo)

        self.view.setVisible(True)
        if hasattr(self.view, "draw_node"):
            self.view.draw_node()
        elif hasattr(self.view, "update_size"):
            self.view.update_size()
        self.update_unnamed_cols(mode)
        self.old_effect = mode

    def reapply_arg_params(self):
        mode = self.get_property(self.arg_setter_prop)
        new_params = self.arg_prop_map().get(mode)
        for arg, prop in new_params.items():
            self.show_or_make_prop_widget(arg, prop, mode, True)

    def show_or_make_prop_widget(self, arg, prop_name, mode, push_undo):        # we wanna deprecate prop_name later
        widget_name = arg if arg not in self.widget_props else f'{arg}_arg'
        widget = self.get_widget(widget_name)
        if widget is None:
            widget = self.add_param_widget(widget_name, prop_name)
        else:
            self.show_widget(widget_name, push_undo)
        # widget.set_label(new_params[prop])
        current_val = widget.get_value()                     # get widget current value

        if current_val in ['', 0]:              # possible default
            arg_info = self.argument_info_map()[mode]['Arguments'][arg]
            preset_val = self.get_property('arg_params').get(widget_name)  # if player hasnt edited them, set to new default
            if preset_val is not None and preset_val not in ['', 0]:
                self.set_widget_and_prop(widget_name, preset_val)
                return
            default_val = arg_info['DefaultValue']
            if default_val is not None:                             # get default val for arg based on type
                arg_type = arg_info['ArgumentType']
                arg_type = arg_type if arg_type not in ['database', 'text', ''] else 'text'
                widget_accepted_types = widget.val_accept
                if isinstance(default_val, widget_accepted_types):
                    self.set_widget_and_prop(widget_name, default_val)
                else:
                    if isinstance(default_val, bool):
                        raise TypeError(f'transforming old param of type {widget_accepted_types} to new_param boolean'
                                        f'. arg: {arg}, mode: {mode}')
                    else:
                        # could not numberify string, try string convert to bool
                        casted_default = None
                        if isinstance(default_val, str):
                            casted_default = to_number(default_val)
                            if casted_default is None:
                                if arg_type == 'bool':
                                    if default_val.lower() in ['false', 'true']:
                                        casted_default = eval(default_val.capitalize())
                                    else:
                                        casted_default = False
                        if casted_default is None:
                            if arg_type in ['database', 'text', ''] and not isinstance(default_val, str):
                                casted_default = ''
                            elif arg_type in ['int', 'uint'] and not isinstance(default_val, int):
                                casted_default = 0
                            elif arg_type == 'float' and not isinstance(default_val, float):
                                casted_default = 0.0
                            elif isinstance(arg_type, float) and math.isnan(arg_type):
                                casted_default = 0
                    if isinstance(casted_default, widget_accepted_types):
                        self.set_widget_and_prop(widget_name, casted_default)

    def hide_prop_widget(self, arg, push_undo):
        widget_name = arg if arg not in self.widget_props else f'{arg}_arg'
        widget = self.get_widget(widget_name)
        if widget:
            self.hide_widget(widget_name, push_undo=push_undo)

    def add_param_widget(self, arg, prop):
        lower_prop = prop.lower()
        if 'text' in lower_prop or 'database' in lower_prop:
            self.add_custom_widget(ExpandingLineEdit(parent=self.view, label=arg, name=arg), tab='fields')
        elif 'bool' in lower_prop:
            self.set_bool_checkbox(arg, default_val=None, display_in_prop_bin=False)
        elif 'int' in lower_prop:
            self.add_custom_widget(IntSpinNodeWidget(arg, self.view), tab='fields')
        elif 'float' in lower_prop:
            self.add_custom_widget(FloatSpinNodeWidget(arg, self.view), tab='fields')
        else:
            raise Exception(f'unhandled arg {arg} with prop {prop}')
        self.get_property('arg_params')[arg] = None
        return self.get_widget(arg)

    def update_unnamed_cols(self, mode):      # will be overridden
        return

    def arg_prop_map(self):
        return {}

    def argument_info_map(self):
        return {}

    def migrate_extra_params(self):             # we should technically cover this anyways
        lazy_params = self.get_property('arg_params')
        custom_properties = self.model._custom_prop
        migrated_properties = {}
        for param, val in lazy_params.items():
            if param in custom_properties:
                lazy_params[param] = custom_properties[param]           # just insurance
                migrated_properties[param] = custom_properties[param]
                del custom_properties[param]
        return migrated_properties

    def restore_extra_params(self, migrated_properties):
        lazy_params = self.get_property('arg_params')
        for param, val in migrated_properties.items():
            self.create_property(param, val)

    def safe_set_widget_value(self, param, val):
        widget = self.get_widget(param)
        if widget is not None:
            widget_accepted_types = widget.val_accept
            if isinstance(val, widget_accepted_types):
                self.set_widget_and_prop(param, val)
            else:
                casted_val = None
                if isinstance(val, str):
                    casted_val = to_number(val)
                    if casted_val is None:
                        if widget.val_accept == bool:
                            if val in ['False', 'false', 'FALSE', 'True', 'true', 'True']:
                                casted_val = eval(val.capitalize())
                                self.set_widget_and_prop(param, casted_val)
                    else:
                        if widget.val_accept in [int, float]:
                            self.set_widget_and_prop(param, casted_val)
                elif isinstance(val, int):
                    # check if we can convert into str
                    casted_val = str(val)
                    if widget_accepted_types == str:
                        self.set_widget_and_prop(param, casted_val)
                if casted_val is None:
                    raise TypeError(f'could not find type for param:val {param}: {val}')

    def set_widget_and_prop(self, widget_name, value):
        widget = self.get_widget(widget_name)
        if widget:
            widget.set_value(value)
            self.get_property('arg_params')[widget_name] = value


class GameEffectNode(BaseEffectNode):
    __identifier__ = 'db.game_effects'
    NODE_NAME = 'CustomGameEffect'
    old_effect = None
    arg_setter_prop = 'EffectType'
    output_port_tables = {}

    def __init__(self):
        super().__init__()
        self.view.setVisible(False)
        self.create_property('table_name', value='GameEffectCustom')
        # fixed fields
        mod_spec = db_spec.node_templates['Modifiers']
        skipped_modifier_fields = ['SubjectRequirementSetId', 'OwnerRequirementSetId', 'ModifierType', 'ModifierId']
        show_even_with_defaults = ['Permanent', 'RunOnce']
        modifier_hidden_cols = [i for i in mod_spec.get('secondary_texts', [])
                                 if i not in skipped_modifier_fields and i not in show_even_with_defaults]

        self._extra_fields = modifier_hidden_cols

        # dynamicModifiers
        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label='ModifierId', name='ModifierId',
                                                 check_if_edited=True), tab='fields',
                               widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        modifier_arguments = list(db_spec.modifier_argument_info.keys())
        self.add_custom_widget(
            DropDownLineEdit(parent=self.view, label="EffectType",
                             name="EffectType", text=modifier_arguments[0],
                             suggestions=modifier_arguments),
            tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        self.set_search_menu(col='CollectionType', idx=0, col_poss_vals=['COLLECTION_PLAYER_CITIES', 'COLLECTION_OWNER'])
        self.create_property('ModifierType', '', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        self.output_port_tables['ModifierId'] = set_output_port_constraints(self, 'Modifiers',
                                                              SQLValidator.pk_ref_map.get('Modifiers'))
        self.output_port_tables['ModifierId'] = {k: v for k, v in self.output_port_tables['ModifierId'].items()
                                   if SQLValidator.class_table_name_map.get(k, k) not in effect_system_tables}
        reqset_connection_info = {'db.game_effects.RequirementEffectNode': ['ReqSet'],
                                  'db.table.requirementsets.RequirementsetsNode': ['ReqSet']}
        self.output_port_tables['SubjectReq'] = reqset_connection_info
        self.output_port_tables['OwnerReq'] = reqset_connection_info

        # Req Ports

        self.add_output('SubjectReq')
        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label='SubjectRequirementSetId', name='SubjectReq',
                                                 check_if_edited=True), tab='fields',
                               widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        # self.set_search_menu(col='SubjectReq', idx=0, col_poss_vals=[''] + db_possible_vals.get('Modifiers', {})['SubjectRequirementSetId']['vals'], validate=False)
        self.add_output('OwnerReq')
        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label='OwnerRequirementSetId', name='OwnerReq',
                                                 check_if_edited=True), tab='fields',
                               widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        #self.set_search_menu(col='OwnerRequirementSetId', idx=0, col_poss_vals=[''] + db_possible_vals.get('Modifiers', {})['OwnerRequirementSetId']['vals'], validate=False)

        for col in show_even_with_defaults:
            default_val = bool(int(mod_spec['default_values'].get(col, '0')))
            self.set_bool_checkbox(col, default_val=default_val)
        for col in modifier_hidden_cols:
            if col in mod_spec.get('mined_bools', {}):
                self.create_property(col, value=False, widget_type=NodePropWidgetEnum.QCHECK_BOX.value)
            else:
                col_type = SQLValidator.type_map['Modifiers'][col]
                if isinstance(col_type, bool):
                    self.create_property(col, None, widget_type=NodePropWidgetEnum.QCHECK_BOX.value)
                elif isinstance(col_type, int):
                    self.create_property(col, None, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
                else:               # should be SubjectStackLimit, OwnerStackLimit.WOULD BE SPINBOX but can accept null
                    self.create_property(col, value='', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        # ModifierStrings
        self.create_property('Text', value='', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        self.create_property('Context', value='', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        # ModifierMetadata. Only used for resource modifiers.

        self.widget_props = [i for i in self.properties()['custom']]
        self.create_property('RequirementSetDict', {'SubjectReq': {'type': 'REQUIREMENTSET_TEST_ALL', 'reqs': []},
                                                    'OwnerReq': {'type': 'REQUIREMENTSET_TEST_ALL', 'reqs': []}})
        self.create_property('arg_params', {},  widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
        self.view.setVisible(True)
        self._apply_mode(self.get_property(self.arg_setter_prop), push_undo=False)

    def get_link_port(self, connect_table, connect_port):    # uses custom ReqCustom and all Modifier attachment tables
        if connect_port is not None:
            for backlink_table in ['RequirementSets']:
                if backlink_table == self.get_property('table_name'):
                    backlink_spec = db_spec.node_templates[backlink_table]
                    fk_ports = [key for key, val in backlink_spec['foreign_keys'].items() if val == connect_table]
                    if len(fk_ports) > 1:
                        print(f'error multiple ports possible for connect!'
                              f' the connection was: {connect_table} -> {backlink_table}.'
                              f' defaulting to first option')
                    return fk_ports[0]

    def update_unnamed_cols(self, mode):        # change default names if not already named
        collection_type = self.get_property('CollectionType')
        short_collection = collection_type.replace('COLLECTION_', '')

        modifier_id_widget = self.get_widget('ModifierId')
        modifier_type_prop = self.get_property('ModifierType')
        subject_req_widget = self.get_widget('SubjectReq')
        owner_req_widget = self.get_widget('OwnerReq')

        new_modifier_id = f"{mode.replace('EFFECT_', '')}_ON_{short_collection}"
        modifier_id_updates = modifier_id_widget.update_from_state(new_modifier_id)
        if modifier_id_updates:
            new_modifier_type = f"{new_modifier_id}_TYPE"
            new_subject = f"{new_modifier_id}_SUBJECT_REQUIREMENTS"
            new_owner = f"{new_modifier_id}_OWNER_REQUIREMENTS"
            self.set_property('ModifierType', new_modifier_type)
            subject_req_widget.update_from_state(new_subject)
            owner_req_widget.update_from_state(new_owner)

    def arg_prop_map(self):
        return db_spec.mod_type_arg_map

    def argument_info_map(self):
        return db_spec.modifier_argument_info


class RequirementEffectNode(BaseEffectNode):
    __identifier__ = 'db.game_effects'
    NODE_NAME = 'CustomRequirement'
    old_effect = None

    arg_setter_prop = 'RequirementType'
    output_port_tables = {}

    def __init__(self):
        super().__init__()
        self.view.setVisible(False)
        self.create_property('table_name', value='ReqEffectCustom')

        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label='RequirementId', name='RequirementId'),
                               tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        reqs = list(db_spec.requirement_argument_info.keys())
        self.add_custom_widget(
            DropDownLineEdit(parent=self.view, label="RequirementType",
                             name="RequirementType", text=reqs[0],
                             suggestions=reqs),
            tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.add_input('ReqSet')
        self.create_property('ReqSet', '')

        self.widget_props = [i for i in self.properties()['custom']]
        self.create_property('arg_params', {}, widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
        self.view.setVisible(True)
        self._apply_mode(self.get_property(self.arg_setter_prop), push_undo=False)

    def get_link_port(self, connect_table, connect_port): # given an input port, finds the matching output on other node
        if connect_port is not None:
            return 'ReqSet'

    def update_unnamed_cols(self, mode):
        req_count = 1               # TODO used for discerning requirements in same set, set as 1 for now
        unique_req_type_count = 1   # TODO used for discerning requirements of same type, if not named usually
        req_id_widget = self.get_widget('RequirementId')
        if req_id_widget.get_value() == '':             # once hooked, shouldnt change, as could be used in multiple
            req_set = self.get_property('ReqSet')       # can we get connecting node?
            if req_set != '':
                new_req_id = f"{req_set}_{req_count}"
            else:                                                           # if not, name based on requirementType
                new_req_id = f'{mode}_{unique_req_type_count}'
            req_id_widget.set_value(new_req_id)

    def arg_prop_map(self):
        return db_spec.req_type_arg_map

    def argument_info_map(self):
        return db_spec.requirement_argument_info

def to_number(x):
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip()
        try:
            i = int(s)
            return i
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return