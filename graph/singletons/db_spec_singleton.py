import json
import sqlite3
from copy import deepcopy
from threading import Lock
import os
from pathlib import Path
import glob
import re
import logging

from graph.singletons.filepaths import LocalFilePaths
from schema_generator import SQLValidator
from stats import gather_effects
from graph.utils import resource_path


log = logging.getLogger(__name__)


class ResourceLoader:
    _instance = None
    _lock = Lock()
    initialized = False
    node_templates = {}
    possible_vals = {}
    all_possible_vals = {}
    collection_effect_map = {}
    mod_type_arg_map = {}
    req_type_arg_map = {}
    civ_config = ''
    workshop = ''
    civ_install = ''
    age = ''
    patch_time = -1
    patch_change = False
    _files = {}
    metadata = {}
    dlc_mod_ids = []
    attach_tables = []

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, patch_occurred, latest=None):
        with self._lock:
            if not self.initialized:
                SQLValidator.initialize()
                self._load_resources(patch_occurred, latest)
                self.initialized = True

    def _load_resources(self, new_patch_occurred, latest=None):
        self._files = {
            'localized_tags': self.full_resource_path('LocalizedTags.json'),
            'all_possible_vals': self.appdata_path('all_possible_vals.json'),
            'collection_effect_map': self.appdata_path('CollectionEffectMap.json'),
            'collections_list': self.appdata_path('CollectionsList.json'),
            'dlc_mod_ids': self.appdata_path('DLCModIds.json'),
            'dynamic_mod_info': self.appdata_path('DynamicModifierMap.json'),
            'metadata': self.appdata_path('metadata.json'),
            'mod_arg_type_list_map': self.appdata_path('ModifierArgumentTypes.json'),
            'mod_arg_database_types': self.appdata_path('ModifierArgumentDatabaseTypes.json'),
            'modifier_argument_info': self.appdata_path('ModArgInfo.json'),
            'node_templates': self.appdata_path("node_templates.json"),
            'possible_vals': self.appdata_path('possible_vals.json'),
            'requirement_argument_info': self.appdata_path('RequirementInfo.json'),
            'req_type_arg_map': self.appdata_path('RequirementArgumentTypes.json'),
            'req_arg_database_types': self.appdata_path('RequirementArgumentDatabaseTypes.json'),
        }

        if new_patch_occurred:
            log.info('new patch! rebuild all files')        # cant toast as dont have application yet
            self.update_database_spec()
            self.modifier_argument_info = self._read_file(self._files['modifier_argument_info'])
            self.requirement_argument_info = self._read_file(self._files['requirement_argument_info'])
            self.metadata['patch_time'] = latest
            self._write_file(self._files['metadata'], self.metadata)
        mod_ids = get_dlc_mod_ids()
        self.update_mod_ids(mod_ids)
        self.node_templates = self._read_file(self._files['node_templates'])
        self.possible_vals = self._read_file(self._files['possible_vals'])
        self.all_possible_vals = self._read_file(self._files['all_possible_vals'])
        self.collection_effect_map = self._read_file(self._files['collection_effect_map'])

        self.modifier_argument_info = self._read_file(self._files['modifier_argument_info'])
        self.requirement_argument_info = self._read_file(self._files['requirement_argument_info'])
        self.dynamic_mod_info = self._read_file(self._files['dynamic_mod_info'])

        self.mod_type_arg_map = self._read_file(self._files['mod_arg_type_list_map'])
        self.mod_arg_database_types = self._read_file(self._files['mod_arg_database_types'])
        self.req_type_arg_map = self._read_file(self._files['req_type_arg_map'])
        self.req_arg_database_types = self._read_file(self._files['req_arg_database_types'])
        self.localized_tags = self._read_file(self._files['localized_tags'])
        self.collections_list = self._read_file(self._files['collections_list'])
        self.modifier_argument_list = set()
        [self.modifier_argument_list.update(list(v.keys())) for k, v in self.mod_type_arg_map.items()]
        self.req_argument_list = set()
        [self.req_argument_list.update(list(v.keys())) for k, v in self.req_type_arg_map.items()]
        self.dlc_mod_ids = self._read_file(self._files['dlc_mod_ids'])

    @staticmethod
    def _read_file(path):
        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def _write_file(path, data):
        with open(path, 'w') as f:
            json.dump(data, f, separators=(',', ':'), sort_keys=True)

    def update_node_templates(self, data):
        self.node_templates = data
        self._write_file(self._files['node_templates'], data)

    def update_possible_vals(self, data):
        self.possible_vals = data
        self._write_file(self._files['possible_vals'], data)

    def update_all_vals(self, data):
        self.all_possible_vals = data
        self._write_file(self._files['all_possible_vals'], data)

    def update_mod_ids(self, data):
        self.dlc_mod_ids = data
        self._write_file(self._files['dlc_mod_ids'], data)

    def update_civ_config(self, new_path):
        LocalFilePaths.civ_config = new_path
        self.metadata['civ_config'] = new_path
        self._write_file(self._files['metadata'],  self.metadata)

    def update_steam_workshop(self, new_path):
        LocalFilePaths.workshop = new_path
        self.metadata['workshop'] = new_path
        self._write_file(self._files['metadata'],  self.metadata)

    def update_civ_install(self, new_path):
        LocalFilePaths.civ_install = new_path
        self.metadata['civ_install'] = new_path
        self._write_file(self._files['metadata'], self.metadata)

    def update_age(self, text):
        self.age = text
        self.metadata['age'] = text
        self._write_file(self._files['metadata'],  self.metadata)

    def check_firaxis_patched(self):
        if not os.path.exists(self.appdata_path('metadata.json')):
            self.age = 'AGE_ANTIQUITY'
            self.metadata = {'civ_config':  LocalFilePaths.civ_config,
                             'workshop': LocalFilePaths.workshop,
                             'civ_install': LocalFilePaths.civ_install,
                             'age': self.age,
                             'patch_time': self.patch_time
                             }
        else:
            self.metadata = self._read_file(self.appdata_path('metadata.json'))
            self.age = self.metadata.get('age', 'AGE_ANTIQUITY')
            self.patch_time = self.metadata.get('patch_time', -1)

        root = Path(LocalFilePaths.civ_install)       # find the most recent changed file and the time it was changed.
        file_changes = [(p, p.stat().st_mtime) for p in root.rglob("*") if p.is_file()
                        and '/.' not in str(p) and '\.' not in str(p)]
        file_changes.sort(key=lambda x: x[1], reverse=True)
        latest = file_changes[0][1]
        current = self.metadata.get('patch_time')
        if current is None or latest > current:
            self.patch_change = True
            self.patch_time = latest
        if not self.patch_change:
            all_mined_files_exist = all(os.path.exists(v) for k, v in self._files.items())
            if not all_mined_files_exist:
                self.patch_change = True
        return self.patch_change, latest

    def update_database_spec(self):
        mod_ids = get_dlc_mod_ids()
        self.update_mod_ids(mod_ids)
        SQLValidator.state_validation_setup('AGE_ANTIQUITY', self, first_run=True)

        database_path = LocalFilePaths.app_data_path_form('gameplay-base_AGE_ANTIQUITY.sqlite')
        db = BaseDB(database_path)
        db.setup_table_infos()
        db.fix_firaxis_missing_bools()
        db.fix_firaxis_missing_fks()                # a concern is these rely on being built by SQLvalidator
        self.update_node_templates(db.table_data)   # which comes later. should be fine if we ship these db tho
        db_paths = {LocalFilePaths.app_data_path_form('gameplay-base_AGE_ANTIQUITY.sqlite'): 'AGE_ANTIQUITY',
                    LocalFilePaths.app_data_path_form('gameplay-base_AGE_EXPLORATION.sqlite'): 'AGE_EXPLORATION',
                    LocalFilePaths.app_data_path_form('gameplay-base_AGE_MODERN.sqlite'): 'AGE_MODERN'}
        possible_vals, all_possible_vals = db.dump_unique_pks(db_paths)
        self.update_possible_vals(possible_vals)
        self.update_all_vals(all_possible_vals)
        gather_effects(SQLValidator.engine_dict, SQLValidator.metadata, self)

    @staticmethod
    def full_resource_path(relative_path):
        rsc_path = resource_path('resources/mined')
        return os.path.join(rsc_path, relative_path)

    @staticmethod
    def appdata_path(relative_path):
        rsc_path = LocalFilePaths.app_data_path_form('db_spec')
        return os.path.join(rsc_path, relative_path)



# harvests information from a prebuilt database using Civ VII loading. Needs to be in here as uses db_spec
class BaseDB:
    all_rows_dict = {}

    def __init__(self, full_path):
        self.table_data = {}
        self.tables = []
        self.db_path = full_path

    def setup_table_infos(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        self.tables = [row[0] for row in cursor.fetchall()]
        for table in self.tables:
            cursor.execute(f"PRAGMA table_info({table})")
            rows = cursor.fetchall()
            columns = [r[1] for r in rows]
            notnulls = [r[3] for r in rows]
            defaults = [r[4] for r in rows]
            primary_texts = [i for idx, i in enumerate(columns) if notnulls[idx] == 1 and defaults[idx] is None]
            secondary_texts = [i for i in columns if i not in primary_texts]
            self.table_data[table] = {}
            self.table_data[table]['primary_keys'] = [i[1] for i in rows if i[5] != 0]
            self.table_data[table]['primary_texts'] = primary_texts
            self.table_data[table]['secondary_texts'] = secondary_texts
            columns.sort(key=lambda x: 0 if x in self.table_data[table]['primary_keys'] else 1)
            self.table_data[table]['all_cols'] = columns
            self.table_data[table]['default_values'] = {i[1]: i[4] for i in rows if i[4] is not None}

        for table in self.tables:
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            self.table_data[table]['foreign_keys'] = {}
            fk_list = cursor.fetchall()
            self.table_data[table]['foreign_key_list'] = [{'foreign_table': ref[2],
                                                           'foreign_key': ref[3],
                                                           'foreign_table_key': ref[4]} for ref in fk_list]
            for ref in fk_list:
                ref_table, table_col, og_col = ref[2], ref[3], ref[4]
                if ref_table in self.tables:
                    self.table_data[table]['foreign_keys'][table_col] = ref_table
                    if not self.table_data[ref_table].get('backlink_fk', False):
                        self.table_data[ref_table]['backlink_fk'] = []
                    self.table_data[ref_table]['backlink_fk'].append(table)  # for backlinks

        conn.close()

    def dump_unique_pks(self, db_path_list):
        possible_firaxis_pks, double_keys, possible_vals, all_possible_vals = {}, [], {}, {}
        for full_path, db_name in db_path_list.items():
            possible_vals[db_name] = {}
            possible_vals_age = possible_vals[db_name]
            conn = sqlite3.connect(full_path)
            cursor = conn.cursor()
            for table in self.tables:
                primary_keys = self.table_data[table]['primary_keys']
                if len(primary_keys) == 1:
                    pk = primary_keys[0]
                    rows = cursor.execute(f"SELECT DISTINCT {pk} FROM {table}").fetchall()
                    possible_firaxis_pks[table] = [r[0] for r in rows]
                else:
                    double_keys.append(table)

            for table in self.tables:
                if table not in possible_vals_age:
                    possible_vals_age[table] = {'_PK_VALS': possible_firaxis_pks.get(table, [])}
                foreign_keys = self.table_data[table]['foreign_keys'].copy()
                foreign_keys.update(
                    {key: val['ref_table'] for key, val in self.table_data[table].get('extra_fks', {}).items()})
                for fk, table_ref in foreign_keys.items():
                    if table_ref == 'Types':  # SKIP Types reference! Makes huge possible vals
                        continue
                    key_possible_vals = possible_firaxis_pks[table_ref]

                    if fk not in possible_vals_age[table]:
                        possible_vals_age[table][fk] = {}
                        possible_vals_age[table][fk]['vals'] = []
                        possible_vals_age[table][fk]['ref'] = table_ref
                    possible_vals_age[table][fk]['vals'].extend(key_possible_vals)

            for tbl, col_poss_dicts in possible_vals_age.items():
                for col in col_poss_dicts:
                    if col != '_PK_VALS':
                        col_poss_dicts[col]['vals'] = sorted(list(set(col_poss_dicts[col]['vals'])))

        for age, poss_vals in possible_vals.items():
            for table, cols in poss_vals.items():
                if table not in all_possible_vals:
                    all_possible_vals[table] = {}
                for col_name, unique_vals in cols.items():
                    if col_name not in all_possible_vals[table]:
                        all_possible_vals[table][col_name] = deepcopy(unique_vals)
                    else:
                        if isinstance(unique_vals, dict):
                            all_possible_vals[table][col_name]['vals'].extend(unique_vals['vals'])
                        else:
                            all_possible_vals[table][col_name].extend(unique_vals)

        for table, cols in all_possible_vals.items():  # setify for uniques
            for col_name, unique_vals in cols.items():
                if isinstance(unique_vals, dict):
                    all_possible_vals[table][col_name]['vals'] = list(set(all_possible_vals[table][col_name]['vals']))
                else:
                    all_possible_vals[table][col_name] = list(set(all_possible_vals[table][col_name]))

        return possible_vals, all_possible_vals

    def fix_firaxis_missing_fks(self):
        # find all primary key columns where theres only one PK.
        # get the example database of antiquity
        conn = sqlite3.connect(LocalFilePaths.app_data_path_form('gameplay-base_AGE_ANTIQUITY.sqlite'))
        unique_pks = {}
        for table in self.tables:
            pk_list = self.table_data[table]['primary_keys']
            if len(pk_list) == 1:  # single key
                pk = pk_list[0]
                if ensure_text_column(conn, table, pk):  # filter unique pks to remove number vals
                    if pk not in unique_pks:
                        unique_pks[pk] = []
                    unique_pks[pk].append(table)

        count_potential_fks = 0
        for table in self.tables:
            # get columns that arent foreign keys
            existing_fks = self.table_data[table]['foreign_keys']
            potential_fks = {}
            for col in [i for i in self.table_data[table]['all_cols'] if i not in existing_fks]:
                uniques = count_unique(conn, table, col)
                for pk_col, pk_tables in unique_pks.items():
                    for pk_tbl in pk_tables:
                        if pk_tbl == table:
                            continue
                        if pk_tbl in self.table_data[table].get('backlink_fk', []):
                            continue
                        viol = fk_violations(conn, table, col, pk_tbl, pk_col)
                        all_fk_present_in_tbl = self.fk_matches(conn, table, col, pk_tbl, pk_col)
                        if len(viol) == 0 and uniques > 0 and all_fk_present_in_tbl:
                            if col not in potential_fks:
                                potential_fks[col] = []
                            potential_fks[col].append({'table': pk_tbl, 'col': pk_col})
                            count_potential_fks += 1
                            log.debug(f'Table {table} has added foreign key reference on col {col}: referencing'
                                      f' table {pk_tbl}.{pk_col}')

            self.table_data[table]['possible_fks'] = potential_fks      # still misses a few, like Ability -> Type

        # THEN we need to recursively work back to deal with "origin" PK that arent actually origin
        # for example Unit_TransitionShadows has Tag as a Primary Key. and no foreign key.
        # Our analysis shows table Unit_ShadowReplacements which has a column Tag, and so it claims
        # it has a foreign key in Unit_TransitionShadows.Tag. And our Unit_TransitionShadows has a foreign key
        # in table Tags.Tag. In reality both have that Tag as FK. Also need to deal with plurality.

        # find fks where theres only one source.
        for key, val in self.table_data.items():
            if val.get('possible_fks', False):
                new_fk_cols = val['possible_fks']
                for fk_col, fk_info_list in new_fk_cols.items():
                    if len(fk_info_list) == 1:
                        ref_col = fk_info_list[0]['col']
                        ref_table = fk_info_list[0]['table']
                        if 'extra_fks' not in self.table_data[key]:
                            self.table_data[key]['extra_fks'] = {}
                        self.table_data[key]['extra_fks'][fk_col] = {'ref_column': ref_col, 'ref_table': ref_table}

        for key, val in self.table_data.items():  # now deal with plural sources
            if val.get('possible_fks', False):
                new_fk_cols = val['possible_fks']
                for fk_col, fk_info_list in new_fk_cols.items():
                    if len(fk_info_list) == 1:
                        continue

                    for fk_info in fk_info_list:  # for plural ones check if the ref table has a primary key
                        if fk_info['table'] == 'Types':  # skip Types table
                            continue
                        col = fk_info['col']
                        table = fk_info['table']
                        ref_table_info = self.table_data[table]
                        # if ref table primary key is not a foreign key, this is the end point
                        # and we can use it

                        if len(ref_table_info['primary_keys']) == 1:
                            ref_pk = ref_table_info['primary_keys'][0]
                            not_in_ref = ref_pk not in [v.get("ref_column")
                                                        for v in ref_table_info.get("extra_fks", [])
                                                        if "ref_column" in v]
                            non_types_fks = {k: v for k, v in ref_table_info['foreign_keys'].items() if v != 'Types'}
                            if ref_pk not in non_types_fks and not_in_ref:
                                if 'extra_fks' not in self.table_data[key]:
                                    self.table_data[key]['extra_fks'] = {}

                                self.table_data[key]['extra_fks'][fk_col] = {'ref_column': ref_pk, 'ref_table': table}

        conn.close()

        for original_table, val in self.table_data.items():  # now get extra backlinks
            if 'extra_fks' in val:
                for col, ref_info in val['extra_fks'].items():
                    ref_table = ref_info['ref_table']
                    if 'extra_backlinks' not in self.table_data[ref_table]:
                        self.table_data[ref_table]['extra_backlinks'] = {}
                    self.table_data[ref_table]['extra_backlinks'][original_table] = col

        # now we want to work back to get all origin tables, as it helps update things faster in app
        def resolve_origin(table_data, table, col, stop_tables):
            seen = set()
            t, c = table, col

            while True:
                k = (t, c)
                if k in seen:
                    return t, c
                seen.add(k)

                fk_map = table_data.get(t, {}).get("foreign_keys", {})
                ref_t = fk_map.get(c)

                if not ref_t or ref_t in stop_tables:
                    return t, c

                ref_pks = table_data.get(ref_t, {}).get("primary_keys", [])
                if len(ref_pks) != 1:
                    return ref_t, None

                t, c = ref_t, ref_pks[0]

        stop_tables = {"Types"}

        origins = {}
        for table, val in self.table_data.items():
            pks = val.get("primary_keys", [])
            if len(pks) != 1:
                continue
            pk = pks[0]
            origins[(table, pk)] = resolve_origin(self.table_data, table, pk, stop_tables)

        origins_ = [k[0] for k, v in origins.items() if k[0] == v[0]]
        for k, v in self.table_data.items():
            if 'origin_pk' in v:
                self.table_data[k]['origin_pk'] = False
            if k in origins_:
                self.table_data[k]['origin_pk'] = True

    def fix_firaxis_missing_bools(self):
        result = {}
        conn = sqlite3.connect(LocalFilePaths.app_data_path_form('gameplay-base_AGE_ANTIQUITY.sqlite'))
        for table in self.tables:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            int_cols = [c[1] for c in cols if "INT" in c[2].upper() or "BOOL" in c[2].upper()]
            for col in int_cols:
                vals = {
                    r[0] for r in conn.execute(
                        f"SELECT {col} FROM {table}"
                    )
                }
                if vals and vals.issubset({0, 1}) and None not in vals:
                    result.setdefault(table, []).append(col)
        for table_name, bool_col_list in result.items():
            self.table_data[table_name]['mined_bools'] = bool_col_list

    def fk_matches(self, conn, from_table, from_col, to_table, to_col):
        cur_2 = conn.execute(
            f"""
                    SELECT *
                    FROM {from_table}
                    WHERE typeof({from_col})='text'
                      AND {from_col} IN (
                            SELECT {to_col}
                            FROM {to_table}
                            WHERE typeof({to_col})='text'
                      )
                    """
        )
        all_matches = cur_2.fetchall()
        if from_table not in self.all_rows_dict:
            cur_3 = conn.execute(
                f"""SELECT * FROM {from_table}"""
            )
            all_rows = cur_3.fetchall()
            self.all_rows_dict[from_table] = all_rows
        else:
            all_rows = self.all_rows_dict[from_table]

        return len(all_rows) == len(all_matches)


def fk_violations(conn, from_table, from_col, to_table, to_col):
    cur = conn.execute(
        f"""
        SELECT {from_col}
        FROM {from_table}
        EXCEPT
        SELECT {to_col}
        FROM {to_table}
        """
    )
    return [r[0] for r in cur.fetchall()]


def count_unique(conn, table, col):
    cur = conn.execute(f"SELECT COUNT(DISTINCT {col}) FROM {table}")
    return cur.fetchone()[0]


def ensure_text_column(conn, table, col):
    cur = conn.execute(f"SELECT {col} FROM {table}")
    vals = cur.fetchall()
    all_string = all(isinstance(i[0], str) for i in vals)
    return all_string


def get_dlc_mod_ids():
    dlc_modinfo_fp_list = [f for f in glob.glob(f"{LocalFilePaths.civ_install}/**/*.modinfo*", recursive=True)]
    dlc_mod_ids = []
    for filepath in dlc_modinfo_fp_list:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        match = re.search(r'<Mod id="([^"]+)"', text)
        if match:
            uuid = match.group(1)
            dlc_mod_ids.append(uuid)
    return dlc_mod_ids


db_spec = ResourceLoader()
