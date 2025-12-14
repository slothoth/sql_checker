from Qt import QtWidgets, QtCore
from graph.db_spec_singleton import ResourceLoader

db_spec = ResourceLoader()
subsets = {}


# used for searchable node creation
class NodeCreationDialog(QtWidgets.QDialog):
    def __init__(self, subset=None):
        super().__init__()
        if subset is None:
            self.templates = db_spec.node_templates
        else:
            valid_tables = db_spec.node_templates[subset.node.name]['backlink_fk'][subset.name]
            self.templates = {key: val for key, val in db_spec.node_templates.items() if key in valid_tables}

        self.setWindowFlags(QtCore.Qt.Popup)
        self.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.search = QtWidgets.QLineEdit()
        self.list = QtWidgets.QListWidget()

        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)

        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._choose_first)
        self.list.itemDoubleClicked.connect(self.accept)

        self._filter("")

    def _filter(self, text):
        self.list.clear()
        q = text.lower()

        scored = []
        for name in self.templates.keys():
            n = name.lower()
            if q in n:
                idx = n.index(q)
                scored.append((idx, len(n) - len(q), name))

        for _, _, name in sorted(scored):
            self.list.addItem(name)

    def _choose_first(self):
        if self.list.count():
            self.list.setCurrentRow(0)
            self.accept()

    def selected(self):
        item = self.list.currentItem()
        return item.text() if item else None

    def showEvent(self, event):
        super().showEvent(event)
        self.search.setFocus(QtCore.Qt.PopupFocusReason)
        self.search.selectAll()


# used for searchable combo box
class SearchListDialog(QtWidgets.QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup)
        self.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.search = QtWidgets.QLineEdit()
        self.list = QtWidgets.QListWidget()
        self.items = items or []

        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)

        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._choose_first)
        self.list.itemDoubleClicked.connect(self.accept)

        self._filter("")

    def showEvent(self, event):
        super().showEvent(event)
        self.search.setFocus(QtCore.Qt.PopupFocusReason)

    def _filter(self, text):
        self.list.clear()
        q = text.lower()
        for item in self.items:
            if q in item.lower():
                self.list.addItem(item)

    def _choose_first(self):
        if self.list.count():
            self.list.setCurrentRow(0)
            self.accept()

    def selected(self):
        item = self.list.currentItem()
        return item.text() if item else None