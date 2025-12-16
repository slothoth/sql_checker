import uuid
import json
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from NodeGraphQt import NodeGraph

from graph.db_node_support import NodeCreationDialog, sync_node_options
from graph.nodes.dynamic_nodes import generate_tables
from graph.db_spec_singleton import ResourceLoader
from graph.set_hotkeys import set_hotkeys

db_spec = ResourceLoader()
# bodge job for blocking recursion
recently_changed = {}


class NodeEditorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph = NodeGraph()
        self.setCentralWidget(self.graph.widget)

        menubar = self.menuBar()

        self.graph.main_window = parent         # needed to trigger run analysis
        mod_uuid = 'SQL_GUI_' + str(uuid.uuid4().hex)
        self.graph.setProperty('meta', {
            'Mod Name': 'SQL_GUI_Mod',
            'Mod Description': "A Mod built with Slothoths SQL GUI. They haven't customised their Description!",
            'Mod Author': 'Slothoth Mod GUI',
            'Mod UUID': mod_uuid,
            'Mod Action': 'always_slothoth_mod_gui',
            'Age': 'AGE_ANTIQUITY',
        })
        set_hotkeys(self, menubar)

        # custom SQL nodes
        table_nodes_list = generate_tables(self.graph)
        self.graph.register_nodes(table_nodes_list)

        graph_widget = self.graph.widget             # show the node graph widget.
        graph_widget.resize(1100, 800)
        graph_widget.setWindowTitle("Database Editor")
        graph_widget.show()

        self.graph.auto_layout_nodes()

        # custom pullout
        self.enable_auto_node_creation()

        self.graph.property_changed.connect(on_property_changed)

        viewer = self.graph.viewer()
        viewer.connection_changed.connect(on_connection_changed)

    def enable_auto_node_creation(self):
        """
        Patches the graph viewer to create a new node when a connection
        is dropped in empty space.
        """
        original_mouse_release = self.graph.viewer().mouseReleaseEvent

        def custom_mouse_release(event):
            # Detect if we are dragging a connection using start port on live connection
            live_pipe = getattr(self.graph.viewer(), '_LIVE_PIPE', None)
            source_port_item = getattr(self.graph.viewer(), '_start_port')

            # check for no port item to do node creation
            items_under_mouse = self.graph.viewer().items(event.pos())
            released_on_port = any(type(i).__name__ == 'PortItem' for i in items_under_mouse)

            original_mouse_release(event)           # release mouse events

            # Create Node if dropped on empty space
            if source_port_item and not released_on_port:
                scene_pos = self.graph.viewer().mapToScene(event.pos())
                src_node = self.graph.get_node_by_id(source_port_item.node.id)

                if src_node:
                    src_port_name = source_port_item.name
                    if source_port_item.port_type == 'out':
                        src_port = src_node.get_output(src_port_name)
                        valid_tables = db_spec.node_templates[src_node.get_property('table_name')]['backlink_fk'][src_port_name]
                        if len(valid_tables) > 1:        # it could be multiple tables, open dialog
                            dialog = NodeCreationDialog(subset=source_port_item)
                            viewer = self.graph.viewer()
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
                        src_port = src_node.get_input(src_port_name)   # No Dialog as fk reference can only be one table
                        name = db_spec.node_templates[src_node.get_property('table_name')]['foreign_keys'][src_port_name]

                    class_name = f"{name.title().replace('_', '')}Node"
                    new_node = self.graph.create_node(f'db.table.{name.lower()}.{class_name}',
                                                 pos=[scene_pos.x(), scene_pos.y()])

                    # Connect nodes
                    if src_port.type_() == 'out':        # Connect to first available input of new node, which should be PK
                        if new_node.input_ports():
                            connect_port = new_node.get_link_port(src_node.get_property('table_name'), source_port_item.name)
                            if connect_port:
                                port_index = next((i for i, s in enumerate(new_node.input_ports()) if s.name() == connect_port), 0)
                                src_port.connect_to(new_node.input_ports()[port_index])
                                old_pk = source_port_item.node.get_widget(source_port_item.name).get_value()  # get val of connecting entry
                                new_node.get_widget(connect_port).set_value(old_pk)
                            else:
                                src_port.connect_to(new_node.input_ports()[0])
                    elif src_port.type_() == 'in':
                        # Connect to first available output of new node, which should be primary key
                        if new_node.output_ports():
                            new_node.output_ports()[0].connect_to(src_port)

        # Apply the patch
        self.graph.viewer().mouseReleaseEvent = custom_mouse_release


def on_property_changed(node, property_name, property_value):
    if 'db.table' not in node.type_:
        return
    age = node.graph.property('meta').get('Age')
    if age == 'ALWAYS':
        age_specific_db = db_spec.all_possible_vals
    else:
        age_specific_db = db_spec.possible_vals.get(age, {})

    pk_list = age_specific_db.get(node.name(), {}).get('primary_keys', {})
    if len(pk_list) == 1 and pk_list[0] == property_name:
        sync_node_options(node.graph)

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
        prop_name_1, prop_name_2 = port1.name, port2.name
        node1, node2 = port1.node, port2.node
        if node1.has_widget(prop_name_1) and node2.has_widget(prop_name_2):
            winning_widget = node1.get_widget(prop_name_1)
            new_value = winning_widget.get_value()
            changing_widget = node2.widgets.get(prop_name_2)
            if changing_widget:
                changing_widget.blockSignals(True)
            changing_widget.set_value(new_value)
            if changing_widget:
                changing_widget.blockSignals(False)
