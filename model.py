import os
import re
import glob
import sqlite3
import shutil
import logging
import sqlparse
from collections import defaultdict


from xml_handler import read_xml
from gameeffects import game_effects, req_build, req_set_build
from graph.singletons.filepaths import LocalFilePaths
from graph.utils import resource_path, LogPusher

log = logging.getLogger(__name__)


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


def convert_xml_to_sql(xml_file, job_type=None):
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
            log.info(f'ignoring message for user as probably on firaxis {message}', ) if (job_type is not None and job_type in ['DLC', 'vanilla']) else log.info(f'ignoring message for user {message}')
            continue
        if isinstance(sql_commands, str):
            message = f'Likely empty xml, this was the value found in table element: {sql_commands}. File: {xml_file}.'
            log.info(f'ignoring message for user as probably on firaxis {message}') if (job_type is not None and job_type in ['DLC', 'vanilla']) else log.info(f'ignoring message for user {message}')
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
                    LogPusher.push_to_log(f'Firaxis typo lol on {xml_file}', log)
                else:
                    LogPusher.push_to_log(f'unknown command: {command}', log)
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
                        log.warning(msg)
                        xml_skips[mod_name] = {'error_type': 'NestedRequirements', 'additional': 'subject'}

    return error_msgs, xml_skips


def query_mod_db(age, log_queue=None):
    files_to_apply = []
    # first we need the modinfos of each mod
    filepath_dlc_mod_infos = [f for f in glob.glob(f"{LocalFilePaths.civ_install}/**/*.modinfo*", recursive=True)]
    filepath_mod_mod_infos = ([f for f in glob.glob(f"{LocalFilePaths.workshop}/**/*.modinfo*", recursive=True)] +
                              [f for f in glob.glob(f"{LocalFilePaths.civ_config}/**/*.modinfo*", recursive=True)])
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
                log.error(f'ERROR: Duplicate modinfo UUID:You likely have a local copy and a workshop copy of '
                               f'the same mod {uuid}.\nCurrent folder path: {folder_path},\nexistin'
                               f'g folder path: {modinfo_uuids[uuid]}\n----------------')
            else:
                modinfo_uuids[uuid] = folder_path
                if filepath in filepath_dlc_mod_infos:
                    dlc_mods.append(uuid)
                else:
                    mod_mods.append(uuid)

    if len(err_string) > 0:
        raise Exception(err_string)
    with open(resource_path('resources/queries/query_VII_mods.sql'), 'r') as f:
        query = f.read()
    query = query.replace('AGE_ANTIQUITY', age)
    conn = sqlite3.connect(f"{LocalFilePaths.civ_config}/Mods.sqlite")
    conn.row_factory = sqlite3.Row  # enables column access by name
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    for row in rows:
        file_info = dict(row)
        mod_folder_path = modinfo_uuids.get(file_info['ModId'], None)
        if mod_folder_path is None:
            LogPusher.push_to_log(f'Mod: {file_info["ModId"]} was not present in modding folder: {mod_folder_path}.'
                               f'\nThis likely means this mod was removed since you last launched Civ. Skipping.',
                        log)
            continue                    # if mod was removed since last civ launch
        file_info['full_path'] = os.path.join(mod_folder_path, file_info['File'])
        del file_info['Disabled']
        files_to_apply.append(file_info)

    # custom order from modding.log: core-game, base-standard
    custom_index = ['core-game', 'base-standard']
    index = {mod: i for i, mod in enumerate(custom_index)}
    files_to_apply = sorted(files_to_apply, key=lambda d: index.get(d["ModId"], len(custom_index)))

    log.info('Mods to apply:')
    db_by_mod_id = defaultdict(dict)

    for i in files_to_apply:
        db_by_mod_id[i['ModId']][i['File']] = i['full_path']

    log.info([i for i in db_by_mod_id.keys()])
    log.info('----------------------------------')
    log.info('Full Files to apply:')
    log.info({k: [key for key in v.keys()] for k, v in db_by_mod_id.items()})
    log.info('Files to apply:')
    log.info(dict(db_by_mod_id))
    LogPusher.push_to_log('Loading DLC:', log)
    LogPusher.push_to_log(list({i['ModId'] for i in files_to_apply if i['ModId'] in dlc_mods}), log)
    LogPusher.push_to_log('-------------------------------------------', log)
    LogPusher.push_to_log('Loading Mods:', log)
    LogPusher.push_to_log(list({i['ModId'] for i in files_to_apply if i['ModId'] in mod_mods}), log)
    LogPusher.push_to_log('--------------------------------------------', log)
    return files_to_apply


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
    LogPusher.push_to_log(f"Collected dlc ({len(dlc_files)}) and mod files ({len(modded)})", log)
    return modded_short, modded, dlc, dlc_files


def load_files(jobs, job_type):
    jobs_short_ref = [('/'.join(i.split('/')[-4:]), i) for i in jobs]
    missed_files, ensure_ordered_sql, firaxis_fails, known_mod_fails = [], [], [], []
    known_mod_fails, sql_statements, sql_cache = [], {}, {}

    for short_name, db_file in jobs_short_ref:
        existing_short = [i[0] for i in ensure_ordered_sql if i[0] == short_name]
        if len(existing_short) > 0:
            error_msg = f'Duplicate file: {short_name} already in list:\n2nd ref: {db_file}. Existing ref: {existing_short}'
            LogPusher.push_to_log(error_msg, log)
        if db_file.endswith('.xml'):
            statements, xml_errors = convert_xml_to_sql(db_file, job_type)
            if isinstance(statements, str):
                missed_files.append(short_name)
                sql_cache[db_file] = []
                if job_type in ['DLC', 'vanilla']:
                    log.debug('ignore as its just firaxis')
                else:
                    log.debug('ignore as its just modders having empty files')
                continue
            sql_statements[short_name], xml_errors = convert_xml_to_sql(db_file, job_type)
            sql_cache[db_file] = sql_statements[short_name]
            ensure_ordered_sql.append((short_name, sql_statements[short_name]))
        if db_file.endswith('.sql'):
            try:
                with open(db_file, 'r') as file:
                    sql_contents = file.read()
            except UnicodeDecodeError as e:
                LogPusher.push_to_log(f'Bad unicode, trying windows-1252: {e}', log)
                with open(db_file, 'r', encoding='windows-1252') as file:
                    sql_contents = file.read()
            comment_cleaned = re.sub(r'--.*?\n', '', sql_contents, flags=re.DOTALL)
            parsed_commands = sqlparse.split(comment_cleaned)
            sql_statements[short_name] = parsed_commands
            sql_cache[db_file] = parsed_commands
            ensure_ordered_sql.append((short_name, sql_statements[short_name]))

    # new logic for linting database entries relies on using a source node. As raw files dont have source,
    # we are just gonna use the filepath i guess
    dictified = {key: [{'sql': i, 'node_source': key} for i in val] for key, val in sql_statements.items()}
    # metrics
    log.info('Missed Files:')
    log.info(missed_files)
    log.info('Modinfo Files and Statements')
    log.info({k: len(v) for k, v in sql_statements.items()})

    return dictified, sql_cache, missed_files
