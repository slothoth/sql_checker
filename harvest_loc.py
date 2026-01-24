import sqlite3
import json

from graph.singletons.filepaths import LocalFilePaths
from graph.utils import resource_path

# get localization, build localisation instead?
conn = sqlite3.connect(f'{LocalFilePaths.civ_config}/Debug/localization-copy.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT Tag FROM LocalizedText;")
localised = [i[0] for i in cursor.fetchall()]
with open(resource_path('resources/mined/LocalizedTags.json'), 'w') as f:
    json.dump(localised, f, separators=(',', ':'), sort_keys=True)
