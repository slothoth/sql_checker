import pytest
from collections import defaultdict


from graph.node_controller import NodeEditorWindow
from graph.transform_json_to_sql import transform_json
from graph.set_hotkeys import write_sql, write_loc_sql

from utils import check_test_against_expected_sql

def test_all_table_nodes(qtbot):
    window = NodeEditorWindow()  # this version has a reqset as connected
    qtbot.addWidget(window)
    sql_commands, loc_lines = transform_json('test/test_data/perf_test_fin.json')
    write_sql(sql_commands)
    write_loc_sql(loc_lines)
    check_test_against_expected_sql('all_table_nodes.sql')


def test_correct_ports(qtbot):          # extremely slow test, move to perf and probably split up
    return
    from schema_generator import SQLValidator
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    existing_nodes, expected_connections = {}, defaultdict(dict)
    print('starting')
    for tbl, class_name in SQLValidator.table_name_class_map.items():
        print(f'table {tbl}')
        if class_name not in existing_nodes:
            node = window.graph.create_node(class_name)
            existing_nodes[class_name] = node
        else:
            node = existing_nodes[class_name]
        pk = SQLValidator.pk_map[tbl][0]
        output_port = node.outputs().get(pk)
        for input_info in node.output_port_tables:      # we changed from list of dicts to dict of key:val, this borked
            input_class_node_name = input_info['class']
            input_port_name = input_info['foreign_port']
            accepting_node = existing_nodes.get(input_class_node_name)
            if accepting_node is None:
                accepting_node = window.graph.create_node(input_class_node_name)
                existing_nodes[input_class_node_name] = accepting_node
            input_port = accepting_node.inputs()[input_port_name]
            if input_class_node_name not in expected_connections.get(class_name, {}):
                expected_connections[class_name][input_class_node_name] = []
            output_port.connect_to(input_port)
            expected_connections[class_name][input_class_node_name].append(input_port_name)
            print(f'connected {tbl} to {input_class_node_name} on {input_port_name}')
        print('-----------------------------------------')
        print(f'finished adding connections for {tbl}')
        print('-----------------------------------------')

    # test connections exist
    bad_connections = {}
    for class_name, outputs in expected_connections.items():
        output_node = existing_nodes[class_name]
        output_port = list(output_node.outputs().values())[0]
        connections = output_port.connected_ports()
        actual_outputs = defaultdict(list)
        for k in connections:
            actual_outputs[k.model.node.type_].append(k.name())
        actual_outputs = dict(actual_outputs)
        actual_tuple_outputs = [(k, tuple(v)) for k, v in actual_outputs.items()]
        actual_set = set(actual_tuple_outputs)
        tuple_outputs = [(k, tuple(v)) for k, v in outputs.items()]
        expected_set = set(tuple_outputs)
        missing = expected_set - actual_set
        extra = actual_set - expected_set
        if len(missing) > 0 or len(extra) > 0:
            for input_table_class, input_list in outputs.items():
                actual_connection = actual_outputs.get(input_table_class)
                if actual_connection is None:
                    print(f'missed connection {input_table_class}')
                else:
                    if not actual_connection == input_list:
                        print('expected')

        if actual_outputs != outputs:
            bad_connections[class_name] = {'missing': missing, 'extra': extra}

    assert len(bad_connections) == 0
