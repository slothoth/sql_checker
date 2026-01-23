from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QVBoxLayout,  QLabel, QWidget, QApplication, )


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
