from collections import defaultdict
from NodeGraphQt import BaseNode
from NodeGraphQt.constants import PortTypeEnum, NodePropWidgetEnum


from graph.db_spec_singleton import db_spec, effect_system_tables, requirement_system_tables
from schema_generator import SQLValidator
from graph.custom_widgets import ExpandingLineEdit, BoolCheckNodeWidget

import logging

log = logging.getLogger(__name__)


class BasicDBNode(BaseNode):

    def __init__(self):
        super().__init__()
        self._extra_visible = False
        self._initial_fields = []
        self._extra_fields = []
        self.output_port_tables = {}
        self.test_error = False
        self.can_validate = False
        self._default_color = self.color()
        self.create_property('sql_form', '') # skipping widget type, as causes weirdness when editing other node vals
        self.create_property('loc_sql_form', '')    # in propBin Widget
        self.create_property('dict_sql', {})        # would be , widget_type=NodePropWidgetEnum.QTEXT_EDIT.value

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

    def set_spec(self, col_dict):
        self.can_validate = False           # delay validation, just needless sql_building
        last_idx = len(col_dict) - 1
        for idx, (col_name, value) in enumerate(col_dict.items()):
            if idx >= last_idx:
                self.can_validate = True
            if value is not None and value != 'NULL':
                widget = self.get_widget(col_name)
                if widget:
                    if 'CheckBox' in type(widget).__name__:
                        if isinstance(value, str):
                            value = int(value)
                        value = True if value != 0 else False
                    if 'LineEdit' in type(widget).__name__:
                        if not isinstance(value, str):
                            value = str(value)
                    widget.set_value(value)
                else:
                    property_exists = self.properties()['custom'].get(col_name, 'DEBUG_MISSED') != 'DEBUG_MISSED'
                    if property_exists:
                        self.set_property(col_name, value)
                    else:
                        self.create_property(col_name, value)

    def set_bool_checkbox(self, col, idx=0, default_val=None, display_in_prop_bin=True):
        is_default_on = default_val is not None and int(default_val) == 1
        self.add_custom_widget(BoolCheckNodeWidget(parent=self.view, prop=col), tab='fields',
                               widget_type=NodePropWidgetEnum.QCHECK_BOX.value if display_in_prop_bin else None)

    def set_text_input(self, col, idx=0, default_val=None, localise=False):
        self.add_custom_widget(ExpandingLineEdit(parent=self.view, label=index_label(idx, col), name=col,
                                                 text=str(default_val or ''), localise=localise), tab='fields',
                               widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
        text_widget = self.get_widget(col)
        text_widget.get_custom_widget().setMinimumHeight(24)

    def update_model(self):
        """
        Update the node model from view. Ensure we dont update hidden properties
        """
        for name, val in self.view.properties.items():
            if name in ['inputs', 'outputs']:
                continue
            self.model.set_property(name, val)

        arg_params = self.model.get_property('arg_params') or {}
        for name, widget in self.view.widgets.items():
            if self.model.get_property(name) is not None:
                self.model.set_property(name, widget.get_value())
            else:
                if name in arg_params:
                    arg_params[name] = widget.get_value()

    def error_color(self, is_error=True):
        if is_error:
            error_color = (200, 30, 30)        # Set to an error color (e.g., Red: R, G, B, A)
            self.set_color(*error_color)
            self.test_error = True
        else:
            self.set_color(*self._default_color)        # Restore original color
            self.test_error = False

    def _update_field_style(self, field_name, is_valid):
        widget = self.get_widget(field_name)
        if widget:
            widget.adjust_color(widget.get_custom_widget(), is_valid)

    def get_properties_to_sql(self):
        custom_properties = {k: v for k, v in self.properties()['custom'].items() if k != 'sql_form'}
        custom_properties = SQLValidator.normalize_node_bools(custom_properties, self.get_property('table_name'))
        custom_properties = {k: v for k, v in custom_properties.items() if v is not None}
        return custom_properties

    def migrate_extra_params(self):
        return

    def restore_extra_params(self, migrated_properties):
        return


def backlink_port_get(original_table, connect_table):
    backlink_spec = db_spec.node_templates[original_table]
    combined_fks = backlink_spec['foreign_keys'].copy()
    combined_fks.update(backlink_spec.get('extra_fks', {}))
    fk_ports = [key for key, val in combined_fks.items() if
                val == connect_table or (isinstance(val, dict) and val.get('ref_table') == connect_table)]
    if len(fk_ports) > 1:
        log.error(f'when connecting backlink ports (for mod import): there were multiple ports possible for connection:'
                  f' {connect_table} -> {original_table}. possible ports: {fk_ports}')
    return fk_ports[0]


def set_output_port_constraints(node, table_name, fk_backlink):     # not actual constraints, handled on input
    pk = SQLValidator.pk_map[table_name][0]
    color = SQLValidator.port_color_map['output'].get(table_name, {}).get(pk)
    port = node.add_output(pk, color=color)
    port_outputs = defaultdict(list)
    for input_port, input_tbl_name_list in fk_backlink['col_first'].items():
        for input_tbl_name in input_tbl_name_list:
            table_class = SQLValidator.table_name_class_map.get(input_tbl_name, '')
            port_outputs[table_class].append(input_port)
    return port_outputs

# helper functions


def index_label(order, text):
    PREFIX = '\u200B\u200B'   # Toxic Zero White Space character to order labels with numbers without those showing
    label = PREFIX * order + text
    return label
