from NodeGraphQt import BaseNode


class DynamicFieldsNode(BaseNode):
    __identifier__ = 'nodes.widget'
    NODE_NAME = 'dynamic'

    def __init__(self):
        super().__init__()
        self._spec = []

    def set_spec(self, spec):
        self._spec = spec
        columns = spec['all_cols']
        for col_name in columns:
            default_val = spec.get("default_values", {}).get(col_name, None)
            fk_table = spec.get("foreign_keys", {}).get(col_name, None)
            fk_backlink = spec.get("backlink_fk", {}).get(col_name, None)

            if fk_table is not None:
                self.add_input(col_name)
                # also need to colour it

            if fk_backlink is not None:
                self.add_output(col_name)
                # also need to colour it

            self.add_text_input(name=col_name, label=col_name, tab='fields')
            if default_val is not None:
                self.set_property(col_name, default_val)

    def _delete_self(self):
        graph = self.graph
        if graph:
            graph.delete_node(self)
