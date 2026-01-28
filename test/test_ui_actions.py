import pytest
import json
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest

from graph.singletons.filepaths import LocalFilePaths       # needed because we want logger initialised
LocalFilePaths.initialize_paths()
from graph.singletons.db_spec_singleton import db_spec
db_spec.initialize(False)

from graph.utils import resource_path
from graph.node_controller import NodeEditorWindow

from utils import setup_types_node, create_node


def test_drag_port_to_empty_space_triggers_release(qtbot):
    node, window = setup_types_node(qtbot)
    viewer = window.graph.viewer()
    port_dict = {i.name(): i for i in node.input_ports()}
    start_port = port_dict['Kind']
    scene_pos = start_port.view.scenePos()
    start_pos = viewer.mapFromScene(scene_pos)
    end_pos = QPoint(400, 400)

    current_nodes = [n for n in window.graph.all_nodes() if 'db.table.' in n.type_] # should be one

    QTest.mousePress(viewer.viewport(), Qt.LeftButton, Qt.NoModifier, start_pos)
    QTest.mouseMove(viewer.viewport(), end_pos)
    QTest.mouseRelease(viewer.viewport(), Qt.LeftButton, Qt.NoModifier, end_pos)

    new_nodes = [n for n in window.graph.all_nodes() if 'db.table.' in n.type_] # should be two

    assert len(new_nodes) > len(current_nodes)

    new_node = list(set(new_nodes) - set(current_nodes))[0]
    assert new_node.get_property('table_name') == 'Kinds'


def test_menu_actions_exist(qtbot):
    window = NodeEditorWindow(parent=None)
    qtbot.addWidget(window)
    window.show()
    shortcuts = window.menuBar().actions()
    shortcut_dict = {action.text(): action.menu().actions() for action in window.menuBar().actions()}
    named_shortcuts = {key: [action.text() for action in val] for key, val in shortcut_dict.items()}
    # get hot_keys.json
    with open(resource_path('resources/hotkeys.json')) as f:
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


def test_update_suggestions(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    qtbot.waitExposed(window)
    unit_stats = create_node(window, 'Unit_Stats')
    qtbot.wait(1)
    init_suggestions = set(unit_stats.get_widget('UnitType')._completer_model.stringList())

    unit = create_node(window, 'Units')
    qtbot.wait(1)
    unit.get_widget('UnitType').set_value('UNIT_TEST')
    qtbot.wait(1)
    new_suggestions = set(unit_stats.get_widget('UnitType')._completer_model.stringList())
    difference = new_suggestions - init_suggestions
    assert 'UNIT_TEST' in difference
    assert len(difference) == 1


def test_update_suggestions_remove_on_change(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    qtbot.waitExposed(window)
    unit_stats = create_node(window, 'Unit_Stats')
    qtbot.wait(1)
    unit = create_node(window, 'Units')
    qtbot.wait(1)
    unit.get_widget('UnitType').set_value('UNIT_TEST')
    qtbot.wait(1)
    unit.get_widget('UnitType').set_value('UNIT_OTHER_TEST')
    qtbot.wait(1)
    newest_suggestions = set(unit_stats.get_widget('UnitType')._completer_model.stringList())
    assert 'UNIT_TEST' not in newest_suggestions
    assert 'UNIT_OTHER_TEST' in newest_suggestions


def test_update_suggestions_remove_on_delete(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    qtbot.waitExposed(window)
    unit_stats = create_node(window, 'Unit_Stats')
    qtbot.wait(1)
    unit = create_node(window, 'Units')
    qtbot.wait(1)
    unit.get_widget('UnitType').set_value('UNIT_TEST')
    qtbot.wait(1)

    window.graph.delete_node(unit)
    qtbot.wait(1)
    suggestions = set(unit_stats.get_widget('UnitType')._completer_model.stringList())
    assert 'UNIT_TEST' not in suggestions


def test_update_suggestions_plural_same_node(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    qtbot.waitExposed(window)
    unit_stats = create_node(window, 'Unit_Stats')
    qtbot.wait(1)
    unit = create_node(window, 'Units')
    qtbot.wait(1)
    unit.get_widget('UnitType').set_value('UNIT_TEST')
    qtbot.wait(1)
    unit_two = create_node(window, 'Units')
    qtbot.wait(1)
    unit_two.get_widget('UnitType').set_value('UNIT_TEST_2')
    qtbot.wait(1)
    suggestions = set(unit_stats.get_widget('UnitType')._completer_model.stringList())
    assert 'UNIT_TEST_2' in suggestions
    assert 'UNIT_TEST' in suggestions