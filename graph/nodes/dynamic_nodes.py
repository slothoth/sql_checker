from NodeGraphQt import BaseNode
from ..db_spec_singleton import ResourceLoader

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

    def get_link_port(self, connect_table, connect_port):
        connect_spec = db_spec.node_templates[connect_table]
        if connect_port is not None:
            backlinks = connect_spec.get('backlink_fk', None)
            if backlinks is not None:
                for backlink_port, backlink_table in backlinks.items():
                    if backlink_table == self.NODE_NAME:
                        return backlink_port

    def _delete_self(self):
        graph = self.graph
        if graph:
            graph.delete_node(self)


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
                self.add_input(col)

            col_poss_vals = self._possible_vals.get(col, None)
            if col_poss_vals is not None:
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
