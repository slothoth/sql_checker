import glob
import re
import sqlparse
from sqlglot.errors import ParseError
import itertools
from itertools import product

from xml_handler import read_xml
from model import convert_xml_to_sql
from ORM import create_instances_from_sql, get_table_and_key_vals, build_fk_index
from graph.windows import get_combo_value
from graph.db_spec_singleton import modifier_system_tables, mod_arg_param_map, req_arg_param_map, ages
# handles extracting a mod from a folder and converting it into our graph format
# this is a bitch because it needs to parse the .modinfo
# unsure if how this will deal with different ages. Possibly our main graph model
# needs to be updated to have 3 separate tabs for each different age.


def parse_mod_folder(mod_folder_path, graph):
    modinfo_list = [f for f in glob.glob(f'{mod_folder_path}/*.modinfo*')]
    if len(modinfo_list) != 1:
        return False

    modinfo_dict = parse_modinfo(modinfo_list[0], mod_folder_path)
    sql_info_dict = modinfo_into_jobs(modinfo_dict)
    possible_workloads = retry_file_permutations(modinfo_dict)
    mod_set = set()
    for crit_name, crit_info in modinfo_dict['criteria'].items():
        for crit_type, crit_list in crit_info.items():
            if 'Mods' in crit_type:
                for mod in crit_list:
                    mod_set.add(mod)

    # make a decision on which ORM to build
    age, mod_dict = get_combo_value(graph.viewer(), ages, list(mod_set))
    if age is None:
        return
    age_dict = {i: False for i in ages if i != age}
    age_dict[age] = True
    mod_dict.update(age_dict)
    file_list = get_files(possible_workloads, mod_dict)
    orm_list = mod_info_into_orm(sql_info_dict, file_list)
    build_graph_from_orm(graph, orm_list)
    return True


def parse_modinfo(modinfo_path, mod_folder_path):
    xml_ = read_xml(modinfo_path)
    xml_ = xml_['{ModInfo}Mod']
    mod_id = xml_['@id']
    criterias = xml_['{ModInfo}ActionCriteria']['{ModInfo}Criteria']
    criteria_dict = {}
    for criteria_info in criterias:
        criteria_dict[criteria_info['@id']] = {}
        specific_criteria = criteria_dict[criteria_info['@id']]
        for key, val in criteria_info.items():
            if key == '@id':
                continue
            if 'ModInUse' in key:
                if isinstance(val, dict):
                    if val.get('@inverse') == '1':
                        if 'ModsOff' in specific_criteria:
                            specific_criteria['ModsOff'].append(val['#text'])
                        else:
                            specific_criteria['ModsOff'] = [val['#text']]
                    else:
                        add_mods_on(specific_criteria, val['#text'])
                elif isinstance(val, str):
                    add_mods_on(specific_criteria, val)
                else:
                    raise Exception('Unknown type for xml handler')

            if 'AgeInUse' in key:
                if isinstance(val, dict):
                    print('uhhh, no idea parsing xml as Age in Use but is dict')
                elif isinstance(val, str):
                    if 'AgeOn' in specific_criteria:
                        specific_criteria['AgeOn'].append(val)
                    else:
                        specific_criteria['AgeOn'] = [val]

    # criterias
    # do we handle dependencies?
    action_groups_dict = {}
    action_groups = xml_['{ModInfo}ActionGroups']['{ModInfo}ActionGroup']
    for action_group in action_groups:
        scope = action_group.get('@scope', None)
        if scope is not None:
            if scope == 'shell':
                continue                # currently not handling shell
            elif scope == 'game':
                action_group_id = action_group['@id']
                action_groups_dict[action_group_id] = {'criteria': action_group.get('@criteria', 'always'),
                                                       'filepaths': []}
                actions = action_group.get('{ModInfo}Actions', None)
                for action_type, action_dict in actions.items():
                    if 'UpdateDatabase' in action_type:
                        for item_name, file_path_list in action_dict.items():
                            if isinstance(file_path_list, str):
                                full_file_path = f"{mod_folder_path}/{file_path_list}"
                                action_groups_dict[action_group_id]['filepaths'].append(full_file_path)
                            else:
                                for mod_file_path in file_path_list:
                                    full_file_path = f"{mod_folder_path}/{mod_file_path}"
                                    action_groups_dict[action_group_id]['filepaths'].append(full_file_path)
            else:
                raise Exception(f'scope on mod {mod_id},'
                      f' with action {action_group.get("@id", "unknown")} had unregistered scope: {scope}')
    mod_info_dict = {'criteria': criteria_dict, 'action_groups': action_groups_dict, 'base_folder': mod_folder_path}
    return mod_info_dict


def add_mods_on(criteria_dict, val):
    if 'ModsOn' in criteria_dict:
        criteria_dict['ModsOn'].append(val)
    else:
        criteria_dict['ModsOn'] = [val]


def modinfo_into_jobs(mod_info_dict):
    base_folder_path = mod_info_dict['base_folder']
    mod_info_dict['sql'] = {}
    for action_group_id, action_group_info in mod_info_dict['action_groups'].items():
        for db_file_path in action_group_info['filepaths']:
            short_name = db_file_path.replace(f'{base_folder_path}/', '')
            if db_file_path.endswith('.xml'):
                statements, xml_errors = convert_xml_to_sql(db_file_path)
                if isinstance(statements, str):
                    print(f'{db_file_path} was an empty file. Skipping it.')
                    continue
                mod_info_dict['sql'][short_name], xml_errors = convert_xml_to_sql(db_file_path)

            elif db_file_path.endswith('.sql'):
                try:
                    with open(db_file_path, 'r') as file:
                        sql_contents = file.read()
                except UnicodeDecodeError as e:
                    print(f'Bad unicode, trying windows-1252: {e}')
                    with open(db_file_path, 'r', encoding='windows-1252') as file:
                        sql_contents = file.read()
                comment_cleaned = re.sub(r'--.*?\n', '', sql_contents, flags=re.DOTALL)
                mod_info_dict['sql'][short_name] = sqlparse.split(comment_cleaned)
            else:
                raise Exception(f'modinfo path does not end with .xml or .sql: {db_file_path}')
    return mod_info_dict


def mod_info_into_orm(sql_info_dict, file_path_list):
    orm_list = []
    for file_path in file_path_list:
        short_path = file_path.replace(f'{sql_info_dict["base_folder"]}/', '')
        sql_commands = sql_info_dict['sql'][short_path]
        for sql_text in sql_commands:
            try:
                instance_list = create_instances_from_sql(sql_text)
                orm_list.extend(instance_list)
            except ParseError as e:
                print(f'could not parse file {short_path}: {e}')

    return orm_list

# technically we cant get the value of the child port with just fk_index. Consider
# parent Types.Type and child DynamicModifiers. All 3 columns in DynamicModifiers could link to Types.


def connect_foreign_keys(fk_index, nodes_dict):
    for (parent_table, parent_col, parent_pk), children in fk_index.items():
        parent_node = nodes_dict[(parent_table, parent_pk)]

        for child_table, child_pk in children:
            child_node = nodes_dict[(child_table, child_pk)]
            primary_key = parent_pk[0]   # technically multiple pks possible, but ports system means just connect one
            src_ports = [i for i in parent_node.output_ports() if i.name() == parent_col]
            if len(src_ports) != 1:
                raise Exception('plural pk col somehow when trying to build graph of loaded mod foreign keys')
            src_port = src_ports[0]
            connect_port_name = child_node.get_link_port(parent_node.get_property('table_name'), primary_key)
            if connect_port_name:
                port_index = next((i for i, s in enumerate(child_node.input_ports()) if s.name() == connect_port_name), 0)
                src_port.connect_to(child_node.input_ports()[port_index])


def criteria_matches(criteria, age):
    if 'AgeOn' in criteria:
        return age in criteria['AgeOn']
    return True


def possible_file_loads(mod_info_dict):
    action_groups = mod_info_dict['action_groups']
    criteria = mod_info_dict['criteria']
    criterion_set = set()
    for crit_dict in criteria.values():
        for crit_type, crit_list in crit_dict.items():
            for item in crit_list:
                if 'On' in crit_type:
                    criterion_set.add(item + '_ON')

    criteria_permutations = list(itertools.permutations(criterion_set))
    all_cases = []

    for age in ages:
        paths = []
        conditions = []

        for group_name, group in action_groups.items():
            crit = criteria[group['criteria']]
            if criteria_matches(crit, age):
                paths.extend(group['filepaths'])
                if crit:
                    conditions.append(group['criteria'])
        all_cases.append({
            'paths': paths,
            'conditions': conditions if len(conditions) > 0 else ['always']
        })
    return all_cases


def retry_file_permutations(data):
    criteria = data['criteria']
    actions = data['action_groups']
    check_keys = set()
    for crit in criteria.values():
        for k, v in crit.items():
            base, vv, _ = _norm_check(k, v)
            check_keys.add((base, vv))
    check_keys = sorted(check_keys)
    states = []
    for bits in product([False, True], repeat=len(check_keys)):
        states.append(dict(zip(check_keys, bits)))
    results = {}
    for state in states:
        loaded = set()
        for _, action in actions.items():
            crit = criteria[action["criteria"]]
            ok = True
            for k, v in crit.items():
                base, vv, want_on = _norm_check(k, v)
                actual_on = state[(base, vv)]
                if actual_on != want_on:
                    ok = False
                    break
            if ok:
                loaded.update(action["filepaths"])
        results[frozenset(state.items())] = frozenset(loaded)

    tree = {}
    for state, files in results.items():
        if not files:
            continue

        cursor = tree
        for (base, vv), on in sorted(state):
            value = vv[0]
            cursor = cursor.setdefault(base, {})
            cursor = cursor.setdefault(value, {})
            cursor = cursor.setdefault("ON" if on else "OFF", {})

        cursor["files"] = list(files)

    compressed_tree = compress(tree)
    return compressed_tree


def _norm_check(k, v):
    vv = tuple(v)
    if k.endswith("On"):
        base = k[:-2]
        return (base, vv, True)
    if k.endswith("Off"):
        base = k[:-3]
        return (base, vv, False)
    return (k, vv, True)


def compress(node):
    if not isinstance(node, dict):
        return node
    if "files" in node and len(node) == 1:
        return node
    for k in list(node.keys()):
        node[k] = compress(node[k])
    if set(node.keys()) == {"ON", "OFF"}:
        on = node["ON"]
        off = node["OFF"]
        if on == off:
            return on

    return node


def get_files(tree, state):
    out = []
    seen = set()

    def add(fs):
        for f in fs:
            if f not in seen:
                seen.add(f)
                out.append(f)

    def walk(node):
        if not isinstance(node, dict):
            return

        if "files" in node:
            add(node["files"])
            return

        if len(node) != 1:
            return

        base, values = next(iter(node.items()))

        if base == "Age":
            for age, branches in values.items():
                on = state.get(age, False)
                key = "ON" if on else "OFF"
                if key in branches:
                    walk(branches[key])
                    return
            return

        for name, branches in values.items():
            on = state.get(name, False)
            key = "ON" if on else "OFF"
            if key in branches:
                walk(branches[key])
                return

    walk(tree)
    return out


def build_graph_from_orm(graph, orm_list):
    fk_index = build_fk_index(orm_list)
    graph.blockSignals(True)
    graph.viewer().blockSignals(True)
    modifier_skipped, modifier_system_entries = {}, {}
    for count, orm_instance in enumerate(orm_list):
        table_name, col_dicts, pk_tuple = get_table_and_key_vals(orm_instance)
        if table_name in modifier_system_tables:
            if table_name not in modifier_system_entries:
                modifier_system_entries[table_name] = {}
            modifier_system_entries[table_name][pk_tuple] = col_dicts
            modifier_skipped[pk_tuple] = True

    # root at dynamicModifiers          TODO is this right? should we filter out any that have existing dynamicModifiers?
    # Would be good to be able to ref a existing dynamic Modifier while using mod args stuff
    game_effect_nodes = {k[0]: {'DynamicModifier': v} for k, v in modifier_system_entries.get('DynamicModifiers', {}).items()}
    for mod_type, v in game_effect_nodes.items():
        matching_mods = {k: v for k, v in modifier_system_entries.get('Modifiers', {}).items() if v['ModifierType'] == mod_type}
        mod_taken = False
        for pk_tuple, entry_info in matching_mods.items():
            if mod_taken:
                modifier_skipped[pk_tuple] = False
            else:
                modifierId = pk_tuple[0]
                mod_taken = True
                game_effect_nodes[mod_type]['Modifiers'] = entry_info
                # find all mod args
                matching_modargs = {k: v for k, v in modifier_system_entries.get('ModifierArguments', {}).items()
                                    if v['ModifierId'] == modifierId}
                for p_tup, mod_arg_info in matching_modargs.items():
                    if 'Arguments' not in game_effect_nodes[mod_type]:
                        game_effect_nodes[mod_type]['Arguments'] = []
                    game_effect_nodes[mod_type]['Arguments'].append(mod_arg_info)

                # find mod string
                matching_modstring = {k: v for k, v in modifier_system_entries.get('ModifierStrings', {}).items()
                                    if v['ModifierId'] == modifierId}
                mod_string_taken = False            # technically we could have multiple but eh
                for p_tup, mod_string_info in matching_modstring.items():
                    if mod_string_taken:
                        modifier_skipped[pk_tuple] = False          # process these normally
                    else:
                        mod_string_taken = True
                        game_effect_nodes[mod_type]['ModifierStrings'] = mod_string_info

    nodes_dict = {}
    for count, orm_instance in enumerate(orm_list):
        table_name, col_dicts, pk_tuple = get_table_and_key_vals(orm_instance)
        if modifier_skipped.get(pk_tuple, True):
            class_name = f"{table_name.title().replace('_', '')}Node"
            node = graph.create_node(f'db.table.{table_name.lower()}.{class_name}')
            node.set_spec(col_dicts)
            nodes_dict[(table_name, pk_tuple)] = node
            print(f'there are now {count} nodes')

    for modifier_type, effects_info in game_effect_nodes.items():
        node = graph.create_node('db.game_effects.GameEffectNode')
        # set spec   # dynamicModifiers first
        dyn_mod_info = effects_info.get('DynamicModifier', {})
        effect_type = dyn_mod_info['EffectType']
        new_props = {}
        for col, val in dyn_mod_info.items():
            new_props[col] = val

        modifier_info = effects_info.get('Modifiers', {})
        for col, val in modifier_info.items():
            if col == 'SubjectRequirementSetId':
                col = 'SubjectReq'
            if col == 'OwnerRequirementSetId':
                col = 'OwnerReq'

            new_props[col] = val

        string_info = effects_info.get('ModifierStrings', {})
        for col, val in string_info.items():
            new_props[col] = val

        # do modarg conversion
        mod_args = effects_info.get('Arguments', {})
        for arg_info in mod_args:        # currently only doing name value
            arg_name = arg_info['Name']
            # use name to get param

            param_name = mod_arg_param_map[effect_type][mod_args[0]['Name']]
            arg_value = arg_info['Value']
            new_props[param_name] = arg_value

        node.set_spec(new_props)
    # if effect dict emptry, there could be a missed dynamicModifier

    connect_foreign_keys(fk_index, nodes_dict)
    graph.blockSignals(False)
    graph.viewer().blockSignals(False)
    return orm_list
