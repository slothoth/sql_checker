
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
