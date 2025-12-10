import sqlite3
import json


class GraphModel:
    nodes = []
    edges = []

    def __init__(self, database_path):
        self.DatabaseModel = BaseDB(database_path)

    def to_dict(self):
        return {"nodes": self.nodes, "edges": self.edges}

    def from_dict(self, data):
        self.nodes = data.get("nodes", [])
        self.edges = data.get("edges", [])


class BaseDB:
    def __init__(self, full_path):
        self.table_data = {}
        self.tables = []
        self.setup_table_infos(full_path)
        self.dump_json_form()
        self.dump_unique_pks(full_path)

    def setup_table_infos(self, db_path):
        full_path = f"resources/{db_path}"
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        self.tables = [row[0] for row in cursor.fetchall()]
        table_to_id = {t: i + 1 for i, t in enumerate(self.tables)}
        for table in self.tables:
            cursor.execute(f"PRAGMA table_info({table})")
            rows = cursor.fetchall()
            columns = [r[1] for r in rows]
            notnulls = [r[3] for r in rows]
            defaults = [r[4] for r in rows]
            primary_texts = [i for idx, i in enumerate(columns) if notnulls[idx] == 1 and defaults[idx] is None]
            secondary_texts = [i for i in columns if i not in primary_texts]
            self.table_data[table] = {}
            self.table_data[table]['primary_keys'] = [i[1] for i in rows if i[5] == 1]
            self.table_data[table]['primary_texts'] = primary_texts
            self.table_data[table]['secondary_texts'] = secondary_texts
            columns.sort(key=lambda x: 0 if x in self.table_data[table]['primary_keys'] else 1)
            self.table_data[table]['all_cols'] = columns
            self.table_data[table]['default_values'] = {i[1]: i[4] for i in rows if i[4] is not None}

        for table in self.tables:
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            self.table_data[table]['foreign_keys'] = {}
            for ref in cursor.fetchall():
                ref_table, table_col = ref[2], ref[3]
                if ref_table in self.tables:
                    self.table_data[table]['foreign_keys'][table_col] = ref_table
                    if not self.table_data[ref_table].get('backlink_fk', None):
                        self.table_data[ref_table]['backlink_fk'] = {}
                    self.table_data[ref_table]['backlink_fk'][table_col] = table         # for backlinks

        conn.close()

    def dump_json_form(self):
        with open('resources/db_spec.json', 'w') as f:
            f.write(json.dumps(self.table_data))

    def dump_unique_pks(self, db_path):
        possible_firaxis_pks, double_keys, possible_vals = {}, [], {}
        full_path = f"resources/{db_path}"
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        for table in self.tables:
            primary_keys = self.table_data[table]['primary_keys']
            if len(primary_keys) == 1:
                pk = primary_keys[0]
                rows = cursor.execute(f"SELECT DISTINCT {pk} FROM {table}").fetchall()
                possible_firaxis_pks[table] = [r[0] for r in rows]
            else:
                double_keys.append(table)

        for table in self.tables:
            foreign_keys = self.table_data[table]['foreign_keys']
            for fk, table_ref in foreign_keys.items():
                key_possible_vals = possible_firaxis_pks[table_ref]
                if table not in possible_vals:
                    possible_vals[table] = {}
                if fk not in possible_vals[table]:
                    possible_vals[table][fk] = []
                possible_vals[table][fk].extend(key_possible_vals)

        for tbl, col_poss_dicts in possible_vals.items():
            for col in col_poss_dicts:
                col_poss_dicts[col] = list(set(col_poss_dicts[col]))
        with open('resources/db_possible_vals.json', 'w') as f:
            f.write(json.dumps(possible_vals))


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
