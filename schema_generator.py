
import os
import sqlite3
from collections import defaultdict
import json
import colorsys
import logging

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import EXCLUDE
from marshmallow import pre_load
from sqlalchemy import create_engine, insert, Integer, Boolean, inspect, text, event, Table, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy.sql.elements import TextClause, ClauseElement
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import sqlite

import sqlglot

from model import query_mod_db, organise_entries, load_files, make_hash
from graph.db_spec_singleton import db_spec, ages
from stats import gather_effects

log = logging.getLogger(__name__)

with open('resources/mined/PreBuiltData.json', 'r') as f:
    prebuilt = json.load(f)


@event.listens_for(Table, "column_reflect")
def force_sqlite_autoincrement(inspector, table, column_info):
    if isinstance(column_info.get('type'), Integer) and column_info.get('primary_key', 0) == 1:
        column_info['autoincrement'] = True


class BaseSchema(SQLAlchemyAutoSchema):
    """Base schema with common configuration."""

    class Meta:
        unknown = EXCLUDE
        load_instance = True


# Cache for schemas to avoid regenerating
_schema_cache = {}


class SchemaInspector:
    """ Class to handle inspect columns and data types """
    Base = None
    session = None
    pk_map = {}
    fk_to_tbl_map = {}
    fk_to_pk_map = {}
    foreign_pk_to_local_fk_map = {}
    pk_ref_map = {}
    type_map = {}
    nullable_map = {}
    default_map = {}
    odd_constraint_map = {}
    required_map = {}
    less_important_map = {}
    port_color_map = {}
    engine_dict = {}
    mod_setup = {}
    include_mods = False

    def __init__(self):
        # setup simple entry validation
        self.Base, self.session, self.empty_engine = self.engine_instantiation('resources/created-db.sqlite')

        tables = self.Base.metadata.tables
        self.metadata = self.Base.metadata

        self.pk_map = {name: [c.name for c in table.primary_key.columns] for name, table in tables.items()}

        self.fk_to_tbl_map = {name: {c.name: list(c.foreign_keys)[0].column.table.name
                                       for c in table.columns if c.foreign_keys}
            for name, table in tables.items()
        }
        extra_fks = {key: {k: v['ref_table'] for k, v in val['extra_fks'].items()} for key, val in
                        db_spec.node_templates.items() if val.get('extra_fks') is not None}
        [self.fk_to_tbl_map[k].update(v) for k, v in extra_fks.items() if k in self.fk_to_tbl_map]
        # for each table, make a dict of all cols with foreign keys, and for val, the name of the foreign
        # key reference table column
        # we also added in the extra fks stuff

        self.fk_to_pk_map = {name: {c.name: list(c.foreign_keys)[0].column.name
                                    for c in table.columns if c.foreign_keys}
            for name, table in tables.items()
        }
        extra_fks = {key: {k: v['ref_column'] for k, v in val['extra_fks'].items()} for key, val in
                        db_spec.node_templates.items() if val.get('extra_fks') is not None}
        [self.fk_to_pk_map[k].update(v) for k, v in extra_fks.items() if k in self.fk_to_pk_map]

        self.foreign_pk_to_local_fk_map = {k: {val: key for key, val in v.items()} for k, v in self.fk_to_pk_map.items()}
        internal_fk_map = {
            name: {
                c.name: {
                    fk.column.table.name: fk.column.name
                    for fk in c.foreign_keys
                }
                for c in table.columns if c.foreign_keys
            }
            for name, table in tables.items()
        }

        self.pk_ref_map = {}            # table first is better as lets you get the pk col in the foreign table
        for model_name, model in tables.items():            # but col first is more handy for fast retrieval and lists
            for ref_tbl, fk_refs in internal_fk_map.items():
                for fk_col, pk_info in fk_refs.items():
                    if len(pk_info) > 1:
                        log.warning('plural pk info?')
                    pk_tbl = list(pk_info.keys())[0]
                    pk_col = pk_info[pk_tbl]
                    if pk_tbl == model_name:
                        if model_name not in self.pk_ref_map:
                            self.pk_ref_map[model_name] = {'table_first': {}, 'col_first': {}}
                        self.pk_ref_map[model_name]['table_first'][ref_tbl] = pk_col

                        if fk_col not in self.pk_ref_map[model_name]['col_first']:
                            self.pk_ref_map[model_name]['col_first'][fk_col] = [ref_tbl]
                        else:
                            self.pk_ref_map[model_name]['col_first'][fk_col].append(ref_tbl)

        extra_backlinks = {key: {k: v for k, v in val['extra_backlinks'].items()} for key, val in
                           db_spec.node_templates.items() if val.get('extra_backlinks') is not None}
        [self.pk_ref_map[k]['table_first'].update(v) for k, v in extra_backlinks.items() if k in self.pk_ref_map]
        for k, v in extra_backlinks.items():
            if k not in self.pk_ref_map:
                self.pk_ref_map[k] = {'col_first': {}, 'table_first': {}}
            for tbl, col in v.items():
                if col not in self.pk_ref_map[k]['col_first']:
                    self.pk_ref_map[k]['col_first'][col] = [tbl]
                else:
                    self.pk_ref_map[k]['col_first'][col].append(tbl)

        self.port_coloring()
        insp = inspect(self.empty_engine)
        basic_defaults = {tbl: {info['name']: info['default'] for info in insp.get_columns(tbl)} for tbl, val in
                                 tables.items()}
        self.type_map = {model_name:  {col.name: col.type.python_type() for col in model.columns}
                         for model_name, model in tables.items()}
        self.nullable_map = {model_name:  {col.name: col.nullable for col in model.columns}
                             for model_name, model in tables.items()}
        self.default_map = {tbl: {col.name: extract_server_default(col, basic_defaults[tbl][col.name]) for col in model.columns if
                                         col.server_default is not None} for tbl, model in tables.items()}
        self.odd_constraint_map = {model_name:  [[c.name for c in constraint.columns]
                             for constraint in model.constraints if isinstance(constraint, UniqueConstraint)]
               for model_name, model in tables.items()}

        self.required_map = {tbl: {col.name: True for col in model.columns if
                                         col.server_default is None and not col.nullable and basic_defaults[tbl][col.name] is None}
                             for tbl, model in tables.items()}
        self.less_important_map = {tbl: [col.name for col in model.columns
                           if col.name not in self.required_map[tbl] and col.name not in self.pk_map[tbl]]
                     for tbl, model in tables.items()}
        self.table_name_class_map = {table_name: f"db.table.{table_name.lower()}.{table_name.title().replace('_', '')}Node"
                                for table_name in self.Base.metadata.tables}

        self.table_name_class_map.update({'GameEffectCustom': 'db.game_effects.GameEffectNode',
                                          'ReqEffectCustom': 'db.game_effects.RequirementEffectNode'})

        self.incremental_pk = {k: v.primary_key.columns[0].autoincrement for k, v in self.Base.metadata.tables.items()
                               if hasattr(v, 'primary_key')
                               and len(v.primary_key.columns) == 1 and v.primary_key.columns[0].autoincrement != 'auto'}

        self.class_table_name_map = {v: k for k, v in self.table_name_class_map.items()}

        self.canonicalise_tables = {name.lower(): name for name in tables}

        self.canonicalise_columns = {name: {col.name.lower(): col.name for col in table.columns}
                                     for name, table in tables.items()}

    def engine_instantiation(self, db_path):
        empty_engine = self.make_base_db(db_path)
        Base = automap_base()

        def no_relationships(*args, **kwargs):
            return None

        Base.prepare(
            autoload_with=empty_engine,
            generate_relationship=no_relationships,
        )
        Session = sessionmaker(bind=empty_engine)
        return Base, Session(), empty_engine

    def validate_field(self, table_name, field_name, field_value, all_data=None):
        """
        Validate a single field value.

        Args:
            table_name: Name of the database table
            field_name: Name of the field to validate
            field_value: Value to validate
            all_data: Optional dictionary of all field values (for context-dependent validation)

        Returns:
            tuple: (is_valid: bool, error_message: str or None)     TODO currently returning error if any val in insert fails
        """  # not just itself
        if all_data is None:
            all_data = {}

        if field_value == '':  # Convert empty strings to None for validation
            field_value = None

        data = {field_name: field_value}
        data.update(all_data)  # Merge with all_data for context
        data[field_name] = field_value  # Ensure our field value takes precedence

        # Remove empty string values from all_data for cleaner validation  # TODO remove the '' as sometimes valid, but need better solution
        cleaned_data = {k: (None if v == '' else v) for k, v in data.items()
                        if k==field_name or v is not None or v == ''}
        # deal with checkbox bools
        cleaned_data = {k: int(v) if isinstance(v, bool) else v for k, v in cleaned_data.items()}
        try:
            is_valid, errors = self.validate_table_data(table_name, cleaned_data, partial=True)

            if not is_valid:
                field_errors = errors.get(field_name, [])
                if field_errors:
                    return False, '; '.join(field_errors) if isinstance(field_errors, list) else str(field_errors)
                return True, 'Validation failed for other columns'

            return True, None
        except Exception as e:
            return True, None  # If schema generation fails, don't block the user to avoid breaking UI

    def validate_table_data(self, table_name, data, partial):
        try:
            schema = self.get_schema_for_table(table_name)
            schema_instance = schema(partial=partial)

            errors = schema_instance.validate(data)

            if errors:
                return False, errors
            return True, {}
        except Exception as e:
            return False, {'_schema': [str(e)]}

    def get_schema_for_table(self, table_name):
        """
        Get or create a Marshmallow schema for a given table name.

        Args:
            table_name: Name of the database table

        Returns:
            A Marshmallow schema class for the table
        """
        if table_name in _schema_cache:
            return _schema_cache[table_name]

        model_class = self.Base.classes[table_name]

        class TableSchema(BaseSchema):
            class Meta:
                model = model_class
                unknown = EXCLUDE
                load_instance = True
                sqla_session = self.session

            @pre_load
            def normalize_empty_strings(self, data, **kwargs):
                table = model_class.__table__

                for name, value in list(data.items()):
                    if value != "":
                        continue

                    col = table.columns.get(name)
                    if col is None:
                        continue

                    if isinstance(col.type, Integer):
                        data[name] = None

                    elif isinstance(col.type, Boolean):
                        data[name] = False

                    else:
                        data[name] = None

                return data

        _schema_cache[table_name] = TableSchema
        return TableSchema

    def state_validation_setup(self, age):
        if age in self.engine_dict:     # setup db state validation
            return False
        else:
            path = f"resources/gameplay-base"
            if db_spec.patch_change:
                # we do all 3 ages
                for age_type in ages:
                    engine = self.make_base_db(f"{path}_{age_type}.sqlite")
                    database_entries = query_mod_db(age=age_type)
                    modded_short, modded, dlc, dlc_files = organise_entries(database_entries)
                    sql_statements_dlc, missed_dlc = load_files(dlc_files, 'DLC')
                    dlc_status_info = lint_database(engine, sql_statements_dlc, keep_changes=True)
                    if self.include_mods:
                        sql_statements_mods, missed_mods = load_files(modded, 'Mod')
                        mod_status_info = lint_database(engine, sql_statements_mods, keep_changes=True)
                    self.engine_dict[age_type] = engine
                gather_effects(self.engine_dict)
                # also do the stats checks
            else:
                engine = create_engine(f"sqlite:///{path}_{age}.sqlite")     # already built
                self.engine_dict[age] = engine

    def state_validation_mod_setup(self, age):               # same but for mods
        database_entries = query_mod_db(age=age)
        modded_short, modded_files, dlc, dlc_files = organise_entries(database_entries)
        # if mod setup is different, so should we we need to reset db
        database_entries = query_mod_db(age=age)
        modded_short, modded, dlc, dlc_files = organise_entries(database_entries)
        engine = self.engine_dict[age]
        sql_statements_mods, missed_mods = load_files(modded, 'Mod')
        mod_status_info = lint_database(engine, sql_statements_mods, keep_changes=True)

    def filter_columns(self, table_name, data, skip_defaults=False):
        cols = {c.key: c for c in self.metadata.tables[table_name].columns}
        non_default_entries = {}
        for k, v in data.items():
            if k not in cols:
                continue

            if skip_defaults:
                col = cols[k]
                default = None
                if col.default is not None and col.default.is_scalar:
                    default = col.default.arg
                elif col.server_default is not None:
                    expr = col.server_default.arg
                    if isinstance(expr, TextClause):
                        default = expr.text.strip('"')
                        if col.type.python_type is bool:
                            if default in ['0', '1']:
                                default = bool(int(default))
                        if col.type.python_type is int:
                            default = int(default)
                    else:
                        raise NotImplementedError('Other type of default ahhh! not handled')
                if v == default:
                    continue
                if col.type.python_type is str and v == '':          # unsure if this is the best case
                    continue

            non_default_entries[k] = v
        return non_default_entries

    def convert_ui_dict_to_text_sql(self, ui_dict, table_name):
        filtered = self.filter_columns(table_name, ui_dict, skip_defaults=True)
        table = self.Base.metadata.tables[table_name]
        bad = self.find_literal_mismatches(table, filtered, sqlite.dialect())

        if len(bad) > 0:
            log.error(f'fails for {table_name} when converting from dict to sql: {ui_dict}')
        for name, coltype, value, err in bad:
            log.error(name, coltype, repr(value))

        if not filtered:
            return 'CUSTOM_ERROR_CODE', filtered

        # TODO now check that not nullables + no default present (we have map) and that primary key is present

        stmt = insert(self.Base.metadata.tables[table_name]).values(**filtered)
        sql = stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
        return str(sql), filtered

    def normalize_node_bools(self, entry, table_name):
        table = self.metadata.tables.get(table_name)
        if table is None:
            return entry

        for name, value in entry.items():
            if not isinstance(value, str):
                continue

            col = table.c.get(name)
            if col is None or not isinstance(col.type, Boolean):
                continue

            v = value.strip().lower()
            if v in ("true", "1", "yes", "on"):
                entry[name] = True
            elif v in ("false", "0", "no", "off", ""):
                entry[name] = False

        return entry

    @staticmethod
    def find_literal_mismatches(table, values, dialect):
        mismatches = []

        for name, value in values.items():
            col = table.c.get(name)
            if col is None:
                continue

            if value is None:
                continue

            try:
                col.type.literal_processor(dialect)(value)
            except Exception as e:
                mismatches.append((name, col.type, value, e))

        return mismatches

    def port_coloring(self):
        port_constraints = sorted([{'key': k, 'item_len': len(v['table_first']), 'items': v['table_first']}
                                   for k, v in self.pk_ref_map.items()],key=lambda x: x['item_len'], reverse=True)
        counts = {}
        for i in port_constraints:
            amount = i['item_len']
            if amount not in counts:
                counts[amount] = 1
            else:
                counts[amount] += 1
        total_constraints = sum([i for k, i in counts.items() if int(k) > 3])
        if total_constraints > 50:
            total_constraints = sum([i for k, i in counts.items() if int(k) > 4])
        self.port_color_map['input'], self.port_color_map['output'] = defaultdict(dict), defaultdict(dict)
        for colour_count, i in enumerate(port_constraints):
            port_inputs = i['items']
            color = constraint_color(colour_count, total_constraints)
            for tbl, col in port_inputs.items():
                self.port_color_map['input'][tbl][col] = color
            origin_table = i['key']
            pks = self.pk_map[origin_table]
            port_output = pks[0]
            self.port_color_map['output'][origin_table][port_output] = color


    @staticmethod
    def make_base_db(db_path):
        if os.path.exists(db_path):
            os.remove(db_path)
        conn = sqlite3.connect(db_path)
        with open(f"{db_spec.civ_install}/Base/Assets/schema/gameplay/01_GameplaySchema.sql", 'r') as f:
            query_tables = f.read()
        cur = conn.cursor()
        conn.create_function("Make_Hash", 1, make_hash)  # setup hash
        cur.executescript(query_tables)
        table_name = 'UnitAbilityModifiers'
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        rows = cur.fetchall()
        # setup prebuilt entries
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.begin() as conn_engine:
            conn_engine.connection.create_function("Make_Hash", 1, make_hash)  # setup hash
            for table_name, table_entries in prebuilt.items():
                # I WISH i could use mallow-alchemy for this, but for some reason it clears entries
                # due to a mismatch where the Type column isnt included in schema because its reserved?
                # anyways causes problems with GameEffects table since its PK is Type
                columns = ", ".join(table_entries[0].keys())
                params = ", ".join(f":{k}" for k in table_entries[0].keys())
                sql = text(f"""
                INSERT INTO {table_name}
                ({columns})
                VALUES
                ({params})
                """)
                conn_engine.execute(sql, table_entries)

        conn.close()
        return engine


def extract_server_default(col, engine_default):
    if engine_default is not None:
        return engine_default
    sd = col.server_default
    if sd is None:
        return None

    arg = sd.arg

    if isinstance(arg, TextClause):
        text = arg.text.strip()
        if (
            (text.startswith("'") and text.endswith("'")) or
            (text.startswith('"') and text.endswith('"'))
        ):
            return text[1:-1]
        return text

    if isinstance(arg, ClauseElement):
        return str(arg)
    return arg


def lint_database(engine, sql_command_dict, keep_changes=False, dict_form_list=None):
    Session = sessionmaker(bind=engine)

    with engine.connect() as conn:
        conn.connection.create_function("Make_Hash", 1, make_hash)
        trans = conn.begin()
        session = Session(bind=conn)
        try:
            results = defaultdict(list)
            for file_name, sql_dict_list in sql_command_dict.items():
                for sql_info in sql_dict_list:
                    try:
                        result_info = sql_info.copy()
                        result_info['passed'] = True
                        session.execute(text(sql_info['sql']))
                        results[file_name].append(result_info)
                    except SQLAlchemyError as e:
                        result_info['passed'] = False
                        result_info['error'] = str(e)
                        result_info['error_type'] = e
                        results[file_name].append(result_info)

            session.execute(text("PRAGMA foreign_keys = ON"))
            fk_errors = session.execute(text("PRAGMA foreign_key_check")).all()
            integrity = session.execute(text("PRAGMA integrity_check")).scalar()

            lint_info = {"results": results, "foreign_key_errors": fk_errors, "integrity": integrity}
            return lint_info

        finally:
            session.close()
            bad_inserts = {k: {idx: i for idx, i in enumerate(v) if not i['passed']} for k, v in results.items()}
            insert_errors = defaultdict(dict)
            if any(len(i) > 0 for i in bad_inserts.values()):
                mark_errors = []
                for file_name, errors in bad_inserts.items():
                    for idx, error_info in errors.items():
                        mark_errors.append(error_info['node_source'])
                        if dict_form_list is not None:
                            dict_info = dict_form_list[idx]['sql']
                            table_name = dict_info['table_name']
                            primary_key_cols = db_spec.node_templates[table_name].get("primary_keys")
                            pk_dict = {k: v for k, v in dict_info['columns'].items() if k in primary_key_cols}
                            pk_string = ", ".join([f'{k}: {v}' for k, v in pk_dict.items()])
                            pk_tuple = tuple([v for k, v in pk_dict.items()])
                        else:       # planned last resort sqlglot
                            log.error('insert error, but we havent handled parsing yet, skipping error')
                            continue
                        error_string = f'Entry {table_name} with primary key: {pk_string}'
                        if isinstance(error_info['error_type'].orig, sqlite3.IntegrityError):
                            simple_error = str(error_info['error_type'].orig)
                            if 'UNIQUE constraint failed' in simple_error:
                                error_string += (f' could not be inserted as that primary key {pk_string} was already'
                                                 f' present.')
                            elif 'NOT NULL constraint failed' in simple_error:
                                col = simple_error.replace('NOT NULL constraint failed: ', '')
                                col = col.replace(f'{table_name}.', '')
                                error_string += f' could not be inserted as {col} was not specified.'
                            elif 'CHECK constraint' in simple_error:
                                uh = 'd'
                                error_string += f' could not be inserted as column {uh}: {uh} is outside constraints.'
                            else:
                                error_string += 'weird error not covered.'
                        else:
                            error_string += f'Some cursed error that is likely not your fault: {str(error_info["error_type"].orig)}'
                            log.error(f"non-user error on running sql statement: {error_info['sql']}\n"
                                      f"{str(error_info['error_type'].orig)}")

                        insert_errors[table_name][pk_tuple] = error_string

                lint_info['insert_error_explanations'] = dict(insert_errors)
                lint_info['marked_nodes'] = mark_errors

            if len(lint_info['foreign_key_errors']) > 0 or lint_info['integrity'] != 'ok':
                explained_error_dict = explain_errors(lint_info, session)
                lint_info['fk_error_explanations'] = {'title_errors': explained_error_dict}

            if keep_changes:
                trans.commit()
            else:
                trans.rollback()


def explain_errors(lint_info, session):
    error_info_list = lint_info['foreign_key_errors']
    error_table_indices = defaultdict(list)
    for i in error_info_list:
        info_list = list(i)
        insertion_table, insertion_index = info_list[0], info_list[1]
        primary_key_table = info_list[2]
        fk_column_index = info_list[3]
        fk_col = db_spec.node_templates[insertion_table]['foreign_key_list'][fk_column_index]['foreign_key']
        error_table_indices[(insertion_table, primary_key_table, fk_col)].append(insertion_index)

    explained_error_dict = {}
    for error_tuple, indices_list in error_table_indices.items():
        insertion_table, primary_key_table, fk_col = error_tuple
        primary_keys = db_spec.node_templates[insertion_table].get("primary_keys")
        foreign_table_pk_list = db_spec.node_templates[primary_key_table]['primary_keys']
        foreign_table_pk = foreign_table_pk_list[0]
        indices_string = ", ".join([str(i) for i in indices_list])
        rows = session.execute(text(f"SELECT * FROM {insertion_table} WHERE rowid IN ({indices_string});")).mappings().fetchall()
        if len(rows) > 1:
            log.warning(f"Multiple rows obtained from explaining foreign key error. Shouldnt be possible."
                        f"Rows:\n {rows}")
        row = dict(rows[0])

        pk_entry = {k: v for k, v in row.items() if k in primary_keys}
        formatted_entry = "".join([f'{k}: {v}\n' for k, v in pk_entry.items()])
        if primary_key_table in lint_info.get('insert_error_explanations', {}):
            pk_tuple = tuple([row[fk_col]])
            insertion_fail = lint_info['insert_error_explanations'][primary_key_table].get(pk_tuple)
            if insertion_fail is not None:
                fk_error_title = '\nAlso causes FOREIGN KEY errors on entries:'
                if fk_error_title not in insertion_fail:
                    lint_info['insert_error_explanations'][primary_key_table][pk_tuple] += fk_error_title
                fk_addition = f'\nINSERT into {insertion_table}: {formatted_entry}'
                lint_info['insert_error_explanations'][primary_key_table][pk_tuple] += fk_addition
            continue

        explained_error_dict[error_tuple] = (f"FOREIGN KEY missing:\nINSERT into {insertion_table}:\n{formatted_entry}"
                                             f"\nThere wasn't a reference entry in {primary_key_table} that had"
                                             f" {foreign_table_pk} = {row[fk_col]}.")
    return explained_error_dict


def constraint_color(index, total,                  # living here as used for init setup so ports dont
                     sat_min=0.55, sat_max=0.85,    # recalculate it
                     val_min=0.65, val_max=0.9):
    """
    index: unique constraint index [0..total-1]
    total: number of distinct constraints
    returns (r, g, b) in 0–255
    """

    hue = (index / total) % 1.0

    # As total grows, compress saturation slightly
    sat = sat_max - (sat_max - sat_min) * (total / 80.0)
    sat = max(sat_min, min(sat, sat_max))

    # Alternate value subtly to improve separation
    val = val_max if index % 2 == 0 else val_min

    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return int(r * 255), int(g * 255), int(b * 255)


def check_valid_sql_against_db(age, sql_dict_list, dict_form_list=None):
    SQLValidator.state_validation_setup(age)
    result_info = lint_database(SQLValidator.engine_dict[age], {'main.sql': sql_dict_list},
                                keep_changes=False, dict_form_list=dict_form_list)
    return result_info


SQLValidator = SchemaInspector()
