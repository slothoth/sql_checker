import sys
from PyQt5.QtWidgets import QApplication

from graph.node_controller import NodeEditorWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NodeEditorWindow()
    window.show()
    sys.exit(app.exec())