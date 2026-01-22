import json
import math
from collections import defaultdict, Counter
from itertools import combinations
from sqlalchemy import create_engine, text, select, Text

from graph.utils import flatten_avoid_string, to_number
from graph.singletons.filepaths import LocalFilePaths

import logging

log = logging.getLogger(__name__)


def get_unique_rows(data, key_columns):
    """Helper to mimic df.drop_duplicates(subset=key_columns)"""
    seen = set()
    unique_data = []
    for row in data:
        # Create a tuple of the values we want to check for uniqueness
        identifier = tuple(row.get(col) for col in key_columns)
        if identifier not in seen:
            seen.add(identifier)
            unique_data.append(row)
    return unique_data


def gather_effects(db_dict, metadata, database_spec):
    collection_types = []
    with db_dict['AGE_ANTIQUITY'].connect() as conn:
        result = conn.execute(text("SELECT Type FROM Types WHERE Kind='KIND_COLLECTION'"))
        column_names = result.keys()
        for row in result:
            collection_types.append(dict(zip(column_names, row)))
    collection_types = [i['Type'] for i in collection_types]
    with open(LocalFilePaths.app_data_path_form('db_spec/CollectionsList.json'), 'w') as f:
        json.dump(collection_types, f, sort_keys=True, separators=(',', ':'))

    with open('resources/manual_assigned/CollectionObjectManualAssignment.json') as f:
        manual_collection_classification = json.load(f)

    with open('resources/manual_assigned/CollectionOwnerMap.json') as f:
        TableOwnerObjectMap = json.load(f)

    with open('resources/manual_assigned/modifier_tables.json') as f:
        mod_tables = json.load(f)

    mine_effects(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap, database_spec)
    mine_requirements(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap, database_spec)
    update_loc_spec(db_dict, database_spec)
    update_possible_vals_spec(db_dict, metadata, database_spec)


def mine_effects(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap, database_spec):
    modifier_arguments_name_df = harvest_modifier_arguments(db_dict)

    mod_arg_dict = defaultdict(lambda: defaultdict(list))
    for row in modifier_arguments_name_df:
        eff_type = row['EffectType']
        name = row['Name']
        value = row['Value']
        if eff_type and name:
            mod_arg_dict[eff_type][name].append(value)

    mod_arg_dict = dict(mod_arg_dict)

    modifier_arguments_unique = get_unique_rows(modifier_arguments_name_df, ['EffectType', 'Name'])
    mod_arg_map = make_mod_arg_map(modifier_arguments_unique)

    # df_effect_args = collect_modifier_args(db_dict, modifier_arguments_name_df)

    (effect_object_mapper, df_collection_object, df_collection_attach_tbl,
     collect_attach_map, collect_effect_map) = map_effect_type_objects(db_dict, mod_tables,
                                                                        manual_collection_classification,
                                                                        TableOwnerObjectMap)

    mod_map = {key: {'Arguments': val, 'Object': effect_object_mapper.get(key, [])}
                for key, val in mod_arg_map.items()}
    for key, modifier_info in mod_map.items():
        for mod_arg, mod_arg_info in modifier_info['Arguments'].items():
            for mod_arg_col, mod_arg_value in mod_arg_info.items():
                if isinstance(mod_arg_value, set):
                    mod_arg_value = list(mod_arg_value)[0] if len(mod_arg_value) == 1 else list(mod_arg_value)

                if mod_arg_value != mod_arg_value:
                    mod_arg_value = None
                mod_arg_info[mod_arg_col] = mod_arg_value

    dynamic_mods_list = mine_sql_per_age(db_dict, """
        SELECT m.ModifierId, m.ModifierType, dm.CollectionType, dm.EffectType
        FROM Modifiers m
        JOIN DynamicModifiers dm ON m.ModifierType = dm.ModifierType;
    """)

    dynamicModifiers = {}
    for row in dynamic_mods_list:
        mod_type = row['ModifierType']
        if mod_type not in dynamicModifiers:
            dynamicModifiers[mod_type] = {
                "CollectionType": row['CollectionType'],
                "EffectType": row['EffectType']
            }

    mod_examples = process_arg_examples(mod_arg_dict)
    mod_type_map, mod_database_references, mod_undiagnosible, mod_missed_database = mine_type_arg_map(mod_examples,
                                                                                                      mod_map,
                                                                                                      database_spec)
    deal_with_defaults(mod_map, mod_type_map)
    eff_required_args, eff_exclusionary_args = extract_argument_stats(modifier_arguments_name_df,
                                                                                         'EffectType',
                                                                                         'ModifierId')
    for effect, info in mod_map.items():
        info['Exclusionary_Arguments'] = [list(i) for i in eff_exclusionary_args[effect]]
        for arg_name, name_info in info['Arguments'].items():
            name_info['MinedNeeded'] = arg_name in eff_required_args[effect]
            name_info['MinedExclusions'] = [j for i in eff_exclusionary_args[effect] if arg_name in i for j in i if j != arg_name]

    # sort for ordering consistency
    mod_arg_dict = {k: {key: sorted(val) for key, val in v.items()} for k, v in mod_arg_dict.items()}
    mod_map = {k: {key: sorted(val) if isinstance(val, list) else val for key, val in v.items()} for k, v in mod_map.items()}
    collect_attach_map = {k: sorted(v) for k, v in collect_attach_map.items()}
    collect_effect_map = {k: sorted(v) for k, v in collect_effect_map.items()}

    with open(LocalFilePaths.app_data_path_form('db_spec/ModifierArgumentTypes.json'), 'w') as f:
        json.dump(mod_type_map, f, separators=(',', ':'), default=convert, sort_keys=True)
    with open(LocalFilePaths.app_data_path_form('db_spec/ModifierArgumentDatabaseTypes.json'), 'w') as f:
        json.dump(mod_database_references, f, separators=(',', ':'), default=convert, sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('unused/AllModArgValues.json'), 'w') as f:
        json.dump(mod_arg_dict, f, separators=(',', ':'), default=convert, sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('db_spec/ModArgInfo.json'), 'w') as f:
        json.dump(mod_map, f, separators=(',', ':'), default=convert, sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('unused/CollectionAttachMap.json'), 'w') as f:
        json.dump(collect_attach_map, f, separators=(',', ':'), sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('db_spec/CollectionEffectMap.json'), 'w') as f:
        json.dump(collect_effect_map, f, separators=(',', ':'), sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('db_spec/DynamicModifierMap.json'), 'w') as f:
        json.dump(dynamicModifiers, f, separators=(',', ':'), sort_keys=True)


def mine_requirements(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap, database_spec):
    reqset_no_modifiers = no_modifier_reqset_harvest(db_dict)
    requirement_object_mapper, req_args_name_df = map_requirement_type_objects(db_dict,
                                                                               manual_collection_classification,
                                                                               TableOwnerObjectMap, mod_tables,
                                                                               reqset_no_modifiers,
                                                                               database_spec)

    # now a simpler task. Get all possible Requirement Arguments Names, Values, Extra, Extra2 and Type
    # combine with GameEffectArguments to get extra info on each if possible
    req_map, gossips = make_req_arg_map(db_dict, requirement_object_mapper)

    req_arg_dict = make_req_arg_dict(reqset_no_modifiers)

    req_examples = process_arg_examples(req_arg_dict)
    req_type_map, req_database_references, req_undiagnosible, req_missed_database = mine_type_arg_map(req_examples,
                                                                                                      req_map,
                                                                                                      database_spec)

    req_required_args, req_exclusionary_args = extract_argument_stats(req_args_name_df, 'RequirementType',
                                                                                           'RequirementId')
    for effect, info in req_map.items():
        info['Exclusionary_Arguments'] = [list(i) for i in req_exclusionary_args[effect]]
        for arg_name, name_info in info['Arguments'].items():
            name_info['MinedNeeded'] = arg_name in req_required_args[effect]
            name_info['MinedExclusions'] = [j for i in req_exclusionary_args[effect] if arg_name in i
                                            for j in i if j != arg_name]
    # we need to adjust the DefaultVal
    deal_with_defaults(req_map, req_type_map)

    req_map = {k: {key: sorted(val) if isinstance(val, list) else val for key, val in v.items()} for k, v in
               req_map.items()}

    with open(LocalFilePaths.app_data_path_form('db_spec/RequirementInfo.json'), 'w') as f:
        json.dump(req_map, f, separators=(',', ':'), default=convert, sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('db_spec/RequirementArgumentTypes.json'), 'w') as f:
        json.dump(req_type_map, f, separators=(',', ':'), default=convert, sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('db_spec/RequirementArgumentDatabaseTypes.json'), 'w') as f:
        json.dump(req_database_references, f, separators=(',', ':'), default=convert, sort_keys=True)

    with open(LocalFilePaths.app_data_path_form('unused/GossipInfo.json'), 'w') as f:
        json.dump(gossips, f, separators=(',', ':'), default=convert, sort_keys=True)


def modifier_req_set_harvest(db_dict, mod_tables):
    query = f"""SELECT dm.CollectionType, dm.EffectType, r.RequirementType, r.RequirementId
                FROM REPLACE_TABLE aa
                JOIN Modifiers m
                ON m.ModifierId = aa.ModifierId
                JOIN DynamicModifiers dm
                ON m.ModifierType = dm.ModifierType
                JOIN RequirementSets rs ON rs.RequirementSetId = m.REPLACE_COL
                JOIN RequirementSetRequirements rsr on rsr.RequirementSetId = rs.RequirementSetId
                JOIN Requirements r on r.RequirementId = rsr.RequirementId;
                """
    reqs = {'SubjectRequirementSetId': [], 'OwnerRequirementSetId': []}
    for col in ['SubjectRequirementSetId', 'OwnerRequirementSetId']:
        for db, engine in db_dict.items():
            for tbl in mod_tables:
                with engine.connect() as conn:
                    result = conn.execute(text(query.replace('REPLACE_TABLE', tbl).replace('REPLACE_COL', col)))
                    cols = result.keys()
                    for row in result:
                        row_dict = dict(zip(cols, row))
                        row_dict['AttachTable'] = tbl
                        reqs[col].append(row_dict)
    return reqs['SubjectRequirementSetId'], reqs['OwnerRequirementSetId']


def no_modifier_reqset_harvest(db_dict):
    combined_rows = []
    query = f"""SELECT r.RequirementType, ra.Name, ra.Value
                        FROM REPLACE_TABLE aa
                        JOIN RequirementSets rs ON rs.RequirementSetId = aa.REPLACE_COL
                        JOIN RequirementSetRequirements rsr on rsr.RequirementSetId = rs.RequirementSetId
                        JOIN Requirements r on r.RequirementId = rsr.RequirementId
                        LEFT JOIN RequirementArguments ra on ra.RequirementId = r.RequirementId
                        """
    for tbl, col in {"Defeats": "RequirementSetId", "LegacyModifiers": "RequirementSetId",
                     "UnlockRequirements": "RequirementSetId", "Victories": "RequirementSetId",
                     "NarrativeStories": "ActivationRequirementSetId",
                     "NarrativeStories_2": "RequirementSetId"}.items():
        if tbl == 'NarrativeStories_2':
            tbl = 'NarrativeStories'

        for db_name, engine in db_dict.items():
            with engine.connect() as conn:
                result = conn.execute(text(query.replace('REPLACE_TABLE', tbl).replace('REPLACE_COL', col)))
                cols = result.keys()
                for row in result:
                    row_dict = dict(zip(cols, row))
                    row_dict['AttachTable'] = tbl
                    combined_rows.append(row_dict)
    return combined_rows


def make_req_arg_dict(reqset_no_modifiers_list):
    """
        Converts the list of requirement rows into a nested dictionary mapping.
        Structure: { RequirementType: { Name: [Values] } }
        """
    # Use a defaultdict of defaultdicts to simplify the initial accumulation
    temp_dict = defaultdict(lambda: defaultdict(list))

    # 1. Accumulate values
    for row in reqset_no_modifiers_list:
        req_type = row.get('RequirementType')
        name = row.get('Name')
        val = row.get('Value')

        # Only process if we have the necessary keys
        if req_type and name:
            temp_dict[req_type][name].append(val)

    # 2. Flatten, Deduplicate, and Convert back to standard dict
    final_dict = {}
    for req_type, names_map in temp_dict.items():
        final_dict[req_type] = {}
        for name, values in names_map.items():
            # Flatten the list of values, then take the set for uniqueness
            flattened = flatten_avoid_string(values)
            final_dict[req_type][name] = list(set(flattened))

    return final_dict


def complex_attach_modifiers_reqset(db_dict):
    unique_modifiers = set()  # To handle drop_duplicates()
    final_results = []
    query_attach = text("""
            SELECT m.ModifierId, dm.CollectionType, ma.Value 
            FROM Modifiers m 
            JOIN ModifierArguments ma ON ma.ModifierId = m.ModifierId
            JOIN DynamicModifiers dm ON dm.ModifierType = m.ModifierType
            WHERE dm.EffectType = 'EFFECT_ATTACH_MODIFIERS';
        """)

    query_main = text("""
            SELECT m.ModifierId, dm.CollectionType, dm.EffectType, r.RequirementType, r.RequirementId
            FROM Modifiers m
            JOIN DynamicModifiers dm ON m.ModifierType = dm.ModifierType
            LEFT JOIN RequirementSets rs ON rs.RequirementSetId = m.SubjectRequirementSetId
            LEFT JOIN RequirementSetRequirements rsr ON rsr.RequirementSetId = rs.RequirementSetId
            LEFT JOIN Requirements r ON r.RequirementId = rsr.RequirementId;
        """)

    for engine in db_dict.values():
        with engine.connect() as conn:
            attach_result = conn.execute(query_attach)
            attach_lookup = defaultdict(list)
            for row in attach_result:
                r_dict = dict(zip(attach_result.keys(), row))
                attach_lookup[r_dict['Value']].append({
                    'ModifierId': r_dict['ModifierId'],
                    'CollectionType': r_dict['CollectionType']
                })

            main_result = conn.execute(query_main)
            main_cols = main_result.keys()

            for row in main_result:
                m_row = dict(zip(main_cols, row))
                attached_id = m_row['ModifierId']
                if attached_id in attach_lookup:
                    for attach_data in attach_lookup[attached_id]:
                        combined_row = {
                            'AttachedModifierId': m_row['ModifierId'],
                            'AttachedCollectionType': m_row['CollectionType'],
                            'AttachedEffectType': m_row['EffectType'],
                            'AttachedReqType': m_row['RequirementType'],
                            'RequirementId': m_row['RequirementId'],
                            'ModifierId': attach_data['ModifierId'],
                            'CollectionType': attach_data['CollectionType']
                        }

                        # 4. Handle drop_duplicates() using a tuple of values
                        row_tuple = tuple(combined_row.values())
                        if row_tuple not in unique_modifiers:
                            unique_modifiers.add(row_tuple)
                            final_results.append(combined_row)
    return final_results


def map_requirement_type_objects(db_dict, manual_collection_classification, TableOwnerObjectMap, mod_tables,
                                 reqset_no_modifiers, database_spec):
    total_subject_req_df, total_owner_req_df = modifier_req_set_harvest(db_dict, mod_tables)
    modifiers_full = complex_attach_modifiers_reqset(db_dict)
    owner_attached_final, not_owner_attached_final, one_owner, both_owners = [], [], [], []

    for row in modifiers_full:
        coll_type = row.get('CollectionType')
        row['AttachingToObject'] = manual_collection_classification.get(coll_type, {}).get('Subject')

        attached_coll_type = row.get('AttachedCollectionType')
        row['AttachedFinalObject'] = manual_collection_classification.get(attached_coll_type, {}).get('Subject')

        if row['AttachedFinalObject'] == 'Owner':
            owner_attached_final.append(row)
            if row['AttachingToObject'] != 'Owner':
                new_row = row.copy()
                new_row['AttachedFinalObject'] = row['AttachingToObject']
                one_owner.append(new_row)
            else:
                both_owners.append(row)
        else:
            not_owner_attached_final.append(row)

    owner_mod_attach_table = derive_owner_attach_modifier_reqset(db_dict, both_owners, database_spec)
    both_owner_map = {}
    for row in owner_mod_attach_table:
        tbl = row['AttachTable']
        obj_list = TableOwnerObjectMap.get(tbl, [])
        both_owner_map[row['ModifierId']] = obj_list[0] if obj_list else None

    for row in both_owners:
        mapped_obj = both_owner_map.get(row['ModifierId'])
        if mapped_obj:
            row["AttachedCollectionType"] = mapped_obj
            row["CollectionType"] = mapped_obj

    combined_mods = not_owner_attached_final + one_owner + both_owners
    final_attach_mod_reqs = []
    seen_mod_reqs = set()

    for row in combined_mods:
        req_type = row.get('AttachedReqType')
        obj = row.get('AttachedFinalObject')
        if (req_type, obj) not in seen_mod_reqs:
            seen_mod_reqs.add((req_type, obj))
            final_attach_mod_reqs.append({'RequirementType': req_type, 'object': obj})

    requirement_to_objects = defaultdict(set)
    all_req_sources = [(total_owner_req_df, 'owner'), (total_subject_req_df, 'subject')]

    for source_df_list, mode in all_req_sources:
        seen_local = set()
        for row in source_df_list:
            coll = row.get('CollectionType')
            req = row.get('RequirementType')
            tbl = row.get('AttachTable')
            if (coll, req, tbl) in seen_local:
                continue
            seen_local.add((coll, req, tbl))
            if coll == 'COLLECTION_OWNER':
                objs = TableOwnerObjectMap.get(tbl, [])
                requirement_to_objects[req].update(objs)
            else:
                classification = manual_collection_classification.get(coll, {})
                obj = classification.get('Owner' if mode == 'owner' else 'Subject')
                if obj:
                    requirement_to_objects[req].add(obj)

    add_to_aggregator(final_attach_mod_reqs, 'RequirementType', 'object', requirement_to_objects)
    for row in reqset_no_modifiers:
        req = row.get('RequirementType')
        tbl = row.get('AttachTable')
        objs = TableOwnerObjectMap.get(tbl, [])
        if req and objs:
            requirement_to_objects[req].update(objs)

    complete_full_reqs = {req: sorted(list(objs)) for req, objs in requirement_to_objects.items()}
    req_all_types = []
    query = f"""SELECT r.RequirementId, RequirementType, Name FROM Requirements r
                LEFT OUTER JOIN RequirementArguments ra ON ra.RequirementId = r.RequirementId """
    for db, engine in db_dict.items():
        with engine.connect() as conn:
            result = conn.execute(text(query))
            column_names = result.keys()
            for row in result:
                req_all_types.append(dict(zip(column_names, row)))

    requirement_object_mapper = complete_full_reqs
    object_requirement_mapper = defaultdict(list)
    for req, obj_list in requirement_object_mapper.items():
        for my_obj in obj_list:
            object_requirement_mapper[my_obj].append(req)
    object_requirement_mapper = {obj: sorted(list(set(reqs))) for obj, reqs in object_requirement_mapper.items()}
    with open(LocalFilePaths.app_data_path_form('unused/RequirementObjectMap.json'), 'w') as f:
        json.dump(requirement_object_mapper, f, separators=(',', ':'), sort_keys=True)
    with open(LocalFilePaths.app_data_path_form('unused/ObjectRequirementMap.json'), 'w') as f:
        json.dump(object_requirement_mapper, f, separators=(',', ':'), sort_keys=True)
    return requirement_object_mapper, req_all_types


def derive_owner_attach_modifier_reqset(db_dict, both_owners, database_spec):
    owner_mod_attach_results = []
    missing_mods = [row['ModifierId'] for row in both_owners]
    if not missing_mods:
        return []

    for tbl in database_spec.attach_tables:
        node = database_spec.node_templates.get(tbl, {})
        col_list = [k for k, v in node.get('foreign_keys', {}).items() if v == 'Modifiers']
        col_list += [k for k, v in node.get('extra_fks', {}).items() if v['ref_table'] == 'Modifiers']

        if len(col_list) == 1:
            col = col_list[0]
        elif tbl == 'NarrativeStory_Rewards':
            col = 'NarrativeRewardType'
        else:
            continue        # Skip tables where the foreign key cannot be determined

        for age, engine in db_dict.items():
            mod_placeholders = "', '".join(missing_mods)
            query = text(f"SELECT {col} FROM {tbl} WHERE {col} IN ('{mod_placeholders}')")
            with engine.connect() as conn:
                result = conn.execute(query)
                for row in result:
                    found_id = row[0]
                    owner_mod_attach_results.append({'ModifierId': found_id, 'AttachTable': tbl, 'Age': age})
    return owner_mod_attach_results


def make_req_arg_map(db_dict, requirement_object_mapper={}):
    all_req_rows = []
    seen_ids = set()

    query = text("""
            SELECT r.RequirementId, r.RequirementType, ra.Name, ra.Value, ra.Type, ra.Extra, ra.SecondExtra,
                   ga.Required, ga.Description, ga.ArgumentType, ga.DatabaseKind, ga.DefaultValue, 
                   ga.MinValue, ga.MaxValue, ga.Type as GameEffectType
            FROM Requirements r
            LEFT JOIN RequirementArguments ra ON r.RequirementId = ra.RequirementId
            LEFT JOIN GameEffectArguments ga ON r.RequirementType = ga.Type AND ra.Name = ga.Name;
        """)

    for engine in db_dict.values():
        with engine.connect() as conn:
            result = conn.execute(query)
            cols = result.keys()
            for row in result:
                r_dict = dict(zip(cols, row))
                row_id = (r_dict['RequirementId'], r_dict['Name'])
                if row_id not in seen_ids:
                    seen_ids.add(row_id)
                    all_req_rows.append(r_dict)

    group_cols = [
        'RequirementType', 'Name', 'Description', 'Required', 'ArgumentType',
        'DatabaseKind', 'DefaultValue', 'MinValue', 'MaxValue'
    ]

    aggregated = {}

    for row in all_req_rows:
        group_key = tuple(row.get(col) for col in group_cols)

        if group_key not in aggregated:
            aggregated[group_key] = {
                "Value": set(),
                "Type,Extra,SecondExtra": set()
            }

        val = row.get("Value")
        if val is not None:
            aggregated[group_key]["Value"].add(val)

        triple = (row.get("Type"), row.get("Extra"), row.get("SecondExtra"))
        aggregated[group_key]["Type,Extra,SecondExtra"].add(triple)

    req_arg_map = {}

    for group_key, sets_data in aggregated.items():
        req_type, name, desc, req, arg_type, db_kind, default, min_v, max_v = group_key
        if name is None:
            continue

        if req_type not in req_arg_map:
            req_arg_map[req_type] = {}

        req_arg_map[req_type][name] = {
            "Description": desc,
            "Required": req,
            "ArgumentType": arg_type,
            "DatabaseKind": db_kind,
            "DefaultValue": default,
            "MinValue": min_v,
            "MaxValue": max_v,
            "Value": sets_data["Value"],
            "Type,Extra,SecondExtra": sets_data["Type,Extra,SecondExtra"]
        }

    req_map = {key: {'Arguments': val, 'Object': requirement_object_mapper.get(key, [])} for key, val in
               req_arg_map.items()}

    for key, modifier_info in req_map.items():
        for mod_arg, mod_arg_info in modifier_info['Arguments'].items():
            for mod_arg_col, mod_arg_value in mod_arg_info.items():
                if isinstance(mod_arg_value, set):
                    if len(mod_arg_value) == 1:
                        req_map[key]['Arguments'][mod_arg][mod_arg_col] = list(mod_arg_value)[0]

    # change req_map to deal with REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_GOSSIPS.
    # removing any args that are capitilised.
    gossips = {k: v for k, v in req_map['REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_GOSSIPS']['Arguments'].items()
               if k.upper() == k}
    req_map['REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_GOSSIPS']['Arguments'] = \
        {k: v for k, v in req_map['REQUIREMENT_PLAYER_HAS_AT_LEAST_NUM_GOSSIPS']['Arguments'].items() if k.upper() != k}

    return req_map, gossips


def harvest_modifier_arguments(db_dict):
    combined_rows = []
    query = """
            SELECT dm.EffectType, dm.CollectionType, m.ModifierId, ma.Name, ma.Value, ma.Type,
                   ma.Extra, ma.SecondExtra,
                   ga.Required, ga.Description, ga.ArgumentType, ga.DatabaseKind, ga.DefaultValue, 
                   ga.MinValue, ga.MaxValue, ga.Type as GameEffectType
            FROM DynamicModifiers dm
            JOIN Modifiers m ON m.ModifierType = dm.ModifierType
            LEFT JOIN ModifierArguments ma ON ma.ModifierId = m.ModifierId
            LEFT JOIN GameEffectArguments ga ON dm.EffectType = ga.Type AND ma.Name = ga.Name;
        """
    for db_name, engine in db_dict.items():
        with engine.connect() as conn:
            result = conn.execute(text(query))
            column_names = result.keys()
            for row in result:
                combined_rows.append(dict(zip(column_names, row)))
    return combined_rows


def make_mod_arg_map(modifier_arguments_list):
    """
    Groups and aggregates modifier arguments into a nested dictionary.
    Replaces Pandas groupby, apply, and to_dict(orient="index").
    """
    group_cols = [
        'EffectType', 'Name', 'Description', 'Required', 'ArgumentType',
        'DatabaseKind', 'DefaultValue', 'MinValue', 'MaxValue'
    ]

    aggregated = {}

    for row in modifier_arguments_list:
        if row.get("Name") is None:
            continue  # Skip rows that don't actually have an argument name
        group_key = tuple(row.get(col) for col in group_cols)

        if group_key not in aggregated:
            aggregated[group_key] = {
                "Value": set(),
                "Type,Extra,SecondExtra": set()
            }

        if row.get("Value") is not None:
            aggregated[group_key]["Value"].add(row.get("Value"))

        triple = (row.get("Type"), row.get("Extra"), row.get("SecondExtra"))
        aggregated[group_key]["Type,Extra,SecondExtra"].add(triple)

    mod_arg_map = {}

    for group_key, sets_data in aggregated.items():
        eff_type, name, desc, req, arg_type, db_kind, default, min_v, max_v = group_key

        if eff_type not in mod_arg_map:
            mod_arg_map[eff_type] = {}

        data_entry = {
            "Description": desc,
            "Required": req,
            "ArgumentType": arg_type,
            "DatabaseKind": db_kind,
            "DefaultValue": default,
            "MinValue": min_v,
            "MaxValue": max_v,
            "Value": sets_data["Value"],
            "Type,Extra,SecondExtra": sets_data["Type,Extra,SecondExtra"]
        }

        mod_arg_map[eff_type][name] = data_entry

    final_map = {}
    for eff_type, names_dict in mod_arg_map.items():
        final_map[eff_type] = {} if all(name is None for name in names_dict.keys()) else names_dict
    return final_map


def collect_modifier_args(db_dict, combined_df):
    all_cols = combined_df[0].keys() if combined_df else []
    df_unique = get_unique_rows(combined_df, all_cols)

    counts = Counter()
    for row in df_unique:
        counts[(row['EffectType'], row['Name'])] += 1

    first_engine = list(db_dict.values())[0]
    game_effect_args_list = []
    query = """
        SELECT ga.Type, ga.Name, ga.ArgumentType, ga.DatabaseKind, ga.DefaultValue, ga.Required
        FROM GameEffectArguments ga;
    """
    with first_engine.connect() as conn:
        result = conn.execute(text(query))
        cols = result.keys()
        for row in result:
            row_dict = dict(zip(cols, row))
            row_dict['EffectType'] = row_dict.pop('Type')
            game_effect_args_list.append(row_dict)

    df_effect_args = []

    gea_lookup = {(r['EffectType'], r['Name']): r for r in game_effect_args_list}

    for (eff_type, name), count in counts.items():
        merged_row = {
            'EffectType': eff_type,
            'Name': name,
            'count': count
        }
        if (eff_type, name) in gea_lookup:
            merged_row.update(gea_lookup[(eff_type, name)])
        else:
            merged_row.update({
                'ArgumentType': None,
                'DatabaseKind': None,
                'DefaultValue': None,
                'Required': None
            })

        df_effect_args.append(merged_row)

    return df_effect_args


def map_effect_type_objects(db_dict, mod_tables, manual_collection_classification, TableOwnerObjectMap):
    simple_collection_map = {key: val['Subject'] for key, val in manual_collection_classification.items()}

    all_rows = []

    for engine in db_dict.values():
        for tbl in mod_tables:
            query = f"""
                SELECT dm.CollectionType, m.ModifierId, dm.EffectType
                FROM {tbl} aa
                JOIN Modifiers m ON m.ModifierId = aa.ModifierId
                JOIN DynamicModifiers dm ON m.ModifierType = dm.ModifierType;
            """
            with engine.connect() as conn:
                result = conn.execute(text(query))
                cols = result.keys()
                for row in result:
                    row_dict = dict(zip(cols, row))
                    row_dict['AttachTable'] = tbl
                    all_rows.append(row_dict)

    coll_attach_effect = defaultdict(set)  # (CollectionType, AttachTable) -> {EffectType}
    attach_coll = defaultdict(set)  # AttachTable -> {CollectionType}
    coll_effect = defaultdict(set)  # CollectionType -> {EffectType}

    for row in all_rows:
        ct, at, et = row['CollectionType'], row['AttachTable'], row['EffectType']
        coll_attach_effect[(ct, at)].add(et)
        attach_coll[at].add(ct)
        coll_effect[ct].add(et)

    effect_to_objects = defaultdict(set)

    for row in all_rows:
        ct = row['CollectionType']
        at = row['AttachTable']
        et = row['EffectType']

        if ct == "COLLECTION_OWNER":
            obj = TableOwnerObjectMap.get(at)
        else:
            obj = simple_collection_map.get(ct)

        if obj:
            objs = obj if isinstance(obj, list) else [obj]
            for o in objs:
                effect_to_objects[et].add(o)

    effect_object_mapper = {k: list(v) for k, v in effect_to_objects.items()}

    collect_attach_map = {at: list(ct_set) for at, ct_set in attach_coll.items()}
    collect_effect_map = {ct: list(et_set) for ct, et_set in coll_effect.items()}

    df_collection_object = []
    obj_aggregator = defaultdict(set)

    for (ct, at), et_set in coll_attach_effect.items():
        obj = simple_collection_map.get(ct)
        if obj:
            obj_key = tuple(obj) if isinstance(obj, list) else obj
            obj_aggregator[(at, obj_key)].update(et_set)

    for (at, obj), et_set in obj_aggregator.items():
        df_collection_object.append({
            'AttachTable': at,
            'CollectionType': list(obj) if isinstance(obj, tuple) else obj,
            'EffectType': et_set
        })

    df_collection_attach_tbl = [
        {'AttachTable': at, 'CollectionType': ct, 'EffectType': et_set}
        for (ct, at), et_set in coll_attach_effect.items()
    ]

    return (effect_object_mapper, df_collection_object, df_collection_attach_tbl,
            collect_attach_map, collect_effect_map)


def mine_empty_effects():
    engine = create_engine(f"sqlite:///{LocalFilePaths.app_data_path_form('created-db.sqlite')}")
    tables_data = {}

    with engine.connect() as conn:
        table_query = text("SELECT name FROM sqlite_master WHERE type='table';")
        table_result = conn.execute(table_query)

        table_names = [row[0] for row in table_result]

        for table_name in table_names:
            query = text(f"SELECT * FROM {table_name}")
            result = conn.execute(query)

            column_names = result.keys()
            rows = []

            for row in result:
                rows.append(dict(zip(column_names, row)))

            if rows:
                tables_data[table_name] = rows

    with open('resources/mined/PreBuiltData.json', 'w') as f:       # TODO should this be in AppData
        json.dump(tables_data, f, separators=(',', ':'), sort_keys=True)


def is_nan(x):
    return isinstance(x, float) and math.isnan(x)


def convert(o):
    if isinstance(o, set):
        new_list = list(o)
        new_list.sort()
        return new_list
    raise TypeError


def mine_sql_per_age(db_dict, sql_string):
    combined_results = []

    for engine in db_dict.values():
        with engine.connect() as conn:
            result = conn.execute(text(sql_string))
            cols = result.keys()
            for row in result:
                # Append each row as a dictionary
                combined_results.append(dict(zip(cols, row)))

    return combined_results


def process_arg_examples(data_examples):
    examples = defaultdict(set)
    for k, v in data_examples.items():
        for key, val in v.items():
            if isinstance(val, list):
                [examples[key].add(i) for i in val]
            else:
                examples[key].add(val)
    return dict(examples)


def mine_type_arg_map(mined_examples, effect_arg_info, database_spec):
    by_type_by_effect = defaultdict(lambda: defaultdict(set))
    arg_examples = defaultdict(set)

    for effect, val in effect_arg_info.items():
        for arg, arg_info in val['Arguments'].items():
            by_type_by_effect[arg_info['ArgumentType']][effect].add(arg)
            default_val = arg_info['DefaultValue']
            examples = arg_info['Value']
            if default_val is not None and default_val != '':
                arg_examples[arg].add(default_val)
            if examples is not None and examples != '':
                if isinstance(examples, (list, set)):
                    [arg_examples[arg].add(i) for i in examples]
                else:
                    arg_examples[arg].add(examples)

    type_list = defaultdict(list)
    type_set = defaultdict(set)
    for t, effmap in by_type_by_effect.items():
        for arg_name, args in effmap.items():
            for a in args:
                type_set[a].add(arg_name)
                type_list[a].append(t)

    convert_map = {'Boolean': 'bool', 'uint': 'int'}
    # some bools as Boolean
    counts = {k: dict(Counter(v)) for k, v in type_list.items()}
    counts = {k: {convert_map.get(key, key): val for key, val in v.items() if key is not None and key != ''} for k, v in counts.items()}
    counts = {k: {key: val for key, val in v.items() if not is_nan(key) and key != ''} for k, v in counts.items()}  # remove NaN.
    plural_counts = {k: v for k, v in counts.items() if len(v) > 1}
    single_counts = {k: list(v)[0] for k, v in counts.items() if len(v) == 1}
    missed_counts = {k: v for k, v in counts.items() if len(v) == 0}

    bool_int, database_text = {'bool', 'int'}, {'database', 'text'}
    #type_map = {k: 'bool' if v == bool_int else 'database' if v == database_text else 'text'
    #            for k, v in plural_counts.items()}
    type_map = {}
    used_examples = {k: {i for i in arg_examples[k] if not is_nan(i)} for k, v in counts.items()}
    undiagnosible = {k: v for k, v in used_examples.items() if len(v) == 0}
    if len(undiagnosible) > 1:          # theres one arg thats NaN for some reason
        for i in undiagnosible:
            log.warning(f'could not find type for {i} as no examples')

    used_examples = {k: [part.strip() for s in v for part in s.split(',')] for k, v in used_examples.items() if len(v) > 0}
    flattened_examples = {k: [part.strip() for s in v for part in s.split(',')] for k, v in mined_examples.items()
                          if None not in v}
    flattened_arg_examples = {k: [part.strip() for s in v
                                 if not (isinstance(s, float) and math.isnan(s))
                                 for part in (s.split(',') if isinstance(s, str) else [])]
                                 for k, v in arg_examples.items()}

    booled = {k: 'bool' for k, v in used_examples.items() if all([i in ['1', '0', 'false', 'true'] for i in v])}
    type_map.update(booled)         # deals with 1 and 0 and false and true
    remaining = {k: v for k, v in used_examples.items() if k not in booled}

    numbered = {k: 'int' for k, v in remaining.items() if all([to_number(i) != 'failed' for i in v])}
    type_map.update(numbered)   # todo deals with number. defaulting int but maybe should override for float in future?
    remaining = {k: v for k, v in remaining.items() if k not in numbered}

    origins = [k for k, v in database_spec.node_templates.items() if v.get('origin_pk') is not None]
    missed_database, databased, database_references, fxs_defines, plural_find_table = {}, {}, {}, {}, False
    for k, v in remaining.items():
        if k in flattened_examples:
            examples = flattened_examples[k]
        else:
            examples = flattened_arg_examples[k]
        find_table = {key: val for key, val in database_spec.all_possible_vals.items()
                      if len(set(examples) - set(val['_PK_VALS'])) != len(set(examples))
                      and len(set(examples) - set(val['_PK_VALS'])) / len(set(examples)) < 0.05}
        # ensure at least 95% of the argument values are in a given table, there can be some fails by firaxis
        if len(find_table) > 1 and 'Types' in find_table:
            del find_table['Types']
        if len(find_table) > 1 and 'NarrativeStory_RewardIcons' in find_table:
            del find_table['NarrativeStory_RewardIcons']
        if len(find_table) > 1 and 'TypeQuotes' in find_table:
            del find_table['TypeQuotes']
        if len(find_table) > 1:
            plural_find_table = True
            find_table = {k: v for k, v in find_table.items() if k in origins}
            if len(find_table) > 1:
                find_table = {k: v for k, v in find_table.items() if
                              database_spec.node_templates[k]['foreign_keys'].get(
                                  database_spec.node_templates[k]['primary_keys'][0], 'Types') == 'Types'}
            if len(find_table) > 1:
                find_table = {k: v for k, v in find_table.items() if
                              database_spec.node_templates[k].get(
                    'extra_fks', {}).get(database_spec.node_templates[k]['primary_keys'][0], 'Types') == 'Types'}
            # now iterate to see if any values are extra_fks or foreign keys
            if len(find_table) > 1:
                fks = {k: list(database_spec.node_templates[k]['foreign_keys'].values()) + [j['ref_table']
                    for j in database_spec.node_templates[k].get('extra_fks', {}).values()] for k, v in find_table.items()}
                find_table = {k: v for k, v in find_table.items() if not any(i in find_table for i in fks[k])}
            # gets rid of tables that are not in origins
        if len(find_table) == 1:
            database_ref = next(i for i in find_table)
            database_references[k] = database_ref
            databased[k] = 'database'
        elif len(find_table) == 0:
            if plural_find_table:               # too much got pared away
                missed_database[k] = find_table
                databased[k] = 'database'
        else:
            missed_database[k] = find_table
            if plural_counts.get(k) is not None:
                plural_vals = plural_counts[k]
                simple_val = 'bool' if plural_vals == bool_int else 'text'
                fxs_defines[k] = simple_val
            elif single_counts.get(k) is not None:
                fxs_defines[k] = single_counts[k] if single_counts[k] != 'database' else 'text'
            # try use singular
        plural_find_table = False

    type_map.update(databased)
    remaining = {k: v for k, v in remaining.items() if k not in databased}

    type_map.update(fxs_defines)
    remaining = {k: v for k, v in remaining.items() if k not in fxs_defines}

    # deal with remaining as text:
    type_map.update({k: 'text' for k, v in remaining.items()})
    typed_arg_info = {k: {key: type_map[key] for key, val in v['Arguments'].items()
                          if not is_nan(key)} for k, v in effect_arg_info.items()}
    return typed_arg_info, database_references, undiagnosible, missed_database


def deal_with_defaults(info_map, type_map):
    delete_refs = []
    for k, v in info_map.items():
        req_info = type_map[k]
        for key, val in v['Arguments'].items():
            if is_nan(key):
                delete_refs.append((k, key))
                continue
            default_val = val['DefaultValue']
            if default_val == '' or is_nan(default_val):
                # make our own? if
                arg_type = req_info[key]
                info_map[k]['Arguments'][key]['DefaultValue'] = None
            else:
                if default_val is not None:
                    arg_type = req_info[key]
                    if arg_type == 'int':
                        if not isinstance(default_val, int):
                            info_map[k]['Arguments'][key]['DefaultValue'] = int(default_val)
                    elif arg_type in ['database', 'text']:
                        if not isinstance(default_val, str):
                            info_map[k]['Arguments'][key]['DefaultValue'] = str(default_val)
                    elif arg_type == 'bool':
                        if not isinstance(default_val, bool):
                            casted_val = True if default_val in ['1', 1, 'true', 'true'] else None
                            if casted_val is None:
                                casted_val = False if default_val in ['0', 0, 'False', 'false'] else None
                            if casted_val is not None:
                                info_map[k]['Arguments'][key]['DefaultValue'] = casted_val
                    else:
                        log.warning(f'oh no, when converting arg {key} default value {default_val} to correct type, had '
                                    f'unhandled argument {arg_type}, skipping')
    for k, key in delete_refs:
        del info_map[k]['Arguments'][key]


def update_loc_spec(db_dict, database_spec):

    with open('resources/mined/LocalizedTags.json') as f:
        localised = json.load(f)

    localised = set(localised)

    localise_table_cols = defaultdict(list)
    for db, engine in db_dict.items():

        for table_name, info in database_spec.node_templates.items():
            for column_name in info['all_cols']:
                with engine.connect() as conn:
                    trans = conn.begin()
                    rows = {i[0] for i in conn.execute(text(f"""SELECT {column_name} FROM {table_name} 
                                            t WHERE {column_name} IS NOT NULL""")).fetchall()}
                trans.rollback()
                if len(rows) == 0:
                    continue
                non_localised = rows - localised
                localised_proportions = (len(rows) - len(non_localised)) / len(rows)
                if localised_proportions >= 0.5:
                    localise_table_cols[table_name].append(column_name)
                else:
                    if column_name in ['Name', 'Description']:
                        log.info(f'missed localisation on these rows for {table_name}.{column_name}:', rows)
    for table_name, table_cols in localise_table_cols.items():
        database_spec.node_templates[table_name]['localised'] = []
        for col in table_cols:
            database_spec.node_templates[table_name]['localised'].append(col)
        database_spec.node_templates[table_name]['localised'] = list(set(database_spec.node_templates[table_name]['localised']))

    database_spec.update_node_templates(database_spec.node_templates)


def update_possible_vals_spec(db_dict, metadata, database_spec):
    age_possible_vals = {}
    for age_type, engine in db_dict.items():
        result = {}
        with engine.connect() as conn:
            for table_name, table in metadata.tables.items():
                table_dict = {}
                spec = database_spec.node_templates[table_name]
                for column in table.c:
                    if table_name in ['ModifierArguments', 'RequirementArguments'] and column.name == 'Value':
                        continue
                    not_covered = column.name not in database_spec.all_possible_vals[table_name]
                    not_covered = not_covered and column.name not in spec.get('localised', [])
                    not_covered = not_covered and column.name not in spec.get('foreign_keys')
                    if isinstance(column.type, Text) and not column.primary_key and not_covered:
                        stmt = select(column).distinct()
                        values = [row[0] for row in conn.execute(stmt) if row[0] is not None]
                        if any('LOC_' in i for i in values) or column.name in ['Description', 'Name']:
                            continue
                        if len(values) > 0:
                            table_dict[column.name] = values
                if len(table_dict) > 0:
                    result[table_name] = table_dict
        age_possible_vals[age_type] = result

    all_possible_vals = defaultdict(dict)
    for table_name, table in metadata.tables.items():
        for column in table.c:
            combined_vals = list(set(val for age in age_possible_vals.keys()
                                     for val in age_possible_vals[age].get(table_name, {}).get(column.name, [])))
            if 400 > len(combined_vals) > 0:  # too many slows performance
                all_possible_vals[table_name][column.name] = combined_vals
                if table_name not in database_spec.all_possible_vals:
                    database_spec.all_possible_vals[table_name] = {}
                if column.name not in database_spec.all_possible_vals[table_name]:
                    database_spec.all_possible_vals[table_name][column.name] = combined_vals

    for age, poss_val_dict in age_possible_vals.items():
        for table_name, table in poss_val_dict.items():
            for column, values in table.items():
                if len(values) < 300:
                    if table_name not in database_spec.possible_vals[age]:
                        database_spec.possible_vals[age][table_name] = {}
                    if column not in database_spec.possible_vals[age][table_name]:
                        database_spec.possible_vals[age][table_name][column] = values

    all_cols = {f'{k}_{col}': items for k, v in all_possible_vals.items() for col, items in v.items()}
    all_cols_tuples = [(k, v) for k, v in all_cols.items()]
    all_cols_tuples.sort(key=lambda t: len(t[1]), reverse=True)

    database_spec.update_possible_vals(database_spec.possible_vals)
    database_spec.update_all_vals(database_spec.all_possible_vals)


def extract_argument_stats(modifier_arguments_list, game_effect_col, effect_id_col):
    """
    Identifies required arguments and exclusionary pairs for each EffectType.
    Replaces Pandas groupby, agg(frozenset), and intersection/union logic.
    """
    id_map = {}
    for row in modifier_arguments_list:
        m_id = row.get(effect_id_col)
        eff = row.get(game_effect_col)
        name = row.get('Name')

        if m_id not in id_map:
            id_map[m_id] = {"effect": eff, "names": set()}

        if name:  # Only add if Name is not None
            id_map[m_id]["names"].add(name)

    effect_to_sets = defaultdict(list)
    for data in id_map.values():
        effect_to_sets[data["effect"]].append(data["names"])

    required = {}
    exclusionary = {}

    for effect, sets in effect_to_sets.items():
        if not sets:
            continue
        required[effect] = set.intersection(*sets)
        all_names = set.union(*sets)
        pairs = []
        for a, b in combinations(all_names, 2):
            covers_all = all((a in s) or (b in s) for s in sets)
            never_together = all(not ({a, b} <= s) for s in sets)
            if covers_all and never_together:
                pairs.append({a, b})
        exclusionary[effect] = pairs

    return required, exclusionary


def add_to_aggregator(data_list, req_key, obj_key, requirement_to_objects):
    for row in data_list:
        req = row.get(req_key)
        obj = row.get(obj_key)
        if req and obj:
            if isinstance(obj, (set, list, tuple)):
                requirement_to_objects[req].update(obj)
            else:
                requirement_to_objects[req].add(obj)
