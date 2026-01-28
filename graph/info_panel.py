import queue
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QPlainTextEdit, QComboBox
)

from syntax_highlighter import LogHighlighter
from constants import ages
from graph.utils import LogPusher
from graph.windows import PathSettingsDialog


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

        content_layout = QVBoxLayout(self.content)
        # Path Settings Button
        self.settings_btn = QPushButton("Path Settings...")
        self.settings_btn.clicked.connect(self.open_settings)
        content_layout.addWidget(self.settings_btn)

        # age for running game config analysis
        self.ageComboBox = QComboBox()
        self.ageComboBox.addItems(ages)
        content_layout.addWidget(self.ageComboBox)

        # Run Analysis button
        self.run_button = QPushButton("Clear Log")
        self.run_button.setStyleSheet("background-color:#0078d7; color:#ffffff; font-weight:bold;")
        self.run_button.clicked.connect(self.clear_log)
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
        LogPusher.set_log_widget(self.log_display)

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

    def expand_panel(self):
        if self.expanded:
            return
        self.expanded = True
        self.content.setVisible(self.expanded)
        self.toggle_btn.setText("▶")

    def clear_log(self):
        self.log_display.clear()

    def open_settings(self):
        dlg = PathSettingsDialog(self)
        dlg.exec_()

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
