import sys
import threading
import queue
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QSizePolicy
)
import os
from pathlib import Path

if sys.platform == 'win32':
    import winreg

from model import model_run
from graph.graph_app import MainWindow as GraphEditorWindow


class App(QWidget):
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
        self.entry1, btn1, self.folder_path_civ_config = self.create_file_row(
            "Civ Config Location:", default_value=find_civ_config(), browse_func=self.set_civ_config
        )
        main_layout.addLayout(self.entry1)
        main_layout.addWidget(btn1)

        # Workshop Folder
        self.entry2, btn2, self.folder_path_workshop_input = self.create_file_row(
            "Workshop Folder:", default_value=find_workshop(), browse_func=self.set_workshop
        )
        main_layout.addLayout(self.entry2)
        main_layout.addWidget(btn2)

        # Civ Install
        self.entry3, btn3, self.folder_path_civ_install = self.create_file_row(
            "Civ Install:", default_value=find_civ_install(), browse_func=self.set_civ_install
        )
        main_layout.addLayout(self.entry3)
        main_layout.addWidget(btn3)

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
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background-color:#ffffff; color:#000000; font-family:Courier New;")
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.log_display)



        self.setLayout(main_layout)


    def create_file_row(self, label_text, default_value="", browse_func=None):
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
        return layout, btn, default_value

    def set_civ_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Civ Config File")
        if path:
            self.folder_path_civ_config = path
            self.layout().itemAt(0).itemAt(1).widget().setText(path)

    def set_workshop(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Workshop Folder")
        if path:
            self.folder_path_workshop_input = path
            self.layout().itemAt(2).itemAt(1).widget().setText(path)

    def set_civ_install(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Civ Install File")
        if path:
            self.folder_path_civ_install = path
            self.layout().itemAt(4).itemAt(1).widget().setText(path)

    def start_analysis(self):
        civ_install = self.folder_path_civ_install
        civ_config = self.folder_path_civ_config
        workshop = self.folder_path_workshop_input
        self.run_button.setEnabled(False)
        threading.Thread(target=model_run, args=(civ_install, civ_config, workshop, self.log_queue), daemon=True).start()

    def timerEvent(self, event):
        try:
            while True:
                message = self.log_queue.get_nowait()
                if message is None:
                    self.run_button.setEnabled(True)
                else:
                    self.log_display.append(str(message))
        except queue.Empty:
            pass

    def popout_graph_planner(self):
        if self.graph_editor_window is None:
            self.graph_editor_window = GraphEditorWindow()
        self.graph_editor_window.show()
        self.graph_editor_window.raise_()
        self.graph_editor_window.activateWindow()


def find_steam_install():
    if sys.platform == 'win32':
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
    elif sys.platform == 'win64':
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Wow6432Node\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
    elif sys.platform == 'darwin':
        user_home = Path.home()
        steam_path = str(user_home / "Library" / "Application Support" / "Steam")
    else:
        return None
    return steam_path


def find_civ_install():
    steam_path = find_steam_install()
    if steam_path is None:
        return None
    if sys.platform == 'win32':
        civ_install = os.path.join(steam_path, "steamapps/common/Sid Meier's Civilization VII")
    elif sys.platform == 'darwin':
        civ_install = os.path.join(steam_path, "steamapps/common/Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources")
    else:
        return None
    return civ_install


def find_workshop():
    steam_path = find_steam_install()
    if steam_path is None:
        return None
    return f"{steam_path}/steamapps/workshop/content/1295660/"


def find_civ_config():
    if sys.platform == 'win32':
        local_appdata = os.getenv('LOCALAPPDATA')
        civ_install = f"{local_appdata}\Firaxis Games\Sid Meier's Civilization VII"
        print(civ_install)
    elif sys.platform == 'darwin':
        user_home = Path.home()
        civ_install = str(user_home / "Library" / "Application Support" / "Civilization VII")
    else:
        return None
    return civ_install


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
