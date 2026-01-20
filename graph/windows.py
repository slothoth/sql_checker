from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QCheckBox, QLabel, QGridLayout)
from graph.db_node_support import sync_node_options_all, set_nodes_visible_by_type
from schema_generator import SQLValidator
from graph.db_spec_singleton import db_spec


class MetaStore:
    @staticmethod
    def get(graph, key, default=None):
        meta = graph.property('meta') or {}
        return meta.get(key, default)

    @staticmethod
    def set(graph, key, value):
        meta = graph.property('meta') or {}
        meta[key] = value
        graph.setProperty('meta', meta)


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
        self.mod_age.addItems(["AGE_ANTIQUITY", "AGE_EXPLORATION", "AGE_MODERN"])

        self.hide_types = QtWidgets.QCheckBox()

        self.mod_name.setText(MetaStore.get(graph, "Mod Name", ""))
        self.mod_desc.setText(MetaStore.get(graph, "Mod Description", ""))
        self.mod_author.setText(MetaStore.get(graph, "Mod Author", ""))
        self.mod_uuid.setText(MetaStore.get(graph, "Mod UUID", ""))
        self.mod_action_id.setText(MetaStore.get(graph, "Mod Action", ""))
        self.mod_age.setCurrentText(MetaStore.get(graph, "Age", "AGE_ANTIQUITY"))
        self.hide_types.setChecked(MetaStore.get(graph, "Hide Types", False))

        meta_group = QtWidgets.QGroupBox("Metadata")
        meta_layout = QtWidgets.QFormLayout(meta_group)

        meta_layout.addRow("Mod Name", self.mod_name)
        meta_layout.addRow("Mod Description", self.mod_desc)
        meta_layout.addRow("Mod Author", self.mod_author)
        meta_layout.addRow("Mod UUID", self.mod_uuid)
        meta_layout.addRow("Mod Action", self.mod_action_id)
        meta_layout.addRow("Age", self.mod_age)
        layout.addWidget(meta_group)

        graph_group = QtWidgets.QGroupBox("Graph")
        graph_setting_layout = QtWidgets.QFormLayout(graph_group)
        graph_setting_layout.addRow("Hide Types", self.hide_types)
        layout.addWidget(graph_group)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def accept(self):
        old_age = MetaStore.get(self.graph, "Age")

        MetaStore.set(self.graph, "Mod Name", self.mod_name.text())
        MetaStore.set(self.graph, "Mod Description", self.mod_desc.text())
        MetaStore.set(self.graph, "Mod Author", self.mod_author.text())
        MetaStore.set(self.graph, "Mod UUID", self.mod_uuid.text())
        MetaStore.set(self.graph, "Mod Action", self.mod_action_id.text())
        MetaStore.set(self.graph, "Age", self.mod_age.currentText())
        MetaStore.set(self.graph, "Hide Types", self.hide_types.isChecked())

        if old_age != self.mod_age.currentText():
            sync_node_options_all(self.graph)
            SQLValidator.state_validation_setup(self.mod_age.currentText())
            # SQLValidator.state_validation_mod_setup(self.mod_age.currentText())
        hide = self.hide_types.isChecked()
        set_nodes_visible_by_type(self.graph, 'db.table.types.TypesNode', not hide)
        super().accept()


def open_metadata_dialog(graph, parent=None):
    dlg = MetadataDialog(graph, parent)
    if dlg.exec() == QtWidgets.QDialog.Accepted:
        return dlg.age.currentText(), {i.text(): i.isChecked() for i in dlg.mod_items}
    return None, None


class ComboDialog(QDialog):
    def __init__(self, parent=None, user_knobs={}):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        age_combo = QComboBox(self)
        age_combo.addItems(user_knobs.get('switches', {}).get('Ages', []))
        layout.addWidget(age_combo)
        self.age = age_combo
        if len(user_knobs.get('configurations', {})) > 0:
            log_label = QLabel("ConfigurationParams")
            layout.addWidget(log_label)

        two_column_grid = QGridLayout()
        self.config_values = {}
        for idx, (configId, configValueList) in enumerate(user_knobs.get('configurations', {}).items()):
            config_combo_box = QComboBox(self)
            config_combo_box.addItems(configValueList)
            two_column_grid.addWidget(QLabel(configId), idx, 0)
            two_column_grid.addWidget(config_combo_box, idx, 1)
            self.config_values[configId] = config_combo_box
        layout.addLayout(two_column_grid)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        layout.addWidget(buttons)

        two_col_checkbox = QGridLayout()
        self.mod_items = []
        content = user_knobs.get('switches', {}).get('Mods', [])
        dlc = [i for i in content if i in db_spec.dlc_mod_ids]
        mods = [i for i in content if i not in db_spec.dlc_mod_ids]
        for col, id_list in enumerate((dlc, mods)):
            for idx, mod in enumerate(id_list):
                mod_tick = QCheckBox(self)
                mod_tick.setText(mod)
                two_col_checkbox.addWidget(mod_tick, idx, col)
                self.mod_items.append(mod_tick)
        layout.addLayout(two_col_checkbox)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)


def get_combo_value(parent, user_knobs):
    dlg = ComboDialog(parent, user_knobs)
    if dlg.exec() == QDialog.Accepted:
        return (dlg.age.currentText(), {i.text(): i.isChecked() for i in dlg.mod_items},
                {k: v.currentText() for k, v in dlg.config_values.items()})
    return None, None, None
