from sqlalchemy.orm import registry
import sqlglot
from sqlglot import exp
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import inspect
from collections import defaultdict
from schema_generator import SQLValidator
from graph.db_spec_singleton import db_spec

mapper_registry = registry()

classes = {}
failed_classes = []
canonical_mapper = {}
for table in SQLValidator.metadata.tables.values():
    clsname = "".join(part.capitalize() for part in table.name.split("_"))
    cls = type(clsname, (), {})
    if not table.primary_key:
        table.append_constraint(PrimaryKeyConstraint(*table.c))

    mapper_registry.map_imperatively(cls, table)
    tbl_name = table.name
    classes[tbl_name] = cls
    canonical_mapper[tbl_name.lower()] = tbl_name


def create_instances_from_sql(sql_text):
    cleaned_sql = clean_sql(sql_text)
    parsed = sqlglot.parse_one(cleaned_sql, dialect="sqlite")

    if not isinstance(parsed, exp.Insert):
        print("SQL must be an INSERT statement")
        return

    table_nodes = list(parsed.find_all(exp.Table))
    if len(table_nodes) != 1:
        print(f"statement had multiple Table mentions. this is probably a INSERT:SELECT: {sql_text}")
        return

    table_name = table_nodes[0].name

    try:
        proper_tbl = canonical_mapper[table_name.lower()]
        TargetClass = classes[proper_tbl]
    except KeyError:
        raise ValueError(f"Table '{proper_tbl}' found in SQL but not in the database schema.")

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

        colmap = {c.key.lower(): c.key for c in TargetClass.__table__.columns}
        kwargs = {colmap[k.lower()]: v for k, v in zip(sql_columns, sql_values)}
        instance_list.append(TargetClass(**kwargs))

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
    if table_name == 'Types':
        del col_dicts['Hash']
    return table_name, col_dicts, pk_tuple


def build_fk_index(instances):
    fk_index = defaultdict(set)
    by_table = defaultdict(list)
    tables_by_name = {}
    for obj in instances:
        t = inspect(obj).mapper.local_table
        by_table[t].append(obj)
        tables_by_name[t.name] = t

    for child in instances:
        sc = inspect(child)
        child_table = sc.mapper.local_table
        child_pk = tuple(
            getattr(child, mapped_attr(child, child_table, c.name)) for c in child_table.primary_key.columns)

        for fk in child_table.foreign_keys:
            parent_table = fk.column.table
            parent_col = fk.column.name

            child_attr = mapped_attr(child, child_table, fk.parent.name)
            parent_val = getattr(child, child_attr)
            if parent_val is None:
                continue

            for parent in by_table.get(parent_table, []):
                parent_attr = mapped_attr(parent, parent_table, parent_col)
                if getattr(parent, parent_attr) == parent_val:
                    parent_pk = tuple(getattr(parent, mapped_attr(parent, parent_table, c.name)) for c in
                                      parent_table.primary_key.columns)
                    fk_index[(parent_table.name, parent_col, parent_pk)].add((child_table.name, child_pk))

        extra = db_spec.node_templates[child_table.name].get("extra_fks", {})
        for child_col_name, fk_info in extra.items():
            ref_table_name = fk_info["ref_table"]
            ref_col_name = fk_info["ref_column"]

            parent_table = tables_by_name.get(ref_table_name)
            if parent_table is None:
                parent_table =  child_table.metadata.tables.get(ref_table_name)
                if parent_table is None:
                    continue

            child_attr = mapped_attr(child, child_table, child_col_name)
            parent_val = getattr(child, child_attr)
            if parent_val is None:
                continue

            for parent in by_table.get(parent_table, []):
                parent_attr = mapped_attr(parent, parent_table, ref_col_name)
                if getattr(parent, parent_attr) == parent_val:
                    parent_pk = tuple(getattr(parent, mapped_attr(parent, parent_table, c.name)) for c in
                                      parent_table.primary_key.columns)
                    fk_index[(parent_table.name, ref_col_name, parent_pk)].add((child_table.name, child_pk))

    return fk_index


def mapped_attr(obj, table, col_name):
    m = inspect(obj).mapper
    col = table.c[col_name]
    try:
        return m.get_property_by_column(col).key
    except Exception:
        return col.key
