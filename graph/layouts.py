import math
import random
from collections import defaultdict
from NodeGraphQt import BaseNode

from graph.utils import auto_layout_nodes_minimise_crossing

import logging

log = logging.getLogger(__name__)


def layout_and_centre_view(graph):
    auto_layout_nodes_minimise_crossing(graph, nodes=graph.all_nodes(), down_stream=True)
    graph._viewer.zoom_to_nodes([n.view for n in graph.all_nodes()])


def normalize_session_coordinates(session_data):
    """Shifts all nodes in the session dictionary so that their collective center is at (0,0)."""
    nodes = session_data.get('nodes', {})
    x_coords, y_coords = [], []
    for node_id, node_data in nodes.items():
        pos = node_data.get('pos', [0.0, 0.0])
        x_coords.append(pos[0])
        y_coords.append(pos[1])

    if not x_coords:
        return session_data

    center_x = (min(x_coords) + max(x_coords)) / 2.0
    center_y = (min(y_coords) + max(y_coords)) / 2.0

    for node_id, node_data in nodes.items():                        # Offset every node by center point
        original_x, original_y = node_data.get('pos', [0.0, 0.0])
        node_data['pos'] = [original_x - center_x, original_y - center_y]

    return session_data


def organize_subgraph_layout(sub_graph, padding=300, vertical_spacing=100):
    input_nodes, output_nodes, content_nodes = [], [], []

    for node in sub_graph.all_nodes():
        if node.type_ == 'nodeGraphQt.nodes.PortInputNode':
            input_nodes.append(node)
        elif node.type_ == 'nodeGraphQt.nodes.PortOutputNode':
            output_nodes.append(node)
        else:
            content_nodes.append(node)

    if not content_nodes:
        mid_x, mid_y, min_x, max_x = 0.0, 0.0, -padding, padding
    else:
        x_positions = [n.x_pos() for n in content_nodes]
        y_positions = [n.y_pos() for n in content_nodes]

        min_x, max_x = min(x_positions), max(x_positions)
        min_y, max_y = min(y_positions), max(y_positions)

        mid_y = (min_y + max_y) / 2.0

    if input_nodes:
        input_nodes.sort(key=lambda n: n.name())

        start_y = mid_y - ((len(input_nodes) * vertical_spacing) / 2.0)
        x_pos = min_x - padding

        for i, node in enumerate(input_nodes):
            node.set_pos(x_pos, start_y + (i * vertical_spacing))

    if output_nodes:
        output_nodes.sort(key=lambda n: n.name())

        start_y = mid_y - ((len(output_nodes) * vertical_spacing) / 2.0)
        x_pos = max_x + padding

        for i, node in enumerate(output_nodes):
            node.set_pos(x_pos, start_y + (i * vertical_spacing))


def layout_force_directed(graph,
                          nodes=None,
                          iterations=100,
                          repulsion_strength=100.0,
                          spring_stiffness=0.05,
                          gravity=0.01,
                          flow_bias=0.0):
    """
    Applies a force-directed layout to the NodeGraphQt instance.

    Args:
        graph (NodeGraph): The main graph controller.
        nodes (list): Optional list of nodes to layout. Defaults to all nodes.
        iterations (int): How many physics steps to run.
        repulsion_strength (float): Factor for how much nodes push apart.
        spring_stiffness (float): How strongly connections pull nodes together.
        gravity (float): How much the graph should pull in on each step
        flow_bias (float): 0.0 to 1.0. Adds a force pushing children to the right
                           to respect the Input(Left)->Output(Right) flow.
    """

    # 1. Setup Phase
    # ---------------------------------------------------------
    if nodes is None:
        nodes = graph.all_nodes()

    # Filter out Backdrops or other non-BaseNodes that shouldn't move independently
    active_nodes = [n for n in nodes if isinstance(n, BaseNode)]

    if not active_nodes:
        return

    # Map node objects to a lightweight data structure for calculation
    # struct: { node_id: {'x': float, 'y': float, 'w': float, 'h': float, 'obj': node} }
    node_data = {}

    # Pre-calculate center points and sizes
    for node in active_nodes:
        # We use the view's width/height to ensure we respect the actual UI size
        w = node.view.width + 50  # Add padding to width
        h = node.view.height + 50  # Add padding to height
        x, y = node.pos()

        node_data[node.id] = {
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'r': (w+h) / 4,
            'dx': 0.0,  # Velocity/Displacement X
            'dy': 0.0,  # Velocity/Displacement Y
            'obj': node
        }

    node_ids = list(node_data.keys())

    # Build efficient edge list for spring forces
    edges = []
    for node in active_nodes:
        # connected_output_nodes returns { port_name: [node_list] }
        outputs = node.connected_output_nodes()
        for port_name, connected_nodes_list in outputs.items():
            for target_node in connected_nodes_list:
                if target_node.id in node_data:
                    edges.append((node.id, target_node.id))

    # 2. Simulation Loop
    # ---------------------------------------------------------

    # Cooling factor: Movement decreases as iterations progress
    initial_temperature = 10.0

    for i in range(iterations):
        progress = i / iterations
        temperature = initial_temperature * (1.0 - progress)

        # A. Reset forces (displacements)
        for nid in node_ids:
            node_data[nid]['dx'] = 0.0
            node_data[nid]['dy'] = 0.0

        # B. Repulsion (All nodes repel all other nodes)
        # Optimized: Only calculate distinct pairs
        for idx, nid1 in enumerate(node_ids):
            n1 = node_data[nid1]
            for nid2 in node_ids[idx + 1:]:
                n2 = node_data[nid2]

                dx = n1['x'] - n2['x']
                dy = n1['y'] - n2['y']

                dist_sq = dx * dx + dy * dy

                # Prevent division by zero and extreme overlaps
                if dist_sq < 0.01:
                    dx = random.uniform(-1, 1)
                    dy = random.uniform(-1, 1)
                    dist = 1.0
                else:
                    dist = math.sqrt(dist_sq)

                # Custom Repulsion:
                # Use the combined radius of the nodes to prevent overlap.
                # Nodes are rectangles, so we approximate "radius" based on width/height.
                min_dist = (n1['w'] + n2['w']) / 2.0

                # If nodes are overlapping or too close, repulsion skyrockets
                force = (repulsion_strength * repulsion_strength) / dist

                # Direction vector
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                n1['dx'] += fx
                n1['dy'] += fy
                n2['dx'] -= fx
                n2['dy'] -= fy

        # C. Attraction (Springs connect related nodes)
        for source_id, target_id in edges:
            n1 = node_data[source_id]
            n2 = node_data[target_id]

            dx = n1['x'] - n2['x']
            dy = n1['y'] - n2['y']
            dist = math.sqrt(dx * dx + dy * dy) or 1.0

            # Hooke's Law: F = -k * (current_length - ideal_length)
            current_spring_length = n1['r'] + n2['r']
            displacement = dist - current_spring_length
            force = displacement * spring_stiffness

            fx = (dx / dist) * force
            fy = (dy / dist) * force

            n1['dx'] -= fx
            n1['dy'] -= fy
            n2['dx'] += fx
            n2['dy'] += fy

            # D. Flow Bias (Directional Force)
            # Push Target to the Right, Source to the Left
            # This helps organize inputs on left, outputs on right
            if flow_bias > 0:
                flow_force = flow_bias * 50.0  # Constant push
                n2['dx'] += flow_force
                n1['dx'] -= flow_force

        # E. Apply Forces & Temperature
        for nid in node_ids:
            node = node_data[nid]

            node['x'] -= node['x'] * gravity       # pull back in
            node['y'] -= node['y'] * gravity

            # Normalize displacement direction
            disp_len = math.sqrt(node['dx'] ** 2 + node['dy'] ** 2)
            if disp_len > 0:
                # Limit movement by temperature to prevent exploding layout
                move_dist = min(disp_len, temperature * 10.0)

                node['x'] += (node['dx'] / disp_len) * move_dist
                node['y'] += (node['dy'] / disp_len) * move_dist

    # 3. Apply to Graph
    # ---------------------------------------------------------

    # Calculate bounds to center the graph after layout
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for nid, data in node_data.items():
        min_x = min(min_x, data['x'])
        max_x = max(max_x, data['x'])
        min_y = min(min_y, data['y'])
        max_y = max(max_y, data['y'])

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    # Apply positions relative to 0,0 (or keep relative to previous center)
    for nid, data in node_data.items():
        # Final set_pos
        data['obj'].set_pos(data['x'] - center_x, data['y'] - center_y)


def arrange_leaves(nodes):
    """
    Post-processing step to neatly stack leaf nodes with one parent vertically.
    """
    parent_leaves, processed_leaves = {}, set()
    for node in nodes:
        # 1. Must be a Parent (has outputs)
        if not node.output_ports():
            continue

        leaves_for_this_parent = []

        # Iterate ports in order (Top -> Bottom)
        for port in node.output_ports():
            target_ports = port.connected_ports()

            for target_port in target_ports:
                leaf_candidate = target_port.node()

                # --- FILTERING LOGIC ---

                # A. Skip if it's the parent itself (loopback)
                if leaf_candidate == node:
                    continue

                # B. Skip if it has outputs (it's not a leaf, it's a branch)
                # connected_output_nodes returns a dict, empty dict means no outputs
                if any(leaf_candidate.connected_output_nodes().values()):
                    continue

                # C. Skip if already processed
                if leaf_candidate.id in processed_leaves:
                    continue

                # D. STRICT PARENT CHECK (The new part)
                # Get all input connections: { 'port_name': [NodeObj, NodeObj] }
                input_data = leaf_candidate.connected_input_nodes()

                # Flatten all lists into one set of unique nodes
                all_parents = set()
                for connected_node_list in input_data.values():
                    all_parents.update(connected_node_list)

                # If there is more than 1 unique parent, let physics handle it.
                if len(all_parents) != 1:
                    continue

                # -----------------------

                leaves_for_this_parent.append(leaf_candidate)
                processed_leaves.add(leaf_candidate.id)

        if leaves_for_this_parent:
            parent_leaves[node] = leaves_for_this_parent

    # 2. Position the Stacks
    for parent, leaves in parent_leaves.items():
        if not leaves:
            continue

        parent_x, parent_y = parent.pos()
        parent_w = parent.view.width
        parent_h = parent.view.height

        # Calculate stack height to center it
        total_stack_height = sum(leaf.view.height for leaf in leaves)
        padding = 10.0
        total_stack_height += padding * (len(leaves) - 1)

        # Start Y: Center of parent - Half of stack height
        start_y = (parent_y + parent_h / 2.0) - (total_stack_height / 2.0)
        start_x = parent_x + parent_w + 100.0

        current_y = start_y
        for leaf in leaves:
            leaf.set_pos(start_x, current_y)
            current_y += leaf.view.height + padding


def pack_orphans(nodes):
    orphans = []
    for node in nodes:
        has_inputs = any(node.connected_input_nodes().values())
        has_outputs = any(node.connected_output_nodes().values())
        if not has_inputs and not has_outputs:
            orphans.append(node)
    if not orphans:
        return []
    orphans.sort(key=lambda n: n.view.height)
    count = len(orphans)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    gap_x, gap_y = 10.0, 10.0
    col_widths = [0.0] * cols
    row_heights = [0.0] * rows

    for i, node in enumerate(orphans):
        col = i % cols
        row = i // cols
        if node.view.width > col_widths[col]:
            col_widths[col] = node.view.width
        if node.view.height > row_heights[row]:
            row_heights[row] = node.view.height

    start_x, start_y = orphans[0].pos()         # Place Nodes: Use the first orphan's position as the anchor
    current_y = start_y
    for r in range(rows):
        current_x = start_x
        r_height = row_heights[r]
        for c in range(cols):
            index = r * cols + c
            if index >= count:
                break
            node = orphans[index]
            c_width = col_widths[c]
            node.set_pos(current_x, current_y)
            current_x += c_width + gap_x        # Move X pointer by this column's width + gap
        current_y += r_height + gap_y           # Move Y pointer by this row's height + gap
    return orphans


def layout_clusters(clusters, iterations=100):
    """
    Treats each list of nodes as a single 'Super Node'.
    Calculates Bounding Boxes and runs a force-directed layout on them.
    """
    if not clusters:
        return

    cluster_data = []
    for i, nodes in enumerate(clusters):
        if not nodes:
            continue

        # Calculate BBox
        min_x = min(n.x_pos() for n in nodes)
        max_x = max(n.x_pos() + n.view.width for n in nodes)
        min_y = min(n.y_pos() for n in nodes)
        max_y = max(n.y_pos() + n.view.height for n in nodes)

        w = max_x - min_x
        h = max_y - min_y
        cx = min_x + w / 2.0
        cy = min_y + h / 2.0

        # Radius = Half diagonal (approximate circle that covers the box)
        radius = math.sqrt(w * w + h * h) / 2.0

        cluster_data.append({
            'id': i,
            'x': cx, 'y': cy,
            'w': w, 'h': h,
            'r': radius,
            'dx': 0.0, 'dy': 0.0,
            'nodes': nodes
        })

    count = len(cluster_data)
    if count < 2:
        return

    # 2. Simulation Loop
    # ---------------------------------------------------------
    temperature = 100.0  # High temp for big movements

    for _ in range(iterations):
        # Reset forces
        for c in cluster_data:
            c['dx'] = 0.0
            c['dy'] = 0.0

            # GRAVITY: Pull all clusters towards center (0,0)
            # This keeps the islands from drifting to infinity
            c['dx'] -= c['x'] * 0.02
            c['dy'] -= c['y'] * 0.02

        # Repulsion (Cluster vs Cluster)
        for i in range(count):
            c1 = cluster_data[i]
            for j in range(i + 1, count):
                c2 = cluster_data[j]

                dx = c1['x'] - c2['x']
                dy = c1['y'] - c2['y']
                dist = math.sqrt(dx * dx + dy * dy) or 1.0

                # SHIELDING REPULSION
                # We want them to touch edges, not centers.
                # Target distance = Sum of Radii + Padding
                min_dist = c1['r'] + c2['r'] + 100.0

                if dist < min_dist:
                    # Overlap detected! Strong repulsive force.
                    force = (min_dist - dist) * 2.0

                    fx = (dx / dist) * force
                    fy = (dy / dist) * force

                    c1['dx'] += fx
                    c1['dy'] += fy
                    c2['dx'] -= fx
                    c2['dy'] -= fy

        # Apply Movement
        for c in cluster_data:
            disp_len = math.sqrt(c['dx'] ** 2 + c['dy'] ** 2)
            if disp_len > 0:
                # Cap movement speed
                move = min(disp_len, temperature)
                c['x'] += (c['dx'] / disp_len) * move
                c['y'] += (c['dy'] / disp_len) * move

        temperature *= 0.95  # Cool down

    # 3. Apply Final Positions
    # ---------------------------------------------------------
    for c in cluster_data:
        # Calculate how much the CENTER moved
        # (Current Center - Original Center is not stored, but we can infer offset)
        # Actually, simpler: We know the NEW center (c['x'], c['y'])
        # We need to compute the offset from the OLD center.

        # Re-calculate old center to be safe
        old_min_x = min(n.x_pos() for n in c['nodes'])
        old_max_x = max(n.x_pos() + n.view.width for n in c['nodes'])
        old_min_y = min(n.y_pos() for n in c['nodes'])
        old_max_y = max(n.y_pos() + n.view.height for n in c['nodes'])

        old_cx = old_min_x + (old_max_x - old_min_x) / 2.0
        old_cy = old_min_y + (old_max_y - old_min_y) / 2.0

        # The Delta
        move_x = c['x'] - old_cx
        move_y = c['y'] - old_cy

        # Move every node in the cluster by that delta
        for node in c['nodes']:
            node.set_pos(node.x_pos() + move_x, node.y_pos() + move_y)


def layout_clusters_shelf(clusters, aspect_ratio=1.77, padding=20.0):
    """
    Packs clusters (lists of nodes) into a rectangle with a target aspect ratio.
    Uses a 'Shelf Packing' algorithm (First-Fit Decreasing Height).
    """
    if not clusters:
        return
    cluster_boxes = []
    total_area = 0.0
    for nodes in clusters:
        if not nodes:
            continue
        # Find the BBox of this cluster
        min_x = min(n.x_pos() for n in nodes)
        max_x = max(n.x_pos() + n.view.width for n in nodes)
        min_y = min(n.y_pos() for n in nodes)
        max_y = max(n.y_pos() + n.view.height for n in nodes)

        w = max_x - min_x
        h = max_y - min_y
        current_x = min_x
        current_y = min_y

        box_w = w + padding      # Add padding to the size calculation so they don't touch
        box_h = h + padding

        total_area += box_w * box_h

        cluster_boxes.append({
            'nodes': nodes,
            'w': box_w,
            'h': box_h,
            'orig_x': current_x,
            'orig_y': current_y,
            'final_x': 0.0,
            'final_y': 0.0
        })

    if not cluster_boxes:
        return

    cluster_boxes.sort(key=lambda b: b['h'], reverse=True)
    target_width = math.sqrt(total_area * aspect_ratio)
    max_cluster_width = max(b['w'] for b in cluster_boxes)
    target_width = max(target_width, max_cluster_width)
    current_x, current_y, current_row_height = 0.0, 0.0, 0.0
    for box in cluster_boxes:           # Check if this box fits on the current shelf
        if current_x + box['w'] > target_width:
            current_x = 0.0             # New Shelf! Move X back to start
            current_y += current_row_height     # Move Y down by the height of the row we just finished
            current_row_height = 0.0        # Reset row height for the new row
        box['final_x'] = current_x
        box['final_y'] = current_y
        if box['h'] > current_row_height:
            current_row_height = box['h']
        current_x += box['w']
    for box in cluster_boxes:
        # Calculate Delta (How far to move from original position)
        move_x = box['final_x'] - box['orig_x']
        move_y = box['final_y'] - box['orig_y']

        for node in box['nodes']:
            node.set_pos(node.x_pos() + move_x, node.y_pos() + move_y)


def get_weakly_connected_components(graph):     # DFS traversal
    visited, components = set(), []

    all_nodes = graph.all_nodes()
    grouped_nodes, original_connections = get_groups_and_connections(all_nodes)

    for node in all_nodes:
        if node in visited:
            continue

        component_nodes, stack = [], [node]
        while stack:
            current_node = stack.pop()
            if current_node in visited:
                continue
            visited.add(current_node)
            component_nodes.append(current_node)
            neighbors = []
            if isinstance(current_node, BaseNode):
                input_conn = current_node.connected_input_nodes()
                for connected_list in input_conn.values():
                    neighbors.extend(connected_list)
                output_conn = current_node.connected_output_nodes()
                for connected_list in output_conn.values():
                    neighbors.extend(connected_list)
            for neighbor in neighbors:                      # Add unvisited neighbors to the stack
                if neighbor not in visited:
                    stack.append(neighbor)
        components.append(component_nodes)
    return components, original_connections


def get_groups_and_connections(node_subset):
    original_connections, grouped_nodes = [], defaultdict(list)
    for node in node_subset:
        table_name = node.get_property('table_name')
        if table_name and table_name not in ['GameEffectCustom', 'ReqEffectCustom']:
            grouped_nodes[table_name].append(node)
        for port_name, port_obj in node.outputs().items():
            for connected_port in port_obj.connected_ports():
                conn_tuple = (node.id, port_name, connected_port.node().id, connected_port.name())
                original_connections.append(conn_tuple)

    return grouped_nodes, original_connections


def layout_with_spring(graph):
    layout_force_directed(graph, iterations=100, repulsion_strength=100.0,
                          spring_stiffness=0.5, gravity=0.01, flow_bias=0.8)
    all_nodes = graph.all_nodes()
    arrange_leaves(all_nodes)


def layout_shelf_clusters(graph):
    clusters, unused_connections = get_weakly_connected_components(graph)
    decent_clusters = [i for i in clusters if len(i) > 1]
    all_nodes = graph.all_nodes()
    orphans = pack_orphans(all_nodes)
    if orphans:
        decent_clusters.append(orphans)
    layout_clusters_shelf(decent_clusters)

