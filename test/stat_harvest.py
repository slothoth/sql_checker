from sqlalchemy import create_engine, select, Text
import json

from graph.db_spec_singleton import ages
from stats import gather_effects, mine_empty_effects, mine_requirements
from schema_generator import SQLValidator
from graph.node_controller import NodeEditorWindow

# mostly just used to generate and save test data for other tests
def test_effects_harvest():
    mine_empty_effects()
    path = f"resources/gameplay-base"
    for age_type in ages:
        engine = create_engine(f"sqlite:///{path}_{age_type}.sqlite")  # already built
        SQLValidator.engine_dict[age_type] = engine
    gather_effects(SQLValidator.engine_dict)

def test_setup_all_unique_nodes(qtbot):
    window = NodeEditorWindow()
    graph = window.graph

    current = graph.current_session()
    possible_nodes = {k: v[0] for k, v in graph.node_factory.names.items()
                      if k not in ['Backdrop', 'CustomRequirement', 'CustomGameEffect']}
    SQLValidator.state_validation_setup('AGE_ANTIQUITY')
    engine = SQLValidator.engine_dict['AGE_ANTIQUITY']
    example_dicts = {}
    with engine.connect() as conn:
        for name, table in SQLValidator.metadata.tables.items():
            row = conn.execute(select(table).limit(1)).first()
            example_dicts[name] = None if row is None else dict(row._mapping)

    for table_name, node_type in possible_nodes.items():
        node = graph.create_node(node_type)
        if example_dicts.get(table_name, None) is not None:
            node.set_spec(example_dicts[table_name])
    file_path = graph.save_dialog(current)
    if file_path:
        graph.save_session(file_path)

def test_req_harvest():
    with open('resources/manual_assigned/CollectionObjectManualAssignment.json') as f:
        manual_collection_classification = json.load(f)

    with open('resources/manual_assigned/CollectionOwnerMap.json') as f:
        TableOwnerObjectMap = json.load(f)

    with open('resources/manual_assigned/modifier_tables.json') as f:
        mod_tables = json.load(f)
    path = f"resources/gameplay-base"
    for age_type in ages:
        engine = create_engine(f"sqlite:///{path}_{age_type}.sqlite")  # already built
        SQLValidator.engine_dict[age_type] = engine

    mine_requirements(SQLValidator.engine_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap)


def test_possible_vals_harvest():
    path = f"resources/gameplay-base"
    for age_type in ages:
        engine = create_engine(f"sqlite:///{path}_{age_type}.sqlite")  # already built
        SQLValidator.engine_dict[age_type] = engine

