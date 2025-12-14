from NodeGraphQt import BaseNode
from ..db_spec_singleton import ResourceLoader
from Qt import QtCore, QtGui

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
        btn.set_value('V' if self._extra_visible else '>')

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
                        if backlink_table == self.NODE_NAME:
                            base_spec = db_spec.node_templates[backlink_table]
                            fk_ports = [key for key, val in base_spec['foreign_keys'].items() if val == connect_table]
                            if len(fk_ports) > 1:
                                print('error multiple ports possible for connect!')
                            return fk_ports[0]

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
def create_table_node_class(table_name, spec):
    class_name = f"{table_name.title().replace('_', '')}Node"

    def init_method(self):
        super(type(self), self).__init__()
        self._initial_fields = list(spec.get('primary_texts', []))
        self._extra_fields = list(spec.get('secondary_texts', []))
        self.create_property('toggle_extra', value='>')
        self.add_button(name='toggle_extra', label='', text='>')
        btn = self.get_widget('toggle_extra')
        btn.value_changed.connect(lambda *a: self._toggle_extra())
        self._possible_vals = db_spec.possible_vals.get(table_name, {})
        # Initialize ports and widgets based on the schema

        for col in spec['all_cols']:
            default_val = spec.get("default_values", {}).get(col, '')
            fk_table = spec.get("foreign_keys", {}).get(col, None)
            if fk_table is not None:
                if col in spec['primary_texts']:            # mandatory FK
                    self.add_input(col)
                else:
                    self.add_input(col, painter_func=draw_square_port)

            col_poss_vals = self._possible_vals.get(col, None)
            if col in spec['mined_bools']:
                default_on = int(spec.get('default_values', {}).get(col, '0')) == 1
                self.add_checkbox(col, label=col, state=default_on)
            elif col_poss_vals is not None:
                self.add_combo_menu(
                    name=col,
                    label=col,
                    items=[''] + col_poss_vals['vals'],
                    tab='fields'
                )
            else:
                self.add_text_input(name=col, label=col, text=str(default_val or ''), tab='fields')
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


def generate_tables():
    all_custom_nodes = []
    for name, spec in db_spec.node_templates.items():
        NodeClass = create_table_node_class(name, spec)
        all_custom_nodes.append(NodeClass)
    return all_custom_nodes
