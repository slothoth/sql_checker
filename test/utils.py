from graph.node_controller import NodeEditorWindow
from graph.transform_json_to_sql import transform_json
from graph.set_hotkeys import write_sql, save_session
from graph.db_spec_singleton import db_spec

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


def check_test_against_expected_sql(test_sql_path):
    with open('resources/main.sql', 'r') as f:
        test_sql = f.readlines()

    with open('resources/main.sql', 'r') as f:
        ref_sql = f.read()

    with open(f'test/test_data/{test_sql_path}', 'r') as f:
        expected_sql = f.readlines()

    test_set = set(test_sql)
    expected_set = set(expected_sql)
    if test_set != expected_set:
        missing_sql = expected_set - test_set
        extra_sql = test_set - expected_set
        assert len(missing_sql) == 0, f'Missed lines {missing_sql}'
        assert len(extra_sql) == 0, f'extra lines {extra_sql}'
