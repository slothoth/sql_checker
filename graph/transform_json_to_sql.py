import json
from graph.db_spec_singleton import (db_spec, req_arg_type_list_map, mod_arg_type_list_map, req_arg_defaults,
                                     effect_arg_defaults, modifier_argument_info, requirement_argument_info)
from schema_generator import SQLValidator

excludes = ['toggle_extra', 'table_name']


def transform_json(json_filepath):
    error_string = ''
    with open(json_filepath) as f:
        data = json.load(f)
    sql_code = []
    for node_id, val in data['nodes'].items():
        custom_properties = val['custom']
        table_name = val.get('table_name', custom_properties['table_name'])
        custom_properties = SQLValidator.normalize_node_bools(custom_properties, table_name)
        if table_name == 'ReqEffectCustom':
            sql_code, error_string = req_custom_transform(data, custom_properties, node_id, sql_code, error_string)

        elif table_name == 'GameEffectCustom':
            sql_code, error_string = effect_custom_transform(custom_properties, sql_code, error_string)

        else:
            sql, error_string = transform_to_sql(custom_properties, table_name, error_string)
            sql_code.append(sql)

    if len(error_string) > 0:
        return error_string

    return [i + '\n' for i in sql_code]


def req_custom_transform(data, custom_properties, node_id, sql_code, error_string):
    req_id = custom_properties['RequirementId']
    req_type = custom_properties['RequirementType']  # need to change on data level as used in cols dict.
    columns_dict = {k: v for k, v in custom_properties.items() if 'param_' not in k and k not in excludes
                    and k != 'ReqSet'}
    sql, error_string = transform_to_sql(columns_dict, 'Requirements', error_string)
    sql_code.append(sql)
    for param, arg_name in req_arg_type_list_map[req_type].items():
        arg_value = custom_properties.get(param)
        widget_default = req_arg_defaults[req_type][param]  # default checks
        arg_info = requirement_argument_info[req_type]['Arguments'][arg_name]
        arg_default = arg_info['DefaultValue']
        is_required = bool(arg_info.get('Required', 0))
        if arg_default == '' or arg_default is None:
            if arg_value != widget_default:  # if no default check against widget default
                sql, error_string = transform_to_sql({'RequirementId': req_id, 'Name': arg_name,
                                                      'Value': arg_value},
                                                     'RequirementArguments', error_string)
                sql_code.append(sql)
            else:
                if is_required:
                    req_arg_error = (f'\nERROR for reqType {req_type}  and arg {arg_name} there was no changed'
                                     f' value, was required and no known default')
                    print(req_arg_error)
                    error_string += req_arg_error

        else:
            if arg_value != arg_default:
                sql, error_string = transform_to_sql({'RequirementId': req_id, 'Name': arg_name,
                                                      'Value': arg_value}, 'RequirementArguments', error_string)
                sql_code.append(sql)

    return sql_code, error_string


def effect_custom_transform(custom_properties, sql_code, error_string):
    no_arg_params = {k: v for k, v in custom_properties.items() if 'param_' not in k and k not in excludes}
    effect_type = no_arg_params['EffectType']
    collection_type = no_arg_params['CollectionType']
    modifier_type = no_arg_params['ModifierType']  # DynamicModifiers
    sql, error_string = transform_to_sql({'ModifierType': modifier_type, 'CollectionType': collection_type,
                                          'EffectType': effect_type}, 'DynamicModifiers', error_string)
    sql_code.append(sql)
    sql, error_string = transform_to_sql({'Type': modifier_type, 'Kind': 'KIND_MODIFIER'},
                                         'Types', error_string)
    sql_code.append(sql)

    # do requirementSets, to handle nesting and multiple connections to different requirementSets and ReqCustom
    rename_mapper = {'SubjectReq': 'SubjectRequirementSetId', 'OwnerReq': 'OwnerRequirementSetId'}
    reqset_used = {}
    reqset_info = no_arg_params['RequirementSetDict']
    for req_object_type, reqset_object_info in reqset_info.items():
        if len(reqset_object_info['reqs']) > 0:
            reqset_used[req_object_type] = rename_mapper[req_object_type]
            reqset_name = no_arg_params[req_object_type]  # make reqset
            reqset_type = reqset_object_info['type']
            sql, error_string = transform_to_sql({'RequirementSetId': reqset_name,
                                                  'RequirementSetType': reqset_type},
                                                 'RequirementSets', error_string)
            sql_code.append(sql)
            for req in reqset_object_info['reqs']:
                req_id = req
                if isinstance(req, dict):
                    print('nesting req')
                    nested_reqset = req['reqset']
                    req_name = f'REQ_IS_MET_{nested_reqset}'

                    sql, error_string = transform_to_sql({'RequirementId': req_name,
                                                          'RequirementType': 'REQUIREMENT_REQUIREMENTSET_IS_MET'},
                                                         'Requirements', error_string)
                    sql_code.append(sql)

                    sql, error_string = transform_to_sql({'RequirementId': req_name,
                                                          'Name': 'REQUIREMENT_REQUIREMENTSET_IS_MET',
                                                          'Value': nested_reqset},
                                                         'RequirementArguments', error_string)
                    sql_code.append(sql)

                    req_id = req_name

                sql, error_string = transform_to_sql({'RequirementSetId': reqset_name,
                                                      'RequirementId': req_id},
                                                     'RequirementSetRequirements', error_string)
                sql_code.append(sql)

    mod_cols = db_spec.node_templates['Modifiers']['all_cols']  # Modifiers
    columns_dict = {reqset_used.get(k, k): v for k, v in no_arg_params.items() if reqset_used.get(k, k) in mod_cols}
    sql, error_string = transform_to_sql(columns_dict, 'Modifiers', error_string)
    sql_code.append(sql)

    for param, arg_name in mod_arg_type_list_map[effect_type].items():  # ModifierArguments
        arg_value = custom_properties.get(param)
        columns_dict = {'ModifierId': no_arg_params['ModifierId'], 'Name': arg_name, 'Value': arg_value}
        sql, error_string = transform_to_sql(columns_dict, 'ModifierArguments', error_string)
        sql_code.append(sql)  # TODO not covering Extra and Extra2, but then we arent in node either

    template = db_spec.node_templates['ModifierStrings']  # ModifierStrings
    mod_string_cols = template['all_cols']
    columns_dict = {k: v for k, v in no_arg_params.items() if k in mod_string_cols}
    if not any([v == '' for k, v in columns_dict.items() if k in template['primary_texts']]):
        sql, error_string = transform_to_sql(columns_dict, 'ModifierStrings', error_string)
        sql_code.append(sql)

    return sql_code, error_string


def transform_to_sql(ui_dict, table_name, error_string):
    if table_name == 'Types':  # deal with Hashed default
        if 'Hash' in ui_dict:
            del ui_dict['Hash']
    if table_name in ['ModifierArguments', 'RequirementArguments']:
        ui_dict['Value'] = str(ui_dict['Value'])
    sql_command = SQLValidator.convert_ui_dict_to_text_sql(ui_dict, table_name)
    return f"{sql_command};", error_string


def old_transform_to_sql(columns_dict, table_name, error_string):

    template = db_spec.node_templates[table_name]
    columns = [key for key in columns_dict.keys()]
    values = [val for val in columns_dict.values()]

    # transform bools into 0 or 1
    values = ['1' if isinstance(val, bool) and val else val for val in values]
    values = ['0' if isinstance(val, bool) and not val else val for val in values]
    # transform '' to NULL?
    values = ['NULL' if val == '' else val for val in values]
    # get rid of weird double quotes like '"NO_RESOURCECLASS"'
    values = [val.replace('"', '') if isinstance(val, str) else val for val in values]

    # lint sql
    pk_satisfied = set(template['primary_keys']).issubset(columns)  # all primary keys present
    # primary texts present. Those that cannot be NULL, and have no default
    req_fields_no_default_satisfied = set(template['primary_texts']).issubset(columns)

    if not pk_satisfied:
        missing_values = list(set(columns) - set(template['primary_keys']))
        error_string += f'Missing Primary Key for {table_name}: {missing_values}\n'

    if not req_fields_no_default_satisfied:
        missing_values = list(set(columns) - set(template['primary_texts']))
        error_string += f'Missing Required Columns for {table_name}: {missing_values}\n'

    if table_name == 'Types':  # deal with Hashed default
        if 'Hash' in columns:
            hash_index = columns.index('Hash')
            columns.remove('Hash')
            values.remove(values[hash_index])
    columns = ", ".join(columns)
    values = [i.replace('"', "'") if isinstance(None, str) and '"' in i else i for i in values] # deals with added quotes
    values = ", ".join(f'"{value}"' if isinstance(value, str) else str(value) for value in values)
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
    sql = sql.replace('"', "'").replace("'NULL'", "NULL")

    return sql, error_string


criteria_names = {
    'ALWAYS': 'always',
    'AGE_ANTIQUITY': 'antiquity-age-current',
    'AGE_EXPLORATION': 'exploration-age-current',
    'AGE_MODERN': 'modern-age-current'
}


def make_modinfo(graph):
    meta_info = graph.property('meta')
    mod_name = meta_info['Mod Name']
    mod_description = meta_info['Mod Description']
    mod_author = meta_info['Mod Author']
    mod_uuid = meta_info['Mod UUID']
    mod_action_id = meta_info['Mod Action']
    mod_age = meta_info['Age']
    mod_age_criteria = criteria_names[mod_age]

    with open('resources/template.modinfo', 'r') as f:
        template = f.read()
    template = template.replace('$UUID$', mod_uuid)
    template = template.replace('$MODNAME$', mod_name)
    template = template.replace("$MOD_DESCRIPTION$", mod_description)
    template = template.replace("$YOUR_NAME$", mod_author)
    template = template.replace("$actionID$", mod_action_id)
    template = template.replace("$actionCriteria$", mod_age_criteria)
    return template, mod_name
