import json
import math
from collections import defaultdict, Counter
import sqlite3
import pandas as pd
from itertools import combinations
from sqlalchemy import create_engine, text, select, Text

from graph.db_spec_singleton import db_spec, attach_tables
from graph.utils import flatten, flatten_avoid_string, to_number

import logging

log = logging.getLogger(__name__)


def combine_db_df(df_combined, df_to_add):
    if df_combined is None:
        df_combined = df_to_add
    else:
        df_combined = pd.concat([df_combined, df_to_add], ignore_index=True)
    return df_combined


def gather_effects(db_dict, metadata):
    collection_types = pd.read_sql("SELECT Type FROM Types WHERE Kind='KIND_COLLECTION'", db_dict['AGE_ANTIQUITY'])
    collection_types = list(collection_types['Type'])
    with open('resources/db_spec/CollectionsList.json', 'w') as f:
        json.dump(collection_types, f, indent=2, sort_keys=True)

    with open('resources/manual_assigned/CollectionObjectManualAssignment.json') as f:
        manual_collection_classification = json.load(f)

    with open('resources/manual_assigned/CollectionOwnerMap.json') as f:
        TableOwnerObjectMap = json.load(f)

    with open('resources/manual_assigned/modifier_tables.json') as f:
        mod_tables = json.load(f)

    mine_effects(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap)
    # --------------------------------------------------------------------------------
    # -------------------------   Requirements    ------------------------------------
    # --------------------------------------------------------------------------------
    # first get requirements from modifier tables
    mine_requirements(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap)

    update_loc_spec(db_dict)

    update_possible_vals_spec(db_dict, metadata)


def mine_effects(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap):
    modifier_arguments_name_df, combined_df = harvest_modifier_arguments(db_dict)
    modifier_arguments_name_df[['EffectType', 'Name', 'Value', 'Type', 'Extra', 'SecondExtra', 'CollectionType']].to_csv('resources/mined/AllModArgValues')

    mod_arg_dict = defaultdict(lambda: defaultdict(list))
    for a, b, c in modifier_arguments_name_df[['EffectType', 'Name', 'Value']].itertuples(index=False):
        mod_arg_dict[a][b].append(c)
    for key, val in mod_arg_dict.items():
        for k, v in val.items():
            mod_arg_dict[key][k] = list(set(mod_arg_dict[key][k]))

    mod_arg_dict = dict(mod_arg_dict)

    modifier_arguments_name_df = modifier_arguments_name_df.drop_duplicates(['EffectType', 'Name'])
    mod_arg_map = make_mod_arg_map(modifier_arguments_name_df)

    df_effect_args = collect_modifier_args(db_dict, combined_df)

    (effect_object_mapper, df_collection_object, df_collection_attach_tbl,
     collect_attach_map, collect_effect_map) = map_effect_type_objects(db_dict, mod_tables,
                                                                        manual_collection_classification,
                                                                        TableOwnerObjectMap)

    mod_map = {key: {'Arguments': val, 'Object': effect_object_mapper.get(key, [])} for key, val in
               mod_arg_map.items()}

    mod_map = {key: {k: v if k == 'Object' else {k_: {k_a: None if is_nan(v_a) else v_a for k_a, v_a in v_.items()}
                                                 for k_, v_ in v.items()} for k, v in val.items()}
               for key, val in mod_map.items()}

    for key, modifier_info in mod_map.items():
        for mod_arg, mod_arg_info in modifier_info['Arguments'].items():
            for mod_arg_col, mod_arg_value in mod_arg_info.items():
                if isinstance(mod_arg_value, set):
                    if len(mod_arg_value) == 1:
                        mod_map[key]['Arguments'][mod_arg][mod_arg_col] = list(mod_arg_value)[0]

    dynamic_mods = mine_sql_per_age(db_dict, f"""
                               SELECT m.ModifierId, m.ModifierType, dm.CollectionType, dm.EffectType
                               FROM Modifiers m
                               JOIN DynamicModifiers dm
                               ON m.ModifierType = dm.ModifierType;
                               """)
    dynamicModifiers = dynamic_mods.groupby("ModifierType", as_index=True).first()[[
        "CollectionType", "EffectType"]].to_dict("index")

    mod_examples = process_arg_examples(mod_arg_dict)
    mod_type_map, mod_database_references, mod_undiagnosible, mod_missed_database = mine_type_arg_map(mod_examples,
                                                                                                      mod_map)
    deal_with_defaults(mod_map, mod_type_map)
    # get modifiers and aggregate by id
    eff_required_args, eff_exclusionary_args = extract_argument_stats(modifier_arguments_name_df,
                                                                                         'EffectType',
                                                                                         'ModifierId')
    for effect, info in mod_map.items():
        info['Exclusionary_Arguments'] = [list(i) for i in eff_exclusionary_args[effect]]
        for arg_name, name_info in info['Arguments'].items():
            name_info['MinedNeeded'] = arg_name in eff_required_args[effect]
            name_info['MinedExclusions'] = [j for i in eff_exclusionary_args[effect] if arg_name in i for j in i if j != arg_name]

    with open('resources/db_spec/ModifierArgumentTypes.json', 'w') as f:
        json.dump(mod_type_map, f, indent=2, default=convert, sort_keys=True)
    with open('resources/db_spec/ModifierArgumentDatabaseTypes.json', 'w') as f:
        json.dump(mod_database_references, f, indent=2, default=convert, sort_keys=True)

    with open('resources/unused/AllModArgValues.json', 'w') as f:
        json.dump(mod_arg_dict, f, indent=2, default=convert, sort_keys=True)

    with open('resources/db_spec/ModArgInfo.json', 'w') as f:
        json.dump(mod_map, f, indent=2, default=convert, sort_keys=True)

    df_effect_args.to_csv('resources/unused/ModifierEffectArguments.csv')
    df_collection_object.to_csv('resources/mined/CollectionObjectAttach.csv')
    df_collection_attach_tbl.to_csv('resources/mined/CollectionAttach.csv')

    with open('resources/unused/CollectionAttachMap.json', 'w') as f:
        json.dump(collect_attach_map, f, indent=2, sort_keys=True)

    with open('resources/db_spec/CollectionEffectMap.json', 'w') as f:
        json.dump(collect_effect_map, f, indent=2, sort_keys=True)

    with open('resources/db_spec/DynamicModifierMap.json', 'w') as f:
        json.dump(dynamicModifiers, f, indent=2, sort_keys=True)


def mine_requirements(db_dict, manual_collection_classification, mod_tables, TableOwnerObjectMap):

    reqset_no_modifiers = no_modifier_reqset_harvest(db_dict)

    requirement_object_mapper, req_args_name_df = map_requirement_type_objects(db_dict, manual_collection_classification,
                                                             TableOwnerObjectMap, mod_tables, reqset_no_modifiers)

    # now a simpler task. Get all possible Requirement Arguments Names, Values, Extra, Extra2 and Type
    # combine with GameEffectArguments to get extra info on each if possible
    req_map, gossips = make_req_arg_map(db_dict, requirement_object_mapper)

    req_arg_dict = make_req_arg_dict(reqset_no_modifiers)

    req_examples = process_arg_examples(req_arg_dict)
    req_type_map, req_database_references, req_undiagnosible, req_missed_database = mine_type_arg_map(req_examples,
                                                                                                      req_map)

    req_required_args, req_exclusionary_args = extract_argument_stats(req_args_name_df,
                                                                                         'RequirementType',
                                                                                         'RequirementId')
    for effect, info in req_map.items():
        info['Exclusionary_Arguments'] = [list(i) for i in req_exclusionary_args[effect]]
        for arg_name, name_info in info['Arguments'].items():
            name_info['MinedNeeded'] = arg_name in req_required_args[effect]
            name_info['MinedExclusions'] = [j for i in req_exclusionary_args[effect] if arg_name in i
                                            for j in i if j != arg_name]
    # we need to adjust the DefaultVal
    deal_with_defaults(req_map, req_type_map)

    with open('resources/db_spec/RequirementInfo.json', 'w') as f:
        json.dump(req_map, f, indent=2, default=convert, sort_keys=True)

    with open('resources/db_spec/RequirementArgumentTypes.json', 'w') as f:
        json.dump(req_type_map, f, indent=2, default=convert, sort_keys=True)

    with open('resources/db_spec/RequirementArgumentDatabaseTypes.json', 'w') as f:
        json.dump(req_database_references, f, indent=2, default=convert, sort_keys=True)

    with open('resources/unused/GossipInfo.json', 'w') as f:
        json.dump(gossips, f, indent=2, default=convert, sort_keys=True)


def modifier_req_set_harvest(db_dict, mod_tables):
    total_subject_req_df, subject_req_combined_df, owner_req_combined_df, total_owner_req_df = None, None, None, None
    for db, engine in db_dict.items():
        for tbl in mod_tables:
            df = pd.read_sql(
                f"""
                            SELECT dm.CollectionType, dm.EffectType, r.RequirementType, r.RequirementId
                            FROM {tbl} aa
                            JOIN Modifiers m
                            ON m.ModifierId = aa.ModifierId
                            JOIN DynamicModifiers dm
                            ON m.ModifierType = dm.ModifierType
                            JOIN RequirementSets rs ON rs.RequirementSetId = m.SubjectRequirementSetId
                            JOIN RequirementSetRequirements rsr on rsr.RequirementSetId = rs.RequirementSetId
                            JOIN Requirements r on r.RequirementId = rsr.RequirementId;
                            """,
                engine
            )
            df['AttachTable'] = tbl
            subject_req_combined_df = combine_db_df(subject_req_combined_df, df)

            owner_df = pd.read_sql(
                f"""SELECT dm.CollectionType, dm.EffectType, r_o.RequirementType, r_o.RequirementId
                        FROM {tbl} aa
                        JOIN Modifiers m
                        ON m.ModifierId = aa.ModifierId
                        JOIN DynamicModifiers dm
                        ON m.ModifierType = dm.ModifierType
                        JOIN RequirementSets rs_o ON rs_o.RequirementSetId = m.OwnerRequirementSetId
                        JOIN RequirementSetRequirements rsr_o on rsr_o.RequirementSetId = rs_o.RequirementSetId
                        LEFT JOIN Requirements r_o on r_o.RequirementId = rsr_o.RequirementId;
                        """,
                engine
            )
            owner_df['AttachTable'] = tbl
            owner_req_combined_df = combine_db_df(owner_req_combined_df, owner_df)

        total_subject_req_df = combine_db_df(total_subject_req_df, subject_req_combined_df)
        total_owner_req_df = combine_db_df(total_owner_req_df, owner_req_combined_df)
    return total_subject_req_df, total_owner_req_df


def no_modifier_reqset_harvest(db_dict):
    reqset_tables_per_age, reqset_no_modifiers = None, None
    for db, engine in db_dict.items():
        for tbl, col in {"Defeats": "RequirementSetId", "LegacyModifiers": "RequirementSetId",
                         "UnlockRequirements": "RequirementSetId", "Victories": "RequirementSetId",
                         "NarrativeStories": "ActivationRequirementSetId",
                         "NarrativeStories_2": "RequirementSetId"}.items():
            if tbl == 'NarrativeStories_2':
                tbl = 'NarrativeStories'
            df = pd.read_sql(
                f"""SELECT r.RequirementType, ra.Name, ra.Value
                        FROM {tbl} aa
                        JOIN RequirementSets rs ON rs.RequirementSetId = aa.{col}
                        JOIN RequirementSetRequirements rsr on rsr.RequirementSetId = rs.RequirementSetId
                        JOIN Requirements r on r.RequirementId = rsr.RequirementId
                        LEFT JOIN RequirementArguments ra on ra.RequirementId = r.RequirementId
                        """,
                engine
            )
            df['AttachTable'] = tbl

            reqset_tables_per_age = combine_db_df(reqset_tables_per_age, df)

        reqset_no_modifiers = combine_db_df(reqset_no_modifiers, reqset_tables_per_age)
    return reqset_no_modifiers

def make_req_arg_dict(reqset_no_modifiers):
    req_arg_dict = defaultdict(lambda: defaultdict(list))
    for a, b, c in reqset_no_modifiers[['RequirementType', 'Name', 'Value']].itertuples(index=False):
        req_arg_dict[a][b].append(c)
    for key, val in req_arg_dict.items():
        for k, v in val.items():
            req_arg_dict[key][k] = list(set(flatten_avoid_string(req_arg_dict[key][k])))

    req_arg_dict = dict(req_arg_dict)
    with open('resources/unused/AllReqArgValues.json', 'w') as f:
        json.dump(req_arg_dict, f, indent=2, default=convert, sort_keys=True)
    return req_arg_dict


def complex_attach_modifiers_reqset(db_dict):
    modifiers_full = None
    for db, engine in db_dict.items():
        modifier_attach = pd.read_sql(
            f"""SELECT  m.ModifierId, dm.CollectionType, ma.Value FROM Modifiers m 
                JOIN ModifierArguments ma ON ma.ModifierId = m.ModifierId
                JOIN DynamicModifiers dm ON dm.ModifierType = m.ModifierType
                WHERE dm.EffectType = 'EFFECT_ATTACH_MODIFIERS';
                """,
            engine
        )
        df = pd.read_sql(
            f"""
                SELECT m.ModifierId, dm.CollectionType, dm.EffectType, r.RequirementType, r.RequirementId
                FROM Modifiers m
                JOIN DynamicModifiers dm
                ON m.ModifierType = dm.ModifierType
                LEFT JOIN RequirementSets rs ON rs.RequirementSetId = m.SubjectRequirementSetId
                LEFT JOIN RequirementSetRequirements rsr on rsr.RequirementSetId = rs.RequirementSetId
                LEFT JOIN Requirements r on r.RequirementId = rsr.RequirementId;
                """,
            engine
        )
        df = df.rename(columns={'ModifierId': 'AttachedModifierId', 'CollectionType': 'AttachedCollectionType',
                                'EffectType': 'AttachedEffectType', 'RequirementType': 'AttachedReqType'})
        combined_modifier_attach = df.merge(modifier_attach, left_on="AttachedModifierId", right_on="Value",
                                            how="inner").drop(columns="Value")
        modifiers_full = combine_db_df(modifiers_full, combined_modifier_attach)
    modifiers_full = modifiers_full.drop_duplicates()
    return modifiers_full


def map_requirement_type_objects(db_dict, manual_collection_classification, TableOwnerObjectMap, mod_tables,
                                 reqset_no_modifiers):
    total_subject_req_df, total_owner_req_df = modifier_req_set_harvest(db_dict, mod_tables)
    modifiers_full = complex_attach_modifiers_reqset(db_dict)
    # the COLLECTION OWNER of attached modifiers is the table of the first modifier that causes attachment
    modifiers_full['AttachingToObject'] = modifiers_full['CollectionType'].apply(
        lambda x: manual_collection_classification[x]['Subject'])

    modifiers_full['AttachedFinalObject'] = modifiers_full['AttachedCollectionType'].apply(
        lambda x: manual_collection_classification[x]['Subject'])

    # now work back to deal with owners and inheritance
    owner_attached_final = modifiers_full[modifiers_full['AttachedFinalObject'] == 'Owner']
    not_owner_attached_final = modifiers_full[modifiers_full['AttachedFinalObject'] != 'Owner']

    # where only AttachedFinalObject == Owner but attaching to
    one_owner = owner_attached_final[owner_attached_final['AttachingToObject'] != 'Owner']
    one_owner['AttachedFinalObject'] = one_owner['AttachingToObject']
    # where Owner for both AttachedFinalObject and AttachingToObject we need to find the table of origin for attachment
    both_owners = owner_attached_final[owner_attached_final['AttachingToObject'] == 'Owner']

    # try find modifiers in known tables
    owner_mod_attach_table = derive_owner_attach_modifier_reqset(db_dict, both_owners)

    # reduce to a map
    owner_mod_attach_table = owner_mod_attach_table[['ModifierId', 'AttachTable']]
    owner_mod_attach_table['AttachingToObject'] = owner_mod_attach_table['AttachTable'].apply(
        lambda x: TableOwnerObjectMap[x])
    both_owner_map = owner_mod_attach_table[['ModifierId', 'AttachingToObject']].set_index("ModifierId")[
        "AttachingToObject"].to_dict()
    both_owner_map = {key: val[0] for key, val in both_owner_map.items()}  # TODO add check to make sure not plural

    both_owners["AttachedCollectionType"] = both_owners["ModifierId"].map(both_owner_map).fillna(
        both_owners["AttachedCollectionType"])
    both_owners["CollectionType"] = both_owners["ModifierId"].map(both_owner_map).fillna(both_owners["CollectionType"])
    # then try find in all tables if that fails

    recombined_modifier_reqs = pd.concat([not_owner_attached_final, one_owner, both_owners], ignore_index=True)
    # now reduce this to unique requirementTypes
    recombined_modifier_reqs = recombined_modifier_reqs.drop_duplicates(
        ['AttachedReqType', 'AttachedFinalObject'])
    final_attach_mod_reqs = recombined_modifier_reqs.rename(
        columns={'AttachedReqType': 'RequirementType', 'AttachedFinalObject': 'object'})

    owner_reqs = total_owner_req_df.drop_duplicates(['CollectionType', 'RequirementType', 'AttachTable'])
    owner_reqs = owner_reqs.drop('EffectType', axis=1)
    owner_reqs_OWNER = owner_reqs[owner_reqs['CollectionType'] == 'COLLECTION_OWNER'][
        ['RequirementType', 'AttachTable']]

    owner_reqs_OWNER['object'] = owner_reqs_OWNER['AttachTable'].apply(lambda x: TableOwnerObjectMap[x])

    total_subject_req_df = total_subject_req_df.drop_duplicates()
    subject_reqs = total_subject_req_df.drop_duplicates(['CollectionType', 'RequirementType', 'AttachTable'])
    subject_reqs = subject_reqs.drop(['EffectType'], axis=1)

    subject_reqs_OWNER = subject_reqs[subject_reqs['CollectionType'] == 'COLLECTION_OWNER']
    subject_reqs_OWNER['object'] = subject_reqs_OWNER['AttachTable'].apply(lambda x: TableOwnerObjectMap[x])
    subject_reqs_OWNER = subject_reqs_OWNER[['RequirementType', 'AttachTable', 'object']]

    subject_reqs_no_OWNER = subject_reqs[subject_reqs['CollectionType'] != 'COLLECTION_OWNER']

    all_OWNER_reqs = pd.concat([subject_reqs_OWNER, owner_reqs_OWNER], ignore_index=True)
    all_OWNER_reqs['object'] = all_OWNER_reqs['object'].apply(lambda x: set(x))
    all_OWNER_reqs = all_OWNER_reqs.groupby('RequirementType', as_index=False).agg(
        {'object': lambda s: set().union(*s)})
    # this final all_OWNER_reqs is all requirementTypes used in both Subject and Owner reqset Ids that have
    # COLLECTION_OWNER and mapped that collection to its modifier owner table and thus object

    # now lets do this same process for non COLLECTION_OWNER reqs
    owner_reqs_no_OWNER = owner_reqs[owner_reqs['CollectionType'] != 'COLLECTION_OWNER'][
        ['RequirementType', 'CollectionType', 'AttachTable']]
    owner_reqs_no_OWNER['object'] = owner_reqs_no_OWNER['CollectionType'].apply(
        lambda x: manual_collection_classification[x]['Owner'])
    subject_reqs_no_OWNER['object'] = subject_reqs_no_OWNER['CollectionType'].apply(
        lambda x: manual_collection_classification[x]['Subject'])
    all_no_OWNER_reqs = pd.concat([subject_reqs_no_OWNER, owner_reqs_no_OWNER], ignore_index=True)[
        ['RequirementType', 'object']]

    # now lets combine and aggregate these requirementTypes
    complete_full_reqs = pd.concat([all_OWNER_reqs, all_no_OWNER_reqs], ignore_index=True)
    complete_full_reqs = complete_full_reqs.groupby("RequirementType", as_index=False)["object"].agg(
        lambda s: set().union(*[x if isinstance(x, set) else {x} for x in s]))

    reqset_no_modifiers['object'] = reqset_no_modifiers['AttachTable'].apply(lambda x: set(TableOwnerObjectMap[x]))
    no_modifiers_reqs = reqset_no_modifiers[['RequirementType', 'object']]
    complete_full_reqs = pd.concat([complete_full_reqs, no_modifiers_reqs], ignore_index=True)
    complete_full_reqs = complete_full_reqs.groupby("RequirementType", as_index=False)["object"].agg(
        lambda s: set().union(*[x if isinstance(x, set) else {x} for x in s]))
    # combine with modifier attach
    complete_full_reqs = pd.concat([complete_full_reqs, final_attach_mod_reqs], ignore_index=True)
    complete_full_reqs = complete_full_reqs.groupby("RequirementType", as_index=False)["object"].agg(
        lambda s: set().union(*[x if isinstance(x, set) else {x} for x in s]))

    req_all_types = None
    for db, engine in db_dict.items():
        df = pd.read_sql(
            f"""SELECT r.RequirementId, RequirementType, Name FROM Requirements r
                    LEFT OUTER JOIN RequirementArguments ra ON ra.RequirementId = r.RequirementId """,
            engine
        )
        req_all_types = combine_db_df(req_all_types, df)

    total_without_mined = req_all_types[~req_all_types['RequirementType'].isin(complete_full_reqs['RequirementType'])]
    missed_req_types = set(total_without_mined['RequirementType'])
    # still 23 missing
    # some were unused as modifiers, like player respawn
    # some are missing full stop even if in use. leave for now

    complete_full_reqs['object'] = complete_full_reqs['object'].apply(lambda x: list(x))
    requirement_object_mapper = complete_full_reqs.set_index("RequirementType")["object"].to_dict()
    object_requirement_mapper = {}
    for req, obj_list in requirement_object_mapper.items():
        for my_obj in obj_list:
            if my_obj not in object_requirement_mapper:
                object_requirement_mapper[my_obj] = []
            object_requirement_mapper[my_obj].append(req)
    with open('resources/unused/RequirementObjectMap.json', 'w') as f:
        json.dump(requirement_object_mapper, f, indent=2, sort_keys=True)
    with open('resources/unused/ObjectRequirementMap.json', 'w') as f:
        json.dump(object_requirement_mapper, f, indent=2, sort_keys=True)
    return requirement_object_mapper, req_all_types

def derive_owner_attach_modifier_reqset(db_dict, both_owners):
    owner_mod_attach_table = None
    missing_mods = list(both_owners['ModifierId'])
    for tbl in attach_tables:
        if len(both_owners) > 0:
            owner_mod_attach_table_per_age = None
            col_list = [key for key, val in db_spec.node_templates[tbl]['foreign_keys'].items() if
                        val == 'Modifiers']
            col_list = col_list + [key for key, val in db_spec.node_templates[tbl].get('extra_fks', {}).items() if
                                   val['ref_table'] == 'Modifiers']
            if len(col_list) == 1:
                col = col_list[0]
            else:
                if tbl == 'NarrativeStory_Rewards':
                    col = 'NarrativeRewardType'
                else:
                    log.info(f'missed table {tbl} for doing modifier attachments')
                    continue
            for age, engine in db_dict.items():
                df = pd.read_sql(
                    f"""SELECT m.{col} FROM {tbl} m WHERE m.{col} IN ('{"', '".join(missing_mods)}');""",
                    engine
                )
                df['AttachTable'] = tbl
                df['Age'] = age
                owner_mod_attach_table_per_age = combine_db_df(owner_mod_attach_table_per_age, df)

            owner_mod_attach_table = combine_db_df(owner_mod_attach_table, owner_mod_attach_table_per_age)
    return owner_mod_attach_table


def make_req_arg_map(db_dict, requirement_object_mapper={}):
    requirements_and_args = None
    for db, engine in db_dict.items():
        df = pd.read_sql(
            f"""SELECT r.RequirementId, r.RequirementType, ra.Name, ra.Value, ra.Type, ra.Extra, ra.SecondExtra,
                        ga.Required, ga.Description, ga.ArgumentType, ga.DatabaseKind, ga.DefaultValue, ga.MinValue, 
                        ga.MaxValue, ga.Type as GameEffectType
                        FROM Requirements r
                        LEFT JOIN RequirementArguments ra ON r.RequirementId = ra.RequirementId
                        LEFT JOIN GameEffectArguments ga ON r.RequirementType = ga.Type AND ra.Name = ga.Name;
                        """,
            engine
        )
        requirements_and_args = combine_db_df(requirements_and_args, df)

    requirements_and_args = requirements_and_args.drop_duplicates(['RequirementId', 'Name'])

    requirements_and_args_agg = (
        requirements_and_args
        .groupby(
            ['RequirementType', 'Name', 'Description', 'Required', 'ArgumentType',
             'DatabaseKind', 'DefaultValue', 'MinValue', 'MaxValue'],
            as_index=False, dropna=False,
        )
        .apply(lambda g: pd.Series({
            "Value": set(g["Value"]),
            "Type,Extra,SecondExtra": set(zip(g["Type"], g["Extra"], g["SecondExtra"], ))
        }))
        .reset_index(drop=True)
    )

    cols = [c for c in requirements_and_args_agg.columns if c not in ("RequirementType", "Name")]

    mid_df = requirements_and_args_agg.set_index(["RequirementType", "Name"])[cols].to_dict(orient="index")

    req_arg_map = {
        rt: {
            name: data
            for (rt2, name), data in mid_df.items()
            if rt2 == rt
        }
        for rt in requirements_and_args_agg["RequirementType"].unique()
    }

    req_arg_map = {key: {} if all(is_nan(i) for i in val.keys()) else val for key, val in req_arg_map.items()}

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
    modifier_arguments_name_df, combined_df = None, None
    for db, engine in db_dict.items():
        df = pd.read_sql(
            """
            SELECT dm.EffectType, dm.CollectionType, m.ModifierId, ma.Name, ma.Value, ma.Type,
             ma.Extra, ma.SecondExtra,
             ga.Required, ga.Description, ga.ArgumentType, ga.DatabaseKind, ga.DefaultValue, ga.MinValue, 
             ga.MaxValue, ga.Type as GameEffectType
            FROM DynamicModifiers dm
            JOIN Modifiers m
            ON m.ModifierType = dm.ModifierType
            LEFT JOIN ModifierArguments ma
            ON ma.ModifierId = m.ModifierId
            LEFT JOIN GameEffectArguments ga ON dm.EffectType = ga.Type AND ma.Name = ga.Name;
            """,
            engine
        )
        if combined_df is None:
            combined_df = df
        else:
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        modifier_arguments_name_df = combine_db_df(modifier_arguments_name_df, df)
    return modifier_arguments_name_df, combined_df


def make_mod_arg_map(modifier_arguments_name_df):

    modifiers_and_args_agg = (
        modifier_arguments_name_df
        .groupby(
            ['EffectType', 'Name', 'Description', 'Required', 'ArgumentType',
             'DatabaseKind', 'DefaultValue', 'MinValue', 'MaxValue'],
            as_index=False, dropna=False,
        )
        .apply(lambda g: pd.Series({
            "Value": set(g["Value"]),
            "Type,Extra,SecondExtra": set(zip(g["Type"], g["Extra"], g["SecondExtra"], ))
        }))
        .reset_index(drop=True)
    )

    cols = [c for c in modifiers_and_args_agg.columns if c not in ("EffectType", "Name")]

    mid_df = modifiers_and_args_agg.set_index(["EffectType", "Name"])[cols].to_dict(orient="index")

    mod_arg_map = {
        rt: {
            name: data
            for (rt2, name), data in mid_df.items()
            if rt2 == rt
        }
        for rt in modifiers_and_args_agg["EffectType"].unique()
    }

    mod_arg_map = {key: {} if all(is_nan(i) for i in val.keys()) else val for key, val in mod_arg_map.items()}
    return mod_arg_map


def collect_modifier_args(db_dict, combined_df):
    df = combined_df.drop_duplicates()
    counts = df.groupby(['EffectType', 'Name']).size().reset_index(name='count')
    gameEffectArgs = pd.read_sql(
        """
            SELECT ga.Type, ga.Name, ga.ArgumentType, ga.DatabaseKind, ga.DefaultValue, ga.Required
            FROM GameEffectArguments ga;
            """,
        list(db_dict.values())[0]
    )
    gameEffectArgs = gameEffectArgs.rename(columns={'Type': 'EffectType'})
    df_effect_args = counts.merge(gameEffectArgs, on=['EffectType', 'Name'], how='left')
    return df_effect_args


def map_effect_type_objects(db_dict, mod_tables, manual_collection_classification, TableOwnerObjectMap):
    comb_df, comb_df_simple, agg_collection_effect_map_combined = None, None, None
    comb_collection_attach_df, combined_collection_attach_df, combined_collection_objects_df = None, None, None
    simple_collection_map = {key: val['Subject'] for key, val in manual_collection_classification.items()}

    for db, engine in db_dict.items():
        for tbl in mod_tables:
            df = pd.read_sql(
                f"""
                           SELECT dm.CollectionType, m.ModifierId, dm.EffectType
                           FROM {tbl} aa
                           JOIN Modifiers m
                           ON m.ModifierId = aa.ModifierId
                           JOIN DynamicModifiers dm
                           ON m.ModifierType = dm.ModifierType;
                           """,
                engine
            )
            df['AttachTable'] = tbl
            comb_df = combine_db_df(comb_df, df)

        comb_df_simple = combine_db_df(comb_df_simple, comb_df)
        agg_df = comb_df.groupby(['CollectionType', 'AttachTable'], as_index=False)['EffectType'].agg(list)
        combined_collection_attach_df = combine_db_df(combined_collection_attach_df, agg_df)

        agg_collection_attach = comb_df.groupby(['AttachTable'], as_index=False)['CollectionType'].agg(set)
        comb_collection_attach_df = combine_db_df(comb_collection_attach_df, agg_collection_attach)

        agg_collection_effect_map = comb_df.groupby(['CollectionType'], as_index=False)['EffectType'].agg(set)
        agg_collection_effect_map_combined = combine_db_df(agg_collection_effect_map_combined,
                                                           agg_collection_effect_map)

        agg_df['CollectionType'] = agg_df['CollectionType'].map(simple_collection_map)
        agg_obj_df = (
            agg_df
            .groupby(['AttachTable', 'CollectionType'], as_index=False)
            .agg(EffectType=('EffectType', lambda x: set().union(*x)))
        )
        combined_collection_objects_df = combine_db_df(combined_collection_objects_df, agg_obj_df)

    # do a version for objects to bypass COLLECTION_OWNER issues
    comb_df_simple["object"] = comb_df_simple["CollectionType"].map(simple_collection_map)

    comb_df_simple.loc[comb_df_simple["CollectionType"] == "COLLECTION_OWNER", "object",] = comb_df_simple.loc[
        comb_df_simple["CollectionType"] == "COLLECTION_OWNER",
        "AttachTable",
    ].map(TableOwnerObjectMap)

    # comb_df_simple['object'] = comb_df_simple['AttachTable'].apply(lambda x: TableOwnerObjectMap[x])
    comb_df_simple = comb_df_simple[['object', 'EffectType']]
    comb_df_simple['object'] = comb_df_simple["object"].apply(lambda x: x if isinstance(x, list) else [x])
    comb_df_simple['object'] = comb_df_simple['object'].apply(lambda x: tuple(x))
    comb_df_simple = comb_df_simple.groupby(['EffectType']).agg(object=('object', lambda x: set().union(*x)))
    comb_df_simple['object'] = comb_df_simple['object'].apply(lambda x: list(x))
    effect_object_mapper = comb_df_simple.to_dict()['object']

    # count values of each modifier attachment table and map the collections they use for modifiers to Objects, manual
    # classification we then want to ascertain what object an attach table is, or at the very least what context it has.

    # attachment collections
    df_dict = comb_collection_attach_df.T.to_dict()
    collect_attach_map = {val['AttachTable']: list(val['CollectionType']) for key, val in df_dict.items()}

    #  collections effects
    df_dict = agg_collection_effect_map_combined.T.to_dict()
    collect_effect_map = {val['CollectionType']: list(val['EffectType']) for key, val in df_dict.items()}


    df_collection_object = (
        combined_collection_objects_df
        .groupby(['AttachTable', 'CollectionType'], as_index=False)
        .agg(EffectType=('EffectType', lambda x: set().union(*x)))
    )
    df_collection_attach_tbl = (
        combined_collection_attach_df
        .groupby(['AttachTable', 'CollectionType'], as_index=False)
        .agg(EffectType=('EffectType', lambda x: set().union(*x)))
    )

    return effect_object_mapper, df_collection_object, df_collection_attach_tbl, collect_attach_map, collect_effect_map

def mine_empty_effects():
    engine = create_engine(f"sqlite:///resources/gameplay-copy-cached-base-content.sqlite")
    df = pd.read_sql(
        """
        SELECT DISTINCT tbl_name
        FROM sqlite_master
        """,
        engine
    )
    table_set = set(df['tbl_name'])
    tables_data = {}
    for table_name in table_set:
        df = pd.read_sql(
            f"""
                    SELECT *
                    FROM {table_name}
                    """,
            engine
        )
        if len(df) > 0:
            tables_data[table_name] = df.to_dict('records')

    with open('resources/mined/PreBuiltData.json', 'w') as f:
        json.dump(tables_data, f, indent=2, sort_keys=True)


def is_nan(x):
    return isinstance(x, float) and math.isnan(x)


def convert(o):
    if isinstance(o, set):
        new_list = list(o)
        new_list.sort()
        return new_list
    raise TypeError


def mine_sql_per_age(db_dict, sql_string):
    comb_df, comb_df_simple = None, None  # for doing the attachment tables
    for db, engine in db_dict.items():
        df = pd.read_sql(sql_string, engine)
        comb_df = combine_db_df(comb_df, df)

    comb_df_simple = combine_db_df(comb_df_simple, comb_df)

    return comb_df_simple


def process_arg_examples(data_examples):
    examples = defaultdict(set)
    for k, v in data_examples.items():
        for key, val in v.items():
            if isinstance(val, list):
                [examples[key].add(i) for i in val]
            else:
                examples[key].add(val)
    return dict(examples)


def mine_type_arg_map(mined_examples, effect_arg_info):
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

    origins = [k for k, v in db_spec.node_templates.items() if v.get('origin_pk') is not None]
    missed_database, databased, database_references, fxs_defines, plural_find_table = {}, {}, {}, {}, False
    for k, v in remaining.items():
        if k in flattened_examples:
            examples = flattened_examples[k]
        else:
            examples = flattened_arg_examples[k]
        find_table = {key: val for key, val in db_spec.all_possible_vals.items()
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
                              db_spec.node_templates[k]['foreign_keys'].get(db_spec.node_templates[k]['primary_keys'][0],
                                                                            'Types') == 'Types'}
            if len(find_table) > 1:
                find_table = {k: v for k, v in find_table.items() if
                              db_spec.node_templates[k].get(
                    'extra_fks', {}).get(db_spec.node_templates[k]['primary_keys'][0], 'Types') == 'Types'}
            # now iterate to see if any values are extra_fks or foreign keys
            if len(find_table) > 1:
                fks = {k: list(db_spec.node_templates[k]['foreign_keys'].values()) + [j['ref_table']
                    for j in db_spec.node_templates[k].get('extra_fks', {}).values()] for k, v in find_table.items()}
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


def update_loc_spec(db_dict):

    with open('resources/db_spec/LocalizedTags.json') as f:
        localised = json.load(f)

    localised = set(localised)

    localise_table_cols = defaultdict(list)
    for db, engine in db_dict.items():

        for table_name, info in db_spec.node_templates.items():
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
        db_spec.node_templates[table_name]['localised'] = []
        for col in table_cols:
            db_spec.node_templates[table_name]['localised'].append(col)
        db_spec.node_templates[table_name]['localised'] = list(set(db_spec.node_templates[table_name]['localised']))

    db_spec.update_node_templates(db_spec.node_templates)


def update_possible_vals_spec(db_dict, metadata):
    age_possible_vals = {}
    for age_type, engine in db_dict.items():
        result = {}
        with engine.connect() as conn:
            for table_name, table in metadata.tables.items():
                table_dict = {}
                spec = db_spec.node_templates[table_name]
                for column in table.c:
                    if table_name in ['ModifierArguments', 'RequirementArguments'] and column.name == 'Value':
                        continue
                    not_covered = column.name not in db_spec.all_possible_vals[table_name]
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
                if table_name not in db_spec.all_possible_vals:
                    db_spec.all_possible_vals[table_name] = {}
                if column.name not in db_spec.all_possible_vals[table_name]:
                    db_spec.all_possible_vals[table_name][column.name] = combined_vals

    for age, poss_val_dict in age_possible_vals.items():
        for table_name, table in poss_val_dict.items():
            for column, values in table.items():
                if len(values) < 300:
                    if table_name not in db_spec.possible_vals[age]:
                        db_spec.possible_vals[age][table_name] = {}
                    if column not in db_spec.possible_vals[age][table_name]:
                        db_spec.possible_vals[age][table_name][column] = values

    all_cols = {f'{k}_{col}': items for k, v in all_possible_vals.items() for col, items in v.items()}
    all_cols_tuples = [(k, v) for k, v in all_cols.items()]
    all_cols_tuples.sort(key=lambda t: len(t[1]), reverse=True)

    db_spec.update_possible_vals(db_spec.possible_vals)
    db_spec.update_all_vals(db_spec.all_possible_vals)


def extract_argument_stats(agg_df, game_effect, effect_id_name):
    # get all modifierIds and group by id
    counts = agg_df.groupby(effect_id_name)[game_effect].nunique()
    bad = counts[counts != 1]           # 0 for effects, 3 for reqs, likely due to age shift.
    # ensures we can use first agg

    modifier_id_agg = agg_df[[effect_id_name, game_effect, 'Name']].groupby(
        effect_id_name, as_index=True).agg({game_effect: 'first', 'Name': frozenset})

    required = {}

    for effect, df in modifier_id_agg.groupby(game_effect):
        sets = list(map(set, df['Name']))
        required[effect] = set.intersection(*sets)

    exclusionary = {}

    for effect, df in modifier_id_agg.groupby(game_effect):
        sets = list(map(set, df['Name']))
        all_names = set.union(*sets)

        pairs = []
        for a, b in combinations(all_names, 2):
            covers_all = all((a in s) or (b in s) for s in sets)
            never_together = all(not ({a, b} <= s) for s in sets)

            if covers_all and never_together:
                pairs.append({a, b})

        exclusionary[effect] = pairs

    exclusion_stats = {}

    for effect, df in modifier_id_agg.groupby(game_effect):
        sets = list(map(set, df['Name']))
        total = len(sets)
        all_names = set.union(*sets)

        stats = {}
        for a, b in combinations(all_names, 2):
            only_a = sum((a in s) and (b not in s) for s in sets)
            only_b = sum((b in s) and (a not in s) for s in sets)
            both = sum((a in s) and (b in s) for s in sets)
            neither = total - only_a - only_b - both

            stats[(a, b)] = {
                'total': total,
                'only_a': only_a,
                'only_b': only_b,
                'both': both,
                'neither': neither,
                'coverage': 1 - neither / total,
                'exclusivity': 1 - both / total,
            }

        exclusion_stats[effect] = stats

    return required, exclusionary
