from Qt import QtWidgets


class MetadataDialog(QtWidgets.QDialog):
    def __init__(self, graph, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.setWindowTitle("Mod Metadata")
        self.setMinimumWidth(320)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        form = QtWidgets.QFormLayout()
        self.mod_name = QtWidgets.QLineEdit()
        self.mod_desc = QtWidgets.QLineEdit()
        self.mod_author = QtWidgets.QLineEdit()
        self.mod_uuid = QtWidgets.QLineEdit()
        self.mod_action_id = QtWidgets.QLineEdit()
        self.mod_age = QtWidgets.QComboBox()

        form.addRow("Mod Name", self.mod_name)
        form.addRow("Mod Description", self.mod_desc)
        form.addRow("Mod Author", self.mod_author)
        form.addRow("Mod UUID", self.mod_uuid)
        form.addRow("Mod Action", self.mod_action_id)
        form.addRow("Age", self.mod_age)
        meta = self.graph.get_property('meta')
        self.mod_name.setText(meta.get('Mod Name', ''))
        self.mod_desc.setText(meta.get('Mod Description', ''))
        self.mod_author.setText(meta.get('Mod Author', ''))
        self.mod_uuid.setText(meta.get('Mod UUID', ''))
        self.mod_action_id.setText(meta.get('Mod Action', ''))

        # self.mod_age set default?

        layout.addLayout(form)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)

        apply_btn = QtWidgets.QPushButton("Apply")
        cancel_btn = QtWidgets.QPushButton("Cancel")

        apply_btn.clicked.connect(self.accept_with_changes)
        cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(apply_btn)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

    def values(self):
        return {
            "ModName": self.mod_name.text(),
            "ModDescription": self.mod_desc.text(),
            "ModAuthor": self.mod_author.text(),
            "ModUUID": self.mod_uuid.text(),
            "ModActionId": self.mod_action_id.text(),
            "ModAge": self.mod_age.currentText(),
        }

    def accept_with_changes(self):
        meta = self.graph.get_property('meta')
        meta['Mod Name'] = self.mod_name.text()
        meta['Mod Description'] = self.mod_desc.text()
        meta['Mod Author'] = self.mod_author.text()
        meta['Mod UUID'] = self.mod_uuid.text()
        meta['Mod Action'] = self.mod_action_id.text()
        meta['Age'] = self.mod_age.currentText()
        self.graph.setProperty('meta', meta)
        self.accept()
