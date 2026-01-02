from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QCheckBox, QLabel, QWidget, QApplication)
from graph.db_node_support import sync_node_options_all, set_nodes_visible_by_type
from schema_generator import SQLValidator


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
            db_spec.update_age
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


class Toast(QWidget):
    def __init__(self, message, parent=None, duration=2000):
        super().__init__(parent)

        self.setWindowFlags(
            QtCore.Qt.Tool |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        label = QLabel(message)
        label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(40, 40, 40, 220);
                padding: 10px 14px;
                border-radius: 6px;
            }
        """)
        label.setFont(QtGui.QFont("Arial", 10))

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.setContentsMargins(0, 0, 0, 0)

        self.adjustSize()
        self.setWindowOpacity(0.0)

        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        QtCore.QTimer.singleShot(duration, self.fade_out)

    def fade_out(self):
        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.close)
        self.anim.start()

    def show_at_bottom_right(self, margin=20):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - margin
        y = screen.bottom() - self.height() - margin
        self.move(x, y)
        self.show()


def get_combo_value(parent, age_list, mod_list):
    dlg = ComboDialog(age_list, mod_list, parent)
    if dlg.exec() == QDialog.Accepted:
        return dlg.age.currentText(), {i.text(): i.isChecked() for i in dlg.mod_items}
    return None, None
