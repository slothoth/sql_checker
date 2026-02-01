import os
import sys
import traceback
import logging
from NodeGraphQt import BackdropNode, NodeGraph
from NodeGraphQt.constants import LayoutDirectionEnum

log = logging.getLogger(__name__)


def to_number(x):
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip()
        try:
            i = int(s)
            return i
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return 'failed'


def flatten(xss):
    return [x for xs in xss for x in xs]


def flatten_avoid_string(items):
    out = []
    if isinstance(items, str):
        return items
    for x in items:
        if isinstance(x, (list, tuple)):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def check_civ_install_works(path):
    check_passed = True
    if not os.path.exists(f"{path}/Base/Assets/schema/gameplay"):
        check_passed = False
    return check_passed


def check_civ_config_works(path):
    check_passed = True
    if not os.path.exists(f"{path}/Mods.sqlite"):
        check_passed = False
    return check_passed


def check_workshop_works(path):
    if '1295660' in path:
        return True
    return False


def strip_transient_widgets(graph_nodes):
    graph_migrated_params = {}
    for idx, node in enumerate(graph_nodes):
        migrated_params = node.migrate_extra_params()
        graph_migrated_params[idx] = migrated_params
    return graph_migrated_params


def print_traceback():
    exc_string = traceback.format_exc()
    print(exc_string)


def set_nodes_visible_by_type(graph, node_cls, visible):
    for node in graph.all_nodes():
        if node.type_ == node_cls:
            node.view.setVisible(visible)

            ports = node.view.inputs + node.view.outputs
            for port in ports:
                for pipe in port.connected_pipes:
                    pipe.setVisible(visible)


def auto_layout_nodes_minimise_crossing(self, nodes=None, down_stream=True, start_nodes=None):
    """
    Auto layout the nodes in the node graph.
    """
    self.begin_undo('Auto Layout Nodes')

    nodes = nodes or self.all_nodes()

    # 1. Filter out backdrops and separate Isolated nodes from Connected nodes
    backdrops = {n: n.nodes() for n in nodes if isinstance(n, BackdropNode)}
    filtered_nodes = [n for n in nodes if not isinstance(n, BackdropNode)]

    # Define "Lonely" (Isolated) nodes as those with NO connections at all
    lonely_nodes = []
    connected_nodes = []

    for n in filtered_nodes:
        has_inputs = any(n.connected_input_nodes().values())
        has_outputs = any(n.connected_output_nodes().values())
        if not has_inputs and not has_outputs:
            lonely_nodes.append(n)
        else:
            connected_nodes.append(n)

    # 2. Determine start nodes for the Connected Graph
    start_nodes = start_nodes or []
    if down_stream:
        start_nodes += [
            n for n in connected_nodes
            if not any(n.connected_input_nodes().values())
        ]
    else:
        start_nodes += [
            n for n in connected_nodes
            if not any(n.connected_output_nodes().values())
        ]

    if not start_nodes and not lonely_nodes:
        return

    node_views = [n.view for n in nodes]
    nodes_center_0 = self.viewer().nodes_rect_center(node_views)

    # 3. Compute Ranks for Connected Nodes
    nodes_rank = NodeGraph._compute_node_rank(start_nodes, down_stream)

    # Handle Port Nodes (Optional: Cap Output ports to the end)
    port_out_type = 'nodeGraphQt.nodes.PortOutputNode'
    out_nodes = [n for n in connected_nodes if n.type_ == port_out_type]

    if out_nodes and nodes_rank:
        max_rank = max(nodes_rank.values()) if nodes_rank else 0
        target_rank = max_rank + 1
        for node in out_nodes:
            nodes_rank[node] = target_rank

    # 4. Build Initial Grid & Barycenter Sort for Connected Nodes
    rank_map = {}
    for node, rank in nodes_rank.items():
        if rank not in rank_map: rank_map[rank] = []
        rank_map[rank].append(node)

    # Sort columns by barycenter to untangle
    for rank, col_nodes in rank_map.items():
        if rank == 0: continue  # Rank 0 is usually fixed

        def get_barycenter(n):
            parents = []
            # Get parents based on direction
            source = n.connected_input_nodes() if down_stream else n.connected_output_nodes()
            for nodelist in source.values(): parents.extend(nodelist)

            if not parents: return 0.0
            # Use Y position for horizontal, X for vertical (though typical barycenter uses Y)
            # Since we haven't assigned Y yet, we look at the PARENT'S position in the previous rank?
            # Actually, standard barycenter requires multiple passes or knowing parent positions.
            # Simplification: Sort by the average *Index* of parents in the previous rank if possible,
            # or just keep current simple logic.
            # For this specific step, let's stick to the previous simple heuristic
            # relying on input order or previously set pos if available.
            return sum([p.y_pos() for p in parents]) / len(parents)

        col_nodes.sort(key=get_barycenter)

    # 5. Create Virtual Grid (Coordinate System)
    # grid_slots[(rank, row)] = node
    grid_slots = {}
    occupied_slots = set()

    # Place connected nodes into grid slots
    for rank, col_nodes in rank_map.items():
        for row, node in enumerate(col_nodes):
            coord = (rank, row)
            grid_slots[coord] = node
            occupied_slots.add(coord)

    # 6. Find Holes for Lonely Nodes
    if lonely_nodes:
        # Determine Grid Bounds
        if not occupied_slots:
            min_rank, max_rank = 0, 0
            max_row = 0
        else:
            ranks = [c[0] for c in occupied_slots]
            rows = [c[1] for c in occupied_slots]
            min_rank, max_rank = min(ranks), max(ranks)
            max_row = max(rows)

        # Build Forbidden Set (Adjacency Buffer)
        # We exclude any slot that touches an occupied slot (including diagonals)
        forbidden_slots = set()
        for r, c in occupied_slots:
            # Add node itself
            forbidden_slots.add((r, c))
            # Add 8 neighbors
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    forbidden_slots.add((r + dr, c + dc))

        # Search for holes
        # We scan column by column (Rank), then row by row
        holes = []

        # We scan slightly outside current bounds to allow expansion if needed
        scan_rank_start = min_rank
        scan_rank_end = max_rank + 1
        scan_row_end = max_row + 2  # Allow growing down slightly

        for r in range(scan_rank_start, scan_rank_end + 1):
            for c in range(0, scan_row_end):
                coord = (r, c)
                if coord not in forbidden_slots:
                    holes.append(coord)

        # Sort holes to fill top-left first (or close to center)
        # Let's sort by Rank then Row
        holes.sort(key=lambda x: (x[0], x[1]))

        # Assign Lonely Nodes to Holes
        for node in lonely_nodes:
            if holes:
                # Take the first available hole
                coord = holes.pop(0)
                grid_slots[coord] = node

                # IMPORTANT: Once a hole is filled, it becomes occupied.
                # We must add its neighbors to forbidden so we don't crowd lonely nodes together
                # (Unless you WANT lonely nodes packed tightly.
                # If you want lonely nodes to ALSO have buffer, uncomment lines below)

                # r, c = coord
                # for dr in [-1, 0, 1]:
                #    for dc in [-1, 0, 1]:
                #        forbidden_slots.add((r + dr, c + dc))
                # holes = [h for h in holes if h not in forbidden_slots]

            else:
                # Fallback: If no holes, stack at bottom of first rank
                # Find lowest row in min_rank
                target_rank = min_rank
                target_row = 0
                while (target_rank, target_row) in grid_slots:
                    target_row += 1
                grid_slots[(target_rank, target_row)] = node

    # 7. Convert Virtual Grid to Real Positions
    node_layout_direction = self._viewer.get_layout_direction()
    is_horizontal = node_layout_direction is LayoutDirectionEnum.HORIZONTAL.value

    # We need to determine physical sizes for rows/columns
    # Re-organize into {rank: {row: node}} for easy iteration
    final_cols = {}
    for (rank, row), node in grid_slots.items():
        if rank not in final_cols: final_cols[rank] = {}
        final_cols[rank][row] = node

    sorted_ranks = sorted(final_cols.keys())

    if is_horizontal:
        current_x = 0
        # Constants for grid spacing
        ROW_HEIGHT = 150  # Fixed height to ensure holes align visually
        COL_PADDING = 100

        for rank in sorted_ranks:
            rows_dict = final_cols[rank]
            # Determine width of this column based on widest node
            col_nodes = rows_dict.values()
            max_w = max([n.view.width for n in col_nodes]) if col_nodes else 200

            # Iterate rows from 0 to max row in this column
            max_r = max(rows_dict.keys())

            for row in range(max_r + 1):
                node = rows_dict.get(row)
                if node:
                    # Position node
                    # Y is purely based on grid row index to preserve "hole" spacing
                    pos_y = row * ROW_HEIGHT
                    node.set_pos(current_x, pos_y)

            current_x += max_w + COL_PADDING

    elif node_layout_direction is LayoutDirectionEnum.VERTICAL.value:
        current_y = 0
        COL_WIDTH = 300  # Fixed width for vertical layout "rows"
        ROW_PADDING = 100

        for rank in sorted_ranks:
            rows_dict = final_cols[rank]
            col_nodes = rows_dict.values()
            max_h = max([n.view.height for n in col_nodes]) if col_nodes else 120

            max_r = max(rows_dict.keys())
            for row in range(max_r + 1):
                node = rows_dict.get(row)
                if node:
                    pos_x = row * COL_WIDTH
                    node.set_pos(pos_x, current_y)

            current_y += max_h + ROW_PADDING

    # Recenter
    nodes_center_1 = self.viewer().nodes_rect_center(node_views)
    dx = nodes_center_0[0] - nodes_center_1[0]
    dy = nodes_center_0[1] - nodes_center_1[1]
    [n.set_pos(n.x_pos() + dx, n.y_pos() + dy) for n in nodes]

    # Wrap backdrops
    for backdrop, contained_nodes in backdrops.items():
        backdrop.wrap_nodes(contained_nodes)

    self.end_undo()


class LogPushSingleton:
    def __init__(self):
        self.log_widget = None

    def set_log_widget(self, log_widget):
        if self.log_widget is not None:
            log.error('trying to reset log window, shouldnt happen')
        else:
            self.log_widget = log_widget

    def push_to_log(self, message, other_log):
        other_log.info(f'Pushed to log: {message}')
        log_display = self.log_widget
        if log_display is not None:         # rare occassions where it gets wiped by C++. Not good, but dont crash
            log_display.appendPlainText(str(message) + '\n')  # ensure plain text insertion so the highlighter can run
            cursor = log_display.textCursor()  # keep view scrolled to bottom
            log_display.setTextCursor(cursor)


LogPusher = LogPushSingleton()
