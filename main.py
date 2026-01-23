import sys
from PyQt5.QtWidgets import QApplication

from graph.node_controller import NodeEditorWindow


class SqlChecker():
    def __init__(self):
        self.logger = logging.getLogger('SqlChecker')
        self.logger.setLevel(logging.WARNING)
        self.granularity = 'statement'
        self.errors = []
        config = json.load(open('config.json', 'r'))
        self.log_folder = os.environ.get('CIV_LOG', f"{config['CIV_USER']}/Firaxis Games/Sid Meier's Civilization VI/Logs")
        self.civ_install = os.environ.get('CIV_INSTALL', config['CIV_INSTALL'])
        self.workshop_folder = os.environ.get('WORKSHOP_FOLDER', config['WORKSHOP_FOLDER'])
        self.local_mods_folder = os.environ.get('LOCAL_MODS_FOLDER',
                                           f"{config['CIV_USER']}/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Mods/")
        if not os.path.exists('DebugGameplay_working.sqlite'):
            copy_db_path = f"{config['CIV_USER']}/Firaxis Games/Sid Meier's Civilization VI/Cache/DebugGameplay.sqlite"
            shutil.copy(copy_db_path, 'DebugGameplay.sqlite')
        shutil.copy('DebugGameplay.sqlite', 'DebugGameplay_working.sqlite')  # restore backup db
        self.db_path = 'DebugGameplay_working.sqlite'

        self.known_errors_list = ["UPDATE AiFavoredItems SET Value = '200' WHERE ListType = 'CatherineAltLuxuries' "
                                  "AND PseudoYieldType = 'PSEUDOYIELD_RESOURCE_LUXURY';"]
        self.known_repeats = ['RulersOfEngland/Data/RulersOfEngland_RemoveData.xml', 'GreatNegotiators/Data/GreatNegotiators_RemoveData.xml',
                              'GreatNegotiators/Data/GreatNegotiators_RemoveData.xml']
        # PseudoYieldType isnt a column, it should've been Item but Fireaxis is silly

    def parse_mod_log(self):
        filepath_base_game_infos = []
        filepath_dlc_mod_infos = [f for f in glob.glob(f'{self.civ_install}/**/*.modinfo*', recursive=True)]
        filepath_mod_mod_infos = ([f for f in glob.glob(f'{self.workshop_folder}/**/*.modinfo*', recursive=True)] +
                                  [f for f in glob.glob(f'{self.local_mods_folder}/**/*.modinfo*', recursive=True)])
        filepath_mod_infos = filepath_dlc_mod_infos + filepath_mod_mod_infos
        uuid_map = {ET.parse(filepath).getroot().attrib['id']: "/".join(filepath.split('/')[:-1]) for filepath in
                    filepath_mod_infos}
        with open(self.log_folder + '/Modding.log', 'r') as file:
            logs = file.readlines()
        uuid_pattern = re.compile(
            r'\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}\b')
        file_pattern = re.compile(r'Loading (.*?)\n')
        component_pattern = re.compile(r'Applying Component - (.*?) \(UpdateDatabase\)')
        uuid_component_pattern = re.compile(r' \* (.*?) \(UpdateDatabase\)')
        dupes = []
        database_entries = []
        for idx, i in enumerate(logs):
            if '(UpdateDatabase)' in i and 'Applying Component' not in i:
                if i not in dupes:
                    database_entries.append({'text': i, 'line': idx})
                else:
                    dupes.append({'text': i, 'line': idx})
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

    def convert_xml_to_sql(self, xml_file):
        sql_statements = []
        xml_ = read_xml(xml_file)
        if not xml_:
            raise AttributeError(f"{xml_file} was empty...")
        xml_ = xml_.get('GameInfo', xml_.get('GameData'))
        for table_name, sql_commands in xml_.items():
            if sql_commands is None:
                self.logger.warning(f'None value in SQL command. No commands for table {table_name}.')
                continue
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
        return sql_strings

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
                cursor.execute(replace_into_script)

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

    def test_db(self, file_list, dlc_map):
        db_connection = sqlite3.connect(self.db_path)

        def make_hash(value):
            h = hash(value)
            h = h % (2 ** 32)
            if h >= 2 ** 31:
                h -= 2 ** 32
            return h
        db_connection.create_function("Make_Hash", 1, make_hash)

        cursor = db_connection.cursor()

        unique_fk_errors = set()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA defer_foreign_keys = ON;")
        db_connection.execute('BEGIN')
        for filename, sql_scripts in file_list.items():

            for idx, sql_script in enumerate(sql_scripts):
                try:
                    cursor.execute(sql_script)
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
                            self.should_be_replace(cursor, sql_script, update_dict, filename, e)

                    elif sql_script in self.known_errors_list:
                        self.logger.info(f'Skipping known error on {sql_script}')
                    elif str(e) == 'FOREIGN KEY constraint failed':
                        self.logger.info(f'FOREIGN KEY CONSTRAINT fail.')
                        table_name = sql_script.split('(')[0].split(' ')[-2]
                        labeled_constraints, primary_keys = foreign_key_check(cursor, table_name)
                        foreign_key_pretty_notify(cursor,table_name,uh, labeled_constraints, primary_keys)
                    else:
                        self.row_id_fix(cursor, sql_script)
        try:
            prior_fk_errors = check_foreign_keys(cursor)
            unique_fk_errors.update(prior_fk_errors)
            self.logger.warning(f'FOREIGN KEY CONSTRAINTS: {len(prior_fk_errors)}')
            #self.logger.warning(f'{filename} added to db with {len(prior_fk_errors)} FOREIGN KEY Constraint errors.')
            db_connection.commit()

        except sqlite3.IntegrityError as e:
            self.logger.debug(f"Integrity error occurred: {e}")
            db_connection.rollback()
        fk_errors = check_foreign_keys(cursor)
        self.errors += fk_errors
        cursor.close()
        #print(errors)

    def load_files(self, jobs):
        jobs_short_ref = [('/'.join(i.split('/')[-3:]), i) for i in jobs]
        missed_files = []
        sql_statements = {}
        ensure_ordered_sql = []
        for short_name, db_file in jobs_short_ref:
            existing_short = [i[0] for i in ensure_ordered_sql if i[0] == short_name]
            if len(existing_short) > 0:
                self.logger.warning(f'Duplicate file: {short_name} already in list:\n2nd ref: {db_file}. Existing ref: '
                                    f'{existing_short}')
                if '':
                    print('')
            if db_file.endswith('.xml'):
                try:
                    sql_statements[short_name] = self.convert_xml_to_sql(db_file)
                    ensure_ordered_sql.append((short_name, sql_statements[short_name]))
                except AttributeError as e:
                    print(e)
                    missed_files.append(short_name)
                    continue
            if db_file.endswith('.sql'):
                try:
                    with open(db_file, 'r') as file:
                        sql_contents = file.read()
                except UnicodeDecodeError as e:
                    print(f'Bad unicode, trying windows-1252: {e}')
                    with open(db_file, 'r', encoding='windows-1252') as file:
                        sql_contents = file.read()
                sql_statements[short_name] = sqlparse.split(sql_contents)
                ensure_ordered_sql.append((short_name, sql_statements[short_name]))

        # check that order is maintained in dict (should after python 3.7 ish
        if not [i for i in sql_statements] == [j[1] for j in ensure_ordered_sql]:
            missing = [k for k in ensure_ordered_sql if [i[0] for i in ensure_ordered_sql].count(k[0])>1]           # base files repeat removing data with the same file in some DLC

            raise Exception('SQL Dict is not ordered and cant be trusted for modding operations')
        return sql_statements, missed_files

    def build_vanilla_db(self):
        files = [f for f in glob.glob(f'{self.civ_install}/Assets/Base/Assets/Gameplay/Data/*.xml', recursive=True)]
        schema = [f for f in glob.glob(f'{self.civ_install}/Assets/Base/Assets/Gameplay/Data/Schema/*', recursive=True)]
        database_entries = [{'component': 'Schema', 'full_files': schema}, {'component': 'Data', 'full_files': files}]
        jobs = []
        [jobs.extend(i['full_files']) for i in database_entries]
        return jobs

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


def check_foreign_keys(cursor):
    fk_errors = []
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    tables_violated = set(i[0] for i in violations)
    table_fks = {}
    table_primary_keys = {}

    for table_name in tables_violated:
        if table_name in table_fks:
            continue
        table_fks[table_name], table_primary_keys[table_name] = foreign_key_check(cursor, table_name)

    for table_name, row_id, foreign_table, fk_constraint_index in violations:
        constraint = table_fks[table_name][fk_constraint_index]
        msg = foreign_key_pretty_notify(cursor, table_name, row_id, constraint, table_primary_keys[table_name])
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


def foreign_key_pretty_notify(cursor, table_name, row_id, constraint, table_pk):
    cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = {row_id}")
    record = cursor.fetchone()
    record_col_names = [description[0] for description in cursor.description]
    record_ = {key: val for key, val in zip(record_col_names, record)}
    record_pk = {key: record_[key] for key in table_pk if key in record_}
    return (f"ERROR: {table_name} record {record_pk} has Foreign Key: {constraint['from']} = "
            f"{record_[constraint['from']]} but parent table {constraint['table']} lacks {constraint['to']} = "
            f"{record_[constraint['from']]}.")


def main():
    checker = SqlChecker()
    # get base game entries.
    database_entries = checker.parse_mod_log()
    dlc = []
    [dlc.extend(i['files']) for i in database_entries if 'DLC' in i['mod_dir']]
    modded = []
    modded = [modded.extend(i['files']) for i in database_entries if 'DLC' not in i['mod_dir']]         # later do change to environ set mod directory

    jobs = []
    [jobs.extend(i['full_files']) for i in database_entries]
    sql_statements, missed_dlc = checker.load_files(jobs)
    missed_sql_statements = [i for i in dlc if i not in ["/".join(j.split('/')[1:]) for j in sql_statements]]
    full_dump = []
    dashs = '--------------------'
    [full_dump.extend([dashs + key + dashs] + val) for key, val in sql_statements.items()]
    with open('sql_statements.log', 'w') as file:
        file.write("\n".join(full_dump))

    vanilla_jobs = checker.build_vanilla_db()
    vanilla_sql_statements, missed_vanilla = checker.load_files(vanilla_jobs)
    checker.test_db(vanilla_sql_statements, ['Vanilla'])
    checker.test_db(sql_statements, dlc)
    #  need test that runs only unmodded to verify database integrity.


if __name__ == '__main__':
    main()
