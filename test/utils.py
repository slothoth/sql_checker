from graph.node_controller import NodeEditorWindow
from graph.transform_json_to_sql import transform_json
from graph.set_hotkeys import write_sql, save_session, write_loc_sql
from graph.singletons.db_spec_singleton import db_spec
from graph.singletons.filepaths import LocalFilePaths


def make_window(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    qtbot.waitExposed(window)
    return window


def create_node(window, name):
    class_name = f"{name.title().replace('_', '')}Node"
    node = window.graph.create_node(f'db.table.{name.lower()}.{class_name}')
    return node


def setup_types_node(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window.graph.viewer())
    node = create_node(window, 'Types')
    return node, window


def save(window):
    current = window.graph.current_session()
    if not current:
        current = LocalFilePaths.app_data_path_form('graph.json')
    window.graph._model.session = current
    save_session(window.graph)
    return current


def mod_output_check(window, test_sql_path):
    current = save(window)
    sql_lines, dict_form_list, loc_lines, incompletes_full = transform_json(current)
    write_sql(sql_lines)
    write_loc_sql(loc_lines)
    check_test_against_expected_sql(test_sql_path, LocalFilePaths.app_data_path_form('main.sql'))


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


def update_delete_node_setup(sql_command, qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    qtbot.waitExposed(window)
    node = window.graph.create_node('db.where.WhereNode')
    qtbot.wait(1)
    node.set_property('sql_form', sql_command)
    qtbot.wait(1)
    value = node.get_widget('changes').get_value()
    return node, value


def setup_effect_req(window, qtbot):
    effect_node = window.graph.create_node('db.game_effects.GameEffectNode')
    qtbot.wait(1)
    effect_node.set_property('EffectType', 'EFFECT_ADJUST_PLAYER_YIELD_FOR_RESOURCE')
    qtbot.wait(1)
    effect_node.set_property('CollectionType', 'COLLECTION_ALL_PLAYERS')
    qtbot.wait(1)
    cast_test_input('Amount', '2', effect_node)
    qtbot.wait(1)
    cast_test_input('YieldType', 'YIELD_FOOD',  effect_node)
    qtbot.wait(1)
    effect_node.set_property('EffectType', 'EFFECT_ADJUST_UNIT_RESOURCE_DAMAGE')
    qtbot.wait(1)
    cast_test_input('Amount', '6', effect_node)
    qtbot.wait(1)
    cast_test_input('ResourceClassType', 'RESOURCECLASS_EMPIRE', effect_node)
    qtbot.wait(1)

    req_node = window.graph.create_node('db.game_effects.RequirementEffectNode')
    qtbot.wait(1)
    req_node.set_property('RequirementType', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_UNIT_TYPE')
    qtbot.wait(1)
    cast_test_input('Amount', '4', req_node)
    qtbot.wait(1)
    cast_test_input('UnitType', 'UNIT_TEST', req_node)
    qtbot.wait(1)

    req_node.set_property('RequirementType', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_BUILDINGS')
    qtbot.wait(1)
    cast_test_input('BuildingType', 'BUILDING_TEST', req_node)
    qtbot.wait(1)
    return effect_node, req_node


def check_test_against_expected_sql(test_sql_path, generated_sql_path):
    with open(generated_sql_path, 'r') as f:
        generated_sql = f.readlines()

    with open(generated_sql_path, 'r') as f:
        ref_sql = f.read()

    with open(f'test/test_data/{test_sql_path}', 'r') as f:
        expected_sql = f.readlines()

    generated_set = set(generated_sql)
    expected_set = set(expected_sql)
    if generated_set != expected_set:
        missing_sql = expected_set - generated_set
        extra_sql = generated_set - expected_set
        assert len(missing_sql) == 0, f'Missed lines {missing_sql}'
        assert len(extra_sql) == 0, f'extra lines {extra_sql}'
