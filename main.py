import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen, QProgressBar, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

from graph.singletons.filepaths import LocalFilePaths       # needed because we want logger initialised
from graph.utils import resource_path
from graph.windows import show_dialog_if_missed_path


class SetupWorker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str, int)

    def run(self):
        self.progress.emit(resource_path("resources/DB_Start.png"), 0)   # Checking Civ install state for changes...
        from graph.singletons.db_spec_singleton import db_spec
        paths = {'config': LocalFilePaths.civ_config, 'install': LocalFilePaths.civ_install,
                 'workshop': LocalFilePaths.workshop}
        show_dialog_if_missed_path(paths)
        patch_occurred, latest = db_spec.check_firaxis_patched()
        if patch_occurred:
            self.progress.emit(resource_path("resources/DB_Changes.png"), 10)
        else:
            self.progress.emit(resource_path("resources/DB_Loading.png"), 50)        # Loading Database Specifications...
        db_spec.initialize(patch_occurred, latest)
        self.finished.emit()


def main():
    app = QApplication(sys.argv)

    splash_pix = QPixmap(resource_path("resources/LoadingSplash.png"))
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)

    # --- Overlay Image Label ---
    # This sits on top of the splash background
    overlay_label = QLabel(splash)
    overlay_label.setAlignment(Qt.AlignCenter)
    # Position it where you want the icon to appear (e.g., top right)
    overlay_label.setGeometry(70, splash_pix.height()-80, 900, 75)
    overlay_label.setStyleSheet("background: transparent;")

    progress_bar = QProgressBar(splash)
    progress_bar.setGeometry(10, splash_pix.height() - 30, splash_pix.width() - 20, 20)
    progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 20px;
            }
        """)

    splash.show()

    worker = SetupWorker()

    def update_splash(message, value):
        progress_bar.setValue(value)
        icon_pix = QPixmap(message)
        if not icon_pix.isNull():
            overlay_label.setPixmap(icon_pix)

    worker.progress.connect(update_splash)

    def on_finished():
        from graph.node_controller import NodeEditorWindow
        window = NodeEditorWindow()
        window.show()
        splash.finish(window)

    worker.finished.connect(on_finished)
    worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
