from alembic import context
from app.db import Base, SCHEMA, engine
from app.main import Payment, Payout

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    if type_ == "table" and name == "alembic_version":
        return False
    return name in (None, SCHEMA) if type_ == "schema" else True


if context.is_offline_mode():
    context.configure(url=engine.url, target_metadata=target_metadata, literal_binds=True,
                      version_table_schema=SCHEMA)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_schemas=True,
                          include_name=include_name, version_table_schema=SCHEMA)
        with context.begin_transaction():
            context.run_migrations()
