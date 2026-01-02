import json
import math
from threading import Lock
import os
import sys
from pathlib import Path

if sys.platform == 'win32':
    import winreg


class ResourceLoader:
    _instance = None
    _lock = Lock()
    node_templates = {}
    possible_vals = {}
    all_possible_vals = {}
    collection_effect_map = {}
    civ_config = ''
    workshop = ''
    civ_install = ''
    age = ''
    patch_time = 0.0
    patch_change = False
    _files = {}

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_resources()
        return cls._instance

    def _load_resources(self):
        self._files = {
            'node_templates': self.resource_path("resources/db_spec.json"),
            'possible_vals': self.resource_path('resources/db_possible_vals.json'),
            'all_possible_vals': self.resource_path('resources/all_possible_vals.json'),
            'collection_effect_map': self.resource_path('resources/CollectionEffectMap.json'),
            'metadata': self.resource_path('resources/metadata.json'),
        }
        self.node_templates = self._read_file(self._files['node_templates'])
        self.possible_vals = self._read_file(self._files['possible_vals'])
        self.all_possible_vals = self._read_file(self._files['all_possible_vals'])
        self.collection_effect_map = self._read_file(self._files['collection_effect_map'])

        if not os.path.exists(self._files['metadata']):
            self.civ_config = find_civ_config()
            self.workshop = find_workshop()
            self.civ_install = find_civ_install()
            self.age = 'AGE_ANTIQUITY'
            self.patch_time = None
            self.metadata = {'civ_config':  self.civ_config,
                             'workshop': self.workshop,
                             'civ_install': self.civ_install,
                             'age': self.age,
                             'patch_time': self.patch_time
                             }
        else:
            self.metadata = self._read_file(self._files['metadata'])
            self.civ_config = self.metadata['civ_config']
            self.workshop = self.metadata['workshop']
            self.civ_install = self.metadata['civ_install']
            self.age = self.metadata['age']
            self.patch_time = self.metadata['patch_time']
        self.check_firaxis_patched()

    @staticmethod
    def _read_file(path):
        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def _write_file(path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def update_node_templates(self, data):
        self.node_templates = data
        self._write_file(self._files['node_templates'], data)

    def update_possible_vals(self, data):
        self.possible_vals = data
        self._write_file(self._files['possible_vals'], data)

    def update_all_vals(self, data):
        self.all_possible_vals = data
        self._write_file(self._files['all_possible_vals'], data)

    def update_game_effects(self,data):
        self.game_effects_info = data
        self._write_file(self._files['game_effects_info'], data)

    def update_civ_config(self,data):
        self.civ_config = data
        self.metadata['civ_config'] = data
        self._write_file(self._files['metadata'],  self.metadata)

    def update_steam_workshop(self,data):
        self.workshop = data
        self.metadata['workshop'] = data
        self._write_file(self._files['metadata'],  self.metadata)

    def update_civ_install(self,data):
        self.civ_install = data
        self.metadata['civ_install'] = data
        self._write_file(self._files['metadata'], self.metadata)

    def update_age(self, text):
        self.age = text
        self.metadata['age'] = text
        self._write_file(self._files['metadata'],  self.metadata)

    def update_last_patch_time(self, value):
        self.patch_time = value
        self.metadata['patch_time'] = value
        self._write_file(self._files['metadata'], self.metadata)

    def check_firaxis_patched(self):
        root = Path(self.civ_install)
        latest = max(
            p.stat().st_mtime
            for p in root.rglob("*")
            if p.is_file()
        )
        current = self.metadata.get('patch_time')
        if current is None or latest > current:
            self.patch_change = True
            self.update_last_patch_time(latest)


    @staticmethod
    def resource_path(relative_path):
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        return os.path.join(base_path, relative_path)


def find_steam_install():
    if sys.platform == 'win32':
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
    elif sys.platform == 'win64':
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Wow6432Node\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
    elif sys.platform == 'darwin':
        user_home = Path.home()
        steam_path = str(user_home / "Library" / "Application Support" / "Steam")
    else:
        return None
    return steam_path


def find_civ_install():
    steam_path = find_steam_install()
    if steam_path is None:
        return None
    if sys.platform == 'win32':
        civ_install = os.path.join(steam_path, "steamapps/common/Sid Meier's Civilization VII")
    elif sys.platform == 'darwin':
        civ_install = os.path.join(steam_path, "steamapps/common/Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources")
    else:
        return None
    return civ_install


def find_workshop():
    steam_path = find_steam_install()
    if steam_path is None:
        return None
    return f"{steam_path}/steamapps/workshop/content/1295660/"


def find_civ_config():
    if sys.platform == 'win32':
        local_appdata = os.getenv('LOCALAPPDATA')
        civ_config = f"{local_appdata}/Firaxis Games/Sid Meier's Civilization VII"
    elif sys.platform == 'darwin':
        user_home = Path.home()
        civ_config = str(user_home / "Library" / "Application Support" / "Civilization VII")
    else:
        return None
    return civ_config


modifier_system_tables = ("Modifiers", "ModifierArguments", "DynamicModifiers", "ModifierStrings",
                          "Requirements", "RequirementArguments", "RequirementSets",
                          "RequirementSetRequirements", "ModifierMetadatas")

effect_system_tables = ("Modifiers", "ModifierArguments", "DynamicModifiers", "ModifierStrings")

requirement_system_tables = ("Requirements", "RequirementArguments", "RequirementSets", "RequirementSetRequirements")

modifierAttachTables = {"EnterStageModifiers": "ModifierId", "EnvoysInActionModifiers": "ModifierId",
                        "EnvoysInStageModifiers": "ModifierId",
                        "GovernmentModifiers": "ModifierId", "MementoModifiers": "ModifierId",
                        "TraditionModifiers": "ModifierId", "TraitModifiers": "ModifierId",
                        "UnitAbilityModifiers": "ModifierId", "UnitPromotionModifiers": "ModifierId",
                        "NarrativeStory_Rewards": "NarrativeRewardType"}

ages = ['AGE_ANTIQUITY', 'AGE_EXPLORATION', 'AGE_MODERN']

with open('resources/ModArgInfo.json', 'r') as f:
    modifier_argument_info = json.load(f)

with open('resources/RequirementInfo.json', 'r') as f:
    requirement_argument_info = json.load(f)

db_spec = ResourceLoader()

attach_tables = [i for i in db_spec.node_templates['Modifiers']['extra_backlinks']] + db_spec.node_templates['Modifiers']['backlink_fk']
attach_tables = [i for i in attach_tables if i not in modifier_system_tables]


def flatten(xss):
    return [x for xs in xss for x in xs]

# TODO move this into database patch, dont do every time
length_mod_args = {}
for key, val in modifier_argument_info.items():
    len_args = len(val['Arguments'])
    if len_args not in length_mod_args:
        length_mod_args[len_args] = []
    length_mod_args[len_args].append(key)

length_req_args = {}
for key, val in requirement_argument_info.items():
    len_args = len(val['Arguments'])
    if len_args not in length_req_args:
        length_req_args[len_args] = []
    length_req_args[len_args].append(key)


mod_arg_type_list_map = {}
for effect, val in modifier_argument_info.items():
    mod_arg_type_list_map[effect] = {}
    arg_type_count = {}
    for arg, arg_info in val['Arguments'].items():
        arg_type = arg_info['ArgumentType']
        arg_type = 'text' if arg_type is None or arg_type == '' else arg_type
        if arg_type not in arg_type_count:
            arg_type_count[arg_type] = 1
        else:
            arg_type_count[arg_type] += 1

        mod_arg_type_list_map[effect][f'param_{arg_type}_{arg_type_count[arg_type]}'] = arg

mod_arg_param_map = {k: {val: key for key, val in v.items()} for k, v in mod_arg_type_list_map.items()}
all_param_arg_fields = list(set(flatten([list(val.keys()) for key, val in mod_arg_type_list_map.items()])))
all_param_arg_fields.sort()

default_val_types = []
default_val_list_lists = [[j['DefaultValue'] for i, j in v['Arguments'].items()] for k,v in modifier_argument_info.items()]
[default_val_types.extend(i) for i in default_val_list_lists]

convert_map = {'Boolean': 'bool', 'uint': 'int', None: 'text', '': 'text'}
req_arg_type_list_map = {}
for effect, val in requirement_argument_info.items():
    req_arg_type_list_map[effect] = {}
    arg_type_count = {}
    for arg, arg_info in val['Arguments'].items():
        arg_type = arg_info['ArgumentType']
        arg_type = convert_map.get(arg_type, arg_type)
        if isinstance(arg_type, float) and math.isnan(arg_type):
            arg_type = 'text'
        if arg_type not in arg_type_count:
            arg_type_count[arg_type] = 1
        else:
            arg_type_count[arg_type] += 1

        req_arg_type_list_map[effect][f'param_{arg_type}_{arg_type_count[arg_type]}'] = arg

req_arg_param_map = {k: {val: key for key, val in v.items()} for k, v in req_arg_type_list_map.items()}
req_all_param_arg_fields = list(set(flatten([list(val.keys()) for key, val in req_arg_type_list_map.items()])))
req_all_param_arg_fields.sort()


def build_param_map(all_arg_fields):
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
    return default_map


req_default_map = build_param_map(req_all_param_arg_fields)
req_arg_defaults = {key: {k: req_default_map[k] for k, v in val.items()} for key, val in req_arg_type_list_map.items()}

effect_default_map = build_param_map(all_param_arg_fields)
effect_arg_defaults = {key: {k: effect_default_map[k] for k, v in val.items()}
                       for key, val in mod_arg_type_list_map.items()}
