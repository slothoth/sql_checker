from PyQt5.QtWidgets import QGraphicsScene, QMenu, QAction, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import QPointF

from graph.view import EdgeItem, NodeItem


class GraphController(QGraphicsScene):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.node_counter = 0
        self.setBackgroundBrush(QBrush(QColor("#f0f0f0")))
        self.sorted_positions = {}

    def add_node(self, pos, primary_texts=None, secondary_texts=None, node_id=None):
        if primary_texts is None:
            primary_texts = [None, None]
        if secondary_texts is None:
            secondary_texts = [None, None]
        if node_id is None:
            self.node_counter += 1
            node_id = f"node_{self.node_counter}"
        node = NodeItem(node_id, primary_texts=primary_texts, secondary_texts=secondary_texts)
        node.setPos(pos)
        self.addItem(node)
        return node

    def add_edge(self, start_node, start_field_index, end_node, end_field_index):
        edge = EdgeItem(start_node, start_field_index, end_node, end_field_index)
        self.addItem(edge)
        start_node.edges.append(edge)
        end_node.edges.append(edge)
        return edge

    def contextMenuEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        field_index = None

        # find if the click is on a text field
        if isinstance(item, QGraphicsTextItem) and isinstance(item.parentItem(), NodeItem):
            node_item = item.parentItem()
            if item in node_item.text_items:
                field_index = node_item.text_items.index(item)
        else:
            # find the node by walking up parents
            while item and not isinstance(item, NodeItem):
                item = item.parentItem()
            node_item = item

        menu = QMenu()

        if isinstance(node_item, NodeItem):
            add_conn = QAction("Add Connecting Node", menu)
            add_conn.triggered.connect(
                lambda: self.add_connecting_node(node_item, event.scenePos(), field_index)
            )

            delete = QAction("Delete Node", menu)
            delete.triggered.connect(lambda: self.delete_node(node_item))

            menu.addAction(add_conn)
            menu.addSeparator()
            menu.addAction(delete)
        else:
            add_node = QAction("Add Node", menu)
            add_node.triggered.connect(lambda: self.add_node(event.scenePos()))
            menu.addAction(add_node)

        menu.exec_(event.screenPos())

    def add_connecting_node(self, start_node, pos, start_field_index=None):
        new_node = self.add_node(pos + QPointF(50, 50))
        if start_field_index is None:
            start_field_index = 0
        self.add_edge(start_node, start_field_index, new_node, 0)
        return new_node

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
                    "texts": [i.toPlainText() for i in item.text_items],
                    "pos": {"x": item.pos().x(), "y": item.pos().y()}
                })
            elif isinstance(item, EdgeItem):
                if item.start_node.node_id != item.end_node.node_id:
                    edges.append({
                        "start_node_id": item.start_node.node_id,
                        "start_field_index": item.start_field_index,
                        "end_node_id": item.end_node.node_id,
                        "end_field_index": item.end_field_index
                    })
        return {"nodes": nodes, "edges": edges}

    def load_graph_data(self, data):
        self.clear_scene()
        nodes = {}
        for node_data in data.get("nodes", []):
            n = self.add_node(
                QPointF(node_data["pos"]["x"], node_data["pos"]["y"]),
                primary_texts=node_data["primary_texts"], secondary_texts=node_data["secondary_texts"],
                node_id=node_data["id"]
            )
            nodes[n.node_id] = n

        for edge_data in data.get("edges", []):
            s = nodes.get(edge_data["start_node_id"])
            e = nodes.get(edge_data["end_node_id"])
            idx = edge_data.get("start_field_index", 0)
            end_index = edge_data.get("end_field_index", 0)
            if s and e:
                self.add_edge(s, idx, e, end_index)

    def sort_graph(self):       # orphaned from when we were dynamically sorting. Might be useful for user generated
        edges = []              # stuff later tho
        nodes = {}

        # Collect all nodes and edges from the scene
        for item in self.items():
            if isinstance(item, NodeItem):
                nodes[item.node_id] = item
            elif isinstance(item, EdgeItem):
                edges.append((item.start_node.node_id, item.end_node.node_id))

        # Build adjacency and indegree counts
        adjacency = {nid: [] for nid in nodes}
        indegree = {nid: 0 for nid in nodes}
        for start, end in edges:
            adjacency[start].append(end)
            indegree[end] += 1

        # Topological-like layering
        layers = []
        current_layer = [n for n, deg in indegree.items() if deg == 0]
        visited = set(current_layer)
        while current_layer:
            layers.append(current_layer)
            next_layer = []
            for node in current_layer:
                for target in adjacency[node]:
                    indegree[target] -= 1
                    if indegree[target] == 0 and target not in visited:
                        next_layer.append(target)
                        visited.add(target)
            current_layer = next_layer

        # Fallback if graph isn't acyclic
        if not layers:
            layers = [list(nodes.keys())]

        # Apply layout: horizontal layers, vertical spacing
        x_spacing, y_spacing = 250, 150
        for layer_idx, layer in enumerate(layers):
            for i, node_id in enumerate(layer):
                node = nodes[node_id]
                x = layer_idx * x_spacing
                y = i * y_spacing
                node.setPos(QPointF(x, y))
                node.position_changed.emit()

        # Update edges visually
        for item in self.items():
            if isinstance(item, EdgeItem):
                item.update_position()
