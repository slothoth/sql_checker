from graph.view import EdgeItem, NodeItem
from PyQt5.QtWidgets import QGraphicsScene, QMenu, QAction
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import QPointF


class GraphController(QGraphicsScene):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.node_counter = 0
        self.setBackgroundBrush(QBrush(QColor("#f0f0f0")))

    def add_node(self, pos, text1=None, text2=None, node_id=None):
        if node_id is None:
            self.node_counter += 1
            node_id = f"node_{self.node_counter}"
        node = NodeItem(node_id, text1 or "New Node", text2 or "Click to edit...")
        node.setPos(pos)
        self.addItem(node)
        return node

    def add_edge(self, start_node, end_node):
        edge = EdgeItem(start_node, end_node)
        start_node.edges.append(edge)
        end_node.edges.append(edge)
        self.addItem(edge)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        while item and not isinstance(item, NodeItem):
            item = item.parentItem()
        menu = QMenu()
        if isinstance(item, NodeItem):
            add_conn = QAction("Add Connecting Node", menu)
            add_conn.triggered.connect(lambda: self.add_connecting_node(item, event.scenePos()))
            delete = QAction("Delete Node", menu)
            delete.triggered.connect(lambda: self.delete_node(item))
            menu.addAction(add_conn)
            menu.addSeparator()
            menu.addAction(delete)
        else:
            add_node = QAction("Add Node", menu)
            add_node.triggered.connect(lambda: self.add_node(event.scenePos()))
            menu.addAction(add_node)
        menu.exec_(event.screenPos())

    def add_connecting_node(self, node, pos):
        end_node = self.add_node(pos + QPointF(50, 50))
        self.add_edge(node, end_node)

    def delete_node(self, node):
        for edge in list(node.edges):
            self.removeItem(edge)
            other = edge.start_node if edge.end_node == node else edge.end_node
            if edge in other.edges:
                other.edges.remove(edge)
        self.removeItem(node)

    def clear_scene(self):
        self.clear()
        self.node_counter = 0

    def get_graph_data(self):
        nodes, edges = [], []
        for item in self.items():
            if isinstance(item, NodeItem):
                nodes.append({
                    "id": item.node_id,
                    "text1": item.text1_item.toPlainText(),
                    "text2": item.text2_item.toPlainText(),
                    "pos": {"x": item.pos().x(), "y": item.pos().y()}
                })
            elif isinstance(item, EdgeItem):
                if item.start_node.node_id < item.end_node.node_id:
                    edges.append({
                        "start_node_id": item.start_node.node_id,
                        "end_node_id": item.end_node.node_id
                    })
        return {"nodes": nodes, "edges": edges}

    def load_graph_data(self, data):
        self.clear_scene()
        nodes = {}
        for node_data in data.get("nodes", []):
            n = self.add_node(QPointF(node_data["pos"]["x"], node_data["pos"]["y"]),
                              node_data["text1"], node_data["text2"], node_data["id"])
            nodes[n.node_id] = n
        for edge_data in data.get("edges", []):
            s, e = nodes.get(edge_data["start_node_id"]), nodes.get(edge_data["end_node_id"])
            if s and e:
                self.add_edge(s, e)
