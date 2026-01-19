import os
import re
import glob
import sqlite3
import shutil
import logging
import sys
import tempfile
import time
import sqlparse
import traceback

from xml_handler import read_xml
from gameeffects import game_effects, req_build, req_set_build
from sql_errors import get_query_details, full_matcher_sql, primary_key_matcher, check_foreign_keys, foreign_key_check, foreign_key_pretty_notify
from graph.db_spec_singleton import db_spec

# FOr getting the DB, its NOT just loading up civ and using the existing empty one in shell. as that misses collections
# added  as types, What it ended up being was loading an antiquity civ game, except editing the modinfo for it so
# the criteria is AGE_EXPLORATION for those entries that arent always (those are needed for shell to start antiquity),
# then copying the db after it fails to load.
DEBUG_LOGFILE = os.path.expanduser('~/CivVII_backend_debug.log')
logger = logging.getLogger(__name__)
logging.basicConfig(filename=DEBUG_LOGFILE, level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')


class NonBlockingQueue:
    def __init__(self, q, fallback_path=DEBUG_LOGFILE):
        self._q = q
        self._fallback = fallback_path

    def put(self, item):
        try:
            self._q.put(item, block=False)
        except Exception:
            try:
                with open(self._fallback, 'a') as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} QUEUE_FALLBACK: {repr(item)}\n")
            except Exception:
                pass


class SqlChecker:
    def __init__(self, log_queue=None):
        logger = logging.getLogger('SqlChecker')
        logger.setLevel(logging.WARNING)
        self.log_queue = log_queue
        self.errors = []
        self.known_errors_list, self.known_repeats = [], []
        self.file_pattern = re.compile(r'Loading (.*?)\n')
        self.errors_out = {'syntax': [], 'found_command': [], 'no_table': [], 'comment': [], 'mystery': []}
        self.db_path = ''

    def setup_db_existing(self):
        logging.debug("setup_db_existing start")
        copy_db_path = resource_path("resources/gameplay-copy-cached-base-content.sqlite")
        self.db_path = os.path.join(tempfile.gettempdir(), 'discardable-gameplay-copy.sqlite')
        try:
            shutil.copy(copy_db_path, self.db_path)
            logging.debug("copied db from %s to %s size=%s", copy_db_path, self.db_path, os.path.getsize(self.db_path))
            log_message(f"Copied DB to {self.db_path}", self.log_queue)
        except Exception as exc:
            logging.exception("copy failed")
            log_message(f"DB copy failed: {exc}", self.log_queue)
            raise

    def should_be_replace(self, cursor, sql_script, update_dict, filename, error):
        cursor.execute(primary_key_matcher(sql_script, error))
        result_wider = cursor.fetchone()
        if result_wider is not None:
            column_names = [description[0] for description in cursor.description]
            result_dict = {col_name: value for col_name, value in zip(column_names, result_wider)}
            common_keys = set(result_dict.keys()) & set(update_dict.keys())
            different_keys = {}
            for key in common_keys:
                if str(result_dict[key]) != update_dict[key]:
                    different_keys[key] = {'old': str(result_dict[key]), 'new': update_dict[key]}
            if len(different_keys) > 0:
                msg = (f"In {filename}, Differences between INSERT and existing suggests statement should be replace."
                       f" Replacing:\n{different_keys}")
                log_message(msg, self.log_queue)
                replace_into_script = sql_script.replace('INSERT', 'INSERT OR REPLACE')
                try:
                    cursor.execute(replace_into_script)
                except Exception as e:
                    log_message(e, self.log_queue)
                    table_name = replace_into_script.split(' (')[0].split('INSERT OR REPLACE INTO ')[1]
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    for column in columns:
                        log_message(f"Column ID: {column[0]}, Name: {column[1]}, Type: {column[2]}, "
                                    f"Not Null: {column[3]}, Default Value: {column[4]}, Primary Key: {column[5]}",
                                    self.log_queue)

        else:
            msg = f"Unique constraint fail but row not found, really an update? {filename}."
            log_message(msg, self.log_queue)
            self.errors.append(msg)

    def row_id_fix(self, cursor, sql_script):
        table_name, wheres = get_query_details(sql_script)
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_info = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        pragmas = []
        for i in table_info:
            pragmas.append({col_name: value for col_name, value in zip(column_names, i)})
        if 'RowId' in [i['name'] for i in pragmas] and 'RowId' not in wheres:
            select_script = f'SELECT * FROM {table_name}'
            cursor.execute(select_script)
            full_table = cursor.fetchall()
            row_id_index = [description[0] for description in cursor.description].index('RowId')
            new_row_id = int(full_table[-1][row_id_index]) + 1
            col_start = sql_script.index(table_name) + len(table_name + ' (')
            val_start = sql_script.index('VALUES') + len('VALUES (')
            row_id_script = sql_script[:col_start] + 'RowId, ' + sql_script[col_start:val_start] + str(
                new_row_id) + ', ' + sql_script[val_start:]
            row_id_script = row_id_script[:row_id_script.index("'SELECT")] + wheres[
                'SQL'] + ");"  # deals with nasty single quotes
            cursor.execute(row_id_script)
        else:
            pragmas = {i['name']: i for i in pragmas}
            not_null = [i for i, j in pragmas.items() if j['notnull'] == 1]
            missing_not_nulls = [i for i in not_null if i not in wheres]  # doesnt take into account defaults
            msg = f"Missing definitions for {table_name}: {missing_not_nulls}"
            log_message(msg, self.log_queue)
            self.errors.append(msg)

    def test_db(self, file_list, dlc_map, is_base):
        db_connection = sqlite3.connect(self.db_path)
        is_vanilla = dlc_map == ['Vanilla']
        known_script_errors = []

        db_connection.create_function("Make_Hash", 1, make_hash)

        unique_fk_errors = set()
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA defer_foreign_keys = ON;")
        db_connection.execute('BEGIN')
        errors = []
        file_list_tuples = [(filename, sql_scripts) for filename, sql_scripts in file_list.items()]
        for filename, sql_scripts in file_list_tuples:
            commenting = 0
            for idx, sql_script in enumerate(sql_scripts):
                if sql_script in known_script_errors and 'Vanilla' not in dlc_map:
                    continue
                if '/*' in sql_script:
                    commenting += 1
                if '*/' in sql_script:
                    commenting -= 1
                if commenting > 0:
                    self.errors_out['comment'].append((filename, sql_script))
                    continue
                try:
                    cursor.execute(sql_script)
                except sqlite3.Error as e:
                    errors.append(sql_script)
                    if '/'.join(filename.split('/')[1:]) not in dlc_map:
                        commands_used = self.individual_line_run(sql_script, cursor, filename)
                        if len(commands_used) == 0:
                            log_message(f'Errored on {filename}, but no commands found in SQL file', self.log_queue)
                        continue
                    self.unique_error_handler(e, filename, cursor, sql_script)

        try:
            prior_fk_errors = check_foreign_keys(cursor, file_list, True)
            unique_fk_errors.update(prior_fk_errors)
            if len(prior_fk_errors) > 0:
                log_message(f'FOREIGN KEY CONSTRAINT ERRORS: {len(prior_fk_errors)}', self.log_queue)
                for error in unique_fk_errors:
                    log_message(error, self.log_queue)
            db_connection.commit()

        except sqlite3.IntegrityError as e:
            log_message(f"Integrity error occurred: {e}", self.log_queue)
            fk_ch = check_foreign_keys(cursor, file_list)
            for error in fk_ch:
                log_message(error, self.log_queue)
            db_connection.rollback()
        fk_errors = check_foreign_keys(cursor, file_list)
        current_state = check_state(cursor)
        self.errors += fk_errors
        cursor.close()
        if len(fk_errors) > 0:
            for error in fk_errors:
                log_message(error, self.log_queue)
        if not is_vanilla:
            self.show_errors()

    def unique_error_handler(self, e, filename, cursor, sql_script):
        if 'UNIQUE' in str(e):
            check_exists_script, update_dict = full_matcher_sql(sql_script)
            cursor.execute(check_exists_script)
            result = cursor.fetchall()
            if len(result) > 1:
                log_message(f'Skipped inserting duplicate for {filename}:\n {sql_script}', self.log_queue)
            elif len(result) == 0:
                log_message(f'Skipped inserting duplicate for {filename}:\n, Unique, but the value wasnt found',
                            self.log_queue)
            else:
                if result[0][0] == list(update_dict.values())[0]:
                    log_message(f'Skipped inserting duplicate as value is already set correctly for {filename}:'
                                f' {sql_script}', self.log_queue)
                else:
                    self.should_be_replace(cursor, sql_script, update_dict, filename, e)
        elif sql_script in self.known_errors_list:
            log_message(f'Skipping known error on {sql_script}', self.log_queue)
        elif str(e) == 'FOREIGN KEY constraint failed':
            log_message(f'FOREIGN KEY CONSTRAINT fail.', self.log_queue)
            table_name = sql_script.split('(')[0].split(' ')[-2]
            labeled_constraints, primary_keys = foreign_key_check(cursor, table_name)
            foreign_key_pretty_notify(cursor, table_name, 'uh', labeled_constraints, primary_keys)
        else:
            self.row_id_fix(cursor, sql_script)

    def individual_line_run(self, sql_script, cursor, filename=None):
        table_name_pattern = r'\b(\w+)\s*\('
        columns_pattern = r'\(([^)]+)\)'
        values_pattern = r'VALUES\s*\((.*?)\);$'
        commands = []
        search = re.findall(table_name_pattern, sql_script)
        if len(search) > 0:
            table_name = search[0]
            columns = re.search(columns_pattern, sql_script)[1].split(',')
            columns = [j.strip() for j in columns]
            line_scripts = [i.replace(',\n', '').replace('\n', '').strip() + ')' for i in
                            sql_script.split(")")]
            line_scripts = [i.replace(',  ', '').strip() for i in line_scripts if i != ';)']
            if 'INSERT INTO' in line_scripts[0]:
                prefix = line_scripts[0]
                for j in line_scripts[1:]:
                    commands.append(prefix + 'VALUES' + j.replace('VALUES', '') + ';')

        for command in commands:
            try:
                cursor.execute(command)
            except Exception as e:
                string_error = str(e)
                if any(j in string_error for j in ['SYNTAX', 'Syntax', 'syntax']):
                    log_message(e, self.log_queue)
                    self.errors_out['syntax'].append((filename, e, command))
                    continue
                if 'no such table' in string_error:
                    log_message(e, self.log_queue)
                    self.errors_out['no_table'].append((filename, e, command))
                    continue
                column_fails = string_error.split('failed: ')[1].replace(table_name + '.', '')
                unsplit_search = re.search(r'VALUES\s*\((.*?)\);$', command)
                if unsplit_search is not None:
                    unsplit = unsplit_search[0]
                    vals = [i.replace("'", "").strip() for i in unsplit.split(',')]
                    col_plus_val = {key: val for key, val in zip(columns, vals)}
                    if len(column_fails.split(',')) > 1:
                        split_fails = [i.strip() for i in column_fails.split(',')]          # fails on empty strings RunOnce
                        error = str(e) + ' for: ' + str([col_plus_val[i] for i in split_fails])
                    else:
                        error = str(e) + ' on ' + col_plus_val[column_fails]
                    log_message(f'{error} caused by:\n{command}', self.log_queue)
                    self.errors_out['found_command'].append(f'{error} caused by:\n{command} in {filename}')
                else:
                    log_message(f'could not find values of command for {command} in {filename}', self.log_queue)
                    self.errors_out['mystery'].append(command)
        return commands

    def kill_df(self):
        log_message('--------- Finished -----------', self.log_queue)
        log_message(f'wrote to example sqlite db {self.db_path}', self.log_queue)

    def show_errors(self):
        fails = 0
        log_message('--------- Error Summary -------------', self.log_queue)
        for key, val in self.errors_out.items():
            if len(val) == 0:
                continue
            log_message(key, self.log_queue)
            for error in val:
                log_message(error, self.log_queue)
                fails += 1
        if fails == 0:
            log_message('no errors', self.log_queue)


def convert_to_sql(statements):
    sql_list = []
    for stmt in statements:
        if stmt["type"] == "INSERT":
            columns = ", ".join(stmt["columns"])
            for idx, i in enumerate(stmt["values"]):
                if i is not None and '"' in i:
                    stmt["values"][idx] = stmt["values"][idx].replace('"', "'")
            values = ", ".join(f'"{value}"' if isinstance(value, str) else str(value) for value in stmt["values"])
            sql = f"INSERT INTO {stmt['table']} ({columns}) VALUES ({values});"

        elif stmt["type"] == "REPLACE":
            columns = ", ".join(stmt["columns"])
            values = ", ".join(f"'{value}'" if isinstance(value, str) else str(value) for value in stmt["values"])
            sql = f"INSERT OR REPLACE into {stmt['table']} ({columns}) VALUES ({values});"

        elif stmt["type"] == "UPDATE":
            set_clause = ", ".join(f"{col} = '{value}'" if isinstance(value, str) else f"{col} = {value}"
                                   for col, value in stmt["set"].items())
            where_clause = " AND ".join(f"{col} = '{value}'" if isinstance(value, str) else f"{col} = {value}"
                                        for col, value in stmt["where"].items())
            sql = f"UPDATE {stmt['table']} SET {set_clause} WHERE {where_clause};"

        elif stmt["type"] == "DELETE":
            where_clause = " AND ".join(f"{col} = '{value}'" if isinstance(value, str) else f"{col} = {value}"
                                        for col, value in stmt["where"].items())
            sql = f"DELETE FROM {stmt['table']} WHERE {where_clause};"
        elif stmt["type"] == "INSERT IGNORE":
            columns = ", ".join(stmt["columns"])
            values = ", ".join(f"'{value}'" if isinstance(value, str) else str(value) for value in stmt["values"])
            sql = f"INSERT OR IGNORE INTO {stmt['table']} ({columns}) VALUES ({values});"
        else:
            raise Exception("Unknown")
        sql = sql.replace('@', '')
        sql = sql.replace('true', '1')
        sql = sql.replace('True', '1')
        sql = sql.replace('TRUE', '1')
        sql = sql.replace('false', '0')
        sql = sql.replace('False', '0')
        sql = sql.replace('FALSE', '0')
        sql = sql.replace('None', 'NULL')
        if "'’'" in sql:
            sql = sql.replace("'’'", '"’"')
        if "'''" in sql:
            sql = sql.replace("'''", '"\'"')
        sql_list.append(sql)
    return sql_list


def convert_xml_to_sql(xml_file, job_type=None, log_queue=None):
    sql_statements = []
    xml_ = read_xml(xml_file)
    error_messages, skips = validate_xml(xml_)
    if not xml_ or xml_ == '':
        return f"{xml_file} was empty...", {}
    xml_ = xml_.get('Database', xml_.get('{GameEffects}GameEffects'))
    if not xml_ or xml_ == '':
        return f"{xml_file} was empty...", {}
    if 'Table' in xml_:
        if not isinstance(xml_['Table'], list):
            xml_['Table'] = [xml_['Table']]
        sql_strings = []
        for table in xml_['Table']:
            table_name = table['@name']
            sql_string = f"CREATE TABLE '{table_name}' ("
            pks = []
            if not isinstance(table['Column'], list):
                table['Column'] = [table['Column']]
            for i in table['Column']:
                column_string = f"'{i['@name']}' {i['@type'].capitalize()}"
                if i.get('@notnull') == 'true':
                    column_string += " NOT NULL"
                if i.get('@unique') == 'true':
                    column_string += " UNIQUE"
                if i.get('@primarykey') == 'true':
                    pks.append(i['@name'])
                sql_string += column_string + ", "
            sql_string += f"PRIMARY KEY({', '.join([i for i in pks])}));"
            sql_strings.append(sql_string)
        return sql_strings, {}
    # filter out empty strings
    for key, val in xml_.items():
        if isinstance(val, list):
            new_val = [j for j in val if not isinstance(j, str)]
            xml_[key] = new_val
    xml_errors = {}
    for table_name, sql_commands in xml_.items():
        if table_name == 'Row':
            continue                # some orphaned xml with no table
        if sql_commands is None:
            message = f'Table {table_name} was referenced, but did not contain any commands within.'
            logger.info('ignoring message for user as probably on firaxis', message) if (job_type is not None and job_type in ['DLC', 'vanilla']) else logger.info('ignoring message for user', message)
            continue
        if isinstance(sql_commands, str):
            message = f'Likely empty xml, this was the value found in table element: {sql_commands}. File: {xml_file}.'
            logger.info('ignoring message for user as probably on firaxis', message) if (job_type is not None and job_type in ['DLC', 'vanilla']) else logger.info('ignoring message for user', message)
            continue
        if not isinstance(sql_commands, list):
            sql_commands = [sql_commands]
        for sql_commands_dict in sql_commands:
            if table_name == '{GameEffects}Modifier':
                sql_statements, errors = game_effects(sql_statements, sql_commands_dict, xml_file, skips)
                if len(errors) > 0:
                    if xml_errors.get(table_name, False):
                        xml_errors[table_name].append(errors)
                    else:
                        xml_errors[table_name] = [errors]
                continue
            if table_name == '{GameEffects}RequirementSet':
                req_set_id = sql_commands_dict['@id']
                sql_statements = req_set_build(sql_statements, sql_commands_dict, req_set_id)
                continue
            if table_name == '{GameEffects}Requirement':
                req_id = sql_commands_dict['@id']
                sql_statements, req_id = req_build(sql_statements, sql_commands_dict, req_id)
                continue
            for command, details in sql_commands_dict.items():
                if details is None:
                    continue
                if command == 'Delete':
                    if not isinstance(details, list):
                        details = [details]
                    for record in details:
                        for column, value in record.items():
                            sql_statements.append({"type": "DELETE", "table": table_name, "where": {column: value}})
                elif command == 'Update':
                    if not isinstance(details, list):
                        details = [details]
                    for record in details:
                        sql_statements.append({"type": "UPDATE", "table": table_name, "set": record['Set'],
                                                   "where": {i: j for i, j in record['Where'].items()}})
                elif command == 'Row':
                    if not isinstance(details, list):
                        details = [details]
                    for record in details:
                        columns, values = [i for i in record], [j for j in record.values()]
                        sql_statements.append({"type": "INSERT", "table": table_name, "columns": columns, "values": values})
                elif command == 'Replace':
                    if not isinstance(details, list):
                        details = [details]
                    for record in details:
                        columns, values = [i for i in record], [j for j in record.values()]
                        sql_statements.append({"type": "REPLACE", "table": table_name, "columns": columns, "values": values})
                elif command == 'InsertOrIgnore':
                    if not isinstance(details, list):
                        details = [details]
                    for record in details:
                        columns, values = [i for i in record], [j for j in record.values()]
                        sql_statements.append({"type": "INSERT IGNORE", "table": table_name, "columns": columns, "values": values})
                elif command == '#text':
                    log_message(f'Firaxis typo lol on {xml_file}', log_queue)
                else:
                    log_message(f'unknown command: {command}', log_queue)
    sql_strings = convert_to_sql(sql_statements)
    return sql_strings, xml_errors


def validate_xml(xml_dict):
    error_msgs, xml_skips = [], {}
    if '{GameEffects}GameEffects' in xml_dict:
        game_effects_info = xml_dict['{GameEffects}GameEffects']
        if '{GameEffects}Modifier' in game_effects_info:
            modifier_list = game_effects_info['{GameEffects}Modifier']
            if not isinstance(modifier_list, list):
                modifier_list = [modifier_list]
            for modifier_dict in modifier_list:
                mod_name = modifier_dict['@id']
                if '{GameEffects}SubjectRequirements' in modifier_dict:
                    requirement_list = modifier_dict['{GameEffects}SubjectRequirements']
                    if isinstance(requirement_list, list):
                        msg = f'ERROR: Requirements list for {mod_name} had two requirement lists nested, due to bad xml. This will silently error on firaxis side, and only will use the first requirement.'
                        logger.warning(msg)
                        error_msgs.append(msg)
                        xml_skips[mod_name] = {'error_type': 'NestedRequirements', 'additional': 'subject'}

    return error_msgs, xml_skips


def query_mod_db(age, log_queue=None):
    with open(resource_path('resources/queries/query_VII_mods.sql'), 'r') as f:
        query = f.read()
    query = query.replace('AGE_ANTIQUITY', age)
    conn = sqlite3.connect(f"{db_spec.civ_config}/Mods.sqlite")
    conn.row_factory = sqlite3.Row  # enables column access by name
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    files_to_apply = []
    # first we need the modinfos of each mod
    filepath_dlc_mod_infos = [f for f in glob.glob(f"{db_spec.civ_install}/**/*.modinfo*", recursive=True)]
    filepath_mod_mod_infos = ([f for f in glob.glob(f"{db_spec.workshop}/**/*.modinfo*", recursive=True)] +
                              [f for f in glob.glob(f"{db_spec.civ_config}/**/*.modinfo*", recursive=True)])
    filepath_mod_infos = filepath_dlc_mod_infos + filepath_mod_mod_infos
    modinfo_uuids, err_string, dlc_mods, mod_mods = {}, '', [], []

    for filepath in filepath_mod_infos:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        match = re.search(r'<Mod id="([^"]+)"', text)
        if match:
            folder_path = os.path.dirname(filepath)
            uuid = match.group(1)
            if uuid in modinfo_uuids:
                err_string += (f'ERROR: Duplicate modinfo UUID:You likely have a local copy and a workshop copy of '
                               f'the same mod {uuid}.\nCurrent folder path: {folder_path},\nexistin'
                               f'g folder path: {modinfo_uuids[uuid]}\n----------------')
            modinfo_uuids[uuid] = folder_path
            if filepath in filepath_dlc_mod_infos:
                dlc_mods.append(uuid)
            else:
                mod_mods.append(uuid)

    if len(err_string) > 0:
        raise Exception(err_string)
    for row in rows:
        file_info = dict(row)
        mod_folder_path = modinfo_uuids.get(file_info['ModId'], None)
        if mod_folder_path is None:
            log_message(f'Mod: {file_info["ModId"]} was not present in modding folder: {mod_folder_path}.'
                               f'\nThis likely means this mod was removed since you last launched Civ. Skipping.',
                        log_queue)
            continue                    # if mod was removed since last civ launch
        file_info['full_path'] = os.path.join(mod_folder_path, file_info['File'])
        del file_info['Disabled']
        files_to_apply.append(file_info)

    # custom order from modding.log: core-game, base-standard
    custom_index = ['core-game', 'base-standard']
    index = {mod: i for i, mod in enumerate(custom_index)}
    files_to_apply = sorted(files_to_apply, key=lambda d: index.get(d["ModId"], len(custom_index)))

    log_message('Loading DLC:', log_queue)
    log_message(list({i['ModId'] for i in files_to_apply if i['ModId'] in dlc_mods}), log_queue)
    log_message('-------------------------------------------', log_queue)
    log_message('Loading Mods:', log_queue)
    log_message(list({i['ModId'] for i in files_to_apply if i['ModId'] in mod_mods}), log_queue)
    log_message('--------------------------------------------', None)
    return files_to_apply


def log_message(message, log_queue):
    if log_queue is not None:
        log_queue.put(message)
    print(message)


def check_state(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return tables


def make_hash(value):       # SHA1 hash, copies how firaxis does insert into Types
    h = hash(value)
    h = h % (2 ** 32)
    if h >= 2 ** 31:
        h -= 2 ** 32
    return h


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def model_run(log_queue, extra_sql, age):
    start_time = time.time()
    wrapped_q = NonBlockingQueue(log_queue)
    logging.debug("model_run start civ_install=%s civ_config=%s workshop=%s",
                  db_spec.civ_install, db_spec.civ_config, db_spec.workshop)
    try:
        checker = SqlChecker(wrapped_q)
        checker.setup_db_existing()
        database_entries = query_mod_db(age=age, log_queue=wrapped_q)                           # pass metadata as method used outside of class
        modded_short, modded, dlc, dlc_files = organise_entries(database_entries)
        DASHS = '--------------------'
        log_message(f"Modding database had {len(database_entries)} entries", wrapped_q)
        sql_statements_dlc, missed_dlc = load_files(dlc_files, 'DLC', log_queue)
        log_message(f"Loaded dlc files: {len(sql_statements_dlc)}. Excluded empty files: {len(missed_dlc)}", wrapped_q)
        sql_statements_mods, missed_mods = load_files(modded, 'Mod', log_queue)
        log_message(f"Loaded mod files: {len(sql_statements_mods)}. Missed: {len(missed_mods)}", wrapped_q)
        full_dump = []
        for statement_dict in [sql_statements_dlc, sql_statements_mods]:
            for key, val in statement_dict.items():
                full_dump.extend([DASHS + key + DASHS] + val)
        try:
            log_path = os.path.join(tempfile.gettempdir(), 'sql_statements.log')
            with open(log_path, 'w') as file:
                file.write("\n".join(full_dump))
            log_message(f"Wrote transformed SQL as a single file to {log_path}", wrapped_q)
        except Exception:
            logging.exception("failed to write sql_statements.log")
            log_message("failed to write sql_statements.log", wrapped_q)
        dlc_sql_dump = [j for i in sql_statements_dlc.values() for j in i]
        silly_parse_error = [j for j in dlc_sql_dump if ',;' in j] + [j for j in dlc_sql_dump if ', ;' in j]
        if len(silly_parse_error) > 0:
            log_message(f'had some ,; errors: {len(silly_parse_error)}', wrapped_q)
        log_message("Running SQL on Vanilla civ files...", wrapped_q)
        checker.test_db(sql_statements_dlc, ['Vanilla'], True)
        log_message("Finished running Vanilla Files", wrapped_q)
        log_message("Running SQL on Modded files...", wrapped_q)
        checker.test_db(sql_statements_mods, modded_short, False)
        log_message("Finished running Modded Files", wrapped_q)
        if extra_sql:
            with open('resources/main.sql', 'r') as f:
                graph_sql = f.readlines()
            logger.info(graph_sql)
            extra_statements = {'graph_main.sql': graph_sql}
            checker.test_db(extra_statements, ['Graph'], False)
            log_message("Finished running Graph mod", wrapped_q)

        checker.kill_df()
        log_message(f"model_run finished in {time.time()-start_time:.1f}s", wrapped_q)
    except Exception as e:
        wrapped_q.put({
            "type": "crash",
            "error": str(e),
            "traceback": traceback.format_exc(),
        })
        raise


def organise_entries(database_entries, wrap_queue=None):
    modded_short, modded, dlc, dlc_files = [], [], [], []
    for i in database_entries:
        if 'Base/' in i['full_path'] or 'Base\\' in i['full_path']:
            dlc.append(i['File'])
            dlc_files.append(i['full_path'])
        if 'DLC/' in i['full_path'] or 'DLC\\' in i['full_path']:
            dlc.append(i['File'])
            dlc_files.append(i['full_path'])
        if 'Mods' in i['full_path'] or 'workshop' in i['full_path']:
            modded.append(i['full_path'])
    log_message(f"Collected dlc ({len(dlc_files)}) and mod files ({len(modded)})", wrap_queue)
    return modded_short, modded, dlc, dlc_files


def load_files(jobs, job_type, log_queue=None):
    jobs_short_ref = [('/'.join(i.split('/')[-4:]), i) for i in jobs]
    missed_files, ensure_ordered_sql, firaxis_fails, known_mod_fails = [], [], [], []
    known_mod_fails, known_fails, sql_statements = [], [], {}
    for short_name, db_file in jobs_short_ref:
        existing_short = [i[0] for i in ensure_ordered_sql if i[0] == short_name]
        if len(existing_short) > 0:
            error_msg = f'Duplicate file: {short_name} already in list:\n2nd ref: {db_file}. Existing ref: {existing_short}'
            log_message(error_msg, log_queue)
        if db_file.endswith('.xml') and not any(i in db_file for i in known_fails):
            statements, xml_errors = convert_xml_to_sql(db_file, job_type, log_queue=log_queue)
            if isinstance(statements, str):
                missed_files.append(short_name)
                if job_type in ['DLC', 'vanilla']:
                    logger.info('ignore as its just firaxis')
                else:
                    logger.info('ignore as its just modders having empty files')
                    # log_message(statements, log_queue)
                continue
            sql_statements[short_name], xml_errors = convert_xml_to_sql(db_file, job_type, log_queue=log_queue)
            ensure_ordered_sql.append((short_name, sql_statements[short_name]))
        if db_file.endswith('.sql') and not any(i in db_file for i in known_fails):
            try:
                with open(db_file, 'r') as file:
                    sql_contents = file.read()
            except UnicodeDecodeError as e:
                log_message(f'Bad unicode, trying windows-1252: {e}')
                with open(db_file, 'r', encoding='windows-1252') as file:
                    sql_contents = file.read()
            comment_cleaned = re.sub(r'--.*?\n', '', sql_contents, flags=re.DOTALL)
            sql_statements[short_name] = sqlparse.split(comment_cleaned)
            ensure_ordered_sql.append((short_name, sql_statements[short_name]))
    return sql_statements, missed_files
