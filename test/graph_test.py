from graph.node_controller import main as nodeEditorWindow
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    graph_editor_window = nodeEditorWindow()
    sys.exit(app.exec_())
