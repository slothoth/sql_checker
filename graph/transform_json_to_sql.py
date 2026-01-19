import json
from collections import defaultdict

from graph.db_spec_singleton import db_spec
from schema_generator import SQLValidator

excludes = ['toggle_extra', 'table_name']
default_mapper = {'int': 0, 'float': 0.0, 'text': '', 'database': '', 'bool': False}


class FallbackLocNames:
    names = {}

    def get_loc_index(self, table_name):
        if self.names.get(table_name) is None:
            self.names[table_name] = 1
        else:
            self.names[table_name] += 1
        return self.names[table_name]

    def reset_indices(self):
        self.names = {}


fallback_loc = FallbackLocNames()


def transform_json(json_filepath):
    error_string = ''
    fallback_loc.reset_indices()
    with open(json_filepath) as f:
        data = json.load(f)
    sql_code, dict_form_list, loc_dict_list, loc_code = [], [], [], None
    update_nodes = {}
    incompletes_ordered = defaultdict(dict)
    for node_id, val in data['nodes'].items():
        if val['type_'] == 'db.where.WhereNode':
            update_nodes[node_id] = val
        custom_properties = val['custom']
        sql_form = custom_properties.get('sql_form')
        if isinstance(sql_form, str):
            sql_commands = [{'sql': f'{i.strip()};', 'node_source': node_id} for i in sql_form.split(';') if len(i) > 0]
        else:
            sql_commands = [{'sql': i, 'node_source': node_id} for i in sql_form]
        incompletes = {idx: i for idx, i in enumerate(sql_commands) if 'MISSING REQUIRED COLUMNS' in i['sql'] or 'NO COLUMNS PRESENT' in i['sql']}
        completes = [i for i in sql_commands if i not in incompletes.values()]
        sql_code.extend(completes)
        dict_form = custom_properties.get('dict_sql')
        dict_form_list.append({'sql': dict_form, 'node_source': node_id})
        loc_form = custom_properties.get('loc_sql_form', [])
        if len(loc_form) > 0:
            loc_dict_list.extend(loc_form)
        for idx, i in incompletes.items():
            if isinstance(dict_form, list):
                dict_form = dict_form[idx]
            tbl_name = dict_form['table_name']
            primary_key_cols = db_spec.node_templates[tbl_name].get("primary_keys")
            pk_dict = {k: v for k, v in dict_form['columns'].items() if k in primary_key_cols}
            pk_tuple = tuple([v for k, v in pk_dict.items()])
            if len(pk_tuple) == 0 or pk_tuple in incompletes_ordered[tbl_name]:
                key = (i['node_source'], tbl_name)                       # for very broken ones with no pk tuple
            else:
                key = pk_tuple
            incompletes_ordered[tbl_name][key] = i

    if len(error_string) > 0:
        return error_string

    if len(loc_dict_list) > 0:
        loc_code = "INSERT INTO LocalizedText(Language, Tag, Text) VALUES\n"    # doing string manip as no engine for loc
        loc_code = loc_code + ",\n".join(f"('{i['Language']}', '{i['Tag']}', '{i['Text']}')"
                                         for i in loc_dict_list if i['Text'] != '') + ';'

    return sql_code, dict_form_list, loc_code, dict(incompletes_ordered)


def argument_transform(sql_code, error_string, dict_form_list, effect_string, effect_id, custom_properties, type_arg,
                       effect_info, node_id):
    arg_params = custom_properties.get('arg_params', {})
    for arg_name, param in type_arg.items():
        arg_value = custom_properties.get(arg_name)
        if arg_value is None:
            arg_value = arg_params.get(arg_name) if arg_params.get(arg_name) != '' else None
            if arg_value is None:
                continue
        widget_default = default_mapper[param]
        arg_info = effect_info['Arguments'][arg_name]
        arg_default = arg_info['DefaultValue']  # if val is default, we can ignore
        if arg_default is None:
            if widget_default != arg_value:
                sql, dict_form, error_string = transform_to_sql({f'{effect_string}Id': effect_id, 'Name': arg_name,
                                                      'Value': arg_value},
                                                     f'{effect_string}Arguments', error_string)
                sql_code.append(sql)
                dict_form_list.append(dict_form)

        else:
            if arg_value != arg_default:
                sql, dict_form, error_string = transform_to_sql({f'{effect_string}Id': effect_id, 'Name': arg_name,
                                                'Value': arg_value}, f'{effect_string}Arguments', error_string)
                sql_code.append(sql)
                dict_form_list.append(dict_form)


def req_custom_transform(custom_properties, node_id, sql_code, dict_form_list, error_string):
    req_id = custom_properties['RequirementId']
    req_type = custom_properties['RequirementType']  # need to change on data level as used in cols dict.
    if req_type == '':
        error_string += 'Canceled Requirement as no RequirementType to check with'
        return sql_code, dict_form_list, error_string
    columns_dict = {k: v for k, v in custom_properties.items() if 'param_' not in k and k not in excludes
                    and k != 'ReqSet'}
    sql, dict_form, error_string = transform_to_sql(columns_dict, 'Requirements', error_string)
    sql_code.append(sql)
    dict_form_list.append(dict_form)
    if req_type in db_spec.req_type_arg_map:
        argument_transform(sql_code, error_string, dict_form_list, 'Requirement', req_id, custom_properties,
                           db_spec.req_type_arg_map[req_type],
                           db_spec.requirement_argument_info[req_type], node_id=node_id)
    return sql_code, dict_form_list, error_string


def effect_custom_transform(custom_properties, node_id, sql_code, dict_form_list, error_string):
    no_arg_params = {k: v for k, v in custom_properties.items() if 'param_' not in k and k not in excludes}
    effect_type = no_arg_params['EffectType']
    collection_type = no_arg_params['CollectionType']
    modifier_type = no_arg_params['ModifierType']  # DynamicModifiers
    if modifier_type == '' or (collection_type, effect_type) == ('', ''):
        error_string += 'Canceled Effect as no EffectType to check with'
        return sql_code, dict_form_list, error_string
    added_types = [i['sql']['columns']['Type'] for i in dict_form_list if i['sql']['table_name'] == 'Types']
    if modifier_type not in db_spec.dynamic_mod_info and modifier_type not in added_types:      # new ModifierType
        sql, dict_form, error_string = transform_to_sql({'ModifierType': modifier_type,
                                                         'CollectionType': collection_type,
                                              'EffectType': effect_type}, 'DynamicModifiers', error_string)
        sql_code.append(sql)
        dict_form_list.append(dict_form)
        sql, dict_form, error_string = transform_to_sql({'Type': modifier_type, 'Kind': 'KIND_MODIFIER'},
                                             'Types', error_string)
        sql_code.append(sql)
        dict_form_list.append(dict_form)

    # do requirementSets, to handle nesting and multiple connections to different requirementSets and ReqCustom
    rename_mapper = {'SubjectReq': 'SubjectRequirementSetId', 'OwnerReq': 'OwnerRequirementSetId'}
    reqset_used = {}
    reqset_info = no_arg_params['RequirementSetDict']
    for req_object_type, reqset_object_info in reqset_info.items():
        if len(reqset_object_info['reqs']) > 0:
            reqset_used[req_object_type] = rename_mapper[req_object_type]
            reqset_name = no_arg_params[req_object_type]  # make reqset
            reqset_type = reqset_object_info['type']
            sql, dict_form, error_string = transform_to_sql({'RequirementSetId': reqset_name,
                                                  'RequirementSetType': reqset_type},
                                                 'RequirementSets', error_string)
            dict_form_list.append(dict_form)
            sql_code.append(sql)
            for req in reqset_object_info['reqs']:
                req_id = req
                if isinstance(req, dict):
                    nested_reqset = req['reqset']
                    req_name = f'REQ_IS_MET_{nested_reqset}'

                    sql, dict_form, error_string = transform_to_sql({'RequirementId': req_name,
                                                          'RequirementType': 'REQUIREMENT_REQUIREMENTSET_IS_MET'},
                                                         'Requirements', error_string)
                    sql_code.append(sql)
                    dict_form_list.append(dict_form)

                    sql, dict_form, error_string = transform_to_sql({'RequirementId': req_name,
                                                          'Name': 'REQUIREMENT_REQUIREMENTSET_IS_MET',
                                                          'Value': nested_reqset},
                                                         'RequirementArguments', error_string)
                    sql_code.append(sql)
                    dict_form_list.append(dict_form)

                    req_id = req_name

                sql, dict_form, error_string = transform_to_sql({'RequirementSetId': reqset_name,
                                                      'RequirementId': req_id},
                                                     'RequirementSetRequirements', error_string)
                sql_code.append(sql)

    mod_cols = db_spec.node_templates['Modifiers']['all_cols']  # Modifiers
    columns_dict = {reqset_used.get(k, k): v for k, v in no_arg_params.items() if reqset_used.get(k, k) in mod_cols}
    sql, dict_form, error_string = transform_to_sql(columns_dict, 'Modifiers', error_string)
    sql_code.append(sql)
    dict_form_list.append(dict_form)
    if modifier_type in db_spec.dynamic_mod_info:
        effect_type = db_spec.dynamic_mod_info[modifier_type]['EffectType']
        # collection_type = db_spec.dynamic_mod_info[modifier_type]['CollectionType']       # unneeded for now

    argument_transform(sql_code, error_string, dict_form_list, 'Modifier', no_arg_params['ModifierId'],
                       custom_properties, db_spec.mod_type_arg_map[effect_type],
                       db_spec.modifier_argument_info[effect_type], node_id=node_id)

    template = db_spec.node_templates['ModifierStrings']  # ModifierStrings
    mod_string_cols = template['all_cols']
    columns_dict = {k: v for k, v in no_arg_params.items() if k in mod_string_cols}
    if not any([v == '' for k, v in columns_dict.items() if k in template['primary_texts']]):
        sql, dict_form, error_string = transform_to_sql(columns_dict, 'ModifierStrings', error_string)
        sql_code.append(sql)
        dict_form_list.append(dict_form)

    return sql_code, dict_form_list, error_string


def transform_to_sql(ui_dict, table_name, error_string):
    if table_name == 'Types':  # deal with Hashed default
        if 'Hash' in ui_dict:
            del ui_dict['Hash']                                         # TODO we should change this table
    if table_name in ['ModifierArguments', 'RequirementArguments']:
        ui_dict['Value'] = str(ui_dict['Value'])
    sql_command, dict_info = SQLValidator.convert_ui_dict_to_text_sql(ui_dict, table_name)
    return f"{sql_command};", {'table_name': table_name, 'columns': dict_info}, error_string


def transform_localisation(ui_dict, table_name):
    info = db_spec.node_templates[table_name]
    loc_cols = info.get('localised')
    if loc_cols is None:
        return []
    loc_entries = []
    pk_string = '_'.join([str(ui_dict.get(i, fallback_loc.get_loc_index(table_name))) for i in info['primary_keys']])
    for col in loc_cols:
        loc_string = f'LOC_{table_name}_{pk_string}_{col}'
        loc_entry = {'Language': 'en_US', 'Tag': loc_string, 'Text': ui_dict[col]}
        loc_entries.append(loc_entry)
        ui_dict[col] = loc_string
    return loc_entries

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


# test mod stuff