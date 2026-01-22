from NodeGraphQt.constants import NodePropWidgetEnum, PortTypeEnum

from graph.singletons.db_spec_singleton import db_spec
from constants import effect_system_tables
from schema_generator import SQLValidator
from graph.custom_widgets import IntSpinNodeWidget, FloatSpinNodeWidget, ExpandingLineEdit, DropDownLineEdit
from graph.nodes.base_nodes import BasicDBNode, set_output_port_constraints

from graph.transform_json_to_sql import effect_custom_transform, req_custom_transform


import logging

log = logging.getLogger(__name__)

max_db_mod_arg = max(len([val for key, val in v.items() if val == 'database'])
                     for k, v in db_spec.mod_type_arg_map.items())

max_db_req_arg = max(len([val for key, val in v.items() if val == 'database'])
                     for k, v in db_spec.req_type_arg_map.items())


class BaseEffectNode(BasicDBNode):
    arg_setter_prop = None
    widget_props = []
    argument_info_map = {}
    arg_prop_map = {}
    database_arg_map = {}
    reserved_inputs = {}
    arg_inputs_set = {}

    def __init__(self):
        super().__init__()
        self.set_port_deletion_allowed(True)

    def set_property(self, name, value, push_undo=True):
        if name == self.arg_setter_prop:
            if self.graph is not None and self.get_property(self.arg_setter_prop) != value:
                self.graph.begin_undo("change mode")
                super().set_property(name=name, value=value, push_undo=True)
                self._apply_mode(value, push_undo=True, old_mode=self.old_effect)
                self.graph.end_undo()
                return

        if name in self.get_property('arg_params') and self.graph is not None:
            self.get_property('arg_params')[name] = value
            print(f'name: {name} value: {value}')
            arg_info = self.argument_info_map[self.get_property(self.arg_setter_prop)]['Arguments'][name]
            if arg_info.get('MinedNeeded', False):
                if self.arg_prop_map[self.get_property(self.arg_setter_prop)][name] in ['database', 'text']:
                    self._update_field_style(name, value != '')

        super().set_property(name, value, push_undo=push_undo)
        if self.can_validate and name not in {'sql_form', 'loc_sql_form', 'dict_form_list'}:      # prevents looping
            sql_code, dict_form_list, loc = self.convert_to_sql()
            super().set_property('sql_form', sql_code)
            super().set_property('dict_sql', dict_form_list)

    def update(self):
        self._apply_mode(self.get_property(self.arg_setter_prop), push_undo=False)
        super().update()

    def _apply_mode(self, mode, push_undo=False, old_mode=None):
        # show/hide arg_params on change in EffectType/RequirementType
        if old_mode == mode:
            return
        new_params = self.arg_prop_map.get(mode)
        if new_params is None:
            return
        self.view.setVisible(False)

        if old_mode is not None:
            old_params = self.arg_prop_map[old_mode]
            turn_off_params = list(set(old_params) - set(new_params))
            new_param_list = list(set(new_params) - set(old_params))
            new_params = {k: v for k, v in new_params.items() if k in new_param_list}
            for arg in turn_off_params:
                self.hide_prop_widget(arg, push_undo)
        for arg, prop_type in new_params.items():
            self.show_or_make_prop_widget(arg, prop_type, mode, push_undo)

        self.view.setVisible(True)
        if hasattr(self.view, "draw_node"):
            self.view.draw_node()
        elif hasattr(self.view, "update_size"):
            self.view.update_size()
        self.update_unnamed_cols(mode)
        self._update_ports(mode)
        self.old_effect = mode

    def reapply_arg_params(self):
        mode = self.get_property(self.arg_setter_prop)
        new_params = self.arg_prop_map.get(mode)
        for arg, prop in new_params.items():
            self.show_or_make_prop_widget(arg, prop, mode, True)

    def show_or_make_prop_widget(self, arg, prop_type, mode, push_undo):
        widget_name = arg if arg not in self.widget_props else f'{arg}_arg'
        widget = self.get_widget(widget_name)
        arg_info = self.argument_info_map[mode]['Arguments'][arg]
        default_val = arg_info['DefaultValue']
        preset_val = self.get_property('arg_params').get(widget_name)
        if widget is None:
            widget = self.add_param_widget(widget_name, prop_type)
            initial_value = widget.get_value()
            if preset_val is not None:
                widget.set_value(preset_val)
            else:
                if initial_value != default_val and default_val is not None:
                    self.set_widget_and_prop(widget_name, default_val)

        else:
            self.show_widget(widget_name, push_undo)
            current_val = widget.get_value()
            if preset_val is not None:
                widget.set_value(preset_val)

    def hide_prop_widget(self, arg, push_undo):
        widget_name = arg if arg not in self.widget_props else f'{arg}_arg'
        widget = self.get_widget(widget_name)
        if widget:
            self.hide_widget(widget_name, push_undo=push_undo)

    def add_param_widget(self, arg, prop_type):
        if prop_type == 'text':
            self.add_custom_widget(ExpandingLineEdit(parent=self.view, label=arg, name=arg), tab='fields')
        elif prop_type == 'database':
            # get db type and use dropdownlinedit database_arg_map
            arg_table = self.get_param_arg_table(arg)

            base_vals = db_spec.possible_vals[self.graph.property('meta')['Age']].get(arg_table, {}).get('_PK_VALS') or []

            self.add_custom_widget(DropDownLineEdit(parent=self.view, label=arg, name=arg, text='',
                                                    suggestions=base_vals), tab='fields')
            widget = self.get_widget(arg)
            self.graph.suggest_hub.add_custom_watch(arg_table, widget)
        elif prop_type == 'bool':
            self.set_bool_checkbox(arg, default_val=None, display_in_prop_bin=False)
        elif prop_type == 'int':
            self.add_custom_widget(IntSpinNodeWidget(arg, self.view), tab='fields')
        elif prop_type == 'float':
            self.add_custom_widget(FloatSpinNodeWidget(arg, self.view), tab='fields')
        else:
            raise Exception(f'unhandled arg {arg} with prop {prop_type}')
        if arg not in self.get_property('arg_params'):
            self.get_property('arg_params')[arg] = None
        return self.get_widget(arg)

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

    def set_widget_and_prop(self, widget_name, value):
        widget = self.get_widget(widget_name)
        if widget:
            widget.set_value(value)
            self.get_property('arg_params')[widget_name] = value

    def finalize_deserialize(self):
        mode = self.get_property(self.arg_setter_prop)
        self._apply_mode(mode, push_undo=False, old_mode=None)
        self.reapply_arg_params()
        if hasattr(self.view, "draw_node"):
            self.view.draw_node()

    def get_param_arg_table(self, arg):
        arg_table = self.database_arg_map.get(arg)
        if arg_table is None:
            arg_table = self.database_arg_map[arg.replace('_arg', '')]
        return arg_table

    def _update_ports(self, effect_type):
        arg_table = self.arg_prop_map[effect_type]
        new_ports = [k for k, v in arg_table.items() if v == 'database']
        old_ports = {k: v for k, v in self.inputs().items() if k not in self.reserved_inputs}
        remove_ports = {k: v for k, v in old_ports.items() if k not in new_ports}
        add_ports = [name for name in new_ports if name not in old_ports]

        for name, port in remove_ports.items():
            port.clear_connections()  # clear connections so dont error as painter of line finds connection if no node
            self.delete_input(name)
        for name in add_ports:
            made_port = self.add_input(name)
            output_table = self.database_arg_map[name]
            table_class = SQLValidator.table_name_class_map[output_table]
            table_pk_output = SQLValidator.pk_map[output_table][0]
            self.add_accept_port_type(made_port, {
                'node_type': table_class,
                'port_type': PortTypeEnum.OUT.value,
                'port_name': table_pk_output,
            })

    def update_unnamed_cols(self, mode):      # will be overridden
        return

    def convert_to_sql(self):
        return [], {}, ''           # sql_list, dict form, loc


class GameEffectNode(BaseEffectNode):
    __identifier__ = 'db.game_effects'
    NODE_NAME = 'CustomGameEffect'
    argument_info_map = db_spec.modifier_argument_info
    arg_prop_map = db_spec.mod_type_arg_map
    database_arg_map = db_spec.mod_arg_database_types

    def __init__(self):
        super().__init__()
        self.old_effect = None
        self.arg_setter_prop = 'EffectType'
        self.output_port_tables = {}
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
                             name="EffectType", text='',
                             suggestions=modifier_arguments),
            tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        self.add_custom_widget(
            DropDownLineEdit(parent=self.view, label="CollectionType",
                             name="CollectionType", text='',
                             suggestions=db_spec.collections_list),
            tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        self.create_property('ModifierType', '', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        self.output_port_tables['ModifierId'] = set_output_port_constraints(self, 'Modifiers',
                                                              SQLValidator.pk_ref_map.get('Modifiers'))
        self.output_port_tables['ModifierId'] = {k: v for k, v in self.output_port_tables['ModifierId'].items()if SQLValidator.class_table_name_map.get(k, k) not in effect_system_tables}
        reqset_connection_info = {'db.game_effects.RequirementEffectNode': ['ReqSet'],
                                  'db.table.requirementsets.RequirementsetsNode': ['ReqSet']}
        self.output_port_tables['SubjectReq'] = reqset_connection_info
        self.output_port_tables['OwnerReq'] = reqset_connection_info

        # Req Ports

        self.add_output('SubjectReq')
        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label='SubjectRequirementSetId', name='SubjectReq',
                                                 check_if_edited=True), tab='fields',
                               widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        self.add_output('OwnerReq')
        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label='OwnerRequirementSetId', name='OwnerReq',
                                                 check_if_edited=True), tab='fields',
                               widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

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
        # skipping ModifierMetadata. Only used for resource modifiers.

        self.widget_props = [i for i in self.properties()['custom']]
        self.create_property('RequirementSetDict', {'SubjectReq': {'type': 'REQUIREMENTSET_TEST_ALL', 'reqs': []},
                                                    'OwnerReq': {'type': 'REQUIREMENTSET_TEST_ALL', 'reqs': []}})
        self.create_property('arg_params', {},  widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
        self.view.setVisible(True)
        self.reserved_inputs = self.inputs()
        self._apply_mode(self.get_property(self.arg_setter_prop), push_undo=False)
        self.can_validate = True

    def get_link_port(self, connect_table, connect_port):    # uses custom ReqCustom and all Modifier attachment tables
        if connect_port is not None:
            for backlink_table in ['RequirementSets']:
                if backlink_table == self.get_property('table_name'):
                    backlink_spec = db_spec.node_templates[backlink_table]
                    fk_ports = [key for key, val in backlink_spec['foreign_keys'].items() if val == connect_table]
                    if len(fk_ports) > 1:
                        log.error(f'when connecting backlink ports (for mod import): there were multiple ports possible'
                                  f' for connection: {connect_table} -> {backlink_table}. possible ports: {fk_ports}')
                    return fk_ports[0]

    def update_unnamed_cols(self, mode):        # change default names if not already named
        collection_type = self.get_property('CollectionType')
        short_collection = collection_type.replace('COLLECTION_', '')

        modifier_id_widget = self.get_widget('ModifierId')
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

    def convert_to_sql(self):
        custom_properties = self.get_properties_to_sql()
        sql_code, dict_form_list, error_string = [], [], ''
        node_id = self.id
        sql_code, dict_form_list, error_string = effect_custom_transform(custom_properties, node_id,
                                                                     sql_code, dict_form_list, error_string)
        return sql_code, dict_form_list, ''



class RequirementEffectNode(BaseEffectNode):
    __identifier__ = 'db.game_effects'
    NODE_NAME = 'CustomRequirement'
    argument_info_map = db_spec.requirement_argument_info
    arg_prop_map = db_spec.req_type_arg_map
    database_arg_map = db_spec.req_arg_database_types

    def __init__(self):
        super().__init__()
        self.old_effect = None
        self.arg_setter_prop = 'RequirementType'
        self.output_port_tables = {}

        self.view.setVisible(False)
        self.create_property('table_name', value='ReqEffectCustom')

        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label='RequirementId', name='RequirementId',
                                                 check_if_edited=True),
                               tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        reqs = list(db_spec.requirement_argument_info.keys())
        self.add_custom_widget(
            DropDownLineEdit(parent=self.view, label="RequirementType",
                             name="RequirementType", text='',
                             suggestions=reqs),
            tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)

        self.add_input('ReqSet')
        self.create_property('ReqSet', '')

        self.widget_props = [i for i in self.properties()['custom']]
        self.create_property('arg_params', {}, widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
        self.view.setVisible(True)
        self.reserved_inputs = self.inputs()
        self._apply_mode(self.get_property(self.arg_setter_prop), push_undo=False)
        self.can_validate = True

    def get_link_port(self, connect_table, connect_port): # given an input port, finds the matching output on other node
        if connect_port is not None:
            return 'ReqSet'

    def update_unnamed_cols(self, mode):
        req_count = 1               # TODO used for discerning requirements in same set, set as 1 for now
        unique_req_type_count = 1   # TODO used for discerning requirements of same type, if not named usually
        req_id_widget = self.get_widget('RequirementId')
        user_edited = req_id_widget.line_edit.user_edited
        if not user_edited:             # once hooked, shouldnt change, as could be used in multiple
            req_set = self.get_property('ReqSet')
            if req_set != '':
                new_req_id = f"{req_set}_{req_count}"
            else:                                                           # if not, name based on requirementType
                new_req_id = f'{mode}_{unique_req_type_count}'
            req_id_widget.set_value(new_req_id)

    def convert_to_sql(self):
        custom_properties = self.get_properties_to_sql()
        sql_code, dict_form_list, error_string = [], [], ''
        node_id = self.id
        sql_code, dict_form_list, error_string = req_custom_transform(custom_properties, node_id,
                                                                      sql_code, dict_form_list, error_string)
        return sql_code, dict_form_list, ''
