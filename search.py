import pandas as pd
import os
import sqlite3

SQL_PATH = "/Users/samuelmayo/Library/Application Support/Civilization VII/Mods.sqlite"
CSV_FOLDER = 'csv_form'


# AGE = 'exploration'
# AGE = 'modern'


def setup_tables():
    os.makedirs(CSV_FOLDER, exist_ok=True)
    # build pandas tables
    # ran once, to convert database to pandas for conversion
    conn = sqlite3.connect(SQL_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = cursor.fetchall()
    tables = [table[0] for table in table_names] + ['sqlite_master']
    dfs = {}
    wd = f'{CSV_FOLDER}'
    os.makedirs(wd, exist_ok=True)
    for table in tables:
        query = f"SELECT * FROM {table}"
        dfs[table] = pd.read_sql_query(query, conn)
        dfs[table].to_csv(f"{wd}/{table}.csv", index=False)
    conn.close()


def search_tables():
    # STRATEGOI_MOD_COMMANDER_XP UNIT_CLASS_COMMAND REQUIREMENT_UNIT_TAG_MATCHES
    substring = 'load'
    substr_two = ''
    records = {}
    for i in os.listdir(f'{CSV_FOLDER}'):
        if i == 'Kinds.csv':
            continue
        if i.endswith('.csv'):
            df = pd.read_csv(f'{CSV_FOLDER}/{i}')
            records['i'] = []
            for column in df.columns:
                if df[column].astype(str).str.contains(substring, case=False, na=False).any():
                    try:
                        found_in_table = df[df[column].astype(str).str.contains(substring, case=False).fillna(False)]
                        if substr_two != '':
                            found_in_table = found_in_table[found_in_table[column].str.contains(substr_two, case=False).fillna(False)]
                        if len(found_in_table) > 0:
                            records['i'].append(df[df[column].astype(str).str.contains(substring, case=False).fillna(False)])

                    except Exception as e:
                        print(f'failed read on {i}.{column} with error {e}')
if not os.path.exists(f'{CSV_FOLDER}'):
    setup_tables()
search_tables()
