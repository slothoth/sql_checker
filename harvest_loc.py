import sqlite3
import json

from graph.db_spec_singleton import db_spec
# get localization, build localisation instead?
conn = sqlite3.connect(f'{db_spec.civ_config}/Debug/localization-copy.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT Tag FROM LocalizedText;")
localised = [i[0] for i in cursor.fetchall()]
with open('resources/db_spec/LocalizedTags.json', 'w') as f:
    json.dump(localised, f, sort_keys=True)
