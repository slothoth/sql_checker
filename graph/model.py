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


def load_db_graph(db_path):
    full_path = f'resources/{db_path}'
    conn = sqlite3.connect(full_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    table_to_id = {t: i + 1 for i, t in enumerate(tables)}

    nodes = []
    for table, node_id in table_to_id.items():
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        nodes.append({
            "id": node_id,
            "texts": [table] + columns,
            "pos": {"x": node_id * 220.0, "y": 100.0}
        })

    edges = []
    for table, node_id in table_to_id.items():
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for ref in cursor.fetchall():
            ref_table = ref[2]
            if ref_table in table_to_id:
                start_id = node_id
                end_id = table_to_id[ref_table]
                edge = {
                    "start_node_id": min(start_id, end_id),
                    "end_node_id": max(start_id, end_id)
                }
                if edge not in edges:
                    edges.append(edge)

    conn.close()
    return {"nodes": nodes, "edges": edges}