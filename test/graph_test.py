import pytest
import json

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest


from graph.node_controller import NodeEditorWindow
from graph.transform_json_to_sql import transform_json, make_modinfo
from graph.set_hotkeys import write_sql
from graph.db_spec_singleton import (modifier_argument_info, requirement_argument_info, req_arg_type_list_map,
                                     mod_arg_type_list_map, db_spec)


def setup_types_node(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window.graph.viewer())
    name = 'Types'
    class_name = f"{name.title().replace('_', '')}Node"
    node = window.graph.create_node(f'db.table.{name.lower()}.{class_name}')
    return node, window


def mod_output_check(window, test_sql_path):
    current = window.graph.current_session()
    if not current:
        current = 'resources/graph.json'

    window.graph.save_session(current)
    sql_lines = transform_json(current)
    write_sql(sql_lines)
    check_test_against_expected_sql(test_sql_path)


def check_test_against_expected_sql(test_sql_path):
    with open('resources/main.sql', 'r') as f:
        test_sql = f.readlines()

    with open(f'test/test_data/{test_sql_path}', 'r') as f:
        expected_sql = f.readlines()

    test_set = set(test_sql)
    expected_set = set(expected_sql)
    if test_set != expected_set:
        missing_sql = expected_set - test_set
        extra_sql = test_set - expected_set
        assert len(missing_sql) == 0, f'Missed lines {missing_sql}'
        assert len(extra_sql) == 0, f'extra lines {extra_sql}'
# UI tests


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

# No UI tests


def test_write_graph_to_mod(qtbot):
    node, window = setup_types_node(qtbot)
    node.set_property('Type', 'TYPE_TEST')
    node.set_property('Kind', 'KIND_ABILITY')
    mod_output_check(window, 'basic_mod.sql')
    # make modinfo
    template, mod_name, = make_modinfo(window.graph)
    # TODO refactor or find a way to get the same modinfo because different UUIDs. I dont wanna regex
    # And also i dont really wanna refactor.


def test_node_value_change(qtbot):
    window = NodeEditorWindow(parent=None)
    qtbot.addWidget(window)
    node = window.graph.create_node('db.game_effects.GameEffectNode')
    missed = []
    for i in modifier_argument_info:
        try:
            node.set_property('EffectType', i)
        except TypeError as e:
            print(f'Errored out on effectType {i}: {e}')
            missed.append(i)
            print(missed)
    print(missed)       # check acti


def test_game_effect_save(qtbot):
    print()


def test_req_effect_value_change(qtbot):
    window = NodeEditorWindow(parent=None)
    qtbot.addWidget(window)
    node = window.graph.create_node('db.game_effects.RequirementEffectNode')
    missed = []
    for i in requirement_argument_info:
        try:
            node.set_property('RequirementType', i)
        except TypeError as e:
            print(f'Errored out on RequirementType {i}: {e}')
            missed.append(i)
            print(missed)
    print(missed)


def test_write_effect_and_req_graph_to_mod(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    effect_1, effect_2 = 'EFFECT_ADJUST_PLAYER_YIELD_FOR_RESOURCE', 'EFFECT_ADJUST_UNIT_RESOURCE_DAMAGE'
    req_1, req_2 = 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_UNIT_TYPE', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_BUILDINGS'
    effect_1_param_map = {v: k for k, v in mod_arg_type_list_map[effect_1].items()}
    effect_2_param_map = {v: k for k, v in mod_arg_type_list_map[effect_2].items()}
    req_1_param_map = {v: k for k, v in req_arg_type_list_map[req_1].items()}
    req_2_param_map = {v: k for k, v in req_arg_type_list_map[req_2].items()}

    # effect changes
    effect_node = window.graph.create_node('db.game_effects.GameEffectNode')
    effect_node.set_property('EffectType', effect_1)
    effect_node.set_property('CollectionType', 'COLLECTION_ALL_PLAYERS')
    effect_node.set_property(effect_1_param_map['Amount'], '2')
    effect_node.set_property(effect_1_param_map['YieldType'], 'YIELD_FOOD')

    effect_node.set_property('EffectType', effect_2)
    effect_node.set_property(effect_2_param_map['Amount'], 6)
    effect_node.set_property(effect_2_param_map['ResourceClassType'], 3)   # will need to change from int once better

    req_node = window.graph.create_node('db.game_effects.RequirementEffectNode')
    req_node.set_property('RequirementType', req_1)
    req_node.set_property(req_1_param_map['Amount'], '4')         # string for some reason
    req_node.set_property(req_1_param_map['UnitType'], 'UNIT_TEST')

    req_node.set_property('RequirementType', req_2)
    req_node.set_property(req_2_param_map['BuildingType'], 'BUILDING_TEST')     # 'BuildingType' 'BUILDING_TEST'
    mod_output_check(window, 'test_effects_not_connected_reqs.sql')


def test_write_effect_and_req_connected_graph_to_mod(qtbot):
    window = NodeEditorWindow()                                 # this version has a reqset as connected
    qtbot.addWidget(window)
    effect_1, effect_2 = 'EFFECT_ADJUST_PLAYER_YIELD_FOR_RESOURCE', 'EFFECT_ADJUST_UNIT_RESOURCE_DAMAGE'
    req_1, req_2 = 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_UNIT_TYPE', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_BUILDINGS'
    effect_1_param_map = {v: k for k, v in mod_arg_type_list_map[effect_1].items()}
    effect_2_param_map = {v: k for k, v in mod_arg_type_list_map[effect_2].items()}
    req_1_param_map = {v: k for k, v in req_arg_type_list_map[req_1].items()}
    req_2_param_map = {v: k for k, v in req_arg_type_list_map[req_2].items()}

    effect_node = window.graph.create_node('db.game_effects.GameEffectNode')        # effect changes
    effect_node.set_property('EffectType', effect_1)
    effect_node.set_property('CollectionType', 'COLLECTION_ALL_PLAYERS')
    effect_node.set_property(effect_1_param_map['Amount'], '2')
    effect_node.set_property(effect_1_param_map['YieldType'], 'YIELD_FOOD')

    effect_node.set_property('EffectType', effect_2)
    effect_node.set_property(effect_2_param_map['Amount'], 6)
    effect_node.set_property(effect_2_param_map['ResourceClassType'], 3)   # will need to change from int once better

    req_node = window.graph.create_node('db.game_effects.RequirementEffectNode')        # req changes
    req_node.set_property('RequirementType', req_1)
    req_node.set_property(req_1_param_map['Amount'], '4')                   # string for some reason
    req_node.set_property(req_1_param_map['UnitType'], 'UNIT_TEST')

    req_node.set_property('RequirementType', req_2)
    req_node.set_property(req_2_param_map['BuildingType'], 'BUILDING_TEST')     # 'BuildingType' 'BUILDING_TEST'

    # connect req and effect
    req_input_port = req_node.input_ports()[0]              # ReqSet
    req_output_port = effect_node.output_ports()[0]         # should be SubjectReq
    req_output_port.connect_to(req_input_port)
    mod_output_check(window, 'test_effects_and_reqs.sql')


def test_all_table_nodes(qtbot):
    window = NodeEditorWindow()  # this version has a reqset as connected
    qtbot.addWidget(window)
    sql_commands = transform_json('test/test_data/perf_test_fin.json')
    write_sql(sql_commands)
    check_test_against_expected_sql('all_table_nodes.sql')
