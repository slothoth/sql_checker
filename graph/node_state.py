from PyQt5 import QtCore
from graph.custom_widgets import ExpandingLineEdit, DropDownLineEdit
from schema_generator import SQLValidator


class SuggestionHub(QtCore.QObject):
    def __init__(self, graph):
        super().__init__()
        self.graph = graph

        self._wired = set()
        self._nodes_by_table = {}
        self._dropdowns_by_target_table = {}

        self.graph.node_created.connect(self._on_node_created)
        self.graph.nodes_deleted.connect(self._on_nodes_deleted)

        self.rebuild()

    def rebuild(self):
        self._wired.clear()
        self._nodes_by_table.clear()
        self._dropdowns_by_target_table.clear()

        for node in self.graph.all_nodes():
            self._track_node(node)

        self.refresh_all()

    def _on_node_created(self, node):
        QtCore.QTimer.singleShot(0, lambda n=node: self._track_and_refresh(n))

    def _track_and_refresh(self, node):
        self._track_node(node)
        self.refresh_all()

    def _on_nodes_deleted(self, *_):
        self.rebuild()

    def _track_node(self, node):
        table = node.get_property("table_name")
        if table:
            self._nodes_by_table.setdefault(table, set()).add(node)

        widgets = node.widgets() or {}
        for _, w in widgets.items():
            if not isinstance(w, (ExpandingLineEdit, DropDownLineEdit)):
                continue

            key = (node.id, id(w))
            if key not in self._wired:
                self._wired.add(key)
                if hasattr(w, "committed"):
                    w.committed.connect(self._on_widget_committed)
                else:
                    le = w.get_custom_widget()
                    if hasattr(le, "editingFinished"):
                        le.editingFinished.connect(lambda w=w: self._on_widget_committed(w))

            if isinstance(w, DropDownLineEdit) and table:
                watch_spec = SQLValidator.fk_to_tbl_map.get(table, {})
                fk_widget_name = w.get_name()
                target_table = watch_spec.get(fk_widget_name)
                if target_table:
                    self._dropdowns_by_target_table.setdefault(target_table, set()).add(w)

    def _on_widget_committed(self, w):
        node = getattr(w, "node", None)
        if not node:
            return

        table = node.get_property("table_name")
        pk_name = node.get_property("primary_key")
        if table and pk_name and w.get_name() == pk_name:
            self.refresh_table(table)

    def refresh_all(self):
        for target_table in list(self._dropdowns_by_target_table.keys()):
            self.refresh_table(target_table)

    def refresh_table(self, target_table):
        dynamic = []
        for node in self._nodes_by_table.get(target_table, set()):
            pk_name = node.get_property("primary_key")
            if not pk_name:
                continue
            w = node.get_widget(pk_name)
            if not w or not isinstance(w, (ExpandingLineEdit, DropDownLineEdit)):
                continue
            v = w.get_value()
            if v:
                dynamic.append(v)

        for dd in self._dropdowns_by_target_table.get(target_table, set()):
            dd.set_dynamic_suggestions(dynamic)
