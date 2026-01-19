import pytest

from graph.transform_json_to_sql import transform_json
from graph.set_hotkeys import mod_test_session, check_valid_sql_against_db
from utils import (check_test_against_expected_sql, create_node, setup_types_node, save, mod_output_check,
                   cast_test_input, make_window, update_delete_node_setup, setup_effect_req)


def test_state_validation_fail_fk():
    sql_commands, dict_form_list, loc_lines, incompletes_full = transform_json('test/test_data/test_graph.json')
    result = check_valid_sql_against_db('AGE_ANTIQUITY', sql_commands)
    expected_mod_trait_error = "There wasn't a reference entry in Modifiers that had ModifierId = MISSING_MOD_TRAIT."
    expected_mod_ability_error = "There wasn't a reference entry in Modifiers that had ModifierId = MISSING_MOD_ABILITY."
    assert len(result['foreign_key_errors']) == 2
    fk_title_errors = result['fk_error_explanations']['title_errors']
    assert expected_mod_trait_error in fk_title_errors[('TraitModifiers', 'Modifiers', 'ModifierId')]
    assert expected_mod_ability_error in fk_title_errors[('UnitAbilityModifiers', 'Modifiers', 'ModifierId')]


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
    assert "There wasn't a reference entry in Districts that had DistrictType = DISTRICT_TEST." in log_lines


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
    assert 'There were 1 Invalid Nodes that were not run:' in log_lines
    assert 'Node Constructibles had problem MISSING REQUIRED COLUMNS: ConstructibleClass;' in log_lines


def test_log_discards_errors_from_no_fk_due_to_fail_insert(qtbot):      # fake fails when ran in sequence
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
