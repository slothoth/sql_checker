import sqlite3
import networkx as nx
import json
import graphviz

def load_db_graph(db_path):
    full_path = f'resources/{db_path}'
    conn = sqlite3.connect(full_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    table_to_id = {t: i + 1 for i, t in enumerate(tables)}

    nodes = []
    table_columns = {}
    for table, node_id in table_to_id.items():
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        table_columns[table] = columns
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
            ref_column = ref[3]  # the column in the foreign table
            if ref_table in table_to_id:
                start_field_index = table_columns[table].index(ref[3]) + 1  # +1 because 0 is the table name
                edges.append({
                    "start_node_id": node_id,
                    "start_field_index": start_field_index,
                    "end_node_id": table_to_id[ref_table],
                    "end_field_index": 0  # connect to table name of target
                })

    conn.close()
    return {"nodes": nodes, "edges": edges}


def separate_db_graphs(db_path):
    full_path = f"resources/{db_path}"
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
            "pos": {"x": node_id * 200.0, "y": 100.0}
        })

    adjacency = {t: set() for t in tables}
    type_connections = set()

    for table in tables:
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for ref in cursor.fetchall():
            ref_table = ref[2]
            if ref_table not in tables:
                continue
            if "Types" in (table, ref_table):
                type_connections.add((table, ref_table))
                continue
            adjacency[table].add(ref_table)
            adjacency[ref_table].add(table)

    conn.close()

    seen = set()
    groups = []
    for t in tables:
        if t in seen or t == "Types":
            continue
        stack = [t]
        group = set()
        while stack:
            curr = stack.pop()
            if curr in seen:
                continue
            seen.add(curr)
            group.add(curr)
            stack.extend(adjacency[curr])
        groups.append(group)

    # include Types in any group it connects to
    for group in groups:
        connected_to_types = any(
            ("Types", t) in type_connections or (t, "Types") in type_connections
            for t in group
        )
        if connected_to_types and "Types" in tables:
            group.add("Types")

    views = []
    for i, group in enumerate(groups, start=1):
        group_nodes = [n for n in nodes if n["texts"][0] in group]
        group_edges = []
        for table in group:
            cursor = sqlite3.connect(full_path).cursor()
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            for ref in cursor.fetchall():
                ref_table = ref[2]
                if ref_table in group:
                    edge = {
                        "start_node_id": table_to_id[table],
                        "end_node_id": table_to_id[ref_table]
                    }
                    if edge not in group_edges and {
                        "start_node_id": edge["end_node_id"],
                        "end_node_id": edge["start_node_id"]
                    } not in group_edges:
                        group_edges.append(edge)
            cursor.connection.close()
        sorted_graph_data = presort({"nodes": group_nodes, "edges": group_edges})

        views.append({
            "name": f"View_{i + 1}",
            "nodes": sorted_graph_data["nodes"],
            "edges": sorted_graph_data["edges"]
        })

    return views


def presort(data):
    edges = []
    nodes = {}

    for idx, node_data in enumerate(data.get("nodes", [])):
        nodes[node_data["id"]] = node_data
        node_data['idx'] = idx

    for edge_data in data.get("edges", []):
        edges.append((edge_data["start_node_id"], edge_data["end_node_id"]))

    adjacency = {nid: [] for nid in nodes}
    indegree = {nid: 0 for nid in nodes}
    for start, end in edges:
        adjacency[start].append(end)
        indegree[end] += 1

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

    x_spacing, y_spacing = 250, 150
    for layer_idx, layer in enumerate(layers):
        for i, node_id in enumerate(layer):
            node = nodes[node_id]
            x = layer_idx * x_spacing
            y = i * y_spacing
            node["pos"]["x"], node["pos"]["y"] = x, y

    sorted_nodes = sorted([i for i in nodes.values()], key=lambda val: val["idx"])
    return {"nodes": sorted_nodes, "edges": data.get("edges", [])}



def get_table_info(full_path):
    conn = sqlite3.connect(full_path)
    cursor = conn.cursor()

    # 1. Get All Tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    all_tables = [row[0] for row in cursor.fetchall()]
    table_to_id = {t: i + 1 for i, t in enumerate(all_tables)}

    # 2. Get Node Info (Columns & Visual Height)
    node_info = {}
    for table in all_tables:
        cursor.execute(f"PRAGMA table_info({table})")
        rows = cursor.fetchall()
        columns = [r[1] for r in rows]
        notnulls = [r[3] for r in rows]
        defaults = [r[4] for r in rows]
        primary_texts = [i for idx, i in enumerate(columns) if notnulls[idx] == 1 and defaults[idx] is None]
        secondary_texts = [i for i in columns if i not in primary_texts]
        # get cols where there needs to be a value, but there isnt a default value
        # Calculate height roughly based on column count
        height = 70 + len(primary_texts) * 18
        node_info[table] = {
            "id": table_to_id[table],
            "primary_texts": [table] + primary_texts,
            "secondary_texts": secondary_texts,
            "height": height
        }
    conn.close()
    return node_info, all_tables, table_to_id


def scale_factor(raw_pos, padding, target_size):
    min_x = min(x for x, y in raw_pos.values())
    min_y = min(y for x, y in raw_pos.values())
    max_x_norm = 0.0
    max_y_norm = 0.0
    normalized_pos = {}
    for node, (rx, ry) in raw_pos.items():
        norm_x = rx - min_x          # Apply shift to normalize to (0,0)
        norm_y = ry - min_y
        normalized_pos[node] = (norm_x, norm_y)
        if norm_x > max_x_norm:             # Track the maximum extent
            max_x_norm = norm_x
        if norm_y > max_y_norm:
            max_y_norm = norm_y

    # 2. Calculate the Dynamic Scaling Factor
    # If the graph is just a single line or point (max is 0), use default scale
    if max_x_norm == 0 or max_y_norm == 0:
        dynamic_scale = target_size
    else:                                       # (X or Y) into the TARGET_SIZE minus padding.
        target_dim = target_size - padding      # Calculate the scale factor needed to fit the largest dimension
        scale_x = target_dim / max_x_norm       # The scale factor must be the MINIMUM of the X and Y ratios
        scale_y = target_dim / max_y_norm       # to ensure both dimensions fit within the TARGET_SIZE box.
        dynamic_scale = min(scale_x, scale_y)
    return normalized_pos, dynamic_scale


def force_forward_spring_graphs(db_path, normalise=True):
    PADDING = 50
    TARGET_SIZE = 800  # Target maximum pixel width/height for any graph view
    full_path = f"resources/{db_path}"
    node_info, all_tables, table_to_id = get_table_info(full_path)

    # 3. Build the Master Dependency Graph
    # Direction: Table -> Table it depends on (Foreign Key target)
    MasterG = nx.DiGraph()
    MasterG.add_nodes_from(all_tables)

    conn = sqlite3.connect(full_path)
    cursor = conn.cursor()
    for table in all_tables:
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for ref in cursor.fetchall():
            ref_table = ref[2]
            if ref_table in all_tables:
                MasterG.add_edge(table, ref_table)

    conn.close()

    views = []
    # 4. Create a View tailored for EACH table
    for root_table in all_tables:
        dependencies = nx.descendants(MasterG, root_table)  # nodes reachable from this table (recursive foreign keys)
        group_nodes = list(dependencies) + [root_table]
        if len(group_nodes) < 2:
            continue
        subgraph = MasterG.subgraph(group_nodes)
        # undirected convert to Kamada-Kawai as it calculates geometric distances
        # scale=1.0 gives us coordinates roughly -1 to 1

        # raw_pos = nx.spring_layout(subgraph, k=2, iterations=100, seed=42)
        raw_pos = nx.spectral_layout(subgraph)
        if normalise:
            normalized_pos, dynamic_scale = scale_factor(raw_pos, PADDING, TARGET_SIZE)
        else:
            normalized_pos, dynamic_scale = raw_pos, 1

        # E. Apply Dynamic Scale and Output
        final_nodes = []
        for node in group_nodes:
            info = node_info[node]
            norm_x, norm_y = normalized_pos[node]

            # Apply the calculated scale factor
            pixel_x = float(norm_x * dynamic_scale) + PADDING / 2
            pixel_y = float(norm_y * dynamic_scale) + PADDING / 2

            final_nodes.append({
                "id": info["id"],
                "primary_texts": info["primary_texts"],
                "secondary_texts": info["secondary_texts"],
                "pos": {
                    "x": pixel_x,
                    "y": pixel_y
                }
            })

        # E. Define Edges (Only those existing within this subgraph)
        final_edges = []
        for u, v in subgraph.edges():
            final_edges.append({
                "start_node_id": table_to_id[u],
                "end_node_id": table_to_id[v]
            })

        views.append({
            "name": f"View_{root_table}",
            "root_table": root_table,
            "nodes": final_nodes,
            "edges": final_edges
        })

    # Sort views by name or complexity
    views.sort(key=lambda v: v['name'])
    return views


def force_forward_kamada_kamai_graphs(db_path):
    PADDING = 50
    TARGET_SIZE = 800  # Target maximum pixel width/height for any graph view
    full_path = f"resources/{db_path}"
    node_info, all_tables, table_to_id = get_table_info(full_path)

    # 3. Build the Master Dependency Graph
    # Direction: Table -> Table it depends on (Foreign Key target)
    MasterG = nx.DiGraph()
    MasterG.add_nodes_from(all_tables)

    conn = sqlite3.connect(full_path)
    cursor = conn.cursor()
    for table in all_tables:
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for ref in cursor.fetchall():
            ref_table = ref[2]
            if ref_table in all_tables:
                MasterG.add_edge(table, ref_table)

    conn.close()

    views = []
    # 4. Create a View tailored for EACH table
    for root_table in all_tables:
        dependencies = nx.descendants(MasterG, root_table)  # nodes reachable from this table (recursive foreign keys)
        group_nodes = list(dependencies) + [root_table]
        if len(group_nodes) < 2:
            continue
        subgraph = MasterG.subgraph(group_nodes)
        # undirected convert to Kamada-Kawai as it calculates geometric distances
        # scale=1.0 gives us coordinates roughly -1 to 1
        try:
            raw_pos = nx.kamada_kawai_layout(subgraph.to_undirected(), scale=1.0)
        except Exception:
            raw_pos = nx.spring_layout(subgraph, k=1)    # Fallback for tiny/weird graphs

        normalized_pos, dynamic_scale = scale_factor(raw_pos, PADDING, TARGET_SIZE)

        # E. Apply Dynamic Scale and Output
        final_nodes = []
        for node in group_nodes:
            info = node_info[node]
            norm_x, norm_y = normalized_pos[node]

            # Apply the calculated scale factor
            pixel_x = float(norm_x * dynamic_scale) + PADDING / 2
            pixel_y = float(norm_y * dynamic_scale) + PADDING / 2

            final_nodes.append({
                "id": info["id"],
                "primary_texts": info["primary_texts"],
                "secondary_texts": info["secondary_texts"],
                "pos": {
                    "x": pixel_x,
                    "y": pixel_y
                }
            })

        # E. Define Edges (Only those existing within this subgraph)
        final_edges = []
        for u, v in subgraph.edges():
            final_edges.append({
                "start_node_id": table_to_id[u],
                "end_node_id": table_to_id[v]
            })

        views.append({
            "name": f"View_{root_table}",
            "root_table": root_table,
            "nodes": final_nodes,
            "edges": final_edges
        })

    # Sort views by name or complexity
    views.sort(key=lambda v: v['name'])
    return views


def graphviz_scale_factor(raw_pos, padding, target_size):
    # --- IMPORTANT: Re-implement this for Graphviz's bottom-left origin and points unit ---
    # Graphviz coordinates need vertical inversion and scaling relative to the viewbox

    # For this example, we'll return a fixed scale factor just to show the structure
    dynamic_scale = target_size / 2.0

    # Example transformation (replace with your actual logic based on Graphviz bounds)
    normalized_pos = {}
    for node, (x, y) in raw_pos.items():
        # Graphviz 'pos' is "x,y" in points, typically bottom-left origin.
        # We need to map the points to the 0-1 range before final scaling.
        # This requires knowing the total graph size from the JSON output ('bb' field)
        normalized_pos[node] = (x, y)  # Placeholder, actual scaling logic is complex

    return normalized_pos, dynamic_scale


def graphviz_layout_for_db_graphs_with_dimensions(db_path, TARGET_SIZE=800, PADDING=50):
    full_path = f"resources/{db_path}"
    node_info, all_tables, table_to_id = get_table_info(full_path)
    # Direction: Table -> Table it depends on (Foreign Key target)
    MasterG = nx.DiGraph()
    MasterG.add_nodes_from(all_tables)

    conn = sqlite3.connect(full_path)
    cursor = conn.cursor()
    for table in all_tables:
        # Check foreign keys from 'table' to 'ref_table'
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for ref in cursor.fetchall():
            ref_table = ref[2]  # ref[2] is the referenced table name
            if ref_table in all_tables:
                # Add edge: Current_Table -> Referenced_Table
                MasterG.add_edge(table, ref_table)
    conn.close()

    views = []

    # 3. Create a View tailored for EACH table
    # Standard width for a table node in Graphviz (in inches, 1 inch = 72 points)
    # 2 inches is a reasonable default for visibility.
    NODE_WIDTH_INCHES = 2.0

    for root_table in all_tables:
        dependencies = nx.descendants(MasterG, root_table)
        group_nodes = list(dependencies) + [root_table]

        if len(group_nodes) < 2:
            continue

        subgraph_nx = MasterG.subgraph(group_nodes)

        # --- GRAPHVIZ LAYOUT STEP ---
        g = graphviz.Digraph(f'View_{root_table}', engine='dot', format='json')
        # Set overall graph attributes
        g.attr(rankdir='LR')
        g.attr(splines='ortho')
        g.attr(nodesep='0.6')  # Increase vertical separation slightly
        g.attr(ranksep='0.7')  # Increase horizontal separation slightly

        # Set default node style attributes
        g.attr('node', shape='box', style='filled', color='black', fillcolor='lightgray',
               fixedsize='true', width=str(NODE_WIDTH_INCHES))

        # A. Add nodes with their calculated height
        for node in subgraph_nx.nodes():
            info = node_info[node]
            PIXELS_PER_INCH = 100
            height_in_inches = info["height"] / PIXELS_PER_INCH
            g.node(node, height=str(height_in_inches), label=node)  # label is for visualization/layout

        # B. Add edges
        for u, v in subgraph_nx.edges():
            g.edge(u, v)

        # C. Execute the layout engine and parse the JSON output
        try:
            json_output_bytes = g.pipe(encoding='utf-8')
            json_data = json.loads(json_output_bytes)
        except Exception as e:
            print(f"Graphviz layout failed for {root_table}. Ensure executables are installed: {e}")
            continue

            # D. Extract positions and bounding box data
        raw_pos = {}

        # 1. Extract Node Positions (x, y)
        for node_obj in json_data.get('objects', []):
            name = node_obj.get('name')
            pos_string = node_obj.get('pos')
            if name and pos_string:
                try:
                    x_pt, y_pt = map(float, pos_string.split(','))
                    raw_pos[name] = (x_pt, y_pt)
                except ValueError:
                    continue

        # 2. Get Bounding Box and Total Graph Height/Width
        if 'bb' not in json_data or not raw_pos:
            continue

        # bb format: "xmin,ymin,xmax,ymax" in points (pt)
        xmin, ymin, xmax, ymax = map(float, json_data['bb'].split(','))
        graph_width_pts = xmax - xmin
        graph_height_pts = ymax - ymin

        # 3. Calculate Global Scale Factor
        # Calculate max dimension needed to fit graph within (TARGET_SIZE - PADDING)
        max_dim_pts = max(graph_width_pts, graph_height_pts)
        if max_dim_pts <= 0:
            dynamic_scale = 1.0
        else:
            # Scale factor to convert points to pixels for the target size
            dynamic_scale = (TARGET_SIZE - PADDING) / max_dim_pts

        # E. Invert Y-axis, Translate, and Apply Scale
        normalized_pos = {}
        for node in group_nodes:
            if node in raw_pos:
                x_pt, y_pt = raw_pos[node]

                # Invert Y-axis (Graphviz is bottom-left origin, GUI is top-left)
                # y_inverted_pt = (ymax - ymin) - (y_pt - ymin)
                # Simplified: Total height - y_pt (if ymin is 0)
                y_inverted_pt = graph_height_pts - (y_pt - ymin)

                # Translate to remove xmin/ymin offsets and scale to target pixels
                pixel_x = (x_pt - xmin) * dynamic_scale + PADDING / 2
                pixel_y = y_inverted_pt * dynamic_scale + PADDING / 2

                normalized_pos[node] = (pixel_x, pixel_y)

        # F. Apply Final Positions and Output (Same structure as original)
        final_nodes = []
        for node in group_nodes:
            if node in normalized_pos:
                info = node_info[node]
                pixel_x, pixel_y = normalized_pos[node]

                final_nodes.append({
                    "id": info["id"],
                    "primary_texts": info["primary_texts"],
                    "secondary_texts": info["secondary_texts"],
                    "pos": {
                        "x": pixel_x,
                        "y": pixel_y
                    },
                    "height": info["height"]  # Include original pixel height for GUI rendering
                })

        # G. Define Edges (Same as original)
        final_edges = []
        for u, v in subgraph_nx.edges():
            final_edges.append({
                "start_node_id": table_to_id[u],
                "end_node_id": table_to_id[v]
            })

        views.append({
            "name": f"View_{root_table}",
            "root_table": root_table,
            "nodes": final_nodes,
            "edges": final_edges
        })

    views.sort(key=lambda v: v['name'])
    return views
