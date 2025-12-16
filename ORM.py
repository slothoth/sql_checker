from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import registry
import sqlglot
from sqlglot import exp
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import inspect
from collections import defaultdict


db_path = "resources/antiquity-db.sqlite"
engine = create_engine(f"sqlite:///{db_path}")

metadata = MetaData()
metadata.reflect(bind=engine)

mapper_registry = registry()

classes = {}
failed_classes = []
for table in metadata.tables.values():
    clsname = "".join(part.capitalize() for part in table.name.split("_"))
    cls = type(clsname, (), {})
    if not table.primary_key:
        table.append_constraint(PrimaryKeyConstraint(*table.c))

    mapper_registry.map_imperatively(cls, table)
    classes[table.name] = cls



def create_instances_from_sql(sql_text):
    cleaned_sql = clean_sql(sql_text)
    parsed = sqlglot.parse_one(cleaned_sql, dialect="sqlite")

    if not isinstance(parsed, exp.Insert):
        raise ValueError("SQL must be an INSERT statement")

    table_nodes = list(parsed.find_all(exp.Table))
    if len(table_nodes) != 1:
        raise ValueError(f"statement had multiple Table mentions. it shouldnt: {sql_text}")

    table_name = table_nodes[0].name

    try:
        TargetClass = classes[table_name]
    except KeyError:
        raise ValueError(f"Table '{table_name}' found in SQL but not in the database schema.")

    sql_columns = [col.name for col in parsed.this.expressions]

    instance_list = []
    for value_list in parsed.expression.expressions:
        sql_values = []
        for val in value_list.expressions:
            if val.is_string:
                sql_values.append(val.name)
            elif val.is_number:
                sql_values.append(float(val.name) if "." in val.name else int(val.name))
            else:
                sql_values.append(val.name)

        instance_list.append(TargetClass(**dict(zip(sql_columns, sql_values))))

    return instance_list


def clean_sql(sql_text):
    cleaned_sql = sql_text.replace('\xa0', ' ')
    cleaned_sql = cleaned_sql.replace('“', "'").replace('”', "'")
    return cleaned_sql


def get_table_and_key_vals(orm_instance):
    mapper = inspect(orm_instance).mapper
    table_name = mapper.local_table.name
    state = inspect(orm_instance)
    col_dicts = {
        attr.key: state.attrs[attr.key].value
        for attr in state.mapper.column_attrs
    }
    pk_tuple = tuple(
        getattr(orm_instance, col.name)
        for col in mapper.local_table.primary_key.columns
    )
    return table_name, col_dicts, pk_tuple


def build_fk_index(instances):
    fk_index = defaultdict(set)

    by_table = defaultdict(list)
    for obj in instances:
        by_table[inspect(obj).mapper.local_table].append(obj)

    for child in instances:
        sc = inspect(child)
        child_table = sc.mapper.local_table
        child_pk = tuple(
            getattr(child, col.name)
            for col in child_table.primary_key.columns
        )

        for fk in child_table.foreign_keys:
            parent_table = fk.column.table
            parent_col = fk.column.name
            parent_val = getattr(child, fk.parent.name)

            if parent_val is None:
                continue

            for parent in by_table.get(parent_table, []):
                if getattr(parent, parent_col) == parent_val:
                    parent_pk = tuple(
                        getattr(parent, col.name)
                        for col in parent_table.primary_key.columns
                    )

                    fk_index[
                        (parent_table.name, parent_col, parent_pk)
                    ].add(
                        (child_table.name, child_pk)
                    )

    return fk_index
