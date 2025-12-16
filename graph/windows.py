from graph.db_node_support import sync_node_options_all
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QLineEdit, QFormLayout, QHBoxLayout,
                               QPushButton, QCheckBox)


class MetadataDialog(QDialog):
    def __init__(self, graph, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.setWindowTitle("Mod Metadata")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        form = QFormLayout()
        self.mod_name = QLineEdit()
        self.mod_desc = QLineEdit()
        self.mod_author = QLineEdit()
        self.mod_uuid = QLineEdit()
        self.mod_action_id = QLineEdit()
        self.mod_age = QComboBox()

        form.addRow("Mod Name", self.mod_name)
        form.addRow("Mod Description", self.mod_desc)
        form.addRow("Mod Author", self.mod_author)
        form.addRow("Mod UUID", self.mod_uuid)
        form.addRow("Mod Action", self.mod_action_id)
        form.addRow("Age", self.mod_age)
        self.mod_age.addItems(["AGE_ANTIQUITY", "AGE_EXPLORATION", "AGE_MODERN"])

        meta = self.graph.property('meta')
        self.mod_name.setText(meta.get('Mod Name', ''))
        self.mod_desc.setText(meta.get('Mod Description', ''))
        self.mod_author.setText(meta.get('Mod Author', ''))
        self.mod_uuid.setText(meta.get('Mod UUID', ''))
        self.mod_action_id.setText(meta.get('Mod Action', ''))
        self.mod_age.setCurrentText(meta.get('Age', 'AGE_ANTIQUITY'))           # for some reason this fails

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")

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
        meta = self.graph.property('meta')
        meta['Mod Name'] = self.mod_name.text()
        meta['Mod Description'] = self.mod_desc.text()
        meta['Mod Author'] = self.mod_author.text()
        meta['Mod UUID'] = self.mod_uuid.text()
        meta['Mod Action'] = self.mod_action_id.text()
        changed_age = not (meta['Age'] == self.mod_age.currentText())
        meta['Age'] = self.mod_age.currentText()
        self.graph.setProperty('meta', meta)
        if changed_age:
            sync_node_options_all(self.graph)             # todo refactor so it only syncs valid ones
        self.accept()


# dialog for choosing condition on loading mod
class ComboDialog(QDialog):
    def __init__(self, age_list, mod_list, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        age_combo = QComboBox(self)
        age_combo.addItems(age_list)
        layout.addWidget(age_combo)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        layout.addWidget(buttons)

        self.mod_items = []
        for mod in mod_list:
            mod_tick = QCheckBox(self)
            mod_tick.setText(mod)
            layout.addWidget(mod_tick)
            self.mod_items.append(mod_tick)


        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.age = age_combo


def get_combo_value(parent, age_list, mod_list):
    dlg = ComboDialog(age_list, mod_list, parent)
    if dlg.exec() == QDialog.Accepted:
        return dlg.age.currentText(), {i.text(): i.isChecked() for i in dlg.mod_items}
    return None, None