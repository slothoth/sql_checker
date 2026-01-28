import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen, QProgressBar, QLabel, QDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QWaitCondition, QMutex
from PyQt5.QtGui import QPixmap

from graph.utils import resource_path
from graph.windows import PathSettingsDialog
from graph.singletons.filepaths import LocalFilePaths       # needed because we want logger initialised

LocalFilePaths.initialize_paths()


class SetupWorker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str, int)
    request_paths = pyqtSignal(dict)
    dialog = None

    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.condition = QWaitCondition()

    def run(self):
        self.progress.emit("resources/DB_Start.png", 0)
        from graph.singletons.db_spec_singleton import db_spec
        paths = {'config': LocalFilePaths.civ_config, 'install': LocalFilePaths.civ_install,
                 'workshop': LocalFilePaths.workshop}
        if not all(paths.values()):
            self.mutex.lock()
            self.request_paths.emit(paths)  # pauses worker thread until main thread hits wakeAll()
            self.condition.wait(self.mutex)
            self.mutex.unlock()                 # db_spec initialization will continue

        patch_occurred, latest = db_spec.check_firaxis_patched()
        if patch_occurred:
            self.progress.emit(resource_path("resources/DB_Changes.png"), 10)
        else:
            self.progress.emit(resource_path("resources/DB_Loading.png"), 50)
        db_spec.initialize(patch_occurred, latest)

        self.progress.emit("resources/DB_Loading.png", 50)

        db_spec.initialize(patch_occurred, latest)

        self.progress.emit("resources/DB_Done.png", 100)
        self.finished.emit()


class MainController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)        # remove quit on close as optional dialog triggers it

        splash_pix = QPixmap(resource_path("resources/LoadingSplash.png"))
        self.splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        self.progress_bar = QProgressBar(self.splash)

        self.overlay_label = QLabel(self.splash)
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setGeometry(70, splash_pix.height() - 80, 900, 75)    # mid bottom
        self.overlay_label.setStyleSheet("background: transparent;")

        self.progress_bar = QProgressBar(self.splash)
        self.progress_bar.setGeometry(10, splash_pix.height() - 30, splash_pix.width() - 20, 20)    # mid bottom
        self.progress_bar.setStyleSheet("""
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
        self.splash.show()

        self.worker = SetupWorker()
        self.worker.progress.connect(self.update_splash)
        self.worker.request_paths.connect(self.handle_path_request)
        self.worker.finished.connect(self.on_finished)

        self.worker.start()

        self.main_window = None     # kept main window ref for no garbage collection

    def update_splash(self, message, value):
        self.progress_bar.setValue(value)
        icon_pix = QPixmap(message)
        if not icon_pix.isNull():
            self.overlay_label.setPixmap(icon_pix)

    def handle_path_request(self, paths):
        dlg = PathSettingsDialog(paths=paths)
        dlg.exec_()
        self.worker.condition.wakeAll()

    def on_finished(self):
        from graph.node_controller import NodeEditorWindow
        self.main_window = NodeEditorWindow()
        self.main_window.show()
        self.splash.finish(self.main_window)
        self.app.setQuitOnLastWindowClosed(True)            # restore quit on close

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    controller = MainController()
    controller.run()
