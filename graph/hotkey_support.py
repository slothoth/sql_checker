from PyQt5 import QtCore
import logging
import time
import json
from model import query_mod_db, organise_entries, load_files
from schema_generator import SQLValidator, lint_database
from graph.singletons.filepaths import LocalFilePaths
from graph.singletons.db_spec_singleton import db_spec
from collections import defaultdict


log = logging.getLogger(__name__)


class ConfigTestWorker(QtCore.QObject):
    """
    Worker class to run the configuration test in a separate thread.
    """
    finished = QtCore.pyqtSignal()
    log_updated = QtCore.pyqtSignal(str)
    results_ready = QtCore.pyqtSignal(object)

    def __init__(self, age, extra_sql):
        super().__init__()
        self.age = age
        self.extra_sql = extra_sql

    def run(self):
        try:
            self.log_updated.emit(f"Running current mod setup when civ last launched in {self.age}...")
            start_time = time.time()

            engine = SQLValidator.make_base_db(f"{LocalFilePaths.app_data_path_form('current.sqlite')}",
                                               SQLValidator.prebuilt)

            database_entries = query_mod_db(age=self.age)
            modded_short, modded, dlc, dlc_files = organise_entries(database_entries)

            with open(LocalFilePaths.app_data_path_form('cached_base_game_sql.json')) as f:
                preloaded_sql = json.load(f)

            not_preloaded_dlc = [i for i in dlc_files if i not in preloaded_sql]
            preloaded_sql_statements_dlc = {k: v for k, v in preloaded_sql.items() if k in dlc_files}

            sql_statements_dlc, _, missed_dlc = load_files(not_preloaded_dlc, 'DLC')
            sql_statements_dlc.update(preloaded_sql_statements_dlc)

            self.log_updated.emit(
                f"Loaded dlc files: {len(sql_statements_dlc)}. Excluded empty files: {len(not_preloaded_dlc)}"
            )

            sql_statements_mods, _, missed_mods = load_files(modded, 'Mod')
            self.log_updated.emit(f"Loaded mod files: {len(sql_statements_mods)}. Missed: {len(missed_mods)}")

            sql_statements_dlc = {k: [{'sql': i} for i in v] for k, v in sql_statements_dlc.items()}
            self.log_updated.emit("Running SQL on Vanilla civ files...")
            dlc_status_info = lint_database(engine, sql_statements_dlc, keep_changes=True, database_spec=db_spec)

            self.results_ready.emit(dlc_status_info)

            sql_statements_mods = {k: [{'sql': i} for i in v] for k, v in sql_statements_mods.items()}
            self.log_updated.emit("Running SQL on Modded files...")
            mod_status_info = lint_database(engine, sql_statements_mods, keep_changes=True, database_spec=db_spec)

            self.results_ready.emit(mod_status_info)
            self.log_updated.emit("Finished running Modded Files")

            if self.extra_sql:
                with open(LocalFilePaths.app_data_path_form('main.sql'), 'r') as f:
                    graph_sql = f.readlines()
                extra_statements = {'graph_main.sql': graph_sql}
                mod_gui_status_info = lint_database(engine, extra_statements, keep_changes=False, database_spec=db_spec)

                self.results_ready.emit(mod_gui_status_info)
                self.log_updated.emit("Finished running Graph mod")

            self.log_updated.emit(f"model_run finished in {time.time() - start_time:.1f}s")

        except Exception as e:
            self.log_updated.emit(f"Error during threaded execution: {e}")
            log.error("Thread error", exc_info=True)
        finally:
            self.finished.emit()


def group_nodes_by_table(graph):
    """
    Groups all nodes with the same 'table_name' property into GroupNodes.
    Ignores table_names that appear only once.
    """
    # 1. Start the macro for a single Undo step
    graph.begin_undo('Auto Group by Table')
    try:
        original_connections, node_group_map, grouped_nodes = [], {}, defaultdict(list)
        all_nodes = graph.all_nodes()

        for node in all_nodes:
            table_name = node.get_property('table_name')
            if table_name and table_name not in ['GameEffectCustom', 'ReqEffectCustom']:
                grouped_nodes[table_name].append(node)
            for port_name, port_obj in node.outputs().items():
                for connected_port in port_obj.connected_ports():
                    conn_tuple = (node.id, port_name, connected_port.node().id, connected_port.name())
                    original_connections.append(conn_tuple)

        for table_name, nodes in grouped_nodes.items():
            num_nodes = len(nodes)
            if num_nodes < 2:
                continue

            group_node_name = f"{nodes[0].__identifier__.replace('.table.', '.group.')}.{table_name.title()}Node"
            if group_node_name not in graph.registered_nodes():
                group_node_name = 'nodes.group.MyGroupNode'
            position = [int(sum(n.x_pos() for n in nodes) / num_nodes), int(sum(n.y_pos() for n in nodes) / num_nodes)]
            group_node = graph.create_node(group_node_name, name=table_name, push_undo=True, pos=position)

            for node in nodes:
                node_group_map[node.id] = group_node

            session_data = graph._serialize(nodes)
            group_node.set_sub_graph_session(session_data)

            sub_graph = group_node.expand()
            inner_inputs = {n.name(): n for n in sub_graph.get_input_port_nodes()}
            inner_outputs = {n.name(): n for n in sub_graph.get_output_port_nodes()}

            for inner_node in sub_graph.all_nodes():
                if inner_node.type_ in ['nodeGraphQt.nodes.PortInputNode', 'nodeGraphQt.nodes.PortOutputNode']:
                    continue

                for port_name, port in inner_node.inputs().items():
                    if port_name in inner_inputs:
                        inner_inputs[port_name].output(0).connect_to(port)

                for port_name, port in inner_node.outputs().items():
                    if port_name in inner_outputs:
                        inner_outputs[port_name].input(0).connect_to(port)

            # organize_subgraph_layout(sub_graph)
            sub_graph.auto_layout_nodes(nodes=sub_graph.all_nodes(), down_stream=True)
            sub_graph.set_zoom(0)
            sub_graph.center_on(sub_graph.all_nodes())
            group_node.collapse()

            for src_id, src_port, dst_id, dst_port in original_connections:
                src_node = node_group_map.get(src_id) or graph.get_node_by_id(src_id)
                dst_node = node_group_map.get(dst_id) or graph.get_node_by_id(dst_id)

                if not src_node or not dst_node or src_node == dst_node:
                    continue
                try:
                    s_port = src_node.outputs().get(src_port)
                    d_port = dst_node.inputs().get(dst_port)
                    if s_port and d_port:
                        s_port.connect_to(d_port)
                except Exception as e:
                    pass

        nodes_to_delete = []
        for nodes in grouped_nodes.values():
            if len(nodes) >= 2:
                nodes_to_delete.extend(nodes)

        graph.delete_nodes(nodes_to_delete, push_undo=True)
        graph.auto_layout_nodes(nodes=graph.all_nodes(), down_stream=True)
        graph.select_all()
        graph.fit_to_selection()
        graph.clear_selection()

    except Exception as e:
        import traceback
        error = traceback.format_exc()
        print(f"Error grouping nodes: {e}")

    finally:
        # 4. End the macro ensuring the Undo stack is closed even if errors occur
        graph.end_undo()


def normalize_session_coordinates(session_data):
    """
    Shifts all nodes in the session dictionary so that their
    collective center is at (0,0).
    """
    nodes = session_data.get('nodes', {})
    if not nodes:
        return session_data

    # 1. Gather all X and Y positions
    x_coords = []
    y_coords = []

    for node_id, node_data in nodes.items():
        # 'pos' is typically a list [x, y]
        pos = node_data.get('pos', [0.0, 0.0])
        x_coords.append(pos[0])
        y_coords.append(pos[1])

    if not x_coords:
        return session_data

    # 2. Calculate the center point
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0

    # 3. Offset every node by the center point
    for node_id, node_data in nodes.items():
        original_x, original_y = node_data.get('pos', [0.0, 0.0])
        new_x = original_x - center_x
        new_y = original_y - center_y
        node_data['pos'] = [new_x, new_y]

    return session_data


def organize_subgraph_layout(sub_graph, padding=300, vertical_spacing=100):
    """
    Organizes the layout of a subgraph:
    - Inputs on the Left
    - Content (Original Nodes) in the Middle
    - Outputs on the Right
    """
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


def write_sql(sql_dict_list):                               # save SQL, then trigger main run model
    sql_lines = [i['sql'] + '\n' for i in sql_dict_list]
    with open(LocalFilePaths.app_data_path_form('main.sql'), 'w') as f:
        f.writelines(sql_lines)


def write_loc_sql(loc_lines):
    if loc_lines is not None:
        with open(LocalFilePaths.app_data_path_form('loc.sql'), 'w') as f:
            f.writelines(loc_lines)


class NodeTracker:
    def __init__(self):
        self.last_node_id = None

    def get_next_node(self, current_node_ids):
        if not current_node_ids:
            self.last_node_id = None
            return None

        try:
            current_index = current_node_ids.index(self.last_node_id)
            next_index = (current_index + 1) % len(current_node_ids)
        except ValueError:
            next_index = 0

        self.last_node_id = current_node_ids[next_index]
        return self.last_node_id


node_tracker = NodeTracker()
