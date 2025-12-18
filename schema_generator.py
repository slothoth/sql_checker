"""
Marshmallow-SQLAlchemy schema generator for database models.
Auto-generates schemas for all SQLAlchemy models in db_models.
"""
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema
from marshmallow import fields, validate, ValidationError, EXCLUDE
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy.sql.elements import TextClause, ClauseElement

import db_models

db_path = "resources/antiquity-db.sqlite"       # TODO make this change on age transition
engine = create_engine(f"sqlite:///{db_path}")

Session = sessionmaker(bind=engine)
session = Session()


class BaseSchema(SQLAlchemyAutoSchema):
    """Base schema with common configuration."""

    class Meta:
        unknown = EXCLUDE
        load_instance = True


# Cache for schemas to avoid regenerating
_schema_cache = {}


def get_schema_for_table(table_name):
    """
    Get or create a Marshmallow schema for a given table name.

    Args:
        table_name: Name of the database table

    Returns:
        A Marshmallow schema class for the table
    """
    if table_name in _schema_cache:
        return _schema_cache[table_name]

    # Find the model class for this table
    model_class = None

    # Check all attributes in db_models module
    for attr_name in dir(db_models):
        # Skip private attributes
        if attr_name.startswith('_'):
            continue

        attr = getattr(db_models, attr_name)

        # Check if it's a SQLAlchemy model class (has __tablename__)
        if isinstance(attr, type) and hasattr(attr, '__tablename__'):
            if attr.__tablename__ == table_name:
                model_class = attr
                break
        # Check for Table objects (like t_AdvancedStartArmyUnits)
        elif hasattr(attr, 'name') and attr.name == table_name:
            # This is a Table object, we'll need to use ORM classes
            # Don't break, continue to check ORM classes
            pass

    if model_class is None:
        # Try to find it in the ORM classes dict (for Table objects or imperatively mapped classes)
        try:
            from ORM import classes
            if table_name in classes:
                model_class = classes[table_name]
        except ImportError:
            pass

        # Last resort: try to find by matching table name in db_models Table objects
        if model_class is None:
            for attr_name in dir(db_models):
                if attr_name.startswith('t_'):
                    attr = getattr(db_models, attr_name)
                    if hasattr(attr, 'name') and attr.name == table_name:
                        # Use ORM class if available
                        try:
                            from ORM import classes
                            if table_name in classes:
                                model_class = classes[table_name]
                                break
                        except ImportError:
                            pass

        if model_class is None:
            raise ValueError(f"No model found for table '{table_name}'")

    # Create schema dynamically
    schema_class_name = f"{table_name}Schema"

    class TableSchema(BaseSchema):
        class Meta:
            model = model_class
            unknown = EXCLUDE
            load_instance = True
            sqla_session = session

    _schema_cache[table_name] = TableSchema
    return TableSchema


def validate_table_data(table_name, data, partial=True):
    """
    Validate data against a table's schema.

    Args:
        table_name: Name of the database table
        data: Dictionary of field names to values
        partial: If True, only validate provided fields (default: True)

    Returns:
        tuple: (is_valid: bool, errors: dict)
        errors is a dictionary mapping field names to error messages
    """
    try:
        schema = get_schema_for_table(table_name)
        schema_instance = schema(partial=partial)

        errors = schema_instance.validate(data)

        if errors:
            return False, errors
        return True, {}
    except Exception as e:
        return False, {'_schema': [str(e)]}


def validate_field(table_name, field_name, field_value, all_data=None):
    """
    Validate a single field value.

    Args:
        table_name: Name of the database table
        field_name: Name of the field to validate
        field_value: Value to validate
        all_data: Optional dictionary of all field values (for context-dependent validation)

    Returns:
        tuple: (is_valid: bool, error_message: str or None)     TODO currently returning error if any val in insert fails
    """                                                         # not just itself
    if all_data is None:
        all_data = {}

    # Skip validation for empty strings (handled by nullable constraints)
    # Convert empty strings to None for validation
    if field_value == '' or field_value is None:
        field_value = None

    # Create a partial data dict with just this field
    data = {field_name: field_value}

    # Merge with all_data for context
    data.update(all_data)
    data[field_name] = field_value  # Ensure our field value takes precedence

    # Remove empty string values from all_data for cleaner validation
    cleaned_data = {k: (None if v == '' else v) for k, v in data.items() if v is not None or v == ''}
    # deal with checkbox bools
    cleaned_data = {k: int(v) if isinstance(v, bool) else v for k, v in cleaned_data.items()}
    try:
        is_valid, errors = validate_table_data(table_name, cleaned_data, partial=True)

        if not is_valid:
            field_errors = errors.get(field_name, [])
            if field_errors:
                return False, '; '.join(field_errors) if isinstance(field_errors, list) else str(field_errors)
            return False, 'Validation failed'

        return True, None
    except Exception as e:
        # If schema generation fails, don't block the user to avoid breaking UI
        return True, None


class SchemaInspector:
    """ Class to handle inspect columns and data types """
    pk_map = {}
    fk_to_tbl_map = {}
    fk_to_pk_map = {}
    pk_ref_map = {}
    type_map = {}
    nullable_map = {}
    default_map = {}
    odd_constraint_map = {}
    required_map = {}

    def __init__(self):
        models = {key:val for key, val in db_models.Base.registry._class_registry.items() if hasattr(val, "__table__")}
        self.pk_map = {model_name:  [i.name for i in model.__table__.primary_key.columns] for model_name, model in models.items()}
        self.fk_to_tbl_map = {model_name: {i.name: list(i.foreign_keys)[0].column.table.name
                                    for i in model.__table__.columns if len(i.foreign_keys) > 0} for model_name, model in models.items()}
        self.fk_to_pk_map = {model_name: {i.name: list(i.foreign_keys)[0].column.name
                                    for i in model.__table__.columns if len(i.foreign_keys) > 0} for model_name, model in models.items()}
        internal_fk_map = {model_name: {i.name: {j.column.table.name: j.column.name for j in i.foreign_keys}
                                    for i in model.__table__.columns if len(i.foreign_keys) > 0} for model_name, model in models.items()}
        self.pk_ref_map = {}
        for model_name, model in models.items():
            for ref_tbl, fk_refs in internal_fk_map.items():
                for fk_col, pk_info in fk_refs.items():
                    if len(pk_info) > 1:
                        print('plural pk info?')
                    pk_tbl = list(pk_info.keys())[0]
                    pk_col = pk_info[pk_tbl]
                    if pk_tbl == model_name:
                        if model_name not in self.pk_ref_map:
                            self.pk_ref_map[model_name] = {'table_first': {}, 'col_first': {}}
                        if ref_tbl not in self.pk_ref_map[model_name]['table_first']:
                            self.pk_ref_map[model_name]['table_first'][ref_tbl] = [pk_col]
                        else:
                            self.pk_ref_map[model_name]['table_first'][ref_tbl].append(pk_col)

                        if pk_col not in self.pk_ref_map[model_name]['col_first']:
                            self.pk_ref_map[model_name]['col_first'][pk_col] = [ref_tbl]
                        else:
                            self.pk_ref_map[model_name]['col_first'][pk_col].append(ref_tbl)

        self.type_map = {model_name:  {col.name: col.type for col in model.__table__.columns} for model_name, model in models.items()}
        self.nullable_map = {model_name:  {col.name: col.nullable for col in model.__table__.columns} for model_name, model in models.items()}
        self.default_map = {model_name: {col.name: extract_server_default(col) for col in model.__table__.columns if
                                         col.server_default is not None} for model_name, model in models.items()}
        self.odd_constraint_map = {model_name:  [[c.name for c in constraint.columns]
                             for constraint in model.__table__.constraints if isinstance(constraint, UniqueConstraint)]
               for model_name, model in models.items()}

        self.required_map = {model_name: {col.name: True for col in model.__table__.columns if
                                         col.server_default is None and not col.nullable} for model_name, model in models.items()}


def extract_server_default(col):
    sd = col.server_default
    if sd is None:
        return None

    arg = sd.arg

    if isinstance(arg, TextClause):
        text = arg.text.strip()
        if (
            (text.startswith("'") and text.endswith("'")) or
            (text.startswith('"') and text.endswith('"'))
        ):
            return text[1:-1]
        return text

    if isinstance(arg, ClauseElement):
        return str(arg)

    return arg

SchemaInspectorAntiquity = SchemaInspector()

