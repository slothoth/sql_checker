from graph.node_controller import main as nodeEditorWindow
from PyQt5.QtWidgets import QApplication
import sys

# from graph.model import BaseDB
# BaseDB('antiquity-db.sqlite')     # if we need to change database spec in json

if __name__ == '__main__':
    app = QApplication(sys.argv)
    graph_editor_window = nodeEditorWindow()
    sys.exit(app.exec_())
