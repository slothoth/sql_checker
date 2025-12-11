from NodeGraphQt import BaseNode
import json


class DynamicFieldsNode(BaseNode):
    __identifier__ = 'nodes.widget'
    NODE_NAME = 'dynamic'

    def __init__(self, spec_name=None):
        super().__init__()
        self._spec = {}
        self._extra_fields = []
        self._initial_fields = []
        self._possible_vals = []
        self._extra_visible = False

        self.create_property('toggle_extra', value='>')

        self.add_button(name='toggle_extra', label='', text='>')

        btn = self.get_widget('toggle_extra')
        btn.value_changed.connect(lambda *a: self._toggle_extra())
        if spec_name is not None:
            self.set_spec(spec_name)
            self.set_name(spec_name)

    def set_spec(self, name):
        self._spec = node_templates[name]
        self._possible_vals = possible_vals.get(name, {})

        self._initial_fields = list(self._spec.get('primary_texts', []))
        self._extra_fields = list(self._spec.get('secondary_texts', []))

        for col in self._spec['all_cols']:
            default_val = self._spec.get("default_values", {}).get(col, None)
            fk_table = self._spec.get("foreign_keys", {}).get(col, None)
            if fk_table is not None:
                self.add_input(col)

            col_poss_vals = self._possible_vals.get(col, None)
            if col_poss_vals is not None:
                self.add_combo_menu(
                    name=col,
                    label=col,
                    items=col_poss_vals['vals'],
                    tab='fields'
                )
            else:
                self.add_text_input(name=col, label=col, text=str(default_val or ''), tab='fields')
            if col in self._extra_fields:
                self.hide_widget(col, push_undo=False)
            self.set_property(col, default_val if default_val is not None else '')

        fk_backlink = self._spec.get("backlink_fk", None)
        if fk_backlink is not None:
            self.add_output(self._spec["primary_keys"][0])        # what if combined pk? can that even link

        if len(self._extra_fields) == 0:
            btn = self.get_widget('toggle_extra')
            btn.hide()

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
        connect_spec = node_templates[connect_table]
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


with open('resources/db_spec.json', 'r') as f:
    node_templates = json.load(f)

with open('resources/db_possible_vals.json', 'r') as f:
    possible_vals = json.load(f)
