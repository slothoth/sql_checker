import sqlite3


class GraphModel:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def to_dict(self):
        return {"nodes": self.nodes, "edges": self.edges}

    def from_dict(self, data):
        self.nodes = data.get("nodes", [])
        self.edges = data.get("edges", [])


class BaseDB:
    def __init__(self):
        conn = sqlite3.connect("your_database.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        self.tables = [row[0] for row in cur.fetchall()]
        self.table_data = {}
        for table in self.tables:
            print(f"Table: {table}")
            cur.execute(f"SELECT * FROM {table}")
            self.table_data[table] = cur.fetchall()
        # query db for tables


def name_views_hub(views):
    named_views = []
    for i, view in enumerate(views, start=1):
        node_edge_counts = {}
        for edge in view["edges"]:
            node_edge_counts[edge["start_node_id"]] = node_edge_counts.get(edge["start_node_id"], 0) + 1
            node_edge_counts[edge["end_node_id"]] = node_edge_counts.get(edge["end_node_id"], 0) + 1

        hub_node = None
        if node_edge_counts:
            hub_node_id, max_edges = max(node_edge_counts.items(), key=lambda x: x[1])
            if max_edges > 1:  # ensure it actually has more edges than others
                for n in view["nodes"]:
                    if n["id"] == hub_node_id:
                        hub_node = n["texts"][0]  # first line = table name
                        break

        node_count = len(view["nodes"])
        base_name = f"View_{i:02d}"
        if hub_node:
            name = f"{hub_node} ({node_count})"
        elif node_count < 3:
            name = f"{'->'.join(n['texts'][0] for n in view['nodes'])}({node_count})"
        else:
            name = f"{base_name} ({node_count})"

        named_views.append({
            "name": name,
            "nodes": view["nodes"],
            "edges": view["edges"]
        })
    sort_views = sorted(named_views, key=lambda val: len(val["nodes"]), reverse=True)
    return sort_views


def name_views(views):
    named_views = []
    for i, view in enumerate(views, start=1):
        node_edge_counts = {}
        for edge in view["edges"]:
            node_edge_counts[edge["start_node_id"]] = node_edge_counts.get(edge["start_node_id"], 0) + 1
            node_edge_counts[edge["end_node_id"]] = node_edge_counts.get(edge["end_node_id"], 0) + 1

        root_node = view['name'].replace('View_', '')
        node_count = len(view["nodes"])
        base_name = f"View_{i:02d}"
        if root_node:
            name = f"{root_node} ({node_count})"
        elif node_count < 3:
            name = f"{'->'.join(n['texts'][0] for n in view['nodes'])}({node_count})"
        else:
            name = f"{base_name} ({node_count})"

        named_views.append({
            "name": name,
            "nodes": view["nodes"],
            "edges": view["edges"]
        })
    sort_views = sorted(named_views, key=lambda val: len(val["nodes"]), reverse=True)
    return sort_views