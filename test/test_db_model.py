'''Tests TODO:
- A performance run of a full model using a frozen modding.db
- Getter tests, to make sure we can get to the right databases and read from them
- Error tests, to make sure our log is working correctly
- Graph Side:
-- Feature: CreateDynamicNode
--- check Dialog box works? maybe too basic
--- check created dynamic node works
--- check that all possible nodes are populated
-- Feature: ComboBox value
--- Check it updates on changed dependant node value
--- Check it updates when node is destroyed that it relies on
--- Check values change when age is changed
--- Check possible_values generation is correct
--- Check possible_values is all 3 ages combined if ALWAYS set in age.
-- Feature: Connected Node updates
--- Check connection for update is made when new node connection is made
--- Check connection for update made on dragged out node made
--- Check value updates when PK node updates
--- Check value updates when FK node updates
-- Feature: Drag out Node Creation:
--- Check dialog opens correctly
--- Check correct nodes are populated in dialog
--- Check it builds a new DynamicNode instance on dialog click
--- Check that the correct connection is made for new DynamicNode on each port, and its on the right side.
-- Feature: Package graph contents into mod
--- Check that packaged mod matches graph setup
--- Check that we correctly explain why graph is invalid # TODO FEATURE
-- Feature: Metadata setter:
--- Check that it displays all the right values
--- Check that it transmits those values on accept.
-- Feature: Hotkeys:
--- Check that all hotkeys are populated
--- Check all hotkeys are labelled correctly
--- Check that the top menu bar displays those in folders
-- Feature: Convert existing Mod to Graph
--- Check that mod filepath_list options from modinfo parsing make sense
--- Check that ORM model works
--- Check that the right nodes are made
--- Check that layout is done correctly
--- Check that connections are made correctly
'''

import time

from schema_generator import check_valid_sql_against_db
from graph.transform_json_to_sql import transform_json
from schema_generator import SQLValidator


def test_state_validation_fail_fk():
    start_time = time.time()
    sql_commands, dict_form_list, loc_lines = transform_json('test/test_data/test_graph.json')
    result = check_valid_sql_against_db('AGE_ANTIQUITY', sql_commands)
    assert len(result['foreign_key_errors']) == 2
    assert (result['fk_error_explanations']['title_errors'][('TraitModifiers', 'Modifiers', 'ModifierId')] ==
            'FOREIGN KEY missing on TraitModifiers.ModifierId. It needs a corresponding primary key on table Modifiers.')
    assert (result['fk_error_explanations']['title_errors'][('UnitAbilityModifiers', 'Modifiers', 'ModifierId')] ==
            'FOREIGN KEY missing on UnitAbilityModifiers.ModifierId. It needs a corresponding primary key on table Modifiers.')
    end_time = time.time()
    print(end_time - start_time)        # should be like 0.05 seconds, neglible


def test_map_age_databases():
    SQLValidator.state_validation_setup('testfake')

