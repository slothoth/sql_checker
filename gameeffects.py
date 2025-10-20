def game_effects(sql_statements, sql_commands_dict, xml_file, skips):
    collection_ = sql_commands_dict.get('@collection', 'COLLECTION_OWNER')
    sql_statements.append({"type": "INSERT", "table": 'DynamicModifiers',
                           "columns": ['ModifierType', 'CollectionType', 'EffectType'],
                           "values": [f"{sql_commands_dict['@id']}_TYPE", collection_,
                                      sql_commands_dict['@effect']]})
    sql_statements.append({"type": "INSERT", "table": 'Types', "columns": ['Type', 'Kind'],
                           "values": [f"{sql_commands_dict['@id']}_TYPE", 'KIND_MODIFIER']})
    columns, values, errors = [], [], []
    modifier_id, subject_req_set, owner_req_set, subject_req_args, owner_req_args, mod_args = None, None, None, None, None, None
    for col, val in sql_commands_dict.items():
        if col == '@id':
            modifier_id = val
            columns.append('ModifierType')
            values.append(val + '_TYPE')
        if col in ['@collection', '@effect']:
            continue
        if col == '{GameEffects}Argument':
            continue
        elif col == '{GameEffects}String':
            continue
        elif col == '{GameEffects}SubjectRequirements':
            columns.append('SubjectRequirementSetId')
            subject_req_set = f'{modifier_id}_SUBJECT_REQUIREMENTS'
            values.append(subject_req_set)
            subject_req_args = val
            continue
        elif col == '{GameEffects}OwnerRequirements':
            columns.append('OwnerRequirementSetId')
            owner_req_set = f'{modifier_id}_OWNER_REQUIREMENTS'
            values.append(owner_req_set)
            owner_req_args = val
            continue
        elif col == '{GameEffects}Requirement':         # bad input by modder
            errors.append(f'Requirements Tag in wrong place in file: {xml_file}. This requirement will not be seen by Firaxis parser')
            continue
        elif col == '#text':         # bad input by modder
            errors.append(f'random input in odd position, but not blocking, in file: {xml_file}')
            continue

        columns.append(col)
        values.append(val)

    columns = col_replacer(columns, {'@id': 'ModifierId', '@permanent': 'Permanent',
                                          '@run-once': 'RunOnce', '@subject-stack-limit': 'SubjectStackLimit',
                                          '@owner-stack-limit': 'OwnerStackLimit', '@new-only': 'NewOnly'})
    sql_statements.append({"type": "INSERT", "table": 'Modifiers', "columns": columns, "values": values})

    if '{GameEffects}Argument' in sql_commands_dict:
        if isinstance(sql_commands_dict['{GameEffects}Argument'], dict):
            sql_commands_dict['{GameEffects}Argument'] = [sql_commands_dict['{GameEffects}Argument']]
        for arg in sql_commands_dict['{GameEffects}Argument']:
            arg_cols, arg_vals = [i for i in arg], [j for j in arg.values()]
            arg_cols, arg_vals = ['ModifierId'] + arg_cols, [modifier_id] + arg_vals,
            arg_cols = col_replacer(arg_cols, {'@name': 'Name', '#text': 'Value'})

            sql_statements.append(
                {"type": "INSERT", "table": 'ModifierArguments', "columns": arg_cols, "values": arg_vals})

    # if '{GameEffects}String???' in sql_commands_dict:

    if owner_req_args is not None:
        if modifier_id in skips:
            skip = skips[modifier_id]
            if skip['error_type'] == 'NestedRequirements' and skip['additional'] == 'owner':
                if len(sql_commands_dict['{GameEffects}OwnerRequirements']) > 1:
                    sql_commands_dict['{GameEffects}OwnerRequirements'] = sql_commands_dict['{GameEffects}OwnerRequirements'][0]
        req_set_build(sql_statements, sql_commands_dict['{GameEffects}OwnerRequirements'], owner_req_set)
    if subject_req_args is not None:
        if modifier_id in skips:
            skip = skips[modifier_id]
            if skip['error_type'] == 'NestedRequirements' and skip['additional'] == 'subject':
                if len(sql_commands_dict['{GameEffects}SubjectRequirements']) > 1:
                    sql_commands_dict['{GameEffects}SubjectRequirements'] = sql_commands_dict['{GameEffects}SubjectRequirements'][0]
        req_set_build(sql_statements, sql_commands_dict['{GameEffects}SubjectRequirements'], subject_req_set)
    return sql_statements, errors


def req_set_build(sql_statements, sql_commands_dict, reqsetID):
    sql_statements.append(
        {"type": "INSERT", "table": 'RequirementSets', "columns": ['RequirementSetId', 'RequirementSetType'],
         "values": [reqsetID, 'REQUIREMENTSET_TEST_ALL']})
    requirement_list = sql_commands_dict['{GameEffects}Requirement']
    if isinstance(requirement_list, dict):
        requirement_list = [requirement_list]
    for idx, require_info in enumerate(requirement_list):
        req_id = f'{reqsetID}_{idx + 1}'
        sql_statements, req_id = req_build(sql_statements, require_info, req_id)
        sql_statements.append(
            {"type": "INSERT", "table": 'RequirementSetRequirements',
             "columns": ['RequirementSetId', 'RequirementId'],
             "values": [reqsetID, req_id]})
    return sql_statements


def req_build(sql_statements, sql_commands_dict, reqId):
    new_req_id =reqId
    req_set = {}
    for col, val in sql_commands_dict.items():
        if isinstance(val, dict) or isinstance(val, list):
            req_set[col] = val
            continue
    if len(req_set) > 0:
        for key, val in req_set.items():
            if '@xref' in val:
                new_req_id = val['@xref']
                continue  # covered elsewhere
            if 'GameEffect' in key and (
                    '#text' in val or isinstance(val, list)):  # implies its a sole requirement, no reqset
                if not isinstance(val, list):
                    val = [val]
                # do the Requirements entry
                filtered_commands = {i: j_ for i, j_ in sql_commands_dict.items() if
                                     'GameEffects' not in i and '@id' not in i}
                req_cols, req_vals = (['RequirementId'] + [i for i in filtered_commands],
                                      [reqId] + [i for i in filtered_commands.values()])
                req_cols = col_replacer(req_cols, {'@type': 'RequirementType', '@inverse': 'Inverse'})
                sql_statements.append(
                    {"type": "INSERT", "table": 'Requirements', "columns": req_cols, "values": req_vals})

                for req_arg in val:
                    cols, vals = (['RequirementId'] + [i for i in req_arg], [reqId] +
                                  [j for j in req_arg.values()])
                    cols = col_replacer(cols, {'@name': 'Name', '#text': 'Value'})
                    sql_statements.append(
                        {"type": "INSERT", "table": 'RequirementArguments', "columns": cols,
                         "values": vals})
            else:
                req_cols, req_vals = (['RequirementId'] + [i for i in val if 'GameEffects' not in i],
                                      [reqId] + [val_ for key_, val_ in val.items() if 'GameEffects' not in key_])
                req_cols = col_replacer(req_cols, {'@type': 'RequirementType', '@inverse': 'Inverse'})
                sql_statements.append(
                    {"type": "INSERT", "table": 'Requirements', "columns": req_cols, "values": req_vals})

                if '{GameEffects}Argument' in val:
                    req_args = val['{GameEffects}Argument']
                    if isinstance(req_args, dict):
                        req_args = [req_args]
                    for idx, req_arg in enumerate(req_args):
                        cols, vals = (['RequirementId'] + [i for i in req_arg], [reqId] + [j for j in req_arg.values()])
                        cols = col_replacer(cols, {'@name': 'Name', '#text': 'Value'})
                        sql_statements.append(
                            {"type": "INSERT", "table": 'RequirementArguments', "columns": cols,
                             "values": vals})
    else:
        if '@xref' in sql_commands_dict:
            new_req_id = sql_commands_dict['@xref']
        else:
            # a simple requirement no args, TODO doesnt handle inverse, is that handled elsewhere
            sql_statements.append(
                {"type": "INSERT", "table": 'Requirements', "columns": ['RequirementId', 'RequirementType'],
                 "values": [reqId, sql_commands_dict['@type']]})

    return sql_statements, new_req_id


def col_replacer(col_list, keymap):
    new_list = []
    for col in col_list:
        new_list.append(keymap.get(col, col))
    return new_list