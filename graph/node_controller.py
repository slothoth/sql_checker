import uuid
from PySide6 import QtGui, QtWidgets
from NodeGraphQt import NodeGraph

from graph.db_node_support import NodeCreationDialog
from graph.nodes.dynamic_nodes import generate_tables
from graph.db_spec_singleton import ResourceLoader
from graph.set_hotkeys import set_hotkeys

db_spec = ResourceLoader()
# bodge job for blocking recursion
recently_changed = {}


def nodeEditorWindow(main_app_window=None):
    graph = NodeGraph()
    graph.main_window = main_app_window         # needed to trigger run analysis
    mod_uuid = 'SQL_GUI_' + str(uuid.uuid4().hex)
    graph.setProperty('meta', {
        'Mod Name': 'SQL_GUI_Mod',
        'Mod Description': "A Mod built with Slothoths SQL GUI. They haven't customised their Description!",
        'Mod Author': 'Slothoth Mod GUI',
        'Mod UUID': mod_uuid,
        'Mod Action': 'always_slothoth_mod_gui',
        'Age': 'AGE_ANTIQUITY',
    })
    set_hotkeys(graph.get_context_menu('graph'))

    # custom SQL nodes
    table_nodes_list = generate_tables()
    graph.register_nodes(table_nodes_list)

    graph_widget = graph.widget             # show the node graph widget.
    graph_widget.resize(1100, 800)
    graph_widget.setWindowTitle("Database Editor")
    graph_widget.show()

    graph.auto_layout_nodes()

    # custom pullout
    enable_auto_node_creation(graph)

    def on_nodes_deleted(node_ids):
        if False:
            sync_node_b_options(graph)
    graph.nodes_deleted.connect(on_nodes_deleted)
    graph.property_changed.connect(on_property_changed)

    # 2. Connect the connection handler
    viewer = graph.viewer()
    viewer.connection_changed.connect(on_connection_changed)


def enable_auto_node_creation(graph):
    """
    Patches the graph viewer to create a new node when a connection
    is dropped in empty space.
    """
    original_mouse_release = graph.viewer().mouseReleaseEvent

    def custom_mouse_release(event):
        # --- 1. Detect if we are dragging a connection using start port on live connection ---
        live_pipe = getattr(graph.viewer(), '_LIVE_PIPE', None)
        source_port_item = getattr(graph.viewer(), '_start_port')

        # check for no port item to do node creation
        items_under_mouse = graph.viewer().items(event.pos())
        released_on_port = any(type(i).__name__ == 'PortItem' for i in items_under_mouse)

        original_mouse_release(event)           # release mouse events

        # Create Node if dropped on empty space
        if source_port_item and not released_on_port:
            scene_pos = graph.viewer().mapToScene(event.pos())
            src_node = graph.get_node_by_id(source_port_item.node.id)

            if src_node:
                src_port_name = source_port_item.name
                if source_port_item.port_type == 'out':
                    src_port = src_node.get_output(src_port_name)
                    valid_tables = db_spec.node_templates[source_port_item.node.name]['backlink_fk'][src_port_name]
                    if len(valid_tables) > 1:        # it could be multiple tables, open dialog
                        dialog = NodeCreationDialog(subset=source_port_item)
                        viewer = graph.viewer()
                        pos = viewer.mapToGlobal(QtGui.QCursor.pos())
                        dialog.move(pos)

                        if dialog.exec_() != QtWidgets.QDialog.Accepted:
                            return

                        name = dialog.selected()
                        if not name:
                            return
                    else:
                        name = valid_tables[0]

                else:
                    src_port = src_node.get_input(src_port_name)             # No Dialog as fk reference can only be one table
                    name = db_spec.node_templates[source_port_item.node.name]['foreign_keys'][src_port_name]

                class_name = f"{name.title().replace('_', '')}Node"
                new_node = graph.create_node(f'db.table.{name.lower()}.{class_name}',
                                             pos=[scene_pos.x(), scene_pos.y()])

                # Connect nodes
                if src_port.type_() == 'out':        # Connect to first available input of new node, which should be PK
                    if new_node.input_ports():
                        connect_port = new_node.get_link_port(source_port_item.node.name, source_port_item.name)
                        if connect_port:
                            port_index = next((i for i, s in enumerate(new_node.input_ports()) if s.name() == connect_port), 0)
                            src_port.connect_to(new_node.input_ports()[port_index])
                            old_pk = source_port_item.node.get_widget(source_port_item.name).get_value()             # get val of connecting entry
                            new_node.get_widget(connect_port).set_value(old_pk)
                        else:
                            src_port.connect_to(new_node.input_ports()[0])
                elif src_port.type_() == 'in':
                    # Connect to first available output of new node, which should be primary key
                    if new_node.output_ports():
                        new_node.output_ports()[0].connect_to(src_port)

    # Apply the patch
    graph.viewer().mouseReleaseEvent = custom_mouse_release


def sync_node_b_options(graph):
    print('syncing nodes...')
    valid_options_dict = {}

    all_nodes = graph.all_nodes()
    target_nodes = [n for n in all_nodes if 'db.table.' in n.type_]
    for node in target_nodes:
        if node.name() in db_spec.possible_vals:            # if table contributes to possible vals
            primary_key_property_list = db_spec.node_templates[node.name()]['primary_keys']
            if len(primary_key_property_list) == 1:
                val = node.get_property(primary_key_property_list[0])
                if val:
                    if node.name() not in valid_options_dict:
                        valid_options_dict[node.name()] = set()
                    valid_options_dict[node.name()].add(val)

    # add default vals
    for tbl_name, new_options_set in valid_options_dict.items():
        valid_options_dict[tbl_name] = sorted(list(valid_options_dict[tbl_name]))
        valid_options_dict[tbl_name].extend(db_spec.possible_vals[tbl_name]['_PK_VALS'])

    fk_ref_tables = {key: val for key, val in db_spec.possible_vals.items()
     if any(key_j != '_PK_VALS' and val_j['ref'] in valid_options_dict for key_j, val_j in val.items())}
    fk_nodes = [n for n in target_nodes if n.name() in fk_ref_tables]
    for node in fk_nodes:
        node_info = fk_ref_tables[node.name()]
        correct_refs = {col: col_info for col, col_info in node_info.items() if col !='_PK_VALS'
                       and col_info['ref'] in valid_options_dict}
        # tehcnically could be plural, UnitReplaces
        for ref_name, col_info in correct_refs.items():
            combo_widget = node.get_widget(ref_name)
            if combo_widget:
                current_val = node.get_property(ref_name)
                sorted_options = valid_options_dict[col_info['ref']]
                combo_widget.clear()
                # 2. Add the new list of items
                combo_widget.add_items(sorted_options)
                if current_val in sorted_options:
                    combo_widget.set_value(current_val)


def on_property_changed(node, property_name, property_value):
    if 'db.table' not in node.type_:
        return
    pk_list = db_spec.node_templates.get(node.name(), {}).get('primary_keys', {})
    if len(pk_list) == 1 and pk_list[0] == property_name:
        sync_node_b_options(node.graph)

    if recently_changed.get(node.name(),  {}).get(property_name, {}):       # this section handles updating connected port
        recently_changed[node.name()][property_name] = False
        return
    else:
        if node.name() not in recently_changed:
            recently_changed[node.name()] = {}
        recently_changed[node.name()][property_name] = True
        matching_ports = [p for p in list(node.inputs().values()) + list(node.outputs().values()) if p.name() == property_name]
        for matching_port in matching_ports:
            is_connected = bool(matching_port.connected_ports())
            if is_connected:
                propagate_value_by_port_name(node, property_name, node.graph)
        recently_changed[node.name()][property_name] = False


def propagate_value_by_port_name(source_node, prop_name, graph):
    prop_value = source_node.get_property(prop_name)
    all_ports = list(source_node.inputs().values()) + list(source_node.outputs().values())
    for port in all_ports:
        if port.name() == prop_name:
            for connected_port in port.connected_ports():
                target_prop_name = connected_port.name()
                target_node = connected_port.node()
                if target_node.has_property(target_prop_name):
                    # we need to make sure if the target node is a comboBox, we first add the option
                    widget = target_node.get_widget(target_prop_name)
                    if widget.__class__.__name__ == 'NodeComboBox':
                        widget.add_items([prop_value])
                    target_node.set_property(target_prop_name, prop_value)


def on_connection_changed(disconnected_ports, connected_ports):
    for port1, port2 in connected_ports:
        prop_name_1 = port1.name()
        prop_name_2 = port2.name()
        node1 = port1.node()
        node2 = port2.node()

        if node1.has_property(prop_name_1) and node2.has_property(prop_name_2):
            winning_value = node1.get_property(prop_name_1)
            qt_node2 = node2.get_widget_layout()
            if qt_node2:
                qt_node2.blockSignals(True)
            node2.set_property(prop_name_2, winning_value)
            if qt_node2:
                qt_node2.blockSignals(False)
