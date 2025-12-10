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

with open('resources/db_spec.json', 'r') as f:
    templates = json.load(f)
