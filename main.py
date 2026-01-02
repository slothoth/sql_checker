import sys
import threading
import queue
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QSizePolicy, QPlainTextEdit, QComboBox
)

from model import model_run
from graph.node_controller import NodeEditorWindow
from syntax_highlighter import LogHighlighter
from graph.db_spec_singleton import db_spec, ages


class App(QWidget):
    entry1 = None
    entry2 = None
    entry3 = None
    run_button = None
    planner_button = None
    log_display = None
    log_highlighter = None
    ageComboBox = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Analyzer")
        self.setGeometry(100, 100, 700, 520)
        self.log_queue = queue.Queue()
        self.graph_editor_window = None
        self.init_ui()
        self.timer = self.startTimer(100)

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Civ Config
        self.entry1, btn1 = self.create_file_row(
            "Civ Config Location:", default_value=db_spec.civ_config, browse_func=self.set_civ_config
        )
        main_layout.addLayout(self.entry1)
        main_layout.addWidget(btn1)

        # Workshop Folder
        self.entry2, btn2 = self.create_file_row(
            "Workshop Folder:", default_value=db_spec.workshop, browse_func=self.set_workshop
        )
        main_layout.addLayout(self.entry2)
        main_layout.addWidget(btn2)

        # Civ Install
        self.entry3, btn3 = self.create_file_row(
            "Civ Install:", default_value=db_spec.civ_install, browse_func=self.set_civ_install
        )
        main_layout.addLayout(self.entry3)
        main_layout.addWidget(btn3)

        #
        self.ageComboBox = QComboBox()
        self.ageComboBox.addItems(ages)
        main_layout.addWidget(self.ageComboBox)

        # Run Analysis button
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setStyleSheet("background-color:#0078d7; color:#ffffff; font-weight:bold;")
        self.run_button.clicked.connect(self.start_analysis)
        main_layout.addWidget(self.run_button)

        # Graph planner button
        self.planner_button = QPushButton("Graph Planner")
        self.planner_button.setStyleSheet("background-color:#0078d7; color:#ffffff; font-weight:bold;")
        self.planner_button.clicked.connect(self.popout_graph_planner)
        main_layout.addWidget(self.planner_button)

        # Log Output
        log_label = QLabel("Log Output:")
        main_layout.addWidget(log_label)
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_highlighter = LogHighlighter(self.log_display.document())
        main_layout.addWidget(self.log_display, stretch=1)
        self.setLayout(main_layout)

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
            threading.Thread(target=model_run, args=(self.log_queue, True, self.ageComboBox.currentText()), daemon=True).start()
        else:
            threading.Thread(target=model_run, args=(self.log_queue, None, self.ageComboBox.currentText()), daemon=True).start()

    def timerEvent(self, event):
        try:
            while True:
                message = self.log_queue.get_nowait()
                if message is None:
                    self.run_button.setEnabled(True)
                else:
                    self.log_display.appendPlainText(str(message))  # ensure plain text insertion so the highlighter can run
                    cursor = self.log_display.textCursor()      # keep view scrolled to bottom
                    self.log_display.setTextCursor(cursor)
        except queue.Empty:
            pass

    def popout_graph_planner(self):
        if self.graph_editor_window is None:
            self.graph_editor_window = NodeEditorWindow(self)
        self.graph_editor_window.show()
        self.graph_editor_window.raise_()
        self.graph_editor_window.activateWindow()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
