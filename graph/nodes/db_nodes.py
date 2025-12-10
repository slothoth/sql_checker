from NodeGraphQt import BaseNode


class DynamicFieldsNode(BaseNode):
    __identifier__ = 'nodes.widget'
    NODE_NAME = 'dynamic'

    def __init__(self):
        super().__init__()
        self._spec = {}
        self._extra_fields = []
        self._initial_fields = []
        self._extra_visible = False

        # create the toggle button; give it an initial label via the add_button 'text' arg
        self.add_button(name='toggle_extra', label='', text='Show More', tab='fields')

        btn = self.get_widget('toggle_extra')
        # connect to the available signal; NodeButton implementations differ across versions
        if hasattr(btn, 'clicked'):
            try:
                btn.clicked.connect(self._toggle_extra)
            except Exception:
                pass
        if hasattr(btn, 'value_changed'):
            try:
                btn.value_changed.connect(lambda *a: self._toggle_extra())
            except Exception:
                pass

    def set_spec(self, spec):
        self._spec = spec
        columns = list(spec.get('all_cols', []))
        if not columns:
            return

        half = len(columns) // 2
        self._initial_fields = columns[:half]
        self._extra_fields = columns[half:]

        for col in self._initial_fields:
            default_val = spec.get("default_values", {}).get(col, None)
            fk_table = spec.get("foreign_keys", {}).get(col, None)
            fk_backlink = spec.get("backlink_fk", {}).get(col, None)

            if fk_table is not None:
                self.add_input(col)

            if fk_backlink is not None:
                self.add_output(col)

            self.add_text_input(name=col, label=col, text=str(default_val or ''), tab='fields')
            if default_val is not None:
                self.set_property(col, default_val)

        for col in self._extra_fields:
            default_val = spec.get("default_values", {}).get(col, None)
            fk_table = spec.get("foreign_keys", {}).get(col, None)
            fk_backlink = spec.get("backlink_fk", {}).get(col, None)

            if fk_table is not None:
                self.add_input(col)

            if fk_backlink is not None:
                self.add_output(col)

            self.add_text_input(name=col, label=col, text=str(default_val or ''), tab='fields')
            self.hide_widget(col, push_undo=False)
            if default_val is not None:
                self.set_property(col, default_val)

    def _safe_set_button_label(self, btn, text):
        if not btn:
            return
        # try likely method names in order; ignore if none exist
        try:
            if hasattr(btn, 'setText'):
                btn.setText(text)
                return
        except Exception:
            pass
        try:
            if hasattr(btn, 'set_label'):
                btn.set_label(text)
                return
        except Exception:
            pass
        try:
            if hasattr(btn, 'setLabel'):
                btn.setLabel(text)
                return
        except Exception:
            pass
        try:
            if hasattr(btn, 'set_value'):
                btn.set_value(text)
                return
        except Exception:
            pass
        try:
            if hasattr(btn, 'setValue'):
                btn.setValue(text)
                return
        except Exception:
            pass
        # last resort, try attribute assignment if available
        try:
            if hasattr(btn, 'text'):
                btn.text = text
        except Exception:
            pass

    def _toggle_extra(self):
        self._extra_visible = not self._extra_visible
        for col in self._extra_fields:
            if self._extra_visible:
                self.show_widget(col, push_undo=False)
            else:
                self.hide_widget(col, push_undo=False)

        btn = self.get_widget('toggle_extra')
        self._safe_set_button_label(btn, 'Hide' if self._extra_visible else 'Show More')

        try:
            self.update()
        except Exception:
            pass

    def _delete_self(self):
        graph = self.graph
        if graph:
            graph.delete_node(self)
