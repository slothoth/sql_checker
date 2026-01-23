from NodeGraphQt.constants import PortTypeEnum, NodePropWidgetEnum
from PyQt5 import QtCore, QtGui

from graph.singletons.db_spec_singleton import db_spec
from schema_generator import SQLValidator
from graph.custom_widgets import IntSpinNodeWidget, FloatSpinNodeWidget, DropDownLineEdit
from graph.nodes.base_nodes import BasicDBNode, set_output_port_constraints, index_label

from graph.transform_json_to_sql import transform_localisation, transform_to_sql

db_map = {'ModifierArguments': db_spec.mod_arg_database_types,
          'RequirementArguments': db_spec.req_arg_database_types}
bonus_col_poss_map = {'Name': {'ModifierArguments': db_spec.modifier_argument_list},
                                  'RequirementArguments': db_spec.req_argument_list}


class DynamicNode(BasicDBNode):

    def _validate_field(self, field_name, field_value, all_data=None):
        if all_data is None:
            all_cols = self._initial_fields + self._extra_fields
            all_data = {k: v for k, v in self.properties()['custom'].items() if k in all_cols}
        table_name = self.get_property('table_name')

        is_valid, error_msg = SQLValidator.validate_field(table_name, field_name, field_value, all_data)

        if is_valid:
            self._validation_errors.pop(field_name, None)
        else:
            self._validation_errors[field_name] = error_msg

        self._update_field_style(field_name, is_valid)

        return is_valid

    def _validate_all_fields(self):
        all_cols = self._initial_fields + self._extra_fields
        all_data = {k: v for k, v in self.properties()['custom'].items() if k in all_cols}
        for col in self._initial_fields:
            widget = self.get_widget(col)
            if widget and widget.widget_string_type == 'QLineEdit':
                value = widget.get_value()
                self._validate_field(col, value, all_data)

    def _arguments_change(self, database_arg_map, old_name, new_name):
        new_table_class, new_pk_output = self.port_info(database_arg_map, new_name)
        if new_table_class is None:
            return
        old_table_class, old_pk_output = self.port_info(database_arg_map, old_name)
        if old_table_class != new_table_class or old_table_class is None:
            port = self.get_input('Value')
            port.clear_connections()
            if old_table_class is not None:
                dict_key = [i for i in self._model._graph_model.accept_connection_types.keys()][0]
                del self._model._graph_model.accept_connection_types[dict_key]          # must be a better way to do this

            self.add_accept_port_type(port, {
                'node_type': new_table_class,
                'port_type': PortTypeEnum.OUT.value,
                'port_name': new_pk_output,
            })

    def port_info(self, database_arg_map, name):
        output_table = database_arg_map.get(name)
        if output_table is None:
            return None, None
        table_class = SQLValidator.table_name_class_map[output_table]
        table_pk_output = SQLValidator.pk_map[output_table][0]
        return table_class, table_pk_output

    def set_property(self, name, value, push_undo=True):
        old_value = self.get_property(name)
        table_name = self.get_property('table_name')
        if table_name in ('ModifierArguments', 'RequirementArguments'):
            super().set_property(name=name, value=value, push_undo=True)
            if name == 'Name':
                database_arg_map = db_map[table_name]
                self._arguments_change(database_arg_map, old_name=old_value, new_name=value)
        else:
            widget = self.get_widget(name)
            if self.can_validate and old_value != value and widget and widget.widget_string_type == 'QLineEdit':
                self._validate_field(name, value)
            super().set_property(name=name, value=value, push_undo=True)
        if self.can_validate and name not in {'sql_form', 'loc_sql_form', 'dict_sql'}:      # prevents looping
            sql_code, dict_form, loc = self.convert_to_sql()
            super().set_property('sql_form', sql_code)
            super().set_property('dict_sql', dict_form)
            super().set_property('loc_sql_form', loc)

    def set_spec(self, col_dict):
        super().set_spec(col_dict=col_dict)
        self._validate_all_fields()

    def convert_to_sql(self):
        custom_properties = self.get_properties_to_sql()
        table_name = self.get_property('table_name')
        loc_entries = transform_localisation(custom_properties, table_name)
        error_string = ''
        sql, dict_form, error_string = transform_to_sql(custom_properties, table_name, error_string)
        return sql, dict_form, loc_entries


# had to auto generate classes rather then generate at node instantition because
# on save they werent storing their properties in such a way they could be loaded again
def create_table_node_class(table_name, graph):
    class_name = f"{table_name.title().replace('_', '')}Node"

    def init_method(self):
        super(type(self), self).__init__()
        self._validation_errors = {}  # Track validation errors for each field
        self.view.setVisible(False)
        primary_keys = SQLValidator.pk_map[table_name]
        prim_texts = [i for i in SQLValidator.required_map[table_name] if i not in primary_keys]
        second_texts = SQLValidator.less_important_map[table_name]

        if table_name in SQLValidator.incremental_pk:
            self._initial_fields = prim_texts
            cols_ordered = prim_texts + second_texts
        else:
            self._initial_fields = primary_keys + prim_texts
            cols_ordered = primary_keys + prim_texts + second_texts

        self._extra_fields = second_texts
        self.create_property('table_name', value=table_name)

        age = graph.property('meta').get('Age')
        if age == 'ALWAYS':
            self._possible_vals = db_spec.all_possible_vals.get(table_name, {})
        else:
            self._possible_vals = db_spec.possible_vals.get(age, {}).get(table_name, {})

        if table_name == 'RequirementSets':
            self.add_input('RequirementSetId')

        if len(primary_keys) == 1:
            self.create_property('primary_key', primary_keys[0])

        default_map = SQLValidator.default_map.get(table_name, {})
        fk_to_tbl_map = SQLValidator.fk_to_tbl_map.get(table_name, {})
        fk_to_pk_map = SQLValidator.fk_to_pk_map.get(table_name, {})
        require_map = SQLValidator.required_map.get(table_name, {})
        localised_cols = db_spec.node_templates[table_name].get('localised', [])
        lazy_params = {}
        for idx, col in enumerate(cols_ordered):
            default_val = default_map.get(col, None)
            fk_to_tbl_link = fk_to_tbl_map.get(col, None)
            fk_to_pk_link = fk_to_pk_map.get(col, None)
            is_required = require_map.get(col, False)
            if fk_to_pk_link is not None:
                color = SQLValidator.port_color_map['input'].get(table_name, {}).get(col)
                if is_required:
                    port = self.add_input(col, color=color)
                else:
                    port = self.add_input(col, painter_func=draw_square_port, color=color)
                self.set_input_port_constraint(port, fk_to_tbl_link, fk_to_pk_link)

            col_poss_vals = bonus_col_poss_map.get(col, {}).get(table_name, self._possible_vals.get(col, None))
            col_type = SQLValidator.type_map[table_name][col]
            if isinstance(col_type, bool):
                if col in self._extra_fields:
                    default_val = bool(int(default_val))if default_val is not None else False
                    lazy_params[col] = default_val
                    self.create_property(col, default_val, widget_type=NodePropWidgetEnum.QCHECK_BOX.value)
                    continue
                self.set_bool_checkbox(col, idx, default_val)
            elif isinstance(col_type, int):
                if col in self._extra_fields:
                    default_val = int(default_val) if default_val is not None else 0
                    lazy_params[col] = default_val
                    self.create_property(col, default_val, widget_type=NodePropWidgetEnum.QSPIN_BOX.value)
                    continue
                custom_widget = IntSpinNodeWidget(col, self.view)
                self.add_custom_widget(custom_widget,
                                       widget_type=NodePropWidgetEnum.QSPIN_BOX.value, tab='fields')
            elif isinstance(col_type, float):
                if col in self._extra_fields:
                    default_val = float(default_val) if default_val is not None else 0.0
                    lazy_params[col] = default_val
                    self.create_property(col, default_val, widget_type=NodePropWidgetEnum.QDOUBLESPIN_BOX.value)
                    continue
                custom_widget = FloatSpinNodeWidget(col, self.view)
                self.add_custom_widget(custom_widget,
                                       widget_type=NodePropWidgetEnum.QDOUBLESPIN_BOX.value, tab='fields')
            elif col_poss_vals is not None:
                if 'vals' in col_poss_vals:
                    col_poss_vals = col_poss_vals['vals']
                if default_val is None:
                    default_val = ''
                if col in self._extra_fields:
                    lazy_params[col] = default_val
                    self.create_property(col, default_val, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
                    continue
                self.add_custom_widget(
                    DropDownLineEdit(parent=self.view, label=index_label(idx, col), name=col, text='',
                                     suggestions=col_poss_vals or []),
                    tab='fields', widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
            else:
                is_localised = col in localised_cols
                if col in self._extra_fields:
                    default_val = default_val if default_val is not None else ''
                    lazy_params[col] = default_val
                    self.create_property(col, default_val, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
                    continue
                self.set_text_input(col, idx, default_val, localise=is_localised)

        self.create_property('arg_params', lazy_params)
        for col in self._initial_fields:            # dont validate on start, takes like 0.2s
            widget = self.get_widget(col)
            if widget is not None and widget.widget_string_type == 'QLineEdit' and widget.get_value() == '':
                self._update_field_style(col, False)

        fk_backlink = SQLValidator.pk_ref_map.get(table_name)
        if fk_backlink is not None:
            self.output_port_tables[SQLValidator.pk_map[table_name][0]] = set_output_port_constraints(self, table_name,
                                                                                                      fk_backlink)
        if table_name in ('ModifierArguments', 'RequirementArguments'):
            self.add_input('Value')
        self.can_validate = True
        self.view.setVisible(True)

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
