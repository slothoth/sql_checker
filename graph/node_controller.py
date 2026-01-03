import uuid
import json
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow, QSizePolicy
)


from NodeGraphQt import NodeGraph
from graph.db_node_support import NodeCreationDialog, sync_node_options, set_nodes_visible_by_type  # expensive  1.7s
from graph.db_spec_singleton import db_spec                                                         # but other times
from graph.set_hotkeys import set_hotkeys       # expensive  1.9s                                   # fast?
from graph.dynamic_nodes import generate_tables, GameEffectNode, RequirementEffectNode
from schema_generator import SQLValidator
from graph.info_panel import CollapsiblePanel
# bodge job for blocking recursion
recently_changed = {}

with open('data/mod_metadata.json') as f:
    default_meta = json.load(f)


class NodeEditorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph = NodeGraph()
        self.setCentralWidget(self.graph.widget)
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

        old_resize = viewer.resizeEvent

        def reposition_panel():
            margin = 10
            panel.resize(panel.width(), viewer.viewport().height() - margin * 2)
            panel.move(viewer.viewport().width() - panel.width() - margin, margin)

        def resize_event(event):
            old_resize(event)
            reposition_panel()

        viewer.resizeEvent = resize_event

        hide = self.graph.property("Hide Types") or False
        set_nodes_visible_by_type(self.graph, 'db.table.types.TypesNode', not hide)

        panel = CollapsiblePanel(viewer)
        self.graph.side_panel = panel
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        panel.show()


    def enable_auto_node_creation(self):
        """
        Patches the graph viewer to create a new node when a connection
        is dropped in empty space.
        """
        original_mouse_release = self.graph.viewer().mouseReleaseEvent

        def custom_mouse_release(event):
            source_port_item = getattr(self.graph.viewer(), '_start_port')      # useful var only present on live conn

            items_under_mouse = self.graph.viewer().items(event.pos())          # ensure drag is not to existing port
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
                        accepted_ports = {i: True for i in src_node.output_port_tables}
                    else:
                        src_port = src_node.get_input(src_port_name)   # Dialog only needed if associated with Effect
                        accepted_ports = src_port.accepted_port_types()
                    if len(accepted_ports) > 1:
                        name = self.node_dialog_name([SQLValidator.class_table_name_map.get(i, i)
                                                      for i in accepted_ports])
                    else:
                        name = SQLValidator.class_table_name_map.get(next(iter(accepted_ports.keys())), '')

                    node_name = SQLValidator.table_name_class_map.get(name, name)
                    if node_name is None:
                        return
                    new_node = self.graph.create_node(node_name, pos=[scene_pos.x(), scene_pos.y()])

                    # Connect nodes
                    if src_port.type_() == 'out':   # Connect to first available input of new node, which should be PK
                        new_node_inputs = new_node.inputs()
                        if new_node_inputs:
                            if len(new_node_inputs) == 1:
                                connect_port = list(new_node_inputs.values())[0]
                            else:
                                connect_port_name = src_node.output_port_tables[node_name][0]    # if plural fks accept
                                connect_port = new_node_inputs[connect_port_name]           # this type, just pick first

                            if connect_port is not None:
                                src_port.connect_to(connect_port)
                                old_pk = src_node.get_widget(src_port_name).get_value()  # get val of connecting entry
                                update_widget_or_prop(node=new_node, widget_name=connect_port, new_val=old_pk)

                    elif src_port.type_() == 'in':                              # Connect to first available output of
                        if new_node.output_ports():                             # new node, which should be primary key
                            output_port = new_node.output_ports()[0]
                            new_node.output_ports()[0].connect_to(src_port)
                            old_fk = src_node.get_widget(src_port_name).get_value()
                            if old_fk != '':                                    # if not default, update new node pk
                                update_widget_or_prop(node=new_node, widget_name=output_port.name(), new_val=old_fk)

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


def update_widget_or_prop(node, widget_name, new_val):
    display_widget = node.get_widget(widget_name)
    if display_widget is not None:
        display_widget.set_value(new_val)
    else:
        hidden_property = node.get_property(widget_name)
        if hidden_property is not None:
            node.set_property(widget_name, new_val)

