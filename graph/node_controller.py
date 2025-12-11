from pathlib import Path
from Qt import QtGui, QtWidgets
from NodeGraphQt import NodeGraph
import json

from graph.db_node_support import NodeCreationDialog
from graph.nodes import custom_ports_node, widget_nodes, db_nodes

BASE_PATH = Path(__file__).parent.resolve()


def main():
    # signal.signal(signal.SIGINT, signal.SIG_DFL)    #   handle SIGINT to make the app terminate on CTRL+C
    graph = NodeGraph()
    hotkey_path = Path(BASE_PATH, 'hotkeys', 'hotkeys.json')        # set up context menu for the node graph.
    graph.set_context_menu_from_file(hotkey_path, 'graph')

    graph.register_nodes([                  # registered example nodes.
        custom_ports_node.CustomPortsNode,
        widget_nodes.DropdownMenuNode,
        widget_nodes.TextInputNode,
        widget_nodes.CheckboxNode,
        db_nodes.DynamicFieldsNode
    ])

    graph_widget = graph.widget             # show the node graph widget.
    graph_widget.resize(1100, 800)
    graph_widget.setWindowTitle("Database Editor")
    graph_widget.show()

    graph.auto_layout_nodes()

    # custom pullout
    enable_auto_node_creation(graph, db_nodes.DynamicFieldsNode)

    def on_nodes_deleted(node_ids):
        if False:
            sync_node_b_options(graph)
    graph.nodes_deleted.connect(on_nodes_deleted)
    graph.property_changed.connect(on_property_changed)


def enable_auto_node_creation(graph, node_class_to_create):
    """
    Patches the graph viewer to create a new node when a connection
    is dropped in empty space.
    """
    original_mouse_release = graph.viewer().mouseReleaseEvent

    def custom_mouse_release(event):
        # --- 1. Detect if we are dragging a connection ---
        # NodeGraphQt stores the active drag pipe in '_live_pipe'
        live_pipe = getattr(graph.viewer(), '_LIVE_PIPE', None)
        source_port_item = getattr(graph.viewer(), '_start_port')

        # --- 2. Check what is under the mouse ---
        # We need to know if the user released over an existing port
        items_under_mouse = graph.viewer().items(event.pos())
        released_on_port = False

        # Check if any item under cursor is a PortItem
        # Note: We check class name to avoid importing internal PortItem class directly
        for item in items_under_mouse:
            if type(item).__name__ == 'PortItem':
                released_on_port = True
                break

        # --- 3. Execute original behavior ---
        # This handles the standard connection logic or clearing the pipe
        original_mouse_release(event)

        # --- 4. Custom Logic: Create Node if dropped on empty space ---
        if source_port_item and not released_on_port:
            # Calculate scene position for the new node
            scene_pos = graph.viewer().mapToScene(event.pos())

            # Find the high-level NodeObject from the low-level PortItem
            # source_port_item.node is the NodeItem (graphic)
            # source_port_item.node.id is the unique identifier
            src_node_id = source_port_item.node.id
            src_node = graph.get_node_by_id(src_node_id)

            if src_node:
                src_port_name = source_port_item.name
                src_port = src_node.get_output(src_port_name) or src_node.get_input(src_port_name)

                # create new node
                if src_port.type_() == 'out':       # it could be multiple tables, open dialog
                    valid_tables = [j for j in templates[source_port_item.node.name]['backlink_fk'].values()]
                    if len(valid_tables) > 1:
                        dialog = NodeCreationDialog(subset=source_port_item.node.name)
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
                    name = templates[source_port_item.node.name]['foreign_keys'][src_port_name]

                new_node = graph.create_node('nodes.widget.DynamicFieldsNode',
                                             pos=[scene_pos.x(), scene_pos.y()])
                new_node.set_spec(name)
                new_node.set_name(name)

                # Connect them!
                # Logic: If dragged from Output -> Connect to New Node Input
                #        If dragged from Input  -> Connect to New Node Output
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
    valid_options_dict = {}

    all_nodes = graph.all_nodes()
    chs = templates
    pck = possible_vals
    target_nodes = [n for n in all_nodes if n.type_ == 'nodes.widget.DynamicFieldsNode']
    for node in target_nodes:
        if node.name() in possible_vals:            # if table contributes to possible vals
            primary_key_property_list = templates[node.name()]['primary_keys']
            if len(primary_key_property_list) == 1:
                val = node.get_property(primary_key_property_list[0])
                if val:
                    if node.name() not in valid_options_dict:
                        valid_options_dict[node.name()] = set()
                    valid_options_dict[node.name()].add(val)

    # add default vals
    for tbl_name, new_options_set in valid_options_dict.items():
        valid_options_dict[tbl_name] = sorted(list(valid_options_dict[tbl_name]))
        valid_options_dict[tbl_name].extend(possible_vals[tbl_name]['_PK_VALS'])

    fk_ref_tables = {key: val for key, val in possible_vals.items()
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
    if node.type_ != 'nodes.widget.DynamicFieldsNode':
        return
    if property_name == 'name':                 # should only happen on instantiation
        sync_node_b_options(node.graph)
    pk_list = templates.get(node.name(), {}).get('primary_keys', {})
    if len(pk_list) == 1 and pk_list[0] == property_name:
        sync_node_b_options(node.graph)


with open('resources/db_spec.json', 'r') as f:
    templates = json.load(f)

with open('resources/db_possible_vals.json', 'r') as f:
    possible_vals = json.load(f)
