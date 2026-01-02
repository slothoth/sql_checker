import pandas as pd
from sqlalchemy import create_engine
import json
import math
from graph.db_spec_singleton import db_spec, attach_tables


def combine_db_df(df_combined, df_to_add):
    if df_combined is None:
        df_combined = df_to_add
    else:
        df_combined = pd.concat([df_combined, df_to_add], ignore_index=True)
    return df_combined


def gather_effects(db_dict):
    combined_df, combined_collection_objects_df, combined_collection_attach_df, comb_collection_attach_df = None, None, None, None
    agg_collection_effect_map_combined, modifier_arguments_name_df = None, None

    with open('resources/CollectionObjectManualAssignment.json') as f:
        manual_collection_classification = json.load(f)

    with open('resources/CollectionOwnerMap.json') as f:
        TableOwnerObjectMap = json.load(f)

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
            gameEffectArgs = pd.read_sql(
        """
            SELECT ga.Type, ga.Name, ga.ArgumentType, ga.DatabaseKind, ga.DefaultValue, ga.Required
            FROM GameEffectArguments ga;
            """,
            engine
        )
        modifier_arguments_name_df = combine_db_df(modifier_arguments_name_df, df)

    ########################################################################################
    modifier_arguments_name_df = modifier_arguments_name_df.drop_duplicates(['EffectType', 'Name'])

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

    ########################################################################################

    df = combined_df.drop_duplicates()
    counts = df.groupby(['EffectType', 'Name']).size().reset_index(name='count')
    gameEffectArgs = gameEffectArgs.rename(columns={'Type': 'EffectType'})
    df_effect_args = counts.merge(gameEffectArgs, on=['EffectType', 'Name'], how='left')
    df_effect_args.to_csv('resources/ModifierEffectArguments.csv')

    simple_collection_map = {key: val['Subject'] for key, val in manual_collection_classification.items()}
    mod_tables = ['EnterStageModifiers', 'EnvoysInActionModifiers', 'EnvoysInStageModifiers',
                  'GovernmentModifiers', 'MementoModifiers', 'TraditionModifiers', 'TraitModifiers',
                  'UnitAbilityModifiers', 'UnitPromotionModifiers', 'BeliefModifiers', 'CityStateBonusModifiers',
                  'ConstructibleModifiers', 'GameModifiers', 'GoldenAgeModifiers', 'MetaprogressionModifiers',
                  'NarrativeRewards', 'PlayerModifiers', 'ProjectModifiers']

    comb_df, comb_df_simple = None, None # for doing the attachment tables
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

    df_collection_object_table = (
        combined_collection_objects_df
        .groupby(['AttachTable', 'CollectionType'], as_index=False)
        .agg(EffectType=('EffectType', lambda x: set().union(*x)))
    )
    df_collection_attach_table = (
        combined_collection_attach_df
        .groupby(['AttachTable', 'CollectionType'], as_index=False)
        .agg(EffectType=('EffectType', lambda x: set().union(*x)))
    )

    df_collection_object_table.to_csv('resources/CollectionObjectAttach.csv')
    df_collection_attach_table.to_csv('resources/CollectionAttach.csv')

    # attachment collections
    df_dict = comb_collection_attach_df.T.to_dict()
    dict_d = {val['AttachTable']: list(val['CollectionType'])for key, val in df_dict.items()}
    with open('resources/CollectionAttachMap.json', 'w') as f:
        json.dump(dict_d, f, indent=2)

    #  collections effects
    df_dict = agg_collection_effect_map_combined.T.to_dict()
    dict_d = {val['CollectionType']: list(val['EffectType']) for key, val in df_dict.items()}
    with open('resources/CollectionEffectMap.json', 'w') as f:
        json.dump(dict_d, f, indent=2)


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



    with open('resources/ModArgInfo.json', 'w') as f:
        json.dump(mod_map, f, indent=2, default=convert)

    # --------------------------------------------------------------------------------
    # -------------------------   Requirements    ------------------------------------
    # --------------------------------------------------------------------------------
    # first get requirements from modifier tables
    mine_requirements(manual_collection_classification, db_dict, mod_tables, TableOwnerObjectMap)


def mine_requirements(manual_collection_classification, db_dict, mod_tables, TableOwnerObjectMap):
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
    del owner_req_combined_df       # deletes just cause i like using debugger and clutter
    del subject_req_combined_df     # and cba refactoring these collating logics into functions
    # now requirements from tables not attached to modifiers
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

    del reqset_tables_per_age
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

    del combined_modifier_attach
    # the COLLECTION OWNER of attached modifiers is the table of the first modifier that causes attachment
    modifiers_full = modifiers_full.drop_duplicates()
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
    missing_mods = list(both_owners['ModifierId'])
    owner_mod_attach_table = None
    for tbl in attach_tables:
        if len(both_owners) > 0:
            owner_mod_attach_table_per_age = None
            col_list = [key for key, val in db_spec.node_templates[tbl]['foreign_keys'].items() if val == 'Modifiers']
            col_list = col_list + [key for key, val in db_spec.node_templates[tbl].get('extra_fks', {}).items() if
                                   val['ref_table'] == 'Modifiers']
            if len(col_list) == 1:
                col = col_list[0]
            else:
                print('ahhh')
            for age, engine in db_dict.items():
                df = pd.read_sql(
                    f"""SELECT m.{col} FROM {tbl} m WHERE m.{col} IN ('{"', '".join(missing_mods)}');""",
                    engine
                )
                df['AttachTable'] = tbl
                df['Age'] = age
                owner_mod_attach_table_per_age = combine_db_df(owner_mod_attach_table_per_age, df)

            owner_mod_attach_table = combine_db_df(owner_mod_attach_table, owner_mod_attach_table_per_age)
    del owner_mod_attach_table_per_age
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
    owner_reqs_no_OWNER = owner_reqs[owner_reqs['CollectionType'] != 'COLLECTION_OWNER'][
        ['RequirementType', 'CollectionType', 'AttachTable']]

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
    # TODO see if we have all RequirementTypes now
    # hang on. Do we need to separate COLLECTION_OWNER for OwnerRequirementSetIds? The collection
    # is for the modifier, and the owner will always just be the owner table for that req. oh well, should
    # not be a problem
    # should be 232 according to SELECT DISTINCT RequirementType, but is actually like 71. because of no arg reqs?
    # find the requirements without arguments, was exactly 100. so quite a lot of missing reqs, 132.

    req_all_types = None
    for db, engine in db_dict.items():
        df = pd.read_sql(
            f"""SELECT RequirementId, RequirementType FROM Requirements r;""",
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
    with open('resources/RequirementObjectMap.json', 'w') as f:
        json.dump(requirement_object_mapper, f, indent=2)
    with open('resources/ObjectRequirementMap.json', 'w') as f:
        json.dump(object_requirement_mapper, f, indent=2)

    # now a simpler task. Get all possible Requirement Arguments Names, Values, Extra, Extra2 and Type
    # combine with GameEffectArguments to get extra info on each if possible
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

    req_map = {key: {'Arguments': val, 'Object': requirement_object_mapper.get(key, [])} for key, val in req_arg_map.items()}

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
    with open('resources/RequirementInfo.json', 'w') as f:
        json.dump(req_map, f, indent=2, default=convert)

    with open('resources/GossipInfo.json', 'w') as f:
        json.dump(gossips, f, indent=2, default=convert)


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

    with open('resources/PreBuiltData.json', 'w') as f:
        json.dump(tables_data, f, indent=2)


def is_nan(x):
    return isinstance(x, float) and math.isnan(x)
def convert(o):
    if isinstance(o, set):
        return list(o)
    raise TypeError