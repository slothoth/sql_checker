
from NodeGraphQt.constants import NodePropWidgetEnum
from PyQt5 import QtCore, QtGui
import math
from collections import defaultdict
import weakref

from graph.db_spec_singleton import db_spec
from schema_generator import SQLValidator
from graph.custom_widgets import IntSpinNodeWidget
from graph.nodes.base_nodes import BasicDBNode, set_output_port_constraints


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


# had to auto generate classes rather then generate at node instantition because
# on save they werent storing their properties in such a way they could be loaded again
def create_table_node_class(table_name, graph):
    class_name = f"{table_name.title().replace('_', '')}Node"

    def init_method(self):
        super(type(self), self).__init__()
        self.view.setVisible(False)
        primary_keys = SQLValidator.pk_map[table_name]
        prim_texts = [i for i in SQLValidator.required_map[table_name] if i not in primary_keys]
        second_texts = SQLValidator.less_important_map[table_name]

        self._initial_fields = primary_keys + prim_texts
        self._extra_fields = second_texts
        self.create_property('table_name', value=table_name)

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
        lazy_params = {}
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
            elif col_poss_vals is not None:
                if col in self._extra_fields:
                    lazy_params[col] = default_val
                    self.create_property(col, default_val, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
                    continue
                self.set_search_menu(col=col, idx=idx, col_poss_vals=[''] + col_poss_vals['vals'],)
            else:
                if col in self._extra_fields:
                    default_val = default_val if default_val is not None else ''
                    lazy_params[col] = default_val
                    self.create_property(col, default_val, widget_type=NodePropWidgetEnum.QLINE_EDIT.value)
                    continue
                self.set_text_input(col, idx, default_val)

        self.create_property('arg_params', lazy_params)
        # Validate all fields after initialization
        self._validate_all_fields()

        fk_backlink = SQLValidator.pk_ref_map.get(table_name)
        if fk_backlink is not None:
            self.output_port_tables[SQLValidator.pk_map[table_name][0]] = set_output_port_constraints(self, table_name,
                                                                                                      fk_backlink)

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
