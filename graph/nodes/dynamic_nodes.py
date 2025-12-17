from NodeGraphQt import BaseNode, NodeBaseWidget
from NodeGraphQt.constants import Z_VAL_NODE_WIDGET
from PyQt5 import QtWidgets

from ..db_node_support import SearchListDialog
from ..db_spec_singleton import ResourceLoader
from PyQt5 import QtCore, QtGui

db_spec = ResourceLoader()


class DynamicNode(BaseNode):
    _initial_fields = []
    _extra_fields = []
    _extra_visible = False

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

    def get_link_port(self, connect_table, connect_port):       # given an input port, finds the matching output on other node
        connect_spec = db_spec.node_templates[connect_table]
        if connect_port is not None:
            backlinks = connect_spec.get('backlink_fk', None)
            if backlinks is not None:
                for backlink_port, backlink_table_list in backlinks.items():
                    for backlink_table in backlink_table_list:
                        if backlink_table == self.get_property('table_name'):
                            backlink_spec = db_spec.node_templates[backlink_table]
                            fk_ports = [key for key, val in backlink_spec['foreign_keys'].items() if val == connect_table]
                            if len(fk_ports) > 1:
                                print(f'error multiple ports possible for connect!'
                                      f' the connection was: {connect_table} -> {backlink_table}.'
                                      f' defaulting to first option')
                            return fk_ports[0]

    def add_search_menu(self, name, label='', items=None, tooltip=None, tab=None):
        self.create_property(
            name,
            value=items[0] if items else '',
            items=items or [],
            widget_type='SEARCH_MENU',
            widget_tooltip=tooltip,
            tab=tab
        )

        widget = NodeSearchMenu(self.view, name, label, items)
        widget.value_changed.connect(lambda k, v: self.set_property(k, v))
        self.view.add_widget(widget)
        self.view.draw_node()

    def set_spec(self, col_dict):
        for col_name, value in col_dict.items():
            if value is not None and value != 'NULL':
                widget = self.get_widget(col_name)
                if widget:
                    current_val = self.get_property(col_name)
                    if 'CheckBox' in type(widget).__name__:
                        if isinstance(value, str):
                            value = int(value)
                        value = True if 0 else False
                    if 'LineEdit' in type(widget).__name__:
                        if not isinstance(value, str):
                            value = str(value)
                    widget.set_value(value)

    def _delete_self(self):
        graph = self.graph
        if graph:
            graph.delete_node(self)


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


# had to auto generate classes rather then generate at node instantition because
# on save they werent storing their properties in such a way they could be loaded again
def create_table_node_class(table_name, spec, graph):
    class_name = f"{table_name.title().replace('_', '')}Node"

    def init_method(self):
        super(type(self), self).__init__()
        self._initial_fields = list(spec.get('primary_texts', []))
        self._extra_fields = list(spec.get('secondary_texts', []))
        self.create_property('table_name', value=table_name)

        toggle = ToggleExtraButton(self.view)
        toggle._btn.clicked.connect(self._toggle_extra)
        self.add_custom_widget(toggle, tab=None)

        age = graph.property('meta').get('Age')
        if age == 'ALWAYS':
            self._possible_vals = db_spec.all_possible_vals.get(table_name, {})
        else:
            self._possible_vals = db_spec.possible_vals.get(age, {}).get(table_name, {})
        # Initialize ports and widgets based on the schema
        primary_keys = spec.get('primary_keys', [])
        prim_texts = [i for i in spec.get('primary_texts', []) if i not in primary_keys]
        second_texts = spec.get('secondary_texts', [])
        cols_ordered = primary_keys + prim_texts + second_texts
        for idx, col in enumerate(cols_ordered):
            default_val = spec.get("default_values", {}).get(col, '')
            fk_table = spec.get("foreign_keys", {}).get(col, None)
            if fk_table is not None:
                if col in spec.get('primary_texts', []):            # Port addition
                    self.add_input(col)
                else:
                    self.add_input(col, painter_func=draw_square_port)

            col_poss_vals = self._possible_vals.get(col, None)
            if col in spec.get('mined_bools', {}):
                default_on = int(spec.get('default_values', {}).get(col, '0')) == 1
                self.add_checkbox(col, label=pad_label(index_label(idx, col)), state=default_on)
                cb = self.get_widget(col).get_custom_widget()
                cb.setMinimumHeight(24)
                cb.setStyleSheet("QCheckBox { padding-top: 2px; }")
            elif col_poss_vals is not None:
                self.add_search_menu(name=col, label=pad_label(index_label(idx, col)),
                                     items=[''] + col_poss_vals['vals'],
                                     tab='fields')
            else:
                self.add_text_input(name=col, label=pad_label(index_label(idx, col)), text=str(default_val or ''), tab='fields')
                widget = self.get_widget(col)
                widget.get_custom_widget().setMinimumHeight(24)
            if col in self._extra_fields:
                self.hide_widget(col, push_undo=False)

        fk_backlink = spec.get("backlink_fk", None)
        if fk_backlink is not None:
            self.add_output(spec["primary_keys"][0])  # what if combined pk? can that even link

        if len(self._extra_fields) == 0:
            btn = self.get_widget('toggle_extra')
            btn.hide()

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


# support for searchable combo box
class NodeSearchMenu(NodeBaseWidget):
    def __init__(self, parent=None, name='', label='', items=None):
        super().__init__(parent, name, label)
        self.setZValue(Z_VAL_NODE_WIDGET + 1)

        self._items = items or []

        self._button = QtWidgets.QToolButton()
        self._button.setMinimumHeight(24)
        self._button.setMinimumWidth(120)
        self._button.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        self._button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self._button.clicked.connect(self._open_dialog)
        self.set_custom_widget(self._button)

    @property
    def type_(self):
        return 'SearchMenuNodeWidget'

    def _open_dialog(self):
        dialog = SearchListDialog(self._items, self.parent())
        dialog.move(QtGui.QCursor.pos())

        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        value = dialog.selected()
        if value is not None:
            self.set_value(value)
            self.on_value_changed()

    def get_value(self):
        return self._button.text()

    def set_value(self, value):
        self._button.setText(value if value else '')

    def add_items(self, items):
        self._items.extend(items)

    def clear(self):
        self._items.clear()
        self.set_value('')


color_hex_swapper = {'#ffcc00': '#00ccff', '#00ccff': '#ffcc00'}


class ToggleExtraButton(NodeBaseWidget):
    def __init__(self, parent=None, name='toggle_extra', label=''):
        super().__init__(parent, name, label)
        self.set_name('toggle_extra')
        self.set_label('')
        btn = QtWidgets.QToolButton()
        btn.setCheckable(True)
        btn.setFixedSize(10, 10)
        btn.setStyleSheet("""
        QToolButton {
            background-color: #333;
        }
        QToolButton:checked {
            background-color: #2e7d32;
        }
        """)

        self._btn = btn
        self.set_custom_widget(btn)

    def set_value(self, value):
        self._btn.setText(value)

    def get_value(self):
        return self._btn.text()


def pad_label(text, width=20):
    return text.ljust(width)


def index_label(order, text):
    PREFIX = '\u200B\u200B'   # Toxic Zero White Space character to order labels with numbers without those showing
    label = PREFIX * order + text
    return label


def generate_tables(graph):
    all_custom_nodes = []
    for name, spec in db_spec.node_templates.items():
        NodeClass = create_table_node_class(name, spec, graph)
        all_custom_nodes.append(NodeClass)
    return all_custom_nodes
