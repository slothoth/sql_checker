from collections import defaultdict, Counter
from NodeGraphQt import BaseNode
from time import time

from graph.singletons.db_spec_singleton import db_spec
from graph.utils import flatten, strip_transient_widgets, auto_layout_nodes_minimise_crossing

import logging

log = logging.getLogger(__name__)


def group_nodes_by_table_with_connections(graph):
    original_connections, node_group_map, grouped_nodes = [], {}, defaultdict(list)
    all_nodes = graph.all_nodes()
    grouped_nodes, original_connections = get_groups_and_connections(all_nodes)
    for table_name, nodes in grouped_nodes.items():
        group_node, connection_map = make_group_node(graph, nodes, node_group_map, table_name)
        if group_node is not None:
            _rewire_graph(graph, group_node, node_group_map, original_connections)

    delete_displaced_nodes(graph, grouped_nodes)
    layout_and_centre_view(graph)


def collate_flowering_trees(graph):
    all_nodes = graph.all_nodes()
    groups = group_flowering_leaves(all_nodes)
    color = (150, 150, 150)
    node_to_created_group, group_counts = {}, {}
    _, original_connections = get_groups_and_connections(all_nodes)
    for (group_id, port_name, port_type), nodes in groups.items():
        nodes_list = list(nodes)
        name = f"{graph.get_node_by_id(group_id).get_property('table_name')}_{port_type}"
        group_node, connection_map = make_group_node(graph, nodes_list, node_to_created_group, name,
                                     group_name='nodes.group.MyGroupNode', color=color)
        group_counts[name] = len(nodes_list)
        sub_graph = group_node.expand()
        _rewire_subgraph(sub_graph)  # wire internal ports and layout
        auto_layout_nodes_minimise_crossing(sub_graph, nodes=sub_graph.all_nodes(), down_stream=True)
        group_node.collapse()

    log.info('nodes grouped:')
    log.info(sorted([(k, v) for k, v in group_counts.items()], key=lambda x: x[0], reverse=True))
    _rewire_outer_graph(graph, original_connections, node_to_created_group)
    delete_displaced_nodes(graph, groups)
    layout_and_centre_view(graph)


def group_leaf_trees(graph, method='leaf_stubs'):
    all_nodes = graph.all_nodes()
    start_time = time()
    if method == 'leaf_stubs':
        groups = group_leaves_allow_stubs(all_nodes)
        color = (30, 30, 150)
    elif method == 'force_forward_chains':
        groups = force_forward_chains(all_nodes)
        color = (150, 30, 30)
    elif method == 'simple_leaf':
        groups = group_leaves(all_nodes)
        color = (150, 150, 30)
    else:
        print('a')
    end_group_time = time()
    print(f'Finished grouping in {end_group_time - start_time}')
    signature_map = defaultdict(list)
    for g_id, nodes in groups.items():
        if len(nodes) > 1:
            sig = get_structural_signature(nodes)
            signature_map[sig].append(nodes)

    groups, node_group_map = merge_signature_components(signature_map)
    _, original_connections = get_groups_and_connections(all_nodes)
    node_to_created_group, group_counts = {}, {}
    for group_id, nodes in groups.items():
        nodes_list = list(nodes)
        best_root = find_best_root(nodes_list, nodes)
        _, name = name_from_root(best_root)
        group_node, connection_map = make_group_node(graph, nodes_list, node_to_created_group, name,
                                     group_name='nodes.group.MyGroupNode', color=color)
        group_counts[name] = len(nodes_list)
        sub_graph = group_node.expand()
        _rewire_subgraph(sub_graph, connection_map)                 # wire internal ports and layout
        auto_layout_nodes_minimise_crossing(sub_graph, nodes=sub_graph.all_nodes(), down_stream=True)
        group_node.collapse()

    log.info('nodes grouped:')
    log.info(sorted([(k, v) for k, v in group_counts.items()], key=lambda x: x[0], reverse=True))

    _rewire_outer_graph(graph, original_connections, node_to_created_group)
    delete_displaced_nodes(graph, groups)

    # second pass to group together same table nodes
    connected = [i for i in graph.all_nodes()
                 if any(port.connected_ports() for port in i.output_ports() + i.input_ports())]
    unconnected = [i for i in graph.all_nodes() if i not in connected and i.type_ != 'nodes.group.MyGroupNode']

    node_group_map = {}
    grouped_nodes, original_connections = get_groups_and_connections(unconnected)

    viable_groups = {k: v for k, v in grouped_nodes.items() if len(v) > 1}
    for table_name, nodes in viable_groups.items():
        make_group_node(graph, nodes, node_group_map, table_name, color=(30, 150, 30))

    delete_displaced_nodes(graph, grouped_nodes)
    layout_and_centre_view(graph)
    graph.clear_selection()


def process_and_group_islands(graph):
    islands, unused_connections = get_weakly_connected_components(graph)
    islands_by_signature = defaultdict(list)
    for island_nodes in islands:
        sig = get_chain_signature(island_nodes)
        islands_by_signature[sig].append(island_nodes)
    for signature, components_list in islands_by_signature.items():
        if len(components_list) == 1 and len(components_list[0]) == 1:
            continue
        sub_nodes = flatten(components_list)
        node_tables = signature.split('->')
        most_common_table = sorted([(k, count) for k, count in Counter(node_tables).items()],
                                   key=lambda x: x[1], reverse=True)[0][0]
        group_node, connection_map = make_group_node(graph, sub_nodes, {}, most_common_table)
        group_node.set_contained_table_description(node_tables)

    layout_and_centre_view(graph)


def merge_signature_components(signature_map):
    groups, node_group_map, group_counter = {}, {}, 0
    for sig, clusters in signature_map.items():
        merged_set = set()
        for c in clusters:
            merged_set.update(c)

        new_id = f"merged_group_{group_counter}"  # assign group id
        groups[new_id] = merged_set
        for n in merged_set:
            node_group_map[n.id] = new_id
        group_counter += 1
    return groups, node_group_map


def get_nodes_with_connections(all_nodes, node_group_map):
    candidate_parents = []  # Find parents that have outputs connected to something
    for node in all_nodes:
        if node.id in node_group_map:
            continue
        if any(p.connected_ports() for p in node.outputs().values()):
            candidate_parents.append(node)
    return candidate_parents


def get_connected_nodes(node, input=True, output=False):
    connected_nodes = set()
    port_connections = []
    if input:
        port_connections = port_connections + node.input_ports()
    if output:
        port_connections = port_connections + node.output_ports()
    for port in port_connections:
        for connected_port in port.connected_ports():
            connected_nodes.add(connected_port.node())
    return connected_nodes


def group_leaves_allow_stubs(all_nodes):                # better than normal leaf algo
    node_group_map, groups = identify_leaves(all_nodes)
    changed = True
    while changed:
        changed = False
        candidate_parents = get_nodes_with_connections(all_nodes, node_group_map)

        for parent in candidate_parents:
            absorbable_groups, children = set(), set()          # Get all children connected to outputs
            children = get_connected_nodes(parent, input=False, output=True)
            if not children:
                continue
            for child in children:
                if child.id not in node_group_map:
                    continue
                unique_parents = get_connected_nodes(child, input=True, output=False)
                non_stub_parents = 0        # Allow merge if other parents are stubs
                for p in unique_parents:
                    has_inputs = any(port.connected_ports() for port in p.inputs().values())   # No Inputs Upstream
                    # Downstream port should only include the child object, so max 1
                    simple_outputs = sum(len(port.connected_ports()) for port in p.outputs().values()) < 2
                    is_stub = (not has_inputs) and simple_outputs
                    if not is_stub:
                        non_stub_parents += 1

                if non_stub_parents < 2:            # only add if one non-stub parent
                    absorbable_groups.add(node_group_map[child.id])

            # Merge parent and valid children groups
            if absorbable_groups:
                primary_set, primary_group_id = merge_existing_groups(groups, absorbable_groups, node_group_map)
                primary_set.add(parent)
                node_group_map[parent.id] = primary_group_id
                changed = True
    return groups


def group_leaves(all_nodes):
    node_group_map, groups = identify_leaves(all_nodes)
    changed = True
    while changed:
        changed = False
        candidate_parents = get_nodes_with_connections(all_nodes, node_group_map)
        for parent in candidate_parents:
            absorbable_groups = set()         # Get all children connected to outputs
            children = get_connected_nodes(parent, input=False, output=True)
            if not children:
                continue
            can_absorb = True
            for child in children:
                if child.id not in node_group_map:          # Must be grouped
                    can_absorb = False
                    break
                unique_parents = get_connected_nodes(child, input=True, output=False)   # Exclusive Check (No Merge)
                if len(unique_parents) != 1:
                    can_absorb = False
                    break

                absorbable_groups.add(node_group_map[child.id])

            if can_absorb and absorbable_groups:
                primary_set, primary_group_id = merge_existing_groups(groups, absorbable_groups, node_group_map)
                primary_set.add(parent)
                node_group_map[parent.id] = primary_group_id
                changed = True

    return groups


def merge_existing_groups(groups, absorbable_groups, node_group_map):
    primary_group_id = list(absorbable_groups)[0]
    primary_set = groups[primary_group_id]

    # Merge existing groups
    for other_id in absorbable_groups:
        if other_id == primary_group_id:
            continue

        nodes_to_move = groups[other_id]
        primary_set.update(nodes_to_move)

        for n in nodes_to_move:
            node_group_map[n.id] = primary_group_id

        del groups[other_id]

    return primary_set, primary_group_id


def identify_leaves(all_nodes):
    node_group_map, groups = {}, {}
    for node in all_nodes:
        is_leaf = True
        for port in node.outputs().values():
            if port.connected_ports():
                is_leaf = False
                break

        if is_leaf:
            group_id = node.id
            node_group_map[node.id] = group_id
            groups[group_id] = {node}
    return node_group_map, groups


def force_forward_chains(nodes):
    """
    Returns a list of lists, where each inner list is a chain of nodes.
    Chains are exclusive (a node belongs to only one chain).
    Chains are formed by grouping nodes connected by non-branching edges.

    Rule: Node U and Node V (U->V) are in the same chain IF U outputs ONLY to V.
    """
    visited, chains = set(), []
    for node in nodes:
        if node in visited:
            continue

        current_chain = []
        queue = [node]
        visited.add(node)

        while queue:
            curr = queue.pop(0)
            current_chain.append(curr)
            curr_out_nodes = get_connected_nodes(curr, output=True, input=False)
            if len(curr_out_nodes) == 1:
                nxt = list(curr_out_nodes)[0]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
            curr_in_nodes = get_connected_nodes(curr, input=True, output=False)
            for prev in curr_in_nodes:
                prev_out_nodes = get_connected_nodes(prev, output=True, input=False)
                if len(prev_out_nodes) == 1:
                    # (Implicitly prev_out_nodes == {curr})
                    if prev not in visited:
                        visited.add(prev)
                        queue.append(prev)

        chains.append(current_chain)
    dict_chains = {i[0].id: i for i in chains}
    return dict_chains


def group_flowering_leaves(all_nodes):
    """Iterates through all nodes, find all output nodes that are stubs, but only
    if more than two output nodes."""
    groups = {}
    for parent_node in all_nodes:
        for port in parent_node.output_ports():
            connected_ports = port.connected_ports()
            nodes_on_this_port = []
            for cp in connected_ports:
                downstream_node = cp.node()
                nodes_on_this_port.append(downstream_node)
            if len(nodes_on_this_port) > 2:
                groups[(parent_node.id, port.name(), 'Outputs')] = nodes_on_this_port
        input_nodes = [i for i in get_connected_nodes(parent_node, input=True, output=False)
                       if len(get_connected_nodes(i, input=True, output=True)) == 1]
        if len(input_nodes) > 2:
            groups[(parent_node.id, 'Input', 'Inputs')] = input_nodes

    return groups


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


def _rewire_graph(graph, group_node, node_group_map, original_connections):
    sub_graph = group_node.expand()
    _rewire_subgraph(sub_graph)

    organize_subgraph_layout(sub_graph)
    auto_layout_nodes_minimise_crossing(sub_graph, nodes=sub_graph.all_nodes(), down_stream=True)
    sub_graph.set_zoom(0)
    sub_graph.center_on(sub_graph.all_nodes())
    group_node.collapse()

    _rewire_outer_graph(graph, original_connections, node_group_map)


def _rewire_subgraph(sub_graph, connection_map=None):
    if connection_map is None:
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
    else:
        bridge_nodes = {n.name(): n for n in sub_graph.get_input_port_nodes()}
        for internal_node in sub_graph.all_nodes():
            if internal_node.type_ in ['nodeGraphQt.nodes.PortInputNode', 'nodeGraphQt.nodes.PortOutputNode']:
                continue
            for port_name, port in internal_node.inputs().items():
                key = (internal_node.id, port_name)
                if key in connection_map:
                    group_port_name = connection_map[key]
                    bridge_node = bridge_nodes.get(group_port_name)
                    if bridge_node:
                        bridge_node.output(0).connect_to(port)


def _rewire_outer_graph(graph, original_connections, node_group_map):
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


def make_group_node(graph, nodes, node_group_map, name, group_name=None, color=None):  # utils
    center_x = sum([n.x_pos() for n in nodes]) / len(nodes)
    center_y = sum([n.y_pos() for n in nodes]) / len(nodes)

    if group_name is None:
        group_name = f"{nodes[0].__identifier__.replace('.table.', '.group.')}.{name.title()}Node"
        if group_name not in graph.registered_nodes():
            group_name = 'nodes.group.MyGroupNode'

    group_node = graph.create_node(group_name, name=name, pos=[center_x, center_y], push_undo=True, selected=False)
    if color is not None:
        group_node.set_color(*color)
    for node in nodes:
        node_group_map[node.id] = group_node

    group_node.set_contained_table_description([i.get_property('table_name') or 'Group' for i in nodes])

    connection_map = {}
    if group_name == 'nodes.group.MyGroupNode':
        node_class_set = {node.get_property('table_name'): node for node in nodes}      # setify
        input_port_names, output_port_names = {}, {}
        for table_name, node in node_class_set.items():
            # Check Inputs
            for port in node.input_ports():
                if port.name() not in input_port_names:
                    group_port = group_node.add_input(name=port.name(), multi_input=True)
                    group_port_name = group_port.name()
                    input_port_names[port.name()] = group_port_name
                else:
                    group_port_name = input_port_names[port.name()]
                connection_map[(node.id, port.name())] = group_port_name
        for table_name, node in node_class_set.items():
            for port in node.output_ports():
                port_name = port.name()
                if port_name in input_port_names:
                    port_name = f"{port_name} 1"
                if port_name not in output_port_names:
                    group_port = group_node.add_output(name=port_name)
                    group_port_name = group_port.name()
                    output_port_names[port_name] = group_port_name
                else:
                    group_port_name = output_port_names[port_name]
                connection_map[(node.id, port_name)] = group_port_name

    graph_migrated_params = strip_transient_widgets(nodes)
    raw_session = graph._serialize(nodes)
    normalized_session = normalize_session_coordinates(raw_session)
    group_node.set_sub_graph_session(normalized_session)
    return group_node, connection_map


def delete_displaced_nodes(graph, grouped_nodes):
    nodes_to_delete = []
    for nodes in grouped_nodes.values():
        if len(nodes) >= 2:
            nodes_to_delete.extend(nodes)

    graph.delete_nodes(list(set(nodes_to_delete)), push_undo=True)


def layout_and_centre_view(graph):
    auto_layout_nodes_minimise_crossing(graph, nodes=graph.all_nodes(), down_stream=True)
    graph.select_all()
    graph.fit_to_selection()
    graph.clear_selection()


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


def get_structural_signature(nodes_set):
    """ Format: (src_index, src_port, dst_index, dst_port)"""
    nodes_list = list(nodes_set)
    nodes_list.sort(key=lambda n: n.__identifier__)
    node_to_idx = {n: i for i, n in enumerate(nodes_list)}
    type_sig = tuple(n.__identifier__ for n in nodes_list)
    conn_sig = []
    for n in nodes_list:
        src_idx = node_to_idx[n]
        for port_name, port in n.outputs().items():
            for cp in port.connected_ports():
                dst_node = cp.node()
                if dst_node in nodes_set:
                    dst_idx = node_to_idx[dst_node]
                    conn_sig.append((src_idx, port_name, dst_idx, cp.name()))

    conn_sig.sort()
    return type_sig, tuple(conn_sig)


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


def find_best_root(nodes_list, nodes):
    """Find a Root for naming purposes. Use the first root-like node, and use its primary key tuple"""
    best_root = nodes_list[0]
    min_internal = 9999
    for n in nodes_list:
        count = 0
        for p in n.inputs().values():
            for cp in p.connected_ports():
                if cp.node() in nodes:
                    count += 1
        if count < min_internal:
            min_internal = count
            best_root = n
    return best_root


def name_from_root(best_root):
    base_id = best_root.__identifier__
    group_class_name = "nodes.group.MyGroupNode"
    if '.table.' in base_id:
        group_class_name = db_spec.table_name_id_mapper[best_root.get_property('table_name')]
    name = best_root.name() + "_Group"
    if 'db.table.' in best_root.type_:  # we can use primary key
        pk_list = best_root.primary_keys  # TODO we currently use pk, but if there are plural signatures, should use signature
        pk_values = [best_root.get_property(i) for i in
                     pk_list]  # TODO translate signature using db_spec.table_name_id_mapper
        if all(pk_values):
            name = ", ".join(pk_values)
    return group_class_name, name


def get_chain_signature(nodes):
    node_names = list(set([i.get_property('table_name') for i in nodes]))
    if not all(i in ['Types', 'Kinds'] for i in node_names):
        node_names = [i for i in node_names if i not in ['Types', 'Kinds']]
    sorted_nodes = sorted(node_names)
    signature = "->".join([name for name in sorted_nodes])      # Create signature from types
    return signature


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
