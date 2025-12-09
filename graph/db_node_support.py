from Qt import QtWidgets, QtCore, QtGui


class NodeCreationDialog(QtWidgets.QDialog):
    def __init__(self, templates):
        super().__init__()
        self.templates = templates

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
        text = text.lower()
        for name in self.templates.keys():
            if text in name.lower():
                self.list.addItem(name)

    def _choose_first(self):
        if self.list.count():
            self.list.setCurrentRow(0)
            self.accept()

    def selected(self):
        item = self.list.currentItem()
        return item.text() if item else None
