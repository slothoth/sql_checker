import os
import re
import glob
import xml.etree.ElementTree as ET
import sqlite3
import shutil
import logging
from copy import deepcopy

import sqlparse
import json
import time
from xml_handler import read_xml


class SqlChecker:
    def __init__(self):
        self.logger = logging.getLogger('SqlChecker')
        self.logger.setLevel(logging.WARNING)
        self.granularity = 'statement'
        self.errors = []
        self.config = json.load(open('config.json', 'r'))
        self.log_folder = os.environ.get('CIV_LOG', f"{self.config['CIV_USER']}/Firaxis Games/Sid Meier's Civilization VI/Logs")
        self.civ_install = os.environ.get('CIV_INSTALL', self.config['CIV_INSTALL'])
        self.workshop_folder = os.environ.get('WORKSHOP_FOLDER', self.config['WORKSHOP_FOLDER'])
        self.local_mods_folder = os.environ.get('LOCAL_MODS_FOLDER',
                                           f"{self.config['CIV_USER']}/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Mods/")
        self.known_errors_list = ["UPDATE AiFavoredItems SET Value = '200' WHERE ListType = 'CatherineAltLuxuries' "
                                  "AND PseudoYieldType = 'PSEUDOYIELD_RESOURCE_LUXURY';"]
        self.known_repeats = ['RulersOfEngland/Data/RulersOfEngland_RemoveData.xml', 'GreatNegotiators/Data/GreatNegotiators_RemoveData.xml',
                              'GreatNegotiators/Data/GreatNegotiators_RemoveData.xml']
        # PseudoYieldType isnt a column, it should've been Item but Fireaxis is silly
        self.file_pattern = re.compile(r'Loading (.*?)\n')
        self.errors_out = {'syntax': [], 'found_command': [], 'no_table': [], 'comment': [], 'mystery': []}

    def setup_db_new(self):
        if not os.path.exists('DebugGameplay_working.sqlite'):
            copy_db_path = f"{self.config['CIV_USER']}/Firaxis Games/Sid Meier's Civilization VI/Cache/DebugGameplay.sqlite"
            shutil.copy(copy_db_path, 'DebugGameplay.sqlite')
        shutil.copy('DebugGameplay.sqlite', 'DebugGameplay_working.sqlite')  # restore backup db
        self.db_path = f'{int(time.time())}.sqlite'

    def setup_db_existing(self):
        copy_db_path = f"{self.config['CIV_USER']}/Sid Meier's Civilization VI/Mods/builder/data/DebugGameplay.sqlite"
        shutil.copy(copy_db_path, 'DebugFrozenGameplay.sqlite')
        self.db_path = f'{int(time.time())}.sqlite'
        shutil.copy('DebugFrozenGameplay.sqlite', self.db_path)  # restore backup db


    def parse_mod_log(self):
        string = '.modinfo'
        filepath_base_game_infos = []
        filepath_dlc_mod_infos = [f for f in glob.glob(f'{self.civ_install}/**/*.modinfo*', recursive=True)]
        filepath_mod_mod_infos = ([f for f in glob.glob(f'{self.workshop_folder}/**/*.modinfo*', recursive=True)] +
                                  [f for f in glob.glob(f'{self.local_mods_folder}/**/*.modinfo*', recursive=True)])
        filepath_mod_infos = filepath_dlc_mod_infos + filepath_mod_mod_infos
        uuid_map = {}
        for filepath in filepath_mod_infos:
            uuid_ = ET.parse(filepath).getroot().attrib['id']
            filepath = "/".join(filepath.replace('\\', '/').split('/')[:-1])
            uuid_map[uuid_] = filepath
        with open(self.log_folder + '/Modding.log', 'r') as file:
            logs = file.readlines()
        uuid_pattern = re.compile(
            r'\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}\b')
        file_pattern = re.compile(r'Loading (.*?)\n')
        component_pattern = re.compile(r'Applying Component - (.*?) \(UpdateDatabase\)')
        uuid_component_pattern = re.compile(r' \* (.*?) \(UpdateDatabase\)')
        database_entries = [{'text': i, 'line': idx} for idx, i in enumerate(logs) if
                            '(UpdateDatabase)' in i and 'Applying Component' not in i]
        database_components = {}
        dupes = {}
        for idx, i in enumerate(logs):
            if '(UpdateDatabase)' in i and 'Applying Component' in i:
                search = component_pattern.findall(i)
                record = {'text': i, 'line': idx, 'component_name': search[0]}
                if len(search) > 1:
                    print('dupe found')
                elif search[0] in database_components:
                    print(f'duplicate found {search[0]}')
                    if search[0] not in dupes:
                        dupes[search[0]] = [database_components.pop(search[0])]      # apply original found in dict to dupes
                        dupes[search[0]].append(record)                          # as found first, order is preserved
                    else:
                        dupes[search[0]].append(record)

                else:
                    database_components[search[0]] = record

        mod_order_start = next((idx for idx, string in enumerate(logs) if 'Target in-game actions (in order of application):' in string), None) + 1
        mod_order_end = next((idx for idx, string in enumerate(logs) if 'Game content needs to change to match target config' in string), None)
        mod_order = ["]".join(i.split(']')[1:]) for i in logs[mod_order_start:mod_order_end]]

        ordered_mods = []
        current_sublist = []
        new_entry = {}
        for item in mod_order:
            if item[:3] != '  *':
                if len(new_entry) > 0:          # add old entry before starting new one
                    ordered_mods.append(new_entry)
                space_split = item.strip().split(' ')
                unique_id = space_split[0]
                current_name = " ".join(space_split[1:])
                new_entry = {'id': unique_id, 'name': current_name, 'components': [], 'not_db_components': []}
            else:
                if 'UpdateDatabase' in item:
                    formatted_item = item.replace('  * ', '').replace(' (UpdateDatabase)\n', '')
                    new_entry['components'].append(formatted_item)
                else:
                    new_entry['not_db_components'].append(item)
        ordered_mods.append(new_entry)                # final entry

        mod_component_start = next(
            (idx for idx, string in enumerate(logs) if 'Modding Framework - Applying Components' in string),
            None) + 1
        mod_component_end = next(
            (idx for idx, string in enumerate(logs) if 'Applied all components of enabled mods.' in string),
            None)
        mod_component_order = ["]".join(i.split(']')[1:]) for i in logs[mod_component_start:mod_component_end]]
        mod_component_order = [i for i in mod_component_order if not ('Successfully released save point.' in i or 'Creating database save point.' in i)]
        files_to_apply = []
        for idx, i in enumerate(ordered_mods):
            template_component = {'uuid': i['id'], 'mod_dir': uuid_map[i['id']], 'files': [], 'full_files': [], 'name': i['name']}
            for j in i['components']:
                complete_component = template_component.copy()
                component_string = f' Applying Component - {j} (UpdateDatabase)'
                complete_component['component'] = component_string
                component_start, found = [(idx + 1, k) for idx, k in enumerate(mod_component_order) if component_string in k][0]
                component_end = next((idx for idx, string in enumerate(mod_component_order[component_start:]) if 'Applying Component' in string), None) + component_start
                component = mod_component_order[component_start:component_end]
                if len(component) > 0:
                    del mod_component_order[component_start-1:component_end]
                else:
                    del mod_component_order[component_start-1]
                complete_component['files'] = [k.replace(' UpdateDatabase - Loading ', '').replace('\n', '') for k in component if 'UpdateDatabase' in k]
                complete_component['aux_files'] = [k for k in component if 'UpdateDatabase' not in k]
                complete_component['full_files'] = [f'{complete_component["mod_dir"]}/{k}' for k in complete_component['files']]
                files_to_apply.append(complete_component)

        no_files = [i for i in files_to_apply if len(i['aux_files'] + i['files']) ==0]

        return files_to_apply, no_files

    def component_file_collect(self, database_components, logs):
        new_db = deepcopy(database_components)
        load_fails = []
        known_load_fails = ['UpdateDatabase - Loading Data/RulersOfTheSahara_RemoveData.xml\n', 'UpdateDatabase - Loading Data/RulersOfTheSahara_RemoveData.xml\n', 'UpdateDatabase - Loading Data/JuliusCaesar_Districts.xml\n', 'UpdateDatabase - Loading Data/JuliusCaesar_Modifiers.xml\n', 'UpdateDatabase - Loading Data/JuliusCaesar_Units.xml\n']
        for component, i in new_db.items():
            line_list = []
            for idx, j in enumerate(logs[i['line'] + 1:]):
                if 'Applying Component' in j or 'Finished Apply Components' in j:
                    break
                if 'Error' in j:
                    continue
                if 'Error' in logs[i['line'] + 1:][idx + 1]:
                    if any(fails in j for fails in known_load_fails):
                        continue
                    else:
                        load_fails.append(j)
                line_list.append(j)
            i['files'] = []
            for k in line_list:
                match = self.file_pattern.search(k)
                if match is None:
                    raise Exception(f"Could not parse out filepath for {k}")
                i['files'].append(match[1])
        print(f'Modding.log show fails at: \n {load_fails}')
        return new_db, load_fails

    def convert_xml_to_sql(self, xml_file, job_type):
        sql_statements = []
        xml_ = read_xml(xml_file)
        if not xml_ or xml_ == '':
            return f"{xml_file} was empty..."
        xml_ = xml_.get('GameInfo', xml_.get('GameData'))
        if not xml_ or xml_ == '':
            return f"{xml_file} was empty..."
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
            return sql_strings
        # filter out empty strings
        for key, val in xml_.items():
            if isinstance(val, list):
                new_val = [j for j in val if not isinstance(j, str)]
                xml_[key] = new_val


        for table_name, sql_commands in xml_.items():
            if table_name == 'Row':
                continue                # some orphaned xml with no table
            if sql_commands is None:
                message = f'None value in SQL command. No commands for table {table_name}.'
                if job_type in ['DLC', 'vanilla']:
                    self.logger.info(message)
                else:
                    self.logger.warning(message)
                continue
            if isinstance(sql_commands, str):
                message = f'Likely empty xml, this was the value found in table element: {sql_commands}. File: {xml_file}.'
                if job_type in ['DLC', 'vanilla']:
                    self.logger.info(message)
                else:
                    self.logger.warning(message)
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
                    elif command == 'InsertOrIgnore':
                        if not isinstance(details, list):
                            details = [details]
                        for record in details:
                            columns, values = [i for i in record], [j for j in record.values()]
                            sql_statements.append({"type": "INSERT IGNORE", "table": table_name, "columns": columns, "values": values})
                    elif command == '#text':
                        self.logger.info(f'Firaxis typo lol on {xml_file}')
                    else:
                        self.logger.warning(f'unknown command: {command}')
        sql_strings = self.convert_to_sql(sql_statements)
        return sql_strings

    def convert_to_sql(self, statements):
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
                self.logger.warning(msg)
                replace_into_script = sql_script.replace('INSERT', 'INSERT OR REPLACE')
                try:
                    cursor.execute(replace_into_script)
                except Exception as e:
                    print(e)
                    table_name = replace_into_script.split(' (')[0].split('INSERT OR REPLACE INTO ')[1]
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    for column in columns:
                        print(f"Column ID: {column[0]}, Name: {column[1]}, Type: {column[2]}, Not Null: {column[3]}, Default Value: {column[4]}, Primary Key: {column[5]}")



        else:
            msg = f"Unique constraint fail but row not found, really an update? {filename}."
            self.logger.critical(msg)
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
            self.logger.critical(msg)
            self.errors.append(msg)

    def test_db(self, file_list, dlc_map, is_base):
        db_connection = sqlite3.connect(self.db_path)
        is_vanilla, is_dlc, is_mod, do_adj = False, False, False, False
        known_script_errors = ['INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("NO_GOVERNMENTBONUS");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_WONDER_CONSTRUCTION");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_COMBAT_EXPERIENCE");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_GREAT_PEOPLE");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_ENVOYS");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_FAITH_PURCHASES");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_GOLD_PURCHASES");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_UNIT_PRODUCTION");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_OVERALL_PRODUCTION");', 'INSERT INTO GovernmentBonusNames (GovernmentBonusType) VALUES ("GOVERNMENTBONUS_DISTRICT_PROJECTS");']
        if dlc_map == ['Vanilla']:
            is_vanilla = True
            with open('lost_sql_defines.sql', 'r') as file:
                lines = file.readlines()
        elif is_base:
            with open('lost_sql_defines_DLC.sql', 'r') as file:
                lines = file.readlines()
            is_dlc = True
        else:
            is_mod = True
        def make_hash(value):
            h = hash(value)
            h = h % (2 ** 32)
            if h >= 2 ** 31:
                h -= 2 ** 32
            return h
        db_connection.create_function("Make_Hash", 1, make_hash)

        known_errors = []
        unique_fk_errors = set()
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA defer_foreign_keys = ON;")
        db_connection.execute('BEGIN')
        errors = []
        file_list_tuples = [(filename, sql_scripts) for filename, sql_scripts in file_list.items()]
        if is_vanilla:
            file_list_tuples = [file_list_tuples[2], file_list_tuples[0], file_list_tuples[1], ('dummy', lines)] + file_list_tuples[3:]
        if is_dlc:
            with open('adjacencyYields.sql', 'r') as file:
                adjacencies = file.readlines()
            file_list_tuples = [('dummy', lines)] + file_list_tuples + [('dummy2', adjacencies)]
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
                        str_errors = str(e)
                        commands_used = self.individual_line_run(sql_script, cursor, filename)
                        if len(commands_used) == 0:
                            print(f'Errored on {filename}, but no commands found in SQL file')
                        continue
                    self.unique_error_handler(e, filename, cursor, sql_script)

        try:
            prior_fk_errors = check_foreign_keys(cursor, file_list, True)
            unique_fk_errors.update(prior_fk_errors)
            if is_dlc:
                to_fix = [i for i in prior_fk_errors]
                not_collects_not_effects = [i for i in set(to_fix) if 'EFFECT' not in i[1] and 'COLLECTION' not in i[1]]
                fixes = {}
                for i in set(to_fix):
                    kind = i[1]
                    if i[0] not in fixes:
                        fixes[i[0]] = []
                    if i[0] == 'Kinds.Kind ':
                        fixes[i[0]].append(f"\nINSERT INTO Kinds(Kind) VALUES('{kind}');")
                    elif 'EFFECT' in kind:
                        fixes[i[0]].append(f"\nINSERT INTO Types(Type, Kind) VALUES('{i[1]}', 'KIND_EFFECT');")
                    elif 'COLLECTION' in kind:
                        fixes[i[0]].append(f"\nINSERT INTO Types(Type, Kind) VALUES('{i[1]}', 'KIND_COLLECTION');")
                    elif 'REQUIREMENT_' in kind:
                        fixes[i[0]].append(f"\nINSERT INTO Types(Type, Kind) VALUES('{i[1]}', 'KIND_REQUIREMENT');")

                beginning = {}
                beginning['Types.Type '] = '\nINSERT INTO Types(Type, Kind) VALUES'
                beginning['Kinds.Kind '] = f"\nINSERT INTO Kinds(Kind) VALUES"
                if not is_dlc:
                    with open('lost_sql_defines.sql', 'w') as file:
                        full_str = ''
                        for i in fixes.items():
                            # full_str += beginning[i[0]]
                            for j in i[1]:
                                full_str += j
                            full_str = full_str[:-1]
                            full_str += ';'
                        file.write(full_str)
            if len(prior_fk_errors) > 0:
                self.logger.warning(f'FOREIGN KEY CONSTRAINT ERRORS: {len(prior_fk_errors)}')
            db_connection.commit()

        except sqlite3.IntegrityError as e:
            self.logger.debug(f"Integrity error occurred: {e}")
            fk_ch = check_foreign_keys(cursor, file_list)
            db_connection.rollback()
        fk_errors = check_foreign_keys(cursor, file_list)
        current_state = self.check_state(cursor)
        self.errors += fk_errors
        cursor.close()
        if len(fk_errors) > 0:
            self.logger.warning(fk_errors)
        self.show_errors()

    def load_files(self, jobs, job_type):
        jobs_short_ref = [('/'.join(i.split('/')[-3:]), i) for i in jobs]
        missed_files = []
        sql_statements = {}
        ensure_ordered_sql = []
        firaxis_fails = ['RulersOfTheSahara_RemoveData.xml', 'JuliusCaesar_Districts.xml', 'JuliusCaesar_Modifiers.xml', 'JuliusCaesar_Units.xml', 'CatherineDeMedici_Modifiers.xml']
        known_mod_fails = ['871861883/custom.sql', '871861883/custom.xml', 'HiddenAgendas/Tourist.sql'] # YnAMP and BearsAgendas
        known_fails = firaxis_fails + known_mod_fails
        for short_name, db_file in jobs_short_ref:
            existing_short = [i[0] for i in ensure_ordered_sql if i[0] == short_name]
            if len(existing_short) > 0:
                error_msg = f'Duplicate file: {short_name} already in list:\n2nd ref: {db_file}. Existing ref: {existing_short}'
                if job_type in ['DLC', 'vanilla']:
                    self.logger.info(error_msg)
                else:
                    self.logger.warning(error_msg)
            if db_file.endswith('.xml') and not any(i in db_file for i in known_fails):
                statements = self.convert_xml_to_sql(db_file, job_type)
                if isinstance(statements, str):
                    missed_files.append(short_name)
                    if job_type in ['DLC', 'vanilla']:
                        self.logger.info(statements)
                    else:
                        self.logger.warning(statements)
                    continue
                sql_statements[short_name] = self.convert_xml_to_sql(db_file, job_type)
                ensure_ordered_sql.append((short_name, sql_statements[short_name]))
            if db_file.endswith('.sql') and not any(i in db_file for i in known_fails):
                try:
                    with open(db_file, 'r') as file:
                        sql_contents = file.read()
                except UnicodeDecodeError as e:
                    print(f'Bad unicode, trying windows-1252: {e}')
                    with open(db_file, 'r', encoding='windows-1252') as file:
                        sql_contents = file.read()
                comment_cleaned = re.sub(r'--.*?\n', '', sql_contents, flags=re.DOTALL)
                sql_statements[short_name] = sqlparse.split(comment_cleaned)
                ensure_ordered_sql.append((short_name, sql_statements[short_name]))

        # check that order is maintained in dict (should after python 3.7 ish)
        """if not [i for i in sql_statements] == [j[1] for j in ensure_ordered_sql]:
            missing = [k for k in ensure_ordered_sql if [i[0] for i in ensure_ordered_sql].count(k[0])>1]           # base files repeat removing data with the same file in some DLC
            concat_missing = set([(k[0], '\n'.join(k[1])) for k in missing])        # checks for dupes
            if not len(missing) / 2 == len(concat_missing):
                raise Exception('SQL Dict is not ordered and cant be trusted for modding operations. ')"""
        return sql_statements, missed_files

    def build_vanilla_db(self):
        files = [f for f in glob.glob(f'{self.civ_install}/Assets/Base/Assets/Gameplay/Data/*.xml', recursive=True)]
        schema = [f for f in glob.glob(f'{self.civ_install}/Assets/Base/Assets/Gameplay/Data/Schema/*', recursive=True)]
        database_entries = [{'component': 'Schema', 'full_files': schema}, {'component': 'Data', 'full_files': files}]
        jobs = []
        [jobs.extend(i['full_files']) for i in database_entries]
        return jobs

    def prepare_db(self):
        original_db = 'DebugGameplay_working.sqlite'
        shutil.copyfile(original_db, self.db_path)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table[0]}")
        conn.commit()
        conn.close()

    def check_state(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        return tables

    def unique_error_handler(self, e, filename, cursor, sql_script):
        if 'UNIQUE' in str(e):
            check_exists_script, update_dict = full_matcher_sql(sql_script)
            cursor.execute(check_exists_script)
            result = cursor.fetchall()
            if len(result) > 1:
                self.logger.info(f'Skipped inserting duplicate for {filename}:\n {sql_script}')
            elif len(result) == 0:
                self.logger.info(f'Skipped inserting duplicate for {filename}:\n, Unique, but the value wasnt found')
            else:
                if result[0][0] == list(update_dict.values())[0]:
                    self.logger.info(
                        f'Skipped inserting duplicate as value is already set correctly for {filename}: {sql_script}')
                else:
                    self.should_be_replace(cursor, sql_script, update_dict, filename, e)
        elif sql_script in self.known_errors_list:
            self.logger.info(f'Skipping known error on {sql_script}')
        elif str(e) == 'FOREIGN KEY constraint failed':
            self.logger.info(f'FOREIGN KEY CONSTRAINT fail.')
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
                    self.logger.warning(e)
                    self.errors_out['syntax'].append((filename, e, command))
                    continue
                if 'no such table' in string_error:
                    self.logger.warning(e)
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
                    print(f'{error} caused by:\n{command}')
                    self.errors_out['found_command'].append(f'{error} caused by:\n{command} in {filename}')
                else:
                    print(f'could not find values of command for {command} in {filename}')
                    self.errors_out['mystery'].append(command)
        return commands

    def kill_df(self):
        os.remove(self.db_path)

    def show_errors(self):
        fails = 0
        for key, val in self.errors_out.items():
            if len(val) == 0:
                continue
            print(key)
            for error in val:
                print(error)
                fails += 1
        if fails == 0:
            print('no errors')






def get_query_details(script):
    table_name_pattern = r'\b(\w+)\s*\('
    columns_pattern = r'\(([^)]+)\)'
    values_pattern = r'VALUES\s*\((.*?)\);$'
    script_ = script.replace('"', "'")
    search = re.findall(table_name_pattern, script_)
    if len(search) > 0:
        table_name = search[0]
        columns = re.search(columns_pattern, script_)[1].split(',')
        values = re.search(values_pattern, script_)[1].split("',")
    else:
        split_space = script_.split(' ')
        if len(split_space) > 1:
            table_name = split_space[1]

    values = [i.strip(" '").replace("'", '"') for i in values]
    wheres = {col.strip(): val for col, val in zip(columns, values)}
    return table_name, wheres


def full_matcher_sql(sql_script):
    table_name, wheres = get_query_details(sql_script)
    wheres.pop('SQL', None)  # ughhh, its hard to parse metaSQL and quotation marks
    equals_format = [f"{col} = '{val.strip()}'" for col, val in wheres.items()]
    assign_vals = "\n AND ".join(equals_format)
    script = f"SELECT *\n FROM {table_name}\n WHERE " + assign_vals + ";"
    return script, {i: j.strip("'").strip('"') for i, j in wheres.items()}

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


def check_foreign_keys(cursor, file_list, do_complex=False):
    fk_errors = []
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    if len(violations) == 0:
        return []
    tables_violated = set(i[0] for i in violations)
    table_fks = {}
    table_primary_keys = {}

    for table_name in tables_violated:
        if table_name in table_fks:
            continue
        table_fks[table_name], table_primary_keys[table_name] = foreign_key_check(cursor, table_name)

    for table_name, row_id, foreign_table, fk_constraint_index in violations:
        constraint = table_fks[table_name][fk_constraint_index]
        msg = foreign_key_pretty_notify(cursor, table_name, row_id, constraint, table_primary_keys[table_name],
                                        file_list, do_complex)
        fk_errors.append(msg)

    return fk_errors


def foreign_key_check(cursor, table_name):
    cursor.execute(f"PRAGMA foreign_key_list({table_name});")
    fk_constraints = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]
    labeled_constraints = [{i: j for i, j in zip(col_names, k)} for k in fk_constraints]
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns_info = cursor.fetchall()
    primary_keys = [column_info[1] for column_info in columns_info if column_info[5] > 0]
    return labeled_constraints, primary_keys


def foreign_key_pretty_notify(cursor, table_name, row_id, constraint, table_pk, file_list, do_complex):
    cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = {row_id}")
    record = cursor.fetchone()
    record_col_names = [description[0] for description in cursor.description]
    record_ = {key: val for key, val in zip(record_col_names, record)}
    record_pk = {key: record_[key] for key in table_pk if key in record_}
    pk_set = [(i, j) for i, j in record_pk.items()]
    if not do_complex:
        message = (f"ERROR: {table_name} record {record_pk} has Foreign Key: {constraint['from']} = "
            f"{record_[constraint['from']]} but parent table {constraint['table']} lacks {constraint['to']} = "
            f"{record_[constraint['from']]}.")
        return message
    intermediate = file_list
    for pk_col, pk_val in pk_set:
        intermediate = {key: val for key, val in intermediate.items() if any(str(pk_val) in item for item in val)}
    found_pk_use = {key: [(idx, item) for idx, item in enumerate(val) if all(str(j_pk) in item for col, j_pk in pk_set)] for key, val in intermediate.items()}
    sql_objects = [[name] + [sqlparse.parse(j[1])[0] for j in i] for name, i in found_pk_use.items()]
    sql_objects_tuple = [(sublist[0], element) for sublist in sql_objects for element in sublist if sublist[0] != element]
    table = [[i[0], "".join([j.normalized for j in i[1].tokens if type(j) != sqlparse.sql.Comment and j.ttype != sqlparse.tokens.Token.Comment.Multiline])] for i in sql_objects_tuple if i[1].is_group] # parse out comments
    table = [i for i in table if len(i[1]) > 0 and '--' not in i[1]]
    table = [i for i in table if 'CREATE' not in i[1] and not ('ALTER' in i[1] and 'ADD' in i[1])]          # filtering out CREATE TRIGGER for now
    table = [i for i in table if 'WITH' not in i[1] and '/*' not in i]           # filters poki's weird WITH
    if len(table) > 200:
        return f'There are {len(table)} records matching on {pk_set} for error. We aint doing that'
    for i in table:         # later should we make a map of all the DDL constraints mapped? so can use column instead of value search
        i.append(i[1].split('(')[0].replace('\t', ' ').replace('INSERT INTO', '').replace('UPDATE', '').replace('DELETE FROM', '')
                 .replace('INSERT OR REPLACE INTO', '').replace('INSERT OR IGNORE INTO', '').replace('OR IGNORE', '').replace('DROP TABLE' ,'')
                 .replace('REPLACE INTO', '').split('SET')[0].split('WHERE')[0].split('VALUES')[0].split('SELECT')[0]
                 .strip())
    possible_culprits = []
    for i in table:
        try:
            cursor.execute(f"PRAGMA table_info({i[2]})")
        except Exception as e:
             continue
        columns_info = cursor.fetchall()
        primary_keys = [column[1] for column in columns_info if column[5] == 1]
        for pk in primary_keys:
            if pk == pk_col:
                possible_culprits.append(i)
    culprits = []
    for i in possible_culprits:
        line_list = i[1].split('\n')
        line_indices = [idx + 1 for idx, i in enumerate(line_list) if pk_val in i]
        culprits.append((f'{i[0]}: Lines:', line_indices))
    message = (f"ERROR: {table_name} record {record_pk} has Foreign Key: {constraint['from']} = "
            f"{record_[constraint['from']]} but parent table {constraint['table']} lacks {constraint['to']} = "
            f"{record_[constraint['from']]}. Likely cause: {culprits}")
    if 'YieldChangeId' not in record_col_names:         # the yieldAdjacency issues
        print(message)
    return (message, constraint['table'], constraint['to'], record_[constraint['from']])

def main():
    checker = SqlChecker()
    config = json.load(open('config.json', 'r'))
    if config.get('USE_EXISTING', False):
        checker.setup_db_existing()
    else:
        checker.setup_db_new()
    database_entries, load_fails = checker.parse_mod_log()
    modded_short, modded, dlc, dlc_files = [], [], [], []
    full_dump = []
    dashs = '--------------------'
    if config.get('USE_EXISTING', False):
        [modded.extend(i['full_files']) for i in database_entries if 'Mods' in i['mod_dir'] or 'workshop' in i['mod_dir']]     # later do change to environ set mod directory
        sql_statements_mods, missed_mods = checker.load_files(modded, 'Mod')
        [full_dump.extend([dashs + key + dashs] + val) for key, val in sql_statements_mods.items()]
    else:
        [dlc.extend(i['files']) for i in database_entries if 'DLC' in i['mod_dir']]
        [dlc_files.extend(i['full_files']) for i in database_entries if 'Mods' not in i['mod_dir'] and 'workshop' not in i['mod_dir']]
        sql_statements_dlc, missed_dlc = checker.load_files(dlc_files, 'DLC')
        missed_sql_statements = [i for i in dlc if i not in ["/".join(j.split('/')[1:]) for j in sql_statements_dlc]]

    with open('sql_statements.log', 'w') as file:
        file.write("\n".join(full_dump))

    if config.get('USE_EXISTING', False):
        checker.test_db(sql_statements_mods, modded_short, False)
    else:
        checker.prepare_db()
        vanilla_jobs = checker.build_vanilla_db()
        vanilla_sql_statements, missed_vanilla = checker.load_files(vanilla_jobs, 'vanilla')
        checker.test_db(vanilla_sql_statements, ['Vanilla'], True)
        checker.test_db(sql_statements_dlc, dlc, True)
        dlc_sql_dump = [j for i in sql_statements_dlc.values() for j in i]
        silly_parse_error = [j for j in dlc_sql_dump if ',;' in j] + [j for j in dlc_sql_dump if ', ;' in j]
        if len(silly_parse_error) > 0:
            print(f'had some ,; errors: {silly_parse_error}')

    checker.kill_df()
    #  need test that runs only unmodded to verify database integrity.


if __name__ == '__main__':
    main()
