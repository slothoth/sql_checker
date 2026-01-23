import threading
import queue
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QSizePolicy, QPlainTextEdit, QComboBox
)

from model import model_run
from syntax_highlighter import LogHighlighter
from graph.singletons.db_spec_singleton import db_spec
from constants import ages
from graph.singletons.filepaths import LocalFilePaths


class CollapsiblePanel(QWidget):
    entry1 = None
    entry2 = None
    entry3 = None
    run_button = None
    planner_button = None
    log_display = None
    log_highlighter = None
    ageComboBox = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_queue = queue.Queue()

        self.toggle_btn = QPushButton("▶")
        self.toggle_btn.setFixedWidth(18)
        self.toggle_btn.clicked.connect(self.toggle)

        self.content = QWidget()
        #self.content.setFixedWidth(220)

        content_layout = QVBoxLayout(self.content)
        # Civ Config
        self.entry1, btn1 = self.create_file_row(
            "Civ Config Location:", default_value=LocalFilePaths.civ_config, browse_func=self.set_civ_config
        )
        content_layout.addLayout(self.entry1)
        content_layout.addWidget(btn1)

        # Workshop Folder
        self.entry2, btn2 = self.create_file_row(
            "Workshop Folder:", default_value=LocalFilePaths.workshop, browse_func=self.set_workshop
        )
        content_layout.addLayout(self.entry2)
        content_layout.addWidget(btn2)

        # Civ Install
        self.entry3, btn3 = self.create_file_row(
            "Civ Install:", default_value=LocalFilePaths.civ_install, browse_func=self.set_civ_install
        )
        content_layout.addLayout(self.entry3)
        content_layout.addWidget(btn3)

        # age for running game config analysis
        self.ageComboBox = QComboBox()
        self.ageComboBox.addItems(ages)
        content_layout.addWidget(self.ageComboBox)

        # Run Analysis button
        self.run_button = QPushButton("Run Current Game Configuration")
        self.run_button.setStyleSheet("background-color:#0078d7; color:#ffffff; font-weight:bold;")
        self.run_button.clicked.connect(self.start_analysis)
        content_layout.addWidget(self.run_button)

        # Log Output
        log_label = QLabel("Log Output")
        content_layout.addWidget(log_label)
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_highlighter = LogHighlighter(self.log_display.document())
        content_layout.addWidget(self.log_display, stretch=1)

        content_layout.addStretch()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.content)
        layout.addWidget(self.toggle_btn)

        self.expanded = True
        self.timer = self.startTimer(100)

    def toggle(self):
        self.expanded = not self.expanded
        self.content.setVisible(self.expanded)
        if self.expanded:
            self.toggle_btn.setText("▶")
        else:
            self.toggle_btn.setText("◀")

    @staticmethod
    def create_file_row(label_text, default_value="", browse_func=None):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        line_edit = QLineEdit()
        line_edit.setText(default_value)
        btn = QPushButton("Browse...")
        if browse_func:
            btn.clicked.connect(browse_func)
        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(btn)
        return layout, btn

    def set_civ_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Civ Config File")
        if path:
            db_spec.update_civ_config(path)
            self.layout().itemAt(0).itemAt(1).widget().setText(path)

    def set_workshop(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Workshop Folder")
        if path:
            db_spec.update_steam_workshop(path)
            self.layout().itemAt(2).itemAt(1).widget().setText(path)

    def set_civ_install(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Civ Install File")
        if path:
            db_spec.update_civ_install(path)
            self.layout().itemAt(4).itemAt(1).widget().setText(path)

    def start_analysis(self, extra_sql=None):
        self.run_button.setEnabled(False)
        if extra_sql is not None:
            threading.Thread(target=model_run, args=(self.log_queue, True, self.ageComboBox.currentText()),
                             daemon=True).start()
        else:
            threading.Thread(target=model_run, args=(self.log_queue, None, self.ageComboBox.currentText()),
                             daemon=True).start()

    def timerEvent(self, event):
        try:
            while True:
                message = self.log_queue.get_nowait()
                if message is None:
                    self.run_button.setEnabled(True)
                else:
                    self.log_display.appendPlainText(
                        str(message))  # ensure plain text insertion so the highlighter can run
                    cursor = self.log_display.textCursor()  # keep view scrolled to bottom
                    self.log_display.setTextCursor(cursor)
        except queue.Empty:
            pass
