from graph.node_controller import nodeEditorWindow
from PySide6.QtWidgets import QApplication
import sys

from graph.graph_model import BaseDB
from graph.db_spec_singleton import ResourceLoader

db_spec = ResourceLoader()
database_path = 'gameplay-copy-cached-base-content.sqlite'
db = BaseDB(database_path)     # if we need to change database spec in json
db.setup_table_infos(database_path)
db.fix_firaxis_missing_bools()
db.fix_firaxis_missing_fks(database_path)
db_spec.update_node_templates(db.table_data)
db.dump_unique_pks({'antiquity-db.sqlite': 'AGE_ANTIQUITY',
                    'exploration-db.sqlite': 'AGE_EXPLORATION',
                    'modern-db.sqlite': 'AGE_MODERN'})

if __name__ == '__main__':
    app = QApplication(sys.argv)
    graph_editor_window = nodeEditorWindow()
    sys.exit(app.exec())
