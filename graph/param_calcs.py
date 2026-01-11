import math
from collections import defaultdict
from itertools import combinations
from graph.utils import flatten


def stats_find_arg_length(argument_info):
    length_args = defaultdict(list)
    for key, val in argument_info.items():
        len_args = len(val['Arguments'])
        length_args[len_args].append(key)
    return length_args


convert_map = {'Boolean': 'bool', 'uint': 'int', None: 'text', '': 'text'}


def norm_type(t):
    t = convert_map.get(t, t)
    if isinstance(t, float) and math.isnan(t):
        return 'text'
    return t


def build_arg_type_list_map(argument_info, tightness=0.0):
    """
    Builds a map from Argument_Info, where each key is the same as the dict, but each val is dict of the arguments
    in each original val, with the key being their new string name and the value being their original arg name.
    Tightness is a float from 0.0 to 1.0. low tightness minimises the number of unique string names. High tightness
    minimises differences between keys, so that changing key value will retain say, the Amount arg name as param_int_1
    on both. Also produces an inverse for like Amount: param_int_1 and full list of keys
    """
    by_type_by_effect = defaultdict(lambda: defaultdict(set))
    freq = defaultdict(lambda: defaultdict(int))

    for effect, val in argument_info.items():
        for arg, arg_info in val['Arguments'].items():
            t = norm_type(arg_info['ArgumentType'])
            by_type_by_effect[t][effect].add(arg)

    for t, effmap in by_type_by_effect.items():
        for args in effmap.values():
            for a in args:
                freq[t][a] += 1

    color_by_type = {}

    for t, effmap in by_type_by_effect.items():
        nodes = set()
        adj = defaultdict(set)

        for args in effmap.values():
            args = list(args)
            nodes.update(args)
            for a, b in combinations(args, 2):
                adj[a].add(b)
                adj[b].add(a)

        nodes = list(nodes)
        deg = {a: len(adj[a]) for a in nodes}
        order = sorted(nodes, key=lambda a: (-freq[t][a], -deg[a], a))

        color = {}
        max_c = 0
        for a in order:
            used = {color[n] for n in adj[a] if n in color}
            c = 1
            while c in used:
                c += 1
            color[a] = c
            if c > max_c:
                max_c = c

        n_nodes = len(nodes)
        min_colors = max_c
        target = int(round(min_colors + max(0.0, min(1.0, tightness)) * (n_nodes - min_colors)))
        target = max(min_colors, min(n_nodes, target))

        if target > min_colors:
            classes = defaultdict(list)
            for a, c in color.items():
                classes[c].append(a)

            next_c = min_colors
            while next_c < target:
                candidates = [(c, classes[c]) for c in classes if len(classes[c]) > 1]
                if not candidates:
                    break
                c_old, group = max(
                    candidates,
                    key=lambda item: (sum(freq[t][a] for a in item[1]), len(item[1]), item[0])
                )
                a_move = max(group, key=lambda a: (freq[t][a], deg[a], a))
                group.remove(a_move)
                next_c += 1
                color[a_move] = next_c
                classes[next_c] = [a_move]

        color_by_type[t] = color

    arg_type_list_map = {}
    for effect, val in argument_info.items():
        m = {}
        for arg, arg_info in val['Arguments'].items():
            t = norm_type(arg_info['ArgumentType'])
            i = color_by_type[t][arg]
            m[f'param_{t}_{i}'] = arg
        arg_type_list_map[effect] = m

    all_unique_fields = list(set(flatten([list(val.keys()) for key, val in arg_type_list_map.items()])))
    all_unique_fields.sort()
    return arg_type_list_map, all_unique_fields


def build_param_map(all_arg_fields, arg_type_list_map):
    default_map = {}
    for param in all_arg_fields:
        if 'bool' in param:
            default_map[param] = False
        elif 'database' in param:
            default_map[param] = ''
        elif 'text' in param:
            default_map[param] = ''
        elif 'int' in param:
            default_map[param] = 0
        elif 'float' in param:
            default_map[param] = 0.0
        else:
            print(f'missed setting default value for {param}')
    arg_defaults = {key: {k: default_map[k] for k, v in val.items()}
                           for key, val in arg_type_list_map.items()}
    return default_map, arg_defaults


# now a version to rebuild when alreadt existing:

def parse_param_field(field):
    if not field.startswith("param_"):
        return None, None
    parts = field.split("_")
    if len(parts) < 3:
        return None, None
    try:
        return parts[1], int(parts[2])
    except:
        return None, None


def build_effect_args_by_type(requirement_argument_info):
    by_type_by_effect = defaultdict(lambda: defaultdict(list))
    for effect, val in requirement_argument_info.items():
        for arg, arg_info in val["Arguments"].items():
            t = norm_type(arg_info.get("ArgumentType"))
            by_type_by_effect[t][effect].append(arg)
    return by_type_by_effect


def build_graph_and_freq(by_type_by_effect):
    adj = defaultdict(lambda: defaultdict(set))
    freq = defaultdict(lambda: defaultdict(int))
    for t, effmap in by_type_by_effect.items():
        for args in effmap.values():
            s = list(dict.fromkeys(args))
            for a in s:
                freq[t][a] += 1
            for a, b in combinations(s, 2):
                adj[t][a].add(b)
                adj[t][b].add(a)
    return adj, freq


def seed_from_old_map(old_req_arg_type_list_map):
    old_color = defaultdict(dict)
    used = defaultdict(set)
    for effect, m in old_req_arg_type_list_map.items():
        for p, arg in m.items():
            t, idx = parse_param_field(p)
            if t is None:
                continue
            if arg in old_color[t]:
                used[t].add(old_color[t][arg])
            else:
                old_color[t][arg] = idx
                used[t].add(idx)
    return old_color, used


def incremental_assign(old_req_arg_type_list_map, requirement_argument_info):
    by_type_by_effect = build_effect_args_by_type(requirement_argument_info)
    adj, freq = build_graph_and_freq(by_type_by_effect)
    old_color, used = seed_from_old_map(old_req_arg_type_list_map)

    color = defaultdict(dict)
    for t, m in old_color.items():
        color[t].update(m)

    for t, effmap in by_type_by_effect.items():
        nodes = set()
        for args in effmap.values():
            nodes.update(args)

        deg = {a: len(adj[t][a]) for a in nodes}
        new_nodes = [a for a in nodes if a not in color[t]]
        new_nodes.sort(key=lambda a: (-freq[t][a], -deg[a], a))

        for a in new_nodes:
            forbidden = {color[t][n] for n in adj[t][a] if n in color[t]}
            if not used[t]:
                idx = 1
                used[t].add(idx)
            else:
                idx = 1
                while idx in forbidden:
                    idx += 1
                used[t].add(idx)
            color[t][a] = idx

        for effect, args in effmap.items():
            args = list(dict.fromkeys(args))
            buckets = defaultdict(list)
            for a in args:
                buckets[color[t][a]].append(a)

            conflicts = [grp for grp in buckets.values() if len(grp) > 1]
            if not conflicts:
                continue

            def move_cost(a):
                return (0 if a not in old_color[t] else 1, freq[t][a], a)

            for grp in conflicts:
                grp_sorted = sorted(grp, key=move_cost)
                keep = grp_sorted[-1]
                for a in grp_sorted[:-1]:
                    forbidden = {color[t][n] for n in adj[t][a] if n in color[t]}
                    forbidden.add(color[t][keep])
                    idx = 1
                    while idx in forbidden:
                        idx += 1
                    used[t].add(idx)
                    color[t][a] = idx

    out = {}
    for effect, val in requirement_argument_info.items():
        m = {}
        for arg, arg_info in val["Arguments"].items():
            t = norm_type(arg_info.get("ArgumentType"))
            idx = color[t][arg]
            m[f"param_{t}_{idx}"] = arg
        out[effect] = m
    return out
