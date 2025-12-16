from graph.node_controller import NodeEditorWindow
import pytest
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMainWindow
import json



def test_menu_actions_exist(qtbot):
    window = NodeEditorWindow(parent=None)
    qtbot.addWidget(window)
    window.show()
    shortcuts = window.menuBar().actions()
    shortcut_dict = {action.text(): action.menu().actions() for action in window.menuBar().actions()}
    named_shortcuts = {key: [action.text() for action in val] for key, val in shortcut_dict.items()}
    # get hot_keys.json
    with open('resources/hotkeys.json') as f:
        hotkeys_setup = json.load(f)
    shortcut_correct_structure = {}
    for hotkey_info in hotkeys_setup:
        if hotkey_info.get("type", '') == "menu":
            label = hotkey_info.get("label")
            shortcut_correct_structure[label] = [i['label'] for i in hotkey_info.get('items', []) if i.get('type', '') == 'command']
    assert shortcut_correct_structure == named_shortcuts


def test_graph_widget_loaded(qtbot):
    window = NodeEditorWindow(parent=None)
    qtbot.addWidget(window)
    window.show()

    assert window.graph is not None
    assert window.centralWidget() == window.graph.widget


def test_drag_port_to_empty_space_triggers_release(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    window.show()

    viewer = window.graph.viewer()
    qtbot.waitExposed(viewer)

    # setup node
    name = 'Types'
    class_name = f"{name.title().replace('_', '')}Node"
    node = window.graph.create_node(f'db.table.{name.lower()}.{class_name}')
    ports = node.input_ports()
    port_dict = {i.name(): i for i in ports}
    start_port = port_dict['Kind']
    scene_pos = start_port.view.scenePos()
    start_pos = viewer.mapFromScene(scene_pos)
    end_pos = QPoint(400, 400)

    current_nodes = [n for n in window.graph.all_nodes() if 'db.table.' in n.type_] # should be one

    QTest.mousePress(
        viewer.viewport(),
        Qt.LeftButton,
        Qt.NoModifier,
        start_pos
    )

    QTest.mouseMove(
        viewer.viewport(),
        end_pos
    )

    QTest.mouseRelease(
        viewer.viewport(),
        Qt.LeftButton,
        Qt.NoModifier,
        end_pos
    )

    new_nodes = [n for n in window.graph.all_nodes() if 'db.table.' in n.type_] # should be two

    assert len(new_nodes) > len(current_nodes)

    new_node = list(set(new_nodes) - set(current_nodes))[0]
    assert new_node.get_property('table_name') == 'Kinds'


