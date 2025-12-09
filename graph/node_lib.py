import signal
from pathlib import Path

from Qt import QtCore, QtWidgets

# import example nodes from the "nodes" sub-package
from graph.nodes import basic_nodes, custom_ports_node, group_node, widget_nodes
from NodeGraphQt import (
    NodeGraph,
    NodesPaletteWidget,
    NodesTreeWidget,
    PropertiesBinWidget,
)

BASE_PATH = Path(__file__).parent.resolve()


def main():
    # handle SIGINT to make the app terminate on CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtWidgets.QApplication([])

    # create graph controller.
    graph = NodeGraph()

    # set up context menu for the node graph.
    hotkey_path = Path(BASE_PATH, 'hotkeys', 'hotkeys.json')
    graph.set_context_menu_from_file(hotkey_path, 'graph')

    # registered example nodes.
    graph.register_nodes([
        basic_nodes.BasicNodeA,
        basic_nodes.BasicNodeB,
        basic_nodes.CircleNode,
        basic_nodes.SVGNode,
        custom_ports_node.CustomPortsNode,
        group_node.MyGroupNode,
        widget_nodes.DropdownMenuNode,
        widget_nodes.TextInputNode,
        widget_nodes.CheckboxNode
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)
    graph_widget.setWindowTitle("NodeGraphQt Example")
    graph_widget.show()

    # fit nodes to the viewer.
    graph.clear_selection()
    graph.fit_to_selection()

    # adjust layout of node to be vertical (for all nodes).
    # graph.set_layout_direction(LayoutDirectionEnum.VERTICAL.value)

    # Custom builtin widgets from NodeGraphQt
    # ---------------------------------------

    # create a node properties bin widget.
    properties_bin = PropertiesBinWidget(node_graph=graph, parent=graph_widget)
    properties_bin.setWindowFlags(QtCore.Qt.Tool)

    # example show the node properties bin widget when a node is double-clicked.
    def display_properties_bin(node):
        if not properties_bin.isVisible():
            properties_bin.show()

    # wire function to "node_double_clicked" signal.
    graph.node_double_clicked.connect(display_properties_bin)

    # create a nodes tree widget.
    nodes_tree = NodesTreeWidget(node_graph=graph)
    nodes_tree.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
    nodes_tree.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
    nodes_tree.set_category_label('nodes.widget', 'Widget Nodes')
    nodes_tree.set_category_label('nodes.basic', 'Basic Nodes')
    nodes_tree.set_category_label('nodes.group', 'Group Nodes')
    # nodes_tree.show()

    # create a node palette widget.
    nodes_palette = NodesPaletteWidget(node_graph=graph)
    nodes_palette.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
    nodes_palette.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
    nodes_palette.set_category_label('nodes.widget', 'Widget Nodes')
    nodes_palette.set_category_label('nodes.basic', 'Basic Nodes')
    nodes_palette.set_category_label('nodes.group', 'Group Nodes')
    # nodes_palette.show()

    app.exec_()


if __name__ == '__main__':
    main()