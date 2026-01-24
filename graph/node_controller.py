import uuid
import json

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QSizePolicy

from NodeGraphQt import NodeGraph, PropertiesBinWidget
# patches
from NodeGraphQt.widgets.node_widgets import _NodeGroupBox
from graph.patchs import _patched_size_hint

from graph.db_node_support import NodeCreationDialog, set_nodes_visible_by_type
from graph.set_hotkeys import set_hotkeys
from graph.nodes.dynamic_nodes import generate_tables
from graph.nodes.effect_nodes import GameEffectNode, RequirementEffectNode
from graph.nodes.update_nodes import WhereNode
from graph.port import port_connect_transmit, update_widget_or_prop
from graph.node_state import SuggestionHub
from schema_generator import SQLValidator
from graph.info_panel import CollapsiblePanel
from graph.utils import resource_path

import logging

log = logging.getLogger(__name__)


with open(resource_path('resources/template_mod_metadata.json')) as f:
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
        self.graph.register_nodes(table_nodes_list + [GameEffectNode, RequirementEffectNode, WhereNode])

        graph_widget = self.graph.widget             # show the node graph widget.
        graph_widget.setWindowTitle("Database Editor")
        graph_widget.show()

        self.graph.auto_layout_nodes()

        # custom pullout
        self.enable_auto_node_creation()

        self.graph.port_connected.connect(port_connect_transmit)
        self.graph.suggest_hub = SuggestionHub(self.graph)

        viewer = self.graph.viewer()
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

        def display_properties_bin(node):
            if not properties_bin.isVisible():
                properties_bin.show()

        # wire function to "node_double_clicked" signal.
        self.graph.node_double_clicked.connect(display_properties_bin)

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
                        log.error(f'When pulling out a node connection, failed node creation on drop! Could not find a'
                                  f'valid port for node {src_node.get_property("table_name")} with port {src_port_name}'
                                  f'on the {source_port_item.port_type} side.')
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


###############################################################################################
# Patches to NodeGraphQt ######################################################################
###############################################################################################

_NodeGroupBox.sizeHint = _patched_size_hint
