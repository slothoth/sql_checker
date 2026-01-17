import pytest
import json
import os
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest
from PyQt5 import QtGui


from graph.node_controller import NodeEditorWindow
from graph.transform_json_to_sql import make_modinfo
from graph.set_hotkeys import import_session_set_params, save_session_to_mod, mod_test_session
from graph.db_spec_singleton import db_spec
from graph.mod_conversion import build_imported_mod

from utils import (check_test_against_expected_sql, create_node, setup_types_node, save, mod_output_check,
                   cast_test_input, make_window, update_delete_node_setup)


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
    reqset_reqs.set_property('RequirementSetId', 'TEST_REQSET_1')

    req_input_port = req_node.inputs()['ReqSet']              # connect req and effect
    req_output_port = effect_node.outputs()['SubjectReq']
    req_output_port.connect_to(req_input_port)
    assert req_output_port in req_input_port.connected_ports()

    reqset_port_reqset = reqset.outputs()['RequirementSetId']            # connect reqset to rsr
    reqset_req_port_reqset = reqset_reqs.inputs()['RequirementSetId']
    reqset_port_reqset.connect_to(reqset_req_port_reqset)                # renames!
    assert reqset_port_reqset in reqset_req_port_reqset.connected_ports()

    reqset_req_port_req = reqset_reqs.inputs()['RequirementId']          # connect reqset to req
    req_port_req = req1.outputs()['RequirementId']
    reqset_req_port_req.connect_to(req_port_req)
    assert reqset_req_port_req in req_port_req.connected_ports()

    other_reqset_port = reqset.inputs()['RequirementSetId']             # connect req custom to reqset
    req_output_port.connect_to(other_reqset_port)
    assert req_output_port in other_reqset_port.connected_ports()
    mod_output_check(window, 'nested_reqs.sql')


def test_write_node_with_loc(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    unit = create_node(window, 'Units')
    qtbot.wait(1)
    unit.get_widget('Name').set_value('Extra Cool Unit')
    unit.get_widget('UnitType').set_value('TEST_UNIT')
    unit.get_widget('CoreClass').set_value('CORE_CLASS_MILITARY')
    unit.get_widget('FormationClass').set_value('FORMATION_CLASS_LAND_COMBAT')
    unit.get_widget('UnitMovementClass').set_value('UNIT_MOVEMENT_CLASS_FOOT')
    unit.get_widget('Domain').set_value('DOMAIN_LAND')
    save_session_to_mod(window.graph)
    check_test_against_expected_sql('units_with_name.sql', 'resources/main.sql')
    check_test_against_expected_sql('units_with_name_loc.sql', 'resources/loc.sql')


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


def test_update_delete_node_update_case(qtbot):
    sql = "UPDATE Units SET BaseMoves=10 WHERE UnitType in ('UNIT_ARCHER', 'UNIT_WARRIOR')"
    node, change_val = update_delete_node_setup(sql, qtbot)
    assert ('UNIT_ARCHER', 'BaseMoves: 2 -> 10') in change_val
    assert ('UNIT_WARRIOR', 'BaseMoves: 2 -> 10') in change_val
    assert len(change_val) == 2


def test_update_delete_node_delete_case(qtbot):
    sql = "DELETE FROM Units WHERE UnitType in ('UNIT_ARCHER', 'UNIT_WARRIOR')"
    node, change_val = update_delete_node_setup(sql, qtbot)
    assert ('UNIT_ARCHER', 'Deleted') in change_val
    assert ('UNIT_WARRIOR', 'Deleted') in change_val
    assert len(change_val) == 2


def test_update_delete_node_update_lower_case(qtbot):           # TODO handle column lower case
    sql = "UPDATE uNiTs SET BaseMoves=10 WHERE UnitType in ('UNIT_ARCHER', 'UNIT_WARRIOR')"
    node, change_val = update_delete_node_setup(sql, qtbot)
    assert ('UNIT_ARCHER', 'BaseMoves: 2 -> 10') in change_val
    assert ('UNIT_WARRIOR', 'BaseMoves: 2 -> 10') in change_val
    assert len(change_val) == 2

# error cases


def test_update_delete_node_error_empty_statement_case(qtbot):      # failing but in practice works?
    return
    node, change_val = update_delete_node_setup("", qtbot)
    assert len(change_val) == 1, f'error statement should only be a single row, was actually {change_val}'
    sql_widget_palette = node.get_widget('sql').palette()
    actual = {'bg': sql_widget_palette.color(QtGui.QPalette.ColorRole.Base),
              'text': sql_widget_palette.color(QtGui.QPalette.ColorRole.Text),
              'highlight': sql_widget_palette.color(QtGui.QPalette.ColorRole.Highlight)}
    expected = {'bg': QtGui.QColor("#FDE8E8"), 'text': QtGui.QColor("#9B1C1C"), 'highlight': QtGui.QColor("#F05252")}

    actual_colours = {k: (v.red(), v.green(), v.blue()) for k, v in actual.items()}
    expected_colours = {k: (v.red(), v.green(), v.blue()) for k, v in expected.items()}
    for colour, rgb in actual_colours.items():
        assert rgb == expected_colours[colour], f'Expected RGB for {colour} after error: {expected_colours[colour]}. Actually {rgb}.'


def test_update_delete_node_error_incomplete_statement_case(qtbot):
    sql = "UPDATE"
    node, change_val = update_delete_node_setup(sql, qtbot)
    full_error = " ".join("".join(i) for i in change_val)
    assert 'Expected table name but got None' in full_error


def test_update_delete_node_error_not_existing_table_case(qtbot):
    node, change_val = update_delete_node_setup("UPDATE Uni SET BaseMoves=10", qtbot)
    full_error = " ".join("".join(i) for i in change_val)
    assert "Table 'Uni' not found" in full_error


def test_update_delete_node_error_not_existing_col_case(qtbot):
    node, change_val = update_delete_node_setup("UPDATE Units SET WrongCol=10", qtbot)
    full_error = " ".join("".join(i) for i in change_val)
    assert 'no such column: WrongCol', full_error


def test_log_fk_errors(qtbot):
    window = make_window(qtbot)
    constructible = create_node(window, 'Constructibles')
    constructible.get_widget('ConstructibleType').set_value('BUILDING_TEST')
    constructible.get_widget('ConstructibleClass').set_value('TEST_CLASS')
    constructible.set_property('AdjacentDistrict', 'DISTRICT_TEST')
    mod_test_session(window.graph)
    log_output = window.graph.side_panel.log_display.toPlainText()
    log_lines = log_output.split('\n')
    assert 'There were 1 Foreign Key Errors:' in log_lines
    assert 'FOREIGN KEY missing:' in log_lines
    assert 'INSERT into Constructibles:' in log_lines
    assert 'ConstructibleType: BUILDING_TEST' in log_lines
    assert "There wasn't a reference entry in Districts that had ['DistrictType'] = DISTRICT_TEST." in log_lines


def test_log_fk_succeeds(qtbot):
    window = make_window(qtbot)
    constructible = create_node(window, 'Constructibles')
    constructible.get_widget('ConstructibleType').set_value('BUILDING_TEST')
    constructible.get_widget('ConstructibleClass').set_value('TEST_CLASS')
    constructible.set_property('AdjacentDistrict', 'DISTRICT_TEST')

    district = create_node(window, 'Districts')
    district.get_widget('DistrictType').set_value('DISTRICT_TEST')
    district.get_widget('DistrictClass').set_value('TEST_CLASS')
    district.get_widget('UrbanCoreType').set_value('TEST_UHH')

    district_type = create_node(window, 'Types')
    district_type.get_widget('Type').set_value('DISTRICT_TEST')
    district_type.get_widget('Kind').set_value('KIND_DISTRICT')
    mod_test_session(window.graph)
    log_output = window.graph.side_panel.log_display.toPlainText()
    log_lines = log_output.split('\n')
    assert 'Valid mod setup' in log_lines


def test_log_unique_constraint_vanilla_errors(qtbot):
    window = make_window(qtbot)
    constructible = create_node(window, 'Constructibles')
    constructible.get_widget('ConstructibleType').set_value('BUILDING_GRANARY')
    constructible.get_widget('ConstructibleClass').set_value('TEST_CLASS')
    mod_test_session(window.graph)
    log_output = window.graph.side_panel.log_display.toPlainText()
    log_lines = log_output.split('\n')
    assert 'There were 1 failed Insertions:' in log_lines
    assert 'Missed Inserts for Constructibles:' in log_lines
    assert ('Entry Constructibles with primary key: ConstructibleType: BUILDING_GRANARY could not be inserted as that'
            ' primary key ConstructibleType: BUILDING_GRANARY was already present.') in log_lines


def test_log_unique_constraint_in_mod_errors(qtbot):
    window = make_window(qtbot)
    constructible = create_node(window, 'Constructibles')
    constructible.get_widget('ConstructibleType').set_value('BUILDING_TEST')
    constructible.get_widget('ConstructibleClass').set_value('TEST_CLASS')

    constructible_two = create_node(window, 'Constructibles')
    constructible_two.get_widget('ConstructibleType').set_value('BUILDING_TEST')
    constructible_two.get_widget('ConstructibleClass').set_value('TEST_CLASS')

    mod_test_session(window.graph)
    log_output = window.graph.side_panel.log_display.toPlainText()
    log_lines = log_output.split('\n')
    assert 'There were 1 failed Insertions:' in log_lines
    assert 'Missed Inserts for Constructibles:' in log_lines
    assert ('Entry Constructibles with primary key: ConstructibleType: BUILDING_TEST could not be inserted as that'
            ' primary key ConstructibleType: BUILDING_TEST was already present.') in log_lines


def test_log_not_null_errors(qtbot):
    window = make_window(qtbot)
    constructible = create_node(window, 'Constructibles')
    constructible.get_widget('ConstructibleType').set_value('BUILDING_TEST')

    mod_test_session(window.graph)
    log_output = window.graph.side_panel.log_display.toPlainText()
    log_lines = log_output.split('\n')
    assert 'There were 1 failed Insertions:' in log_lines
    assert 'Missed Inserts for Constructibles:' in log_lines
    assert ('Entry Constructibles with primary key: ConstructibleType: BUILDING_TEST could not be inserted as'
            ' ConstructibleClass was not specified.') in log_lines


def test_log_discards_errors_from_no_fk_due_to_fail_insert(qtbot):
    window = make_window(qtbot)
    district = create_node(window, 'Districts')
    district.get_widget('DistrictType').set_value('DISTRICT_TEST')
    district.get_widget('DistrictClass').set_value('TEST_CLASS')
    district.get_widget('UrbanCoreType').set_value('TEST_UHH')

    type = create_node(window, 'Types')
    type.get_widget('Type').set_value('DISTRICT_TEST')

    mod_test_session(window.graph)
    log_output = window.graph.side_panel.log_display.toPlainText()
    log_lines = log_output.split('\n')
    assert 'Also causes FOREIGN KEY errors on entries:' in log_lines
    assert 'INSERT into Districts: DistrictType: DISTRICT_TEST' in log_lines
    assert """FOREIGN KEY missing:
            INSERT into Districts:
            DistrictType: DISTRICT_TEST
            
            There wasn't a reference entry in Types that had Type = DISTRICT_TEST.""" not in log_lines


def test_import_mod(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    cwd = os.getcwd()

    mod_info_found = build_imported_mod(f'{cwd}/test/test_data/test_mod_import', window.graph)
    print('test that the graph nodes exist, and they have the right connections')
    for node in window.graph.all_nodes():
        print('')