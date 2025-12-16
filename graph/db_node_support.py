from PyQt5 import QtWidgets, QtCore
from graph.db_spec_singleton import ResourceLoader

db_spec = ResourceLoader()
subsets = {}


# used for searchable node creation
class NodeCreationDialog(QtWidgets.QDialog):
    def __init__(self, subset=None):
        super().__init__()
        if subset is None:
            self.templates = db_spec.node_templates
        else:
            valid_tables = db_spec.node_templates[subset.node.name]['backlink_fk'][subset.name]
            self.templates = {key: val for key, val in db_spec.node_templates.items() if key in valid_tables}

        self.setWindowFlags(QtCore.Qt.Popup)
        self.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.search = QtWidgets.QLineEdit()
        self.list = QtWidgets.QListWidget()

        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)

        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._choose_first)
        self.list.itemDoubleClicked.connect(self.accept)

        self._filter("")

    def _filter(self, text):
        self.list.clear()
        q = text.lower()

        scored = []
        for name in self.templates.keys():
            n = name.lower()
            if q in n:
                idx = n.index(q)
                scored.append((idx, len(n) - len(q), name))

        for _, _, name in sorted(scored):
            self.list.addItem(name)

    def _choose_first(self):
        if self.list.count():
            self.list.setCurrentRow(0)
            self.accept()

    def selected(self):
        item = self.list.currentItem()
        return item.text() if item else None

    def showEvent(self, event):
        super().showEvent(event)
        self.search.setFocus(QtCore.Qt.PopupFocusReason)
        self.search.selectAll()


# used for searchable combo box
class SearchListDialog(QtWidgets.QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup)
        self.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.search = QtWidgets.QLineEdit()
        self.list = QtWidgets.QListWidget()
        self.items = items or []

        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)

        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._choose_first)
        self.list.itemDoubleClicked.connect(self.accept)

        self._filter("")

    def showEvent(self, event):
        super().showEvent(event)
        self.search.setFocus(QtCore.Qt.PopupFocusReason)

    def _filter(self, text):
        self.list.clear()
        q = text.lower()
        for item in self.items:
            if q in item.lower():
                self.list.addItem(item)

    def _choose_first(self):
        if self.list.count():
            self.list.setCurrentRow(0)
            self.accept()

    def selected(self):
        item = self.list.currentItem()
        return item.text() if item else None


# used to resync possible options for node combo boxes when changing age or adding new origin values
# like say a Units entry
def sync_node_options(graph):
    print('syncing nodes...')
    age = graph.property('meta').get('Age')
    if age == 'ALWAYS':
        age_specific_db = db_spec.all_possible_vals
    else:
        age_specific_db = db_spec.possible_vals.get(age, {})

    valid_options_dict = {}             # find all nodes that have an origin PK, and their values
    target_nodes = [n for n in graph.all_nodes() if 'db.table.' in n.type_]
    for node in target_nodes:
        node_table = node.get_property('table_name')
        pk_val = node.get_property(db_spec.node_templates[node_table]['primary_keys'][0])
        if db_spec.node_templates.get(node_table, False):
            if node_table not in valid_options_dict:
                valid_options_dict[node_table] = set([pk_val])
            else:
                valid_options_dict[node_table].add(pk_val)

    # add default values from database
    for tbl_name, new_options_set in valid_options_dict.items():
        valid_options_dict[tbl_name] = sorted(list(valid_options_dict[tbl_name]))
        valid_options_dict[tbl_name].extend(age_specific_db[tbl_name]['_PK_VALS'])

    # get tables that reference new origin tables that arent in db
    fk_ref_tables = {key: val for key, val in age_specific_db.items()
                     if any(key_j != '_PK_VALS' and val_j['ref'] in valid_options_dict for key_j, val_j in val.items())}

    fk_nodes = [n for n in target_nodes if n.get_property('table_name') in fk_ref_tables]       # get nodes from those
    for node in fk_nodes:
        node_info = fk_ref_tables[node.get_property('table_name')]
        combo_boxes_with_fk_ref_to_new_pk = {col: col_info for col, col_info in node_info.items() if col !='_PK_VALS'
                                             and col_info['ref'] in valid_options_dict}
        for ref_name, col_info in combo_boxes_with_fk_ref_to_new_pk.items():
            combo_widget = node.get_widget(ref_name)
            if combo_widget:
                current_val = node.get_property(ref_name)
                sorted_options = valid_options_dict[col_info['ref']]
                combo_widget.clear()
                combo_widget.add_items(sorted_options)              # 2. Add the new list of items
                if current_val in sorted_options:
                    combo_widget.set_value(current_val)


def sync_node_options_all(graph):
    age = graph.property('meta').get('Age')
    if age == 'ALWAYS':
        age_specific_db = db_spec.all_possible_vals
    else:
        age_specific_db = db_spec.possible_vals.get(age, {})

    target_nodes = [n for n in graph.all_nodes() if 'db.table.' in n.type_
                    and age_specific_db.get(n.get_property('table_name'), False)]
    for node in target_nodes:
        combo_box_vals = age_specific_db[node.get_property('table_name')]
        for col_name, new_combo_box_vals in combo_box_vals.items():
            if col_name != '_PK_VALS':
                combo_widget = node.get_widget(col_name)
                if combo_widget:
                    current_val = node.get_property(col_name)
                    sorted_options = new_combo_box_vals['vals']
                    combo_widget.clear()
                    combo_widget.add_items(sorted_options)
                    if current_val in sorted_options:
                        combo_widget.set_value(current_val)
