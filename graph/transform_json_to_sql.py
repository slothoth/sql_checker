import json
from graph.db_spec_singleton import ResourceLoader


db_spec = ResourceLoader()
excludes = ['toggle_extra']


def transform_json(json_file):
    error_string = ''
    with open(json_file) as f:
        data = json.load(f)
    sql_code = []
    for key, val in data['nodes'].items():
        table_name = val['name']
        template = db_spec.node_templates[table_name]
        columns_dict = {key: val for key, val in val['custom'].items() if key not in excludes}
        columns = [key for key in columns_dict.keys()]
        values = [val for val in columns_dict.values()]

        # transform bools into 0 or 1
        values = ['1' if isinstance(val, bool) and val else val for val in values]
        values = ['0' if isinstance(val, bool) and not val else val for val in values]
        # transform '' to NULL?
        values = ['NULL' if val == '' else val for val in values]
        # get rid of weird double quotes like '"NO_RESOURCECLASS"'
        values = [val.replace('"', '') for val in values]

        # lint sql
        pk_satisfied = set(template['primary_keys']).issubset(columns)     # all primary keys present
        # primary texts present. Those that cannot be NULL, and have no default
        req_fields_no_default_satisfied = set(template['primary_texts']).issubset(columns)

        if not pk_satisfied:
            missing_values = list(set(columns) - set(template['primary_keys']))
            error_string += f'Missing Primary Key for {table_name}: {missing_values}\n'

        if not req_fields_no_default_satisfied:
            missing_values = list(set(columns) - set(template['primary_texts']))
            error_string += f'Missing Required Columns for {table_name}: {missing_values}\n'

        columns = ", ".join(columns)
        for idx, i in enumerate(values):
            if i is not None and '"' in i:
                values[idx] = values[idx].replace('"', "'")
        values = ", ".join(f'"{value}"' if isinstance(value, str) else str(value) for value in values)
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
        sql = sql.replace('"', "'").replace("'NULL'", "NULL")
        sql_code.append(sql)

    if len(error_string) > 0:
        return error_string

    # save SQL, then trigger main run model
    with open('resources/main.sql', 'w') as f:
        f.writelines([i + '\n' for i in sql_code])


def start_analysis(main_window):
    main_window.start_analysis(True)
