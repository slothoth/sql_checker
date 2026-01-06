import uuid
import json
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QMainWindow, QSizePolicy
)


from NodeGraphQt import NodeGraph, NodesPaletteWidget, NodesTreeWidget, PropertiesBinWidget
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
        # graph_widget.resize(1100, 800)
        graph_widget.setWindowTitle("Database Editor")
        graph_widget.show()

        self.graph.auto_layout_nodes()

        # custom pullout
        self.enable_auto_node_creation()

        self.graph.property_changed.connect(on_property_changed)

        viewer = self.graph.viewer()
        self.graph.port_connected.connect(on_connection_changed)

        old_resize = viewer.resizeEvent

        panel = CollapsiblePanel(viewer)
        self.graph.side_panel = panel
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        panel.show()

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



        # create a node properties bin widget.
        properties_bin = PropertiesBinWidget(node_graph=self.graph, parent=graph_widget)
        properties_bin.setWindowFlags(QtCore.Qt.Tool)

        # example show the node properties bin widget when a node is double-clicked.
        def display_properties_bin(node):
            if not properties_bin.isVisible():
                properties_bin.show()

        # wire function to "node_double_clicked" signal.
        self.graph.node_double_clicked.connect(display_properties_bin)

        # create a nodes tree widget.
        nodes_tree = NodesTreeWidget(node_graph=self.graph)
        nodes_tree.set_category_label('db.table', 'Database Nodes')
        nodes_tree.set_category_label('db.game_effects', 'GameEffect Nodes')
        nodes_tree.show()

        # create a node palette widget.
        nodes_palette = NodesPaletteWidget(node_graph=self.graph)
        nodes_palette.set_category_label('db.table', 'Database Nodes')
        nodes_palette.set_category_label('db.game_effects', 'GameEffect Nodes')
        nodes_palette.show()


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
                        accepted_ports = {k: True for k, v in src_node.output_port_tables.get(src_port_name, {}).items()}
                    else:
                        src_port = src_node.get_input(src_port_name)   # Dialog only needed if associated with Effect
                        accepted_ports = src_port.accepted_port_types()
                    if len(accepted_ports) > 1:
                        name = self.node_dialog_name([SQLValidator.class_table_name_map.get(i, i)
                                                      for i in accepted_ports])
                    elif len(accepted_ports) == 1:
                        name = SQLValidator.class_table_name_map.get(next(iter(accepted_ports.keys())), '')
                    else:
                        print('failed node creation on drop!')
                        return

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
                                connect_ports_possible = src_node.output_port_tables.get(src_port_name, {}).get(
                                    node_name, [])
                                if len(connect_ports_possible) == 0:
                                    return                                      # error state but dont wanna crash
                                connect_port = new_node_inputs[connect_ports_possible[0]]   # this type, just pick first

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


def on_connection_changed(input_port, output_port):
    input_name, output_name = input_port.name(), output_port.name()
    input_node, output_node = input_port.node(), output_port.node()
    input_widget = input_node.get_widget(input_name)
    current_input_value = input_node.get_property(input_name) if input_widget is None else input_widget.get_value()
    output_widget = output_node.get_widget(output_name)
    current_output_value = output_node.get_property(output_name) if output_widget is None else output_widget.get_value()
    if current_input_value == current_output_value:
        return
    else:
        changing_node, new_value = None, None
        if current_input_value == '' or current_input_value is None:
            changing_node = input_node
            changing_name = input_name
            new_value = current_output_value
        elif current_output_value == '' or current_output_value is None:
            changing_node = output_node
            changing_name = output_name
            new_value = current_input_value
        if changing_node is not None and new_value is not None:
            update_widget_or_prop(changing_node, changing_name, new_value)
    # update gameEffects property to build requirements Set, with nested req OR AND
    if output_node.name() == 'CustomGameEffect' and input_name in ['ReqSet', 'RequirementSetId']:
        current_reqset = output_node.get_property('RequirementSetDict')
        if current_reqset:
            current_reqset = current_reqset[output_name]
            # build new req
            input_node_name = input_node.get_property('table_name')
            if input_node_name == 'ReqEffectCustom':            # add single req to list
                req_id = input_node.get_widget('RequirementId').get_value()
                current_reqset['reqs'].append(req_id)
            elif input_node_name == 'RequirementSets':          # use existant reqset
                reqset_id = input_node.get_widget('RequirementSetId').get_value()
                current_reqset['reqs'].append({'reqset': reqset_id})
            else:
                print(f'oh no! wrong input table: {input_node_name}')


def update_widget_or_prop(node, widget_name, new_val):
    display_widget = node.get_widget(widget_name)
    if display_widget is not None:
        display_widget.set_value(new_val)
    else:
        hidden_property = node.get_property(widget_name)
        if hidden_property is not None:
            node.set_property(widget_name, new_val)

