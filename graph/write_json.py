from graph.graph_model import BaseDB
from graph.db_spec_singleton import db_spec

database_path = 'gameplay-copy-cached-base-content.sqlite'
db = BaseDB(database_path)     # if we need to change database spec in json
db.setup_table_infos(database_path)
db.fix_firaxis_missing_bools()
db.fix_firaxis_missing_fks(database_path)
db_spec.update_node_templates(db.table_data)
db.dump_unique_pks({'gameplay-base_AGE_ANTIQUITY.sqlite': 'AGE_ANTIQUITY',
                    'gameplay-base_AGE_EXPLORATION.sqlite': 'AGE_EXPLORATION',
                    'gameplay-base_AGE_MODERN.sqlite': 'AGE_MODERN'})
