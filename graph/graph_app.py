import json
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog
# project imports
from graph.model import GraphModel
from graph.view import GraphView
from graph.controller import GraphController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph Editor (MVC)")
        self.setGeometry(100, 100, 1000, 800)
        self.model = GraphModel()
        self.controller = GraphController(self.model)
        self.view = GraphView(self.controller)
        self.setCentralWidget(self.view)
        self.create_menu()
        self.new_graph()

    def create_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        new_action = QAction("&New", self)
        new_action.triggered.connect(self.new_graph)
        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.save_graph)
        load_action = QAction("&Load", self)
        load_action.triggered.connect(self.load_graph)
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        for a in (new_action, save_action, load_action, exit_action):
            file_menu.addAction(a)

    def new_graph(self):
        self.controller.clear_scene()

    def save_graph(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
        if not path:
            return
        data = self.controller.get_graph_data()
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving file: {e}")

    def load_graph(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Graph", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self.controller.load_graph_data(data)
        except Exception as e:
            print(f"Error loading file: {e}")
