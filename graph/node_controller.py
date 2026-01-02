import uuid
import json
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from NodeGraphQt import NodeGraph

from graph.db_node_support import NodeCreationDialog, sync_node_options, set_nodes_visible_by_type
from graph.db_spec_singleton import db_spec, modifier_system_tables, attach_tables
from graph.set_hotkeys import set_hotkeys
from graph.dynamic_nodes import generate_tables, GameEffectNode, RequirementEffectNode
from schema_generator import SQLValidator
# bodge job for blocking recursion
recently_changed = {}

with open('data/mod_metadata.json') as f:
    default_meta = json.load(f)


class NodeEditorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph = NodeGraph()
        self.setCentralWidget(self.graph.widget)
        self.graph.main_window = parent
        mod_uuid = 'SQL_GUI_' + str(uuid.uuid4().hex)
        default_meta['Mod UUID'] = mod_uuid
        self.graph.setProperty('meta', default_meta)

        menubar = self.menuBar()
        set_hotkeys(self, menubar)

        # custom SQL nodes
        table_nodes_list = generate_tables(self.graph)
        self.graph.register_nodes(table_nodes_list + [GameEffectNode, RequirementEffectNode])
        # db.game_effects.modifier
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

        hide = self.graph.property("Hide Types") or False
        set_nodes_visible_by_type(self.graph, 'db.table.types.TypesNode', not hide)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

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
                        if src_node.get_property('table_name') == 'GameEffectCustom':
                            if src_port.name() == 'ModifierId':
                                possible_table_info = {k: True for k in attach_tables}
                            else:
                                possible_table_info = {'ReqEffectCustom': True, 'RequirementSets': True}
                        elif src_node.get_property('table_name') == 'ReqEffectCustom':
                            valid_tables = db_spec.node_templates['RequirementSets']['backlink_fk']
                            possible_table_info = {key: 'unused' for key, val in db_spec.node_templates.items() if
                                                   key in valid_tables and key not in modifier_system_tables}
                            possible_table_info['ReqEffectCustom'] = 'GameEffect'
                        else:
                            valid_tables = db_spec.node_templates[src_node.get_property('table_name')]['backlink_fk']
                            possible_table_info = {key: 'unused' for key, val
                                                   in db_spec.node_templates.items() if key in valid_tables}
                            if 'Modifiers' in possible_table_info:
                                possible_table_info['GameEffectCustom'] = 'unused'
                            if 'RequirementSets' in possible_table_info:
                                possible_table_info['ReqEffectCustom'] = 'unused'
                        if len(possible_table_info) > 1:        # it could be multiple tables, open dialog
                            name = self.node_dialog_name(possible_table_info)
                            if not name:
                                return
                        else:
                            name = valid_tables[0]

                    else:
                        src_port = src_node.get_input(src_port_name)   # Dialog only needed if associated with Effect
                        src_node_name = src_node.get_property('table_name')     # System so like TraitModifiers,
                        if src_node_name =='ReqEffectCustom':                # Modifiers.SubjectRequirementSetId
                            name = 'GameEffectCustom'
                        elif src_node_name =='GameEffectCustom':
                            name = 'ReqEffectCustom'
                        elif src_node_name in attach_tables:
                            original_name = SQLValidator.fk_to_tbl_map[src_node_name][src_port_name]
                            name = self.node_dialog_name({original_name: True, 'GameEffectCustom': True})
                        else:
                            name = SQLValidator.fk_to_tbl_map[src_node_name][src_port_name]

                    if name == 'GameEffectCustom':
                        node_name = 'db.game_effects.GameEffectNode'
                    elif name == 'ReqEffectCustom':
                        node_name = 'db.game_effects.RequirementEffectNode'
                    else:
                        node_name = f"db.table.{name.lower()}.{name.title().replace('_', '')}Node"
                    new_node = self.graph.create_node(node_name, pos=[scene_pos.x(), scene_pos.y()])

                    # Connect nodes
                    if src_port.type_() == 'out':   # Connect to first available input of new node, which should be PK
                        new_node_inputs = new_node.input_ports()
                        port_index = None
                        if new_node_inputs:
                            if len(new_node_inputs) == 1:
                                port_index = 0
                                connect_port = new_node_inputs[0]
                            else:
                                connect_port = new_node.get_link_port(src_node.get_property('table_name'), source_port_item.name)
                                if connect_port:
                                    port_index = next((i for i, s in enumerate(new_node_inputs) if s.name() == connect_port), 0)

                            if port_index is not None:
                                src_port.connect_to(new_node_inputs[port_index])
                                old_pk = source_port_item.node.get_widget(source_port_item.name).get_value()  # get val of connecting entry
                                display_widget = new_node.get_widget(connect_port)
                                if display_widget is not None:
                                    display_widget.set_value(old_pk)
                                else:
                                    hidden_property = new_node.get_property(connect_port)
                                    if hidden_property is not None:
                                        new_node.set_property(connect_port, old_pk)

                    elif src_port.type_() == 'in':
                        # Connect to first available output of new node, which should be primary key
                        if new_node.output_ports():
                            new_node.output_ports()[0].connect_to(src_port)

        # Apply the patch
        self.graph.viewer().mouseReleaseEvent = custom_mouse_release

    def node_dialog_name(self, possible_table_info):
        dialog = NodeCreationDialog(table_subset_info=possible_table_info)
        viewer = self.graph.viewer()
        pos = viewer.mapToGlobal(QtGui.QCursor.pos())
        dialog.move(pos)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        name = dialog.selected()
        return name


def on_property_changed(node, property_name, property_value):
    sync_nodes_check(node, property_name)
    propogate_port_check(node, property_name)


def sync_nodes_check(node, property_name):
    age = node.graph.property('meta').get('Age')
    if age == 'ALWAYS':
        age_specific_db = db_spec.all_possible_vals
    else:
        age_specific_db = db_spec.possible_vals.get(age, {})

    pk_list = age_specific_db.get(node.name(), {}).get('primary_keys', {})
    if len(pk_list) == 1 and pk_list[0] == property_name:
        sync_node_options(node.graph)


# handles recursion. We want it so if a node changes a field that is linked to another node, backwards OR forwards
# it updates downstream and upstream, changing fields. This prevents those field change retriggering on the
# original node, ad infinitum. Couldn't find a cleaner way with blocking signals.
def propogate_port_check(node, property_name):
    node_name = node.name()
    if recently_changed.get(node_name,  {}).get(property_name, {}):
        recently_changed[node_name][property_name] = False
        return
    else:
        if node_name not in recently_changed:
            recently_changed[node_name] = {}
        recently_changed[node_name][property_name] = True
        propogate_node_ports(node, property_name)
        recently_changed[node_name][property_name] = False


def propogate_node_ports(node, property_name):
    matching_ports = [p for p in list(node.inputs().values()) + list(node.outputs().values())
                      if p.name() == property_name]
    for matching_port in matching_ports:
        is_connected = bool(matching_port.connected_ports())
        if is_connected:
            propagate_value_by_port_name(node, property_name)


def propagate_value_by_port_name(source_node, prop_name):
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
