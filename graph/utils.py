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


def auto_layout_nodes_minimise_crossing(graph, nodes=None, down_stream=True, start_nodes=None):
    """
    Auto layout the nodes in the node graph. new functionalised version as previous method suckked for overlaps
    Args:
        nodes (list[NodeGraphQt.BaseNode]): list of nodes to auto layout
            if nodes is None then all nodes is layed out.
        down_stream (bool): false to layout up stream.
        start_nodes (list[NodeGraphQt.BaseNode]):
            list of nodes to start the auto layout from (Optional).
    """
    graph.begin_undo('Auto Layout Nodes')

    nodes = nodes or graph.all_nodes()

    # filter out the backdrops.
    backdrops = {n: n.nodes() for n in nodes if isinstance(n, BackdropNode)}
    filtered_nodes = [n for n in nodes if not isinstance(n, BackdropNode)]

    start_nodes = start_nodes or []
    if down_stream:
        start_nodes += [n for n in filtered_nodes if not any(n.connected_input_nodes().values())]
    else:
        start_nodes += [n for n in filtered_nodes if not any(n.connected_output_nodes().values())]

    if not start_nodes:
        return

    node_views = [n.view for n in nodes]
    nodes_center_0 = graph.viewer().nodes_rect_center(node_views)

    nodes_rank = NodeGraph._compute_node_rank(start_nodes, down_stream)

    rank_map = {}
    for node, rank in nodes_rank.items():
        if rank in rank_map:
            rank_map[rank].append(node)
        else:
            rank_map[rank] = [node]

    node_layout_direction = graph._viewer.get_layout_direction()
    is_horizontal = node_layout_direction is LayoutDirectionEnum.HORIZONTAL.value

    # We iterate through the ranks (columns) to place nodes.
    sorted_ranks = sorted(range(len(rank_map)), reverse=not down_stream)
    if is_horizontal:
        current_x = 0
        node_height = 120
        for i, rank in enumerate(sorted_ranks):
            ranked_nodes = rank_map[rank]
            if i == 0:      # Place unconnected nodes at bottom
                # Rank 0: Place "Lonely" nodes (no downstream connections) at the bottom.
                # We sort by connectivity: True (1) first, False (0) last.
                if down_stream:
                    ranked_nodes.sort(key=lambda n: any(n.connected_output_nodes().values()), reverse=True)
                else:
                    ranked_nodes.sort(key=lambda n: any(n.connected_input_nodes().values()), reverse=True)

            else:
                # Rank > 0: Barycenter Method.
                # Sort nodes based on the average Y position of their connected "parents"
                # in the previous rank.
                def get_barycenter(n):
                    parents = []
                    # If downstream, parents are inputs. If upstream, parents are outputs.
                    source_dict = n.connected_input_nodes() if down_stream else n.connected_output_nodes()

                    for nodelist in source_dict.values():
                        parents.extend(nodelist)

                    if not parents:
                        return 0.0

                    # Calculate average Y position of parents
                    y_sum = sum([p.y_pos() for p in parents])
                    return y_sum / len(parents)

                ranked_nodes.sort(key=get_barycenter)
            # -----------------------------

            max_width = max([node.view.width for node in ranked_nodes])
            current_x += max_width
            current_y = 0
            for idx, node in enumerate(ranked_nodes):
                dy = max(node_height, node.view.height)
                current_y += 0 if idx == 0 else dy
                node.set_pos(current_x, current_y)
                current_y += dy * 0.5 + 10

            current_x += max_width * 0.5 + 100

    elif node_layout_direction is LayoutDirectionEnum.VERTICAL.value:
        current_y = 0
        node_width = 250

        for i, rank in enumerate(sorted_ranks):
            ranked_nodes = rank_map[rank]

            # --- CUSTOM SORTING LOGIC (Vertical Layout) ---
            if i == 0:
                if down_stream:
                    ranked_nodes.sort(key=lambda n: any(n.connected_output_nodes().values()), reverse=True)
                else:
                    ranked_nodes.sort(key=lambda n: any(n.connected_input_nodes().values()), reverse=True)
            else:
                def get_barycenter(n):
                    parents = []
                    source_dict = n.connected_input_nodes() if down_stream else n.connected_output_nodes()
                    for nodelist in source_dict.values():
                        parents.extend(nodelist)

                    if not parents:
                        return 0.0

                    # Calculate average X position of parents (X is the sorting axis for Vertical layout)
                    x_sum = sum([p.x_pos() for p in parents])
                    return x_sum / len(parents)

                ranked_nodes.sort(key=get_barycenter)
            # -----------------------------------------------

            max_height = max([node.view.height for node in ranked_nodes])
            current_y += max_height
            current_x = 0
            for idx, node in enumerate(ranked_nodes):
                dx = max(node_width, node.view.width)
                current_x += 0 if idx == 0 else dx
                node.set_pos(current_x, current_y)
                current_x += dx * 0.5 + 10

            current_y += max_height * 0.5 + 100

    nodes_center_1 = graph.viewer().nodes_rect_center(node_views)
    dx = nodes_center_0[0] - nodes_center_1[0]
    dy = nodes_center_0[1] - nodes_center_1[1]
    [n.set_pos(n.x_pos() + dx, n.y_pos() + dy) for n in nodes]

    # wrap the backdrop nodes.
    for backdrop, contained_nodes in backdrops.items():
        backdrop.wrap_nodes(contained_nodes)

    graph.end_undo()


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
