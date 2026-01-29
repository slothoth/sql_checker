from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QCheckBox, QLabel, QGridLayout)
import json
import os
import sys

from graph.db_node_support import sync_node_options_all, set_nodes_visible_by_type
from schema_generator import SQLValidator
from graph.singletons.db_spec_singleton import db_spec
from graph.utils import resource_path
from graph.utils import check_civ_install_works, check_civ_config_works, check_workshop_works

from graph.singletons.filepaths import LocalFilePaths


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
            SQLValidator.state_validation_setup(self.mod_age.currentText(), db_spec)
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


with open(resource_path('resources/style_sheets.json')) as f:
    styles = json.load(f)


class PathSettingsDialog(QtWidgets.QDialog):
    def __init__(self, paths=None):
        super().__init__()
        self.ensure_valid_directory = paths is not None
        if paths is None:
            paths = {}
        self.setWindowTitle("Path Settings")

        layout = QtWidgets.QVBoxLayout(self)
        self.path_edits = {}

        self.b_dict = {}
        self.text_fields = {}

        header_label = QLabel("Could not resolve some filepaths. Red highlighted fields need amending.")
        header_label.setWordWrap(True)
        layout.addWidget(header_label)

        config_label = QLabel("Your Civ Config normally is in Appdata/Local/Firaxis Games/Sid Meier's Civilization VII."
                              " It contains a Mods folder for all non-workshop mods, and a Logs folder.")
        config_label.setWordWrap(True)
        layout.addWidget(config_label)

        config_current = db_spec.metadata.get('civ_config') or paths.get('config') or ''
        self.b_dict['config'], self.text_fields['config'] = self.add_path_row(layout, "Civ Config Location:",
                                                                              config_current, "config")

        workshop_label = QLabel("Your workshop mods folder will normally be inside your Steam installation under "
                                "steamapps/workshop/content/1295560. It should contain many numbered mod folders.")
        workshop_label.setWordWrap(True)
        layout.addWidget(workshop_label)

        workshop_current = db_spec.metadata.get('workshop') or paths.get('workshop') or ''
        self.b_dict['workshop'], self.text_fields['workshop'] = self.add_path_row(layout, "Workshop Folder:",
                                                                                  workshop_current, "workshop")

        install_label = QLabel("Your Civilization Installation. On Steam this is probably under "
                               "steam/steamapps/common/Sid Meier's Civilization VII. It should contain two folders, "
                               "Base and DLC.")
        install_label.setWordWrap(True)
        layout.addWidget(install_label)

        install_current = db_spec.metadata.get('civ_install') or paths.get('install') or ''

        self.b_dict['install'], self.text_fields['install'] = self.add_path_row(layout, "Civ Install:",
                                                                                install_current, "install")
        # Connect Browse buttons
        self.b_dict['config'].clicked.connect(lambda: self.browse_file(self.text_fields['config'], "Select Civ Config Location"))
        self.b_dict['workshop'].clicked.connect(lambda: self.browse_folder(self.text_fields['workshop'], "Select Workshop Folder"))
        self.b_dict['install'].clicked.connect(lambda: self.browse_file(self.text_fields['install'], "Select Civ Install"))

        # Setup Dialog Buttons
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Reference to the OK button to toggle it
        self.ok_button = self.button_box.button(QtWidgets.QDialogButtonBox.Ok)

        # Connect text changes to validation
        for field in self.text_fields.values():
            field.textChanged.connect(self.validate_all_paths)

        self._calculate_initial_width()
        if paths is not None:
            for key, path in paths.items():
                if path is None:
                    self.text_fields[key].setStyleSheet(styles['basic_error'])
                else:
                    self.b_dict[key].setDisabled(True)
                    self.text_fields[key].setReadOnly(True)
                    self.text_fields[key].setStyleSheet("background-color: #e1e1e1; color: #555;")

        self.validate_all_paths()

    def validate_all_paths(self):
        """Checks all three paths and enables/disables the OK button."""
        if not self.ensure_valid_directory:
            return                          # Don't restrict if not required

        cfg_path = self.text_fields['config'].text()
        wrk_path = self.text_fields['workshop'].text()
        ins_path = self.text_fields['install'].text()

        v1 = check_civ_config_works(cfg_path)
        if v1:
            self.text_fields['config'].setStyleSheet("background-color: #e1e1e1; color: #555;")
        v2 = check_workshop_works(wrk_path)
        if v2:
            self.text_fields['workshop'].setStyleSheet("background-color: #e1e1e1; color: #555;")
        v3 = check_civ_install_works(ins_path)
        if v3:
            self.text_fields['install'].setStyleSheet("background-color: #e1e1e1; color: #555;")

        self.ok_button.setEnabled(v1 and v2 and v3)

    def add_path_row(self, parent_layout, label_text, default_value, key):
        row_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label_text)

        line_edit = QtWidgets.QLineEdit()
        line_edit.setText(default_value if default_value else "")

        btn = QtWidgets.QPushButton("Browse...")

        row_layout.addWidget(label)
        row_layout.addWidget(line_edit)
        row_layout.addWidget(btn)
        parent_layout.addLayout(row_layout)
        self.path_edits[key] = line_edit
        return btn, line_edit

    def _calculate_initial_width(self):
        """Calculates the pixel width of the longest path and resizes the dialog."""
        metrics = self.fontMetrics()
        max_path_width = 0

        for edit in self.path_edits.values():
            try:
                text_width = metrics.horizontalAdvance(edit.text())
            except AttributeError:
                text_width = metrics.width(edit.text())

            if text_width > max_path_width:
                max_path_width = text_width

        padding = 40
        for edit in self.path_edits.values():
            edit.setMinimumWidth(max_path_width + padding)

        self.adjustSize()

    def browse_file(self, line_edit, caption):
        start_dir = os.path.dirname(line_edit.text()) if line_edit.text() else ""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, caption, start_dir)
        if path:
            line_edit.setText(path)

    def browse_folder(self, line_edit, caption):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, caption, line_edit.text())
        if path:
            line_edit.setText(path)

    def accept(self):
        civ_config = self.path_edits["config"].text()
        civ_workshop = self.path_edits["workshop"].text()
        civ_install = self.path_edits["install"].text()

        if civ_config:
            LocalFilePaths.civ_config = civ_config
        if civ_workshop:
            LocalFilePaths.workshop = civ_workshop
        if civ_install:
            LocalFilePaths.civ_install = civ_install

        super().accept()

    def reject(self):
        """If paths are mandatory and invalid, shut down the app."""
        if self.ensure_valid_directory:
            cfg = self.text_fields['config'].text()
            wrk = self.text_fields['workshop'].text()
            ins = self.text_fields['install'].text()
            valid = check_civ_config_works(cfg) and check_workshop_works(wrk) and check_civ_install_works(ins)
            if not valid:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Required paths are missing or invalid.")
                msg.setInformativeText("The application cannot continue without these settings. Closing...")
                msg.setWindowTitle("Configuration Error")
                msg.exec_()
                sys.exit()                  # Full application shutdown

        super().reject()
