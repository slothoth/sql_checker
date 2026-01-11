import pytest
import json
import os
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest


from graph.node_controller import NodeEditorWindow
from graph.transform_json_to_sql import transform_json, make_modinfo
from graph.set_hotkeys import write_sql, save_session, import_session_set_params
from graph.db_spec_singleton import db_spec
from graph.mod_conversion import build_imported_mod

from utils import check_test_against_expected_sql


def setup_types_node(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window.graph.viewer())
    name = 'Types'
    class_name = f"{name.title().replace('_', '')}Node"
    node = window.graph.create_node(f'db.table.{name.lower()}.{class_name}')
    return node, window


def save(window):
    current = window.graph.current_session()
    if not current:
        current = 'resources/graph.json'
    window.graph._model.session = current
    save_session(window.graph)
    return current


def mod_output_check(window, test_sql_path):
    current = save(window)
    sql_lines = transform_json(current)
    write_sql(sql_lines)
    check_test_against_expected_sql(test_sql_path)


arg_type_map = {}
for k, v in db_spec.mod_type_arg_map.items():
    for key, val in v.items():
        arg_type_map[key] = val

for k, v in db_spec.req_type_arg_map.items():
    for key, val in v.items():
        arg_type_map[key] = val


def cast_test_input(arg, value, node):
    prop_type = arg_type_map[arg]
    if prop_type == 'text':
        casted_val = str(value)
    elif prop_type == 'database':
        casted_val = str(value)
    elif prop_type == 'bool':
        casted_val = 1 if value in ['1', 1, 'true', 'true'] else None
        if casted_val is None:
            casted_val = 0 if value in ['0', 0, 'False', 'false'] else None
        if casted_val is None:
            casted_val = bool(value)
    elif prop_type == 'int':
        casted_val = int(value)
    elif prop_type == 'float':
        casted_val = float(value)
    else:
        raise Exception(f'unhandled arg {arg} with prop {prop_type}')
    node.set_widget_and_prop(arg, casted_val)

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
    for i in db_spec.modifier_argument_info:
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
    for i in db_spec.requirement_argument_info:
        try:
            node.set_property('RequirementType', i)
        except TypeError as e:
            print(f'Errored out on RequirementType {i}: {e}')
            missed.append(i)
            print(missed)
    print(missed)


def setup_effect_req(window):

    # effect changes
    effect_node = window.graph.create_node('db.game_effects.GameEffectNode')
    effect_node.set_property('EffectType', 'EFFECT_ADJUST_PLAYER_YIELD_FOR_RESOURCE')
    effect_node.set_property('CollectionType', 'COLLECTION_ALL_PLAYERS')
    cast_test_input('Amount', '2', effect_node)
    cast_test_input('YieldType', 'YIELD_FOOD',  effect_node)

    effect_node.set_property('EffectType', 'EFFECT_ADJUST_UNIT_RESOURCE_DAMAGE')

    cast_test_input('Amount', '6', effect_node)
    cast_test_input('ResourceClassType', 'RESOURCECLASS_EMPIRE', effect_node)

    req_node = window.graph.create_node('db.game_effects.RequirementEffectNode')
    req_node.set_property('RequirementType', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_UNIT_TYPE')
    cast_test_input('Amount', '4', req_node)
    cast_test_input('UnitType', 'UNIT_TEST', req_node)

    req_node.set_property('RequirementType', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_BUILDINGS')
    cast_test_input('BuildingType', 'BUILDING_TEST', req_node)

    return effect_node, req_node


def test_write_effect_and_req_graph_after_change_to_mod(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    setup_effect_req(window)
    mod_output_check(window, 'test_effects_not_connected_reqs.sql')


def test_write_effect_and_req_connected_graph_after_change_to_mod(qtbot):     # this version has a reqset as connected
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    effect_node, req_node = setup_effect_req(window)
    req_input_port = req_node.inputs()['ReqSet']              # connect req and effect
    req_output_port = effect_node.outputs()['SubjectReq']
    req_output_port.connect_to(req_input_port)
    mod_output_check(window, 'test_effects_and_reqs.sql')


def test_write_effect_and_req_nested(qtbot):            # this version has a reqset as connected
    window = NodeEditorWindow()                         # -  effect_node -> Reqset -> req1, req2
    qtbot.addWidget(window)                             # -            \-> req_node
    effect_node, req_node = setup_effect_req(window)    # technically wrong as SubjectStackLimit and OwnerStackLimit
    req1 = window.graph.create_node('db.table.requirements.RequirementsNode')   # are included
    req1.set_property('RequirementId', 'TEST_REQ_1')
    req1.set_property('RequirementType', 'REQUIREMENT_OPPONENT_IS_DISTRICT')

    reqset = window.graph.create_node('db.table.requirementsets.RequirementsetsNode')
    reqset.set_property('RequirementSetId', 'TEST_REQSET_1')

    reqset_reqs = window.graph.create_node('db.table.requirementsetrequirements.RequirementsetrequirementsNode')

    req_input_port = req_node.inputs()['ReqSet']              # connect req and effect
    req_output_port = effect_node.outputs()['SubjectReq']
    req_output_port.connect_to(req_input_port)

    reqset_port_reqset = reqset.outputs()['RequirementSetId']            # connect reqset to rsr
    reqset_req_port_reqset = reqset_reqs.inputs()['RequirementSetId']
    reqset_port_reqset.connect_to(reqset_req_port_reqset)

    reqset_req_port_req = reqset_reqs.inputs()['RequirementId']          # connect reqset to req
    req_port_req = req1.outputs()['RequirementId']
    reqset_req_port_req.connect_to(req_port_req)

    other_reqset_port = reqset.inputs()['RequirementSetId']             # connect req custom to reqset
    req_output_port.connect_to(other_reqset_port)
    mod_output_check(window, 'nested_reqs.sql')


def test_save_and_load_on_hidden_params(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    setup_effect_req(window)
    current = save(window)
    window.graph.clear_session()
    import_session_set_params(window.graph, current)
    # assert that req args are kept
    game_effects = [i for i in window.graph.all_nodes() if i.get_property('table_name') == 'GameEffectCustom']
    reqs = [i for i in window.graph.all_nodes() if i.get_property('table_name') == 'ReqEffectCustom']
    effect_node = game_effects[0]
    req_node = reqs[0]

    assert effect_node.get_property('Amount') == 6
    assert effect_node.get_property('ResourceClassType') == 'RESOURCECLASS_EMPIRE'
    assert req_node.get_property('Amount') == 4
    assert req_node.get_property('BuildingType') == 'BUILDING_TEST'


def test_import_mod(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    cwd = os.getcwd()

    mod_info_found = build_imported_mod(f'{cwd}/test/test_data/test_mod_import', window.graph)
    print('test that the graph nodes exist, and they have the right connections')
    for node in window.graph.all_nodes():
        print('')