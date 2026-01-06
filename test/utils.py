
def check_test_against_expected_sql(test_sql_path):
    with open('resources/main.sql', 'r') as f:
        test_sql = f.readlines()

    with open('resources/main.sql', 'r') as f:
        ref_sql = f.read()

    with open(f'test/test_data/{test_sql_path}', 'r') as f:
        expected_sql = f.readlines()

    test_set = set(test_sql)
    expected_set = set(expected_sql)
    if test_set != expected_set:
        missing_sql = expected_set - test_set
        extra_sql = test_set - expected_set
        assert len(missing_sql) == 0, f'Missed lines {missing_sql}'
        assert len(extra_sql) == 0, f'extra lines {extra_sql}'