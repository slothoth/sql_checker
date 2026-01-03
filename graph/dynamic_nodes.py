from NodeGraphQt import BaseNode
from NodeGraphQt.constants import PortTypeEnum
from PyQt5 import QtCore, QtGui
import math
import time
from collections import defaultdict

from graph.db_spec_singleton import (db_spec, requirement_argument_info, requirement_system_tables, effect_system_tables,
                                     req_arg_type_list_map, req_all_param_arg_fields, modifier_argument_info,
                                     mod_arg_type_list_map, all_param_arg_fields)
from schema_generator import SQLValidator
from graph.custom_widgets import NodeSearchMenu, ToggleExtraButton, IntSpinNodeWidget, FloatSpinNodeWidget



class BasicDBNode(BaseNode):
    _extra_visible = False
    _initial_fields = []
    _extra_fields = []
    output_port_tables = {}

    def _toggle_extra(self):
        self._extra_visible = not self._extra_visible
        for col in self._extra_fields:
            if self._extra_visible:
                self.show_widget(col, push_undo=False)
            else:
                self.hide_widget(col, push_undo=False)

        btn = self.get_widget('toggle_extra')
        try:
            self.update()
        except Exception:
            pass

    def get_link_port(self, connect_table, connect_port): # given an input port, finds the matching output on other node
        connection_spec = db_spec.node_templates.get(connect_table, {})
        original_table = self.get_property('table_name')
        if connect_table == 'GameEffectCustom':
            if connect_port == 'ModifierId':
                return backlink_port_get(original_table, 'Modifiers')
            return 'ReqSet'  # needs more complicated behavior as ModifierId now also ports so could have any attach table
        if connect_port is not None:
            return backlink_port_get(original_table, connect_table)

    def set_input_port_constraint(self, port, fk_to_tbl_link, fk_to_pk_link):
        table_class = SQLValidator.table_name_class_map.get(fk_to_tbl_link, '')
        self.add_accept_port_type(port, {
            'node_type': table_class,
            'port_type': PortTypeEnum.OUT.value,
            'port_name': fk_to_pk_link,
        })
        base_table_name = self.get_property('table_name')
        if fk_to_tbl_link == 'Modifiers':
            if base_table_name not in effect_system_tables:
                self.add_accept_port_type(port, {
                    'node_type': 'db.game_effects.GameEffectNode',
                    'port_type': PortTypeEnum.OUT.value,
                    'port_name': fk_to_pk_link,
                })
        if fk_to_tbl_link == 'RequirementSets':
            if base_table_name not in requirement_system_tables:
                self.add_accept_port_type(port, {
                    'node_type': 'db.game_effects.RequirementEffectNode',
                    'port_type': PortTypeEnum.OUT.value,
                    'port_name': fk_to_pk_link,
                })

    def set_output_port_constraints(self, table_name, fk_backlink):
        pk = SQLValidator.pk_map[table_name][0]
        color = SQLValidator.port_color_map['output'].get(table_name, {}).get(pk)
        port = self.add_output(pk, color=color)
        # lets just set a property on each node that handles output port possibilities?
        # {'port1': [list]}
        port_outputs = defaultdict(list)
        for input_port, input_tbl_name_list in fk_backlink['col_first'].items():
            for input_tbl_name in input_tbl_name_list:
                table_class = SQLValidator.table_name_class_map.get(input_tbl_name, '')
                port_outputs[table_class].append(input_port)

        self.output_port_tables = port_outputs

    def set_spec(self, col_dict):
        for col_name, value in col_dict.items():
            if value is not None and value != 'NULL':
                widget = self.get_widget(col_name)
                if widget:
                    current_val = self.get_property(col_name)
                    if 'CheckBox' in type(widget).__name__:
                        if isinstance(value, str):
                            value = int(value)
                        value = True if value != 0 else False
                    if 'LineEdit' in type(widget).__name__:
                        if not isinstance(value, str):
                            value = str(value)
                    widget.set_value(value)

    def set_search_menu(self, col, idx, col_poss_vals, validate=False):
        self.create_property(
            col,
            value=col_poss_vals[0] if col_poss_vals else None,
            items=col_poss_vals or [],
            widget_type='SEARCH_MENU',
            widget_tooltip=None,
            tab='fields'
        )
        widget = NodeSearchMenu(self.view, col, pad_label(index_label(idx, col)), col_poss_vals)
        widget.setToolTip('')

        self.view.add_widget(widget)
        self.view.draw_node()

    def search_menu_on_value_changed(self, k, v):
        self.set_property(k, v)

    def set_bool_checkbox(self, col, idx=0, default_val=None):
        is_default_on = default_val is not None and int(default_val) == 1
        self.add_checkbox(col, label=pad_label(index_label(idx, col)), state=is_default_on)
        cb = self.get_widget(col).get_custom_widget()
        cb.setMinimumHeight(24)
        cb.setStyleSheet("QCheckBox { padding-top: 2px; }")

    def set_text_input(self, col, idx=0, default_val=None):
        lab = pad_label(index_label(idx, col))
        self.add_text_input(name=col, label=lab, text=str(default_val or ''), tab='fields')
        text_widget = self.get_widget(col)
        text_widget.get_custom_widget().setMinimumHeight(24)


class DynamicNode(BasicDBNode):
    _validation_errors = {}  # Track validation errors for each field

    def _validate_field(self, field_name, field_value):
        """
        Validate a single field and update its visual state.

        Args:
            field_name: Name of the field to validate
            field_value: Value to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not hasattr(self, 'NODE_NAME'):
            return True

        table_name = self.get_property('table_name')

        # Get all current field values for context
        all_data = {}
        for col in self._initial_fields + self._extra_fields:
            widget = self.get_widget(col)
            if widget:
                try:
                    val = widget.get_value()
                    if val is not None and val != '':
                        all_data[col] = val
                except:
                    pass

        is_valid, error_msg = SQLValidator.validate_field(table_name, field_name, field_value, all_data)

        if is_valid:
            self._validation_errors.pop(field_name, None)
        else:
            self._validation_errors[field_name] = error_msg

        self._update_field_style(field_name, is_valid)

        return is_valid

    def _update_field_style(self, field_name, is_valid):
        """
        Update the visual style of a field widget based on validation state.

        Args:
            field_name: Name of the field
            is_valid: Whether the field is valid
        """
        widget = self.get_widget(field_name)
        if not widget:
            return

        qt_widget = None
        if hasattr(widget, 'get_custom_widget'):
            qt_widget = widget.get_custom_widget()
        elif hasattr(widget, 'widget'):
            qt_widget = widget.widget

        # For NodeSearchMenu, we need to style the button
        if 'SearchMenu' in type(widget).__name__:
            qt_widget = widget.get_custom_widget() if hasattr(widget, 'get_custom_widget') else None

        if qt_widget is None:
            return

        # Set background color based on validation state
        if is_valid:
            current_style = qt_widget.styleSheet() or ""         # Reset to default (white/transparent)
            # Remove red background but keep other styles
            new_style = current_style.replace("background-color: #ffcccc;", "").strip()
            qt_widget.setStyleSheet(new_style if new_style else "")
        else:
            current_style = qt_widget.styleSheet() or ""        # Set red background for invalid fields
            if "background-color: #ffcccc;" not in current_style:
                new_style = current_style + ("; " if current_style else "") + "background-color: #ffcccc;"
                qt_widget.setStyleSheet(new_style)

    def _validate_all_fields(self):
        """Validate all fields in the node."""
        for col in self._initial_fields + self._extra_fields:
            widget = self.get_widget(col)
            if widget:
                try:
                    value = widget.get_value()
                    self._validate_field(col, value)
                except:
                    pass

    def set_search_menu(self, col, idx, col_poss_vals, validate=False):

        self.create_property(
            col,
            value=col_poss_vals[0] if col_poss_vals else None,
            items=col_poss_vals or [],
            widget_type='SEARCH_MENU',
            widget_tooltip=None,
            tab='fields'
        )
        widget = NodeSearchMenu(self.view, col, pad_label(index_label(idx, col)), col_poss_vals)
        widget.setToolTip('')

        # Connect validation to value changes

        if validate:
            widget.value_changed.connect(self.search_menu_on_value_changed)
        self.view.add_widget(widget)
        self.view.draw_node()

        search_menu_widget = self.get_widget(col)
        if search_menu_widget:
            if validate:
                self.setup_validate(search_menu_widget, col)

    def search_menu_on_value_changed(self, k, v):
        self.set_property(k, v)
        self._validate_field(k, v)


# had to auto generate classes rather then generate at node instantition because
# on save they werent storing their properties in such a way they could be loaded again
def create_table_node_class(table_name, graph):
    class_name = f"{table_name.title().replace('_', '')}Node"

    def init_method(self):
        super(type(self), self).__init__()
        start_time = time.time()
        self.view.setVisible(False)
        primary_keys = SQLValidator.pk_map[table_name]
        prim_texts = [i for i in SQLValidator.required_map[table_name] if i not in primary_keys]
        second_texts = SQLValidator.less_important_map[table_name]

        self._initial_fields = primary_keys + prim_texts
        self._extra_fields = second_texts
        self.create_property('table_name', value=table_name)

        toggle = ToggleExtraButton(self.view)
        toggle._btn.clicked.connect(self._toggle_extra)
        self.add_custom_widget(toggle, tab=None)

        age = graph.property('meta').get('Age')
        if age == 'ALWAYS':
            self._possible_vals = db_spec.all_possible_vals.get(table_name, {})
        else:
            self._possible_vals = db_spec.possible_vals.get(age, {}).get(table_name, {})

        # override for RequirementSet becausse needs output TODO we now know we can change this to have input
        if table_name == 'RequirementSets':
            self.add_input('RequirementSetId')

        cols_ordered = primary_keys + prim_texts + second_texts
        default_map = SQLValidator.default_map.get(table_name, {})
        fk_to_tbl_map = SQLValidator.fk_to_tbl_map.get(table_name, {})
        fk_to_pk_map = SQLValidator.fk_to_pk_map.get(table_name, {})
        require_map = SQLValidator.required_map.get(table_name, {})

        for idx, col in enumerate(cols_ordered):
            default_val = default_map.get(col, None)
            fk_to_tbl_link = fk_to_tbl_map.get(col, None)
            fk_to_pk_link = fk_to_pk_map.get(col, None)
            is_required = require_map.get(col, None)
            if fk_to_pk_link is not None:
                color = SQLValidator.port_color_map['input'].get(table_name, {}).get(col)
                if is_required is not None:
                    port = self.add_input(col, color=color)
                else:
                    port = self.add_input(col, painter_func=draw_square_port, color=color)
                self.set_input_port_constraint(port, fk_to_tbl_link, fk_to_pk_link)

            col_poss_vals = self._possible_vals.get(col, None)
            col_type = SQLValidator.type_map[table_name][col]
            if isinstance(col_type, bool):
                self.set_bool_checkbox(col, idx, default_val)
            elif isinstance(col_type, int):
                self.add_custom_widget(IntSpinNodeWidget(col, self.view), tab='Node')
            elif col_poss_vals is not None:
                self.set_search_menu(col=col, idx=idx, col_poss_vals=[''] + col_poss_vals['vals'])
            else:
                self.set_text_input(col, idx, default_val)

            if col in self._extra_fields:
                self.hide_widget(col, push_undo=False)

        # Validate all fields after initialization
        self._validate_all_fields()

        fk_backlink = SQLValidator.pk_ref_map.get(table_name)
        if fk_backlink is not None:
            self.set_output_port_constraints(table_name, fk_backlink)

        if len(self._extra_fields) == 0:
            btn = self.get_widget('toggle_extra')
            btn.hide()
        self.view.setVisible(True)
        end_time = time.time()
        print(f'Full Dynamic Node time: {end_time - start_time}')

    def set_defaults_method(self):
        self.set_property('table_name', table_name)
        for column_name in self._spec['all_cols']:
            default_val = self._spec.get("default_values", {}).get(column_name, '')
            self.set_property(column_name, default_val)

    NewClass = type(class_name, (DynamicNode,), {
        '__identifier__': f'db.table.{table_name.lower()}',
        'NODE_NAME': f"{table_name}",
        'set_defaults': set_defaults_method,
        '__init__': init_method,
    })
    return NewClass


def generate_tables(graph):
    all_custom_nodes = []
    for name in SQLValidator.Base.metadata.tables:
        NodeClass = create_table_node_class(name, graph)
        all_custom_nodes.append(NodeClass)
    return all_custom_nodes


class BaseEffectNode(BasicDBNode):
    arg_setter_prop = None

    def set_property(self, name, value, push_undo=True):
        if name == self.arg_setter_prop and self.get_property(self.arg_setter_prop) != value and self.graph:
            self.graph.begin_undo("change mode")
            super().set_property(name, value, push_undo=True)
            self._apply_mode(value, push_undo=True, old_mode=self.old_effect)
            self.graph.end_undo()
            return

        super().set_property(name, value, push_undo=push_undo)

    def update(self):
        super().update()
        self._apply_mode(self.get_property(self.arg_setter_prop), push_undo=False)

    def _apply_mode(self, mode, push_undo=False, old_mode=None):
        # show/hide arg_params on change in EffectType/RequirementType
        if old_mode == mode:
            return
        self.view.setVisible(False)
        new_params = self.arg_prop_map()[mode]
        if old_mode is not None:
            old_params = self.arg_prop_map()[old_mode]
            turn_off_params = list(set(old_params) - set(new_params))
            turn_on_params = list(set(new_params) - set(old_params))
            for prop in turn_off_params:
                self.hide_prop_widget(prop, mode, push_undo)
            for prop in turn_on_params:
                self.show_or_make_prop_widget(prop, new_params, mode, push_undo)
        else:
            for prop in new_params:
                self.show_or_make_prop_widget(prop, new_params, mode, push_undo)
        prop_change_time = time.time()
        self.view.setVisible(True)
        self.update_unnamed_cols(mode)
        self.old_effect = mode

    def show_or_make_prop_widget(self, prop, new_params, mode, push_undo):
        widget = self.get_widget(prop)
        if widget is None:
            widget = self.add_param_widget(prop)
        else:
            self.show_widget(prop, push_undo)
        widget.set_label(new_params[prop])
        current_val = widget.get_value()                     # get widget current value

        if current_val == '' or current_val == 0:           # if player hasnt edited them, set to new default
            arg_name = self.arg_prop_map()[mode][prop]
            arg_info = self.argument_info_map()[mode]['Arguments'][arg_name]
            default_val = arg_info['DefaultValue']
            if default_val is not None:                             # get default val for arg based on type
                arg_type = arg_info['ArgumentType']
                if arg_type == 'bool' and not isinstance(default_val, bool):
                    if default_val.lower() in ['false', 'true']:
                        default_val = eval(default_val.capitalize())
                    else:
                        default_val = False

                elif arg_type in ['database', 'text', ''] and not isinstance(default_val, str):
                    default_val = ''
                elif arg_type in ['int', 'uint'] and not isinstance(default_val, int):
                    default_val = 0
                elif arg_type == 'float' and not isinstance(default_val, float):
                    default_val = 0.0
                elif isinstance(arg_type, float) and math.isnan(arg_type):
                    default_val = ''

                widget.set_value(default_val)

    def hide_prop_widget(self, prop, mode, push_undo):
        widget = self.get_widget(prop)
        self.hide_widget(prop, push_undo=push_undo)

    def add_param_widget(self, prop):

        lower_prop = prop.lower()
        if 'text' in lower_prop or 'database' in lower_prop:
            self.add_text_input(lower_prop, label=lower_prop, text="")
        elif 'bool' in lower_prop:
            self.add_checkbox(lower_prop, label=lower_prop)
        elif 'int' in lower_prop:
            self.add_custom_widget(IntSpinNodeWidget(lower_prop, self.view), tab='Node')
        elif 'float' in lower_prop:
            self.add_custom_widget(FloatSpinNodeWidget(lower_prop, self.view), tab='Node')
        else:
            raise Exception(f'unhandled prop {prop}')
        return self.get_widget(prop)

    def arg_prop_map(self):
        return {}

    def argument_info_map(self):
        return {}


class GameEffectNode(BaseEffectNode):
    __identifier__ = 'db.game_effects'
    NODE_NAME = 'CustomGameEffect'
    old_effect = None
    arg_setter_prop = 'EffectType'

    def __init__(self):
        start_time = time.time()
        super().__init__()
        self.view.setVisible(False)
        self.create_property('table_name', value='GameEffectCustom')
        # fixed fields
        mod_spec = db_spec.node_templates['Modifiers']
        skipped_modifier_fields = ['SubjectRequirementSetId', 'OwnerRequirementSetId', 'ModifierType', 'ModifierId']
        modifier_fields = [i for i in mod_spec.get('primary_texts', []) if i not in skipped_modifier_fields]
        modifier_extra_fields = [i for i in mod_spec.get('secondary_texts', []) if i not in skipped_modifier_fields]
        modifier_fields = modifier_fields + modifier_extra_fields

        self._extra_fields = modifier_extra_fields

        # dynamicModifiers
        self.add_text_input('ModifierId', 'ModifierId', tab='fields')
        self.add_output('ModifierId')
        self.add_combo_menu( "EffectType", label="EffectType", items=list(modifier_argument_info.keys()))
        self.set_search_menu(col='CollectionType', idx=0, col_poss_vals=['COLLECTION_PLAYER_CITIES', 'COLLECTION_OWNER'])
        self.create_property('ModifierType', '')
        # Req Ports

        self.add_output('SubjectReq')
        self.add_text_input('SubjectReq', 'SubjectRequirementSetId', tab='fields')
        # self.set_search_menu(col='SubjectReq', idx=0, col_poss_vals=[''] + db_possible_vals.get('Modifiers', {})['SubjectRequirementSetId']['vals'], validate=False)

        self.add_output('OwnerReq')
        self.add_text_input('OwnerReq', 'OwnerRequirementSetId', tab='fields')
        #self.set_search_menu(col='OwnerRequirementSetId', idx=0, col_poss_vals=[''] + db_possible_vals.get('Modifiers', {})['OwnerRequirementSetId']['vals'], validate=False)

        for col in modifier_fields:
            if col in mod_spec.get('mined_bools', {}):
                self.set_bool_checkbox(col)
            else:
                self.set_text_input(col)

            if col in modifier_extra_fields:
                self.hide_widget(col, push_undo=False)

        # ModifierStrings
        self.add_text_input('Text', 'Text', tab='fields')
        self.add_text_input('Context', 'Context', tab='fields')

        # ModifierMetadata. Only used for resource modifiers.

        toggle = ToggleExtraButton(self.view)
        toggle._btn.clicked.connect(self._toggle_extra)
        self.add_custom_widget(toggle, tab=None)

        # new logic
        lazy_arg_params = [prop for prop in all_param_arg_fields]
        self.create_property('arg_params', lazy_arg_params)
        self.view.setVisible(True)
        self._apply_mode(self.get_property("EffectType"), push_undo=False)
        finished_time = time.time()
        print(f'Full Node time: {finished_time - start_time}')

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

    def update_unnamed_cols(self, mode):
        # change default names if not already named
        # ModifierId, ModifierType, SubjectReqSetId, OwnerReqSetId
        collection_type = self.get_property('CollectionType')
        current_modifier_id = self.get_property('ModifierId')

        short_collection = collection_type.replace('COLLECTION_', '')
        # needs to have numbers to deal with plurality of types
        old_modifier_id_default, old_modifier_type_default, old_subject_default, old_owner_default = '', '', '', ''
        if self.old_effect is not None:
            # if has old effect, could have old default. only change if is that default
            old_modifier_id_default = f"{self.old_effect.replace('EFFECT_', '')}_ON_{short_collection}"
            old_modifier_type_default = f"{old_modifier_id_default}_TYPE"
            old_subject_default = f"{old_modifier_id_default}_SUBJECT_REQUIREMENTS"
            old_owner_default = f"{old_modifier_id_default}_OWNER_REQUIREMENTS"

        new_modifier_id = f"{mode.replace('EFFECT_', '')}_ON_{short_collection}"
        new_modifier_type = f"{new_modifier_id}_TYPE"
        new_subject = f"{new_modifier_id}_SUBJECT_REQUIREMENTS"
        new_owner = f"{new_modifier_id}_OWNER_REQUIREMENTS"

        current_modifier_type = self.get_property('ModifierType')
        subject_widget = self.get_widget('SubjectReq')
        owner_widget = self.get_widget('OwnerReq')

        if old_modifier_type_default in [current_modifier_type, '']:
            self.set_property('ModifierType', new_modifier_type)

        if current_modifier_id in [old_modifier_id_default, '']:
            self.get_widget('ModifierId').set_value(new_modifier_id)

        if subject_widget.get_value() in [old_subject_default, '']:
            subject_widget.set_value(new_subject)

        if owner_widget.get_value() in [old_owner_default, '']:
            owner_widget.set_value(new_owner)

    def arg_prop_map(self):
        return mod_arg_type_list_map

    def argument_info_map(self):
        return modifier_argument_info


class RequirementEffectNode(BaseEffectNode):
    __identifier__ = 'db.game_effects'
    NODE_NAME = 'CustomRequirement'
    old_effect = None

    arg_setter_prop = 'RequirementType'

    def __init__(self):
        super().__init__()
        self.view.setVisible(False)
        self.create_property('table_name', value='ReqEffectCustom')

        self.add_text_input('RequirementId', 'RequirementId', tab='fields')
        self.set_search_menu(col='RequirementType', idx=0,
                        col_poss_vals= list(requirement_argument_info.keys()),
                        validate=False)

        self.add_input('ReqSet')
        self.create_property('ReqSet', '')

        lazy_arg_params = [prop for prop in req_all_param_arg_fields]
        self.create_property('arg_params', lazy_arg_params)
        self.view.setVisible(True)
        self._apply_mode(self.get_property("RequirementType"), push_undo=False)


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
        return req_arg_type_list_map

    def argument_info_map(self):
        return requirement_argument_info


# helper functions

def pad_label(text, width=20):
    return text.ljust(width)


def index_label(order, text):
    PREFIX = '\u200B\u200B'   # Toxic Zero White Space character to order labels with numbers without those showing
    label = PREFIX * order + text
    return label


def draw_square_port(painter, rect, info):
    """
    Custom paint function for drawing a Square shaped port.

    Args:
        painter (QtGui.QPainter): painter object.
        rect (QtCore.QRectF): port rect used to describe parameters
                              needed to draw.
        info (dict): information describing the ports current state.
            {
                'port_type': 'in',
                'color': (0, 0, 0),
                'border_color': (255, 255, 255),
                'multi_connection': False,
                'connected': False,
                'hovered': False,
            }
    """
    painter.save()
    if info['hovered']:                         # mouse over port color.
        color = QtGui.QColor(14, 45, 59)
        border_color = QtGui.QColor(136, 255, 35, 255)
    elif info['connected']:                     # port connected color.
        color = QtGui.QColor(195, 60, 60)
        border_color = QtGui.QColor(200, 130, 70)
    else:                                       # default port color
        color = QtGui.QColor(*info['color'])
        border_color = QtGui.QColor(*info['border_color'])

    pen = QtGui.QPen(border_color, 1.8)
    pen.setJoinStyle(QtCore.Qt.MiterJoin)
    painter.setPen(pen)
    painter.setBrush(color)
    painter.drawRect(rect)
    painter.restore()


def backlink_port_get(original_table, connect_table):
    backlink_spec = db_spec.node_templates[original_table]
    combined_fks = backlink_spec['foreign_keys'].copy()
    combined_fks.update(backlink_spec.get('extra_fks', {}))
    fk_ports = [key for key, val in combined_fks.items() if
                val == connect_table or (isinstance(val, dict) and val.get('ref_table') == connect_table)]
    if len(fk_ports) > 1:
        print(f'error multiple ports possible for connect!'
              f' the connection was: {connect_table} -> {original_table}.'
              f' defaulting to first option')
    return fk_ports[0]
