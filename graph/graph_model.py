import sqlite3
from copy import deepcopy
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy import text as SQLA_text
from sqlalchemy.exc import SQLAlchemyError


from model import query_mod_db, organise_entries, load_files, make_hash
from graph.db_spec_singleton import db_spec


# harvests information from a prebuilt database using Civ VII loading.
class BaseDB:
    def __init__(self, full_path):
        self.table_data = {}
        self.tables = []

    def setup_table_infos(self, db_path):
        full_path = f"resources/{db_path}"
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        self.tables = [row[0] for row in cursor.fetchall()]
        table_to_id = {t: i + 1 for i, t in enumerate(self.tables)}
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
            for ref in fk_list:
                ref_table, table_col, og_col = ref[2], ref[3], ref[4]
                if ref_table in self.tables:
                    self.table_data[table]['foreign_keys'][table_col] = ref_table
                    if not self.table_data[ref_table].get('backlink_fk', False):
                        self.table_data[ref_table]['backlink_fk'] = []
                    self.table_data[ref_table]['backlink_fk'].append(table)         # for backlinks

        conn.close()

    def dump_unique_pks(self, db_path_list):
        possible_firaxis_pks, double_keys, possible_vals, all_possible_vals = {}, [], {}, {}
        for db_path, db_name in db_path_list.items():
            possible_vals[db_name] = {}
            possible_vals_age = possible_vals[db_name]
            full_path = f"resources/{db_path}"
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
                foreign_keys = self.table_data[table]['foreign_keys'].copy()
                foreign_keys.update({key: val['ref_table'] for key, val in self.table_data[table].get('extra_fks', {}).items()})
                for fk, table_ref in foreign_keys.items():
                    if table_ref == 'Types':        # SKIP Types reference! Makes huge possible vals
                        continue
                    key_possible_vals = possible_firaxis_pks[table_ref]
                    if table not in possible_vals_age:
                        possible_vals_age[table] = {'_PK_VALS': possible_firaxis_pks.get(table, [])}
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

        for table, cols in all_possible_vals.items():       # setify for uniques
            for col_name, unique_vals in cols.items():
                if isinstance(unique_vals, dict):
                    all_possible_vals[table][col_name]['vals'] = list(set(all_possible_vals[table][col_name]['vals']))
                else:
                    all_possible_vals[table][col_name] = list(set(all_possible_vals[table][col_name]))

        db_spec.update_possible_vals(possible_vals)     #
        db_spec.update_all_vals(all_possible_vals)     #

    def fix_firaxis_missing_fks(self, db_path):
        # find all primary key columns where theres only one PK.
        unique_pks = {}
        for table in self.tables:
            pk_list = self.table_data[table]['primary_keys']
            if len(pk_list) == 1:           # single key
                pk = pk_list[0]
                if pk not in unique_pks:
                    unique_pks[pk] = []
                unique_pks[pk].append(table)

        # get the example database of antiquity
        conn = sqlite3.connect("resources/antiquity-db.sqlite")

        count_potential_fks = 0
        for table in self.tables:
            # get columns that arent foreign keys
            existing_fks = self.table_data[table]['foreign_keys']
            potential_fks = {}
            for col in [i for i in self.table_data[table]['all_cols'] if i not in existing_fks]:
                uniques = count_unique(conn, table, col)
                nulls = count_null(conn, table, col)  # its okay not matching if null
                if nulls > 0:
                    uniques = uniques - 1  # we dont count these
                for pk_col, pk_tables in unique_pks.items():
                    for pk_tbl in pk_tables:
                        if pk_tbl == table:
                            continue
                        if pk_tbl in self.table_data[table].get('backlink_fk', []):
                            continue
                        viol = fk_violations(conn, table, col, pk_tbl, pk_col)
                        matches = fk_matches(conn, table, col, pk_tbl, pk_col)
                        matches_without_nulls = matches - nulls
                        if len(viol) == 0 and matches > 0 and uniques == matches:
                            if col not in potential_fks:
                                potential_fks[col] = []
                            potential_fks[col].append({'table': pk_tbl, 'col': pk_col})
                            count_potential_fks += 1
                            print(f'Table {table} has added foreign key reference on col {col}: referencing table {pk_tbl}.{pk_col}')

            self.table_data[table]['possible_fks'] = potential_fks

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

        for key, val in self.table_data.items():
            if val.get('possible_fks', False):
                new_fk_cols = val['possible_fks']
                for fk_col, fk_info_list in new_fk_cols.items():
                    if len(fk_info_list) == 1:
                        continue
                    # for plural ones check if the ref table has a primary key
                    for fk_info in fk_info_list:
                        if fk_info['table'] == 'Types':     # skip Types table
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
                            if ref_pk not in ref_table_info['foreign_keys'] and not_in_ref:
                                if 'extra_fks' not in self.table_data[key]:
                                    self.table_data[key]['extra_fks'] = {}

                                self.table_data[key]['extra_fks'][fk_col] = {'ref_column': ref_pk, 'ref_table': table}
                                # [fk_col] = {'ref_column': ref_col, 'ref_table': ref_table}


        conn.close()
        # now get extra backlinks
        for original_table, val in self.table_data.items():
            if 'extra_fks' in val:
                for col, ref_info in val['extra_fks'].items():
                    ref_table = ref_info['ref_table']
                    ref_col = ref_info['ref_column']
                    if 'extra_backlinks' not in self.table_data[ref_table]:
                        self.table_data[ref_table]['extra_backlinks'] = {}
                    self.table_data[ref_table]['extra_backlinks'][original_table] = col

        # now we want to work back to get all origin tables, as it helps update things faster in app
        origin_pks = {key: val['primary_keys'][0] for key, val in self.table_data.items()
         if len(val['primary_keys']) == 1 and val['primary_keys'][0] not in val.get('foreign_keys', {}) and
         val['primary_keys'][0] not in val.get('extra_fks', {})}
        for table_name, table_info in self.table_data.items():
            if table_name in origin_pks:
                self.table_data[table_name]['origin_pk'] = True


    def fix_firaxis_missing_bools(self):
        result = {}
        conn = sqlite3.connect("resources/antiquity-db.sqlite")
        for table in self.tables:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            int_cols = [c[1] for c in cols if "INT" in c[2].upper() or "BOOL" in c[2].upper()]

            for col in int_cols:
                vals = {
                    r[0] for r in conn.execute(
                        f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL"
                    )
                }
                if vals and vals.issubset({0, 1}):
                    result.setdefault(table, []).append(col)
        for table_name, bool_col_list in result.items():
            self.table_data[table_name]['mined_bools'] = bool_col_list


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


def fk_matches(conn, from_table, from_col, to_table, to_col):
    cur = conn.execute(
        f"""
            SELECT COUNT(*)
            FROM {from_table}
            WHERE typeof({from_col})='text'
              AND {from_col} IN (
                    SELECT {to_col}
                    FROM {to_table}
                    WHERE typeof({to_col})='text'
              )
            """
    )
    return cur.fetchone()[0]


def count_unique(conn, table, col):
    cur = conn.execute(f"SELECT COUNT(DISTINCT {col}) FROM {table}")
    return cur.fetchone()[0]


def count_null(conn, table, col):
    cur = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
    return cur.fetchone()[0]


def combine_db_df(df_combined, df_to_add):
    if df_combined is None:
        df_combined = df_to_add
    else:
        df_combined = pd.concat([df_combined, df_to_add], ignore_index=True)
    return df_combined

# Builds a database using table CREATE defines, and the prebuilt inserted data not in any values
# this product can then be acted on to build antiquity, exploration or modern databases
# along with mods on top



def make_engine(db_path):
    def no_relationships(base, direction, return_fn, attrname, local_cls, referred_cls, **kw):
        return None

    engine = create_engine(f"sqlite:///{db_path}")
    Base = automap_base()
    Base.prepare(engine, reflect=True, generate_relationship=no_relationships)
    configure_mappers()
