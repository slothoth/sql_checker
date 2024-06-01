import os
import re
import glob
import xml.etree.ElementTree as ET
import tempfile
import sqlite3
import shutil
import logging
import sqlparse

from xml_handler import read_xml

class SqlChecker():
    def __init__(self):
        self.logger = logging.getLogger('SqlChecker')
        self.logger.setLevel(logging.WARNING)
        self.granularity = 'statement'
        self.known_errors_list = ["UPDATE AiFavoredItems SET Value = '200' WHERE ListType = 'CatherineAltLuxuries' AND PseudoYieldType = 'PSEUDOYIELD_RESOURCE_LUXURY';"]

    def parse_mod_log(self):
        log_folder = os.environ.get('CIV_LOG')
        civ_install = os.environ.get('CIV_INSTALL')
        workshop_folder = os.environ.get('WORKSHOP_FOLDER')
        local_mods_folder = os.environ.get('LOCAL_MODS_FOLDER')

        string = '.modinfo'
        filepath_dlc_mod_infos = [f for f in glob.glob(f'{civ_install}/**/*{string}*', recursive=True)]
        filepath_mod_mod_infos = ([f for f in glob.glob(f'{workshop_folder}/**/*{string}*', recursive=True)] +
                                  [f for f in glob.glob(f'{local_mods_folder}/**/*{string}*', recursive=True)])
        filepath_mod_infos = filepath_dlc_mod_infos + filepath_mod_mod_infos
        uuid_map = {ET.parse(filepath).getroot().attrib['id']: "/".join(filepath.split('/')[:-1]) for filepath in
                    filepath_mod_infos}
        with open(log_folder + '/Modding.log', 'r') as file:
            logs = file.readlines()
        uuid_pattern = re.compile(
            r'\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}\b')
        file_pattern = re.compile(r'Loading (.*?)\n')
        component_pattern = re.compile(r'Applying Component - (.*?) \(UpdateDatabase\)')
        uuid_component_pattern = re.compile(r' \* (.*?) \(UpdateDatabase\)')
        database_entries = [{'text': i, 'line': idx} for idx, i in enumerate(logs) if
                            '(UpdateDatabase)' in i and 'Applying Component' not in i]
        database_components = {component_pattern.search(i)[1]: {'text': i, 'line': idx} for idx, i in enumerate(logs) if
                               '(UpdateDatabase)' in i and 'Applying Component' in i}
        for component, i in database_components.items():
            line_list = []
            for idx, j in enumerate(logs[i['line'] + 1:]):
                if 'Applying Component' in j or 'Finished Apply Components' in j:
                    break
                if 'Error' in j:
                    continue
                if 'Error' in logs[i['line'] + 1:][idx + 1]:
                    continue
                line_list.append(j)
            i['files'] = []
            for k in line_list:
                match = file_pattern.search(k)
                if match is None:
                    raise Exception(f"Could not parse out filepath for {k}")
                i['files'].append(match[1])

        for entry in database_entries:
            for item in logs[:entry['line']][::-1]:
                if uuid_pattern.search(item) is not None:
                    entry['uuid'] = uuid_pattern.search(item)[0]
                    entry['mod_dir'] = uuid_map[entry['uuid']]
                    entry['component'] = uuid_component_pattern.search(entry['text'])[1]
                    entry['files'] = database_components[entry['component']]['files']
                    entry['full_files'] = [f"{entry['mod_dir']}/{i}" for i in entry['files']]
                    remove_entries_index = []
                    for idx, filepath in enumerate(entry['full_files']):
                        if not os.path.exists(filepath):
                            raise Exception(f'File {filepath} not found.')
                        #if 'schema' in filepath.lower():
                        #    remove_entries_index.append(idx)
                    for remove_idx in remove_entries_index[::-1]:
                        entry['full_files'].pop(remove_idx)
                    break

        return database_entries

    def convert_xml_to_sql(self, xml_file, line_by_line=False):
        sql_statements = []
        tricky = []
        xml_ = read_xml(xml_file)
        if not xml_:
            raise AttributeError(f"{xml_file} was empty...")
        xml_ = xml_.get('GameInfo', xml_.get('GameData'))
        for table_name, sql_commands in xml_.items():
            if isinstance(sql_commands, str):
                self.logger.info(f'Likely empty xml, this was the value found in table element: {sql_commands}'
                      f'. File: {xml_file}.')
                continue
            if not isinstance(sql_commands, list):
                sql_commands = [sql_commands]
            for sql_commands_dict in sql_commands:
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
                    elif command == '#text':
                        self.logger.info(f'Firaxis typo lol on {xml_file}')
                    else:
                        self.logger.warning(f'unknown command: {command}')
        sql_strings = self.convert_to_sql(sql_statements)
        if line_by_line:
            return sql_strings
        temp_filepath = tempfile.gettempdir() + '/' + xml_file.split('/')[-1].replace('.xml', '.sql')
        with open(temp_filepath, 'w') as file:
            file.write('\n'.join(sql_strings))
        return temp_filepath

    def convert_to_sql(self, statements):
        sql_list = []
        for stmt in statements:
            if stmt["type"] == "INSERT":
                columns = ", ".join(stmt["columns"])
                values = ", ".join(f"'{value}'" if isinstance(value, str) else str(value) for value in stmt["values"])
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
            sql_list.append(sql)
        return sql_list

    def test_db(self, db_connection, file_list, dlc_map, line_by_line=False):
        sql_scripts = {}
        errors = []
        if line_by_line:
            cursor = db_connection.cursor()
            db_connection.execute('BEGIN')
            for filename, sql_scripts in file_list.items():
                for idx, sql_script in enumerate(sql_scripts):
                    try:
                        cursor.executescript(sql_script)
                    except sqlite3.Error as e:
                        if '/'.join(filename.split('/')[1:]) not in dlc_map:
                            print(e)
                            continue
                        if 'UNIQUE' in str(e):
                            check_exists_script, update_dict = full_matcher_sql(sql_script)
                            cursor.execute(check_exists_script)
                            result = cursor.fetchall()
                            if len(result) > 0:
                                self.logger.info(f'Skipped inserting duplicate for {filename}:\n {sql_script}')
                            else:
                                cursor.execute(primary_key_matcher(sql_script, e))
                                result_wider = cursor.fetchone()
                                if result_wider is not None:
                                    column_names = [description[0] for description in cursor.description]
                                    result_dict = {col_name:value for col_name, value in zip(column_names, result_wider)}
                                    common_keys = set(result_dict.keys()) & set(update_dict.keys())
                                    different_keys = {}
                                    for key in common_keys:
                                        if str(result_dict[key]) != update_dict[key]:
                                            different_keys[key] = {'old': str(result_dict[key]), 'new': update_dict[key]}
                                    if len(different_keys) > 0:
                                        msg = (f"Differences between INSERT and existing suggests it should be replaced. Replacing:"
                                               f"\n{different_keys}")
                                        self.logger.warning(msg)
                                        replace_into_script = sql_script.replace('INSERT', 'INSERT OR REPLACE')
                                        cursor.executescript(replace_into_script)

                                else:
                                    msg = (f"Unique constraint fail but row not found, really an update? {filename}."
                                           f"Differences:\n{different_keys}")
                                    self.logger.critical(msg)
                                    errors.append(msg)

                        elif sql_script in self.known_errors_list:
                            self.logger.info(f'Skipping known error on {sql_script}')
                        else:
                            msg = f"f'Stupid RowId not added for {filename}:\n {sql_script}'"
                            # query ddl of table
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
                                row_id_script = sql_script[:col_start] + 'RowId, ' + sql_script[col_start:val_start] + str(new_row_id) + ', ' + sql_script[val_start:]
                                row_id_script = row_id_script[:row_id_script.index("'SELECT")] + wheres['SQL'] + ");"       # deals with nasty single quotes
                                cursor.executescript(row_id_script)
                            else:
                                pragmas = {i['name']: i for i in pragmas}
                                not_null = [i for i, j in pragmas.items() if j['notnull'] == 1]
                                missing_not_nulls = [i for i in not_null if i not in wheres]        # doesnt take into account defaults
                                msg = f"f'Missing definitions for {table_name}: {missing_not_nulls}'"
                                self.logger.critical(msg)
                                errors.append(msg)

            db_connection.commit()
            cursor.close()
            print(errors)

        elif isinstance(file_list, dict):
            for component, file_paths in file_list.items():
                for sql_file_path in file_paths:
                    with open(sql_file_path, 'r') as file:
                        sql_script = file.read()
                    sql_scripts[sql_file_path] = sql_script
                cursor = db_connection.cursor()
                try:
                    db_connection.execute('BEGIN')

                    for filename, sql_script in sql_scripts.items():
                        cursor.executescript(sql_script)
                    self.logger.info(f"{component}.{filename} Success!")
                    db_connection.rollback()  # rollback changes
                except sqlite3.Error as e:
                    # Rollback transaction if any script fails
                    db_connection.rollback()
                    self.logger.critical(f"{e} on file {filename.split('/')[-2:]} on Component {component}.")
                finally:
                    cursor.close()

        else:
            for sql_file_path in file_list:
                with open(sql_file_path, 'r') as file:
                    sql_script = file.read()
                sql_scripts[sql_file_path] = sql_script

            cursor = db_connection.cursor()
            try:
                db_connection.execute('BEGIN')
                for filename, sql_script in sql_scripts.items():
                    cursor.executescript(sql_script)

                db_connection.rollback()                # rollback changes
                cursor.close()
            except sqlite3.Error as e:
                # Rollback transaction if any script fails
                db_connection.rollback()
                self.logger.critical(f"{e} on file {filename.split('/')[-3:]}.")
                cursor.close()


def get_query_details(script):
    table_name_pattern = r'\b(\w+)\s*\('
    columns_pattern = r'\(([^)]+)\)'
    values_pattern = r'VALUES\s*\((.*?)\);$'
    search = re.findall(table_name_pattern, script)
    if len(search) > 0:
        table_name = search[0]
        columns = re.search(columns_pattern, script)[1].split(',')
        values = re.search(values_pattern, script)[1].split("',")
    else:
        split_space = script.split(' ')
        if len(split_space) > 1:
            table_name = split_space[1]


    values = ["'" + i.strip(" '").replace("'", '"') + "'" for i in values]
    wheres = {col.strip(): val for col, val in zip(columns, values)}
    return table_name, wheres

def full_matcher_sql(sql_script):
    table_name, wheres = get_query_details(sql_script)
    wheres.pop('SQL', None)  # ughhh, its hard to parse metaSQL and quotation marks
    assign_vals = "\n AND ".join([f'{col} = {val}' for col, val in wheres.items()])
    script = f"SELECT *\n FROM {table_name}\n WHERE " + assign_vals + ";"
    return script, {i: j.strip("'") for i, j in wheres.items()}


def primary_key_matcher(sql_script, error):
    table_name, wheres = get_query_details(sql_script)
    parsed_error = str(error).replace('UNIQUE constraint failed: ', '').split(',')
    check_cols = []
    for instance in parsed_error:
        check_cols.append(instance.split('.')[1])
    checks = {i: j for i, j in wheres.items() if i in check_cols}
    assign_vals = "\n AND ".join([f'{col} = {val}' for col, val in checks.items()])
    check_exists = f"SELECT * FROM {table_name} WHERE " + assign_vals + ";"
    return check_exists

GRANULARITY = 'statement_level'
if os.path.exists('DebugGameplay_working.sqlite'):
    shutil.copy('DebugGameplay.sqlite', 'DebugGameplay_working.sqlite')  # restore backup db
    db_path = 'DebugGameplay_working.sqlite'
else:
    db_path = os.environ.get('DB_PATH')

conn = sqlite3.connect(db_path)


def make_hash(value):
    h = hash(value)
    h = h % (2 ** 32)
    if h >= 2 ** 31:
        h -= 2 ** 32
    return h

conn.create_function("Make_Hash", 1, make_hash)
checker = SqlChecker()
database_entries = checker.parse_mod_log()
dlc = []
[dlc.extend(i['files']) for i in database_entries if 'DLC' in i['mod_dir']]
modded = []
modded = [modded.extend(i['files']) for i in database_entries if 'DLC' not in i['mod_dir']]         # later do change to environ set mod directory
if GRANULARITY == 'mod_level':
    jobs = {entry['component']: entry['full_files'] for entry in database_entries}
    for key, val in jobs.items():
        for db_file in val:
            if db_file.endswith('.xml'):
                try:
                    db_file = checker.convert_xml_to_sql(db_file)
                except AttributeError as e:
                    print(e)
                    continue

    checker.test_db(conn, jobs)

elif GRANULARITY == 'file_level':
    jobs = []
    [jobs.extend(i['full_files']) for i in database_entries]
    converted_sql_filepaths = []

    for db_file in jobs:
        if db_file.endswith('.xml'):
            try:
                converted_sql_filepaths.append(checker.convert_xml_to_sql(db_file))
            except AttributeError as e:
                print(e)
                continue

    jobs = [i for i in jobs if '.xml' not in i] + converted_sql_filepaths
    checker.test_db(conn, jobs, dlc)

elif GRANULARITY == 'statement_level':
    line_by_line = True
    jobs = []
    [jobs.extend(i['full_files']) for i in database_entries]
    sql_statements = {}
    for db_file in jobs:
        short_name = '/'.join(db_file.split('/')[-3:])
        if db_file.endswith('.xml'):
            try:
                sql_statements[short_name] = checker.convert_xml_to_sql(db_file, line_by_line)
            except AttributeError as e:
                print(e)
                continue
        if db_file.endswith('.sql'):
            try:
                with open(db_file, 'r') as file:
                    sql_contents = file.read()
            except UnicodeDecodeError as e:
                print(f'Bad unicode, trying windows-1252: {e}')
                with open(db_file, 'r', encoding='windows-1252') as file:
                    sql_contents = file.read()
            sql_statements[short_name] = [i + ';' for i in sql_contents.split(';') if len(i) > 5]
    checker.test_db(conn, sql_statements, dlc, line_by_line)
    #  we need to set up a test suite that runs only unmodded to verify database integrity.
