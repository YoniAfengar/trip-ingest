"""Alembic migration environment. Given — do not edit.

Two things worth reading before you write your first revision.

**The URL comes from the environment**, not from `alembic.ini`, so the same revisions run anywhere.

**`target_metadata` is `None`**, and that is not an oversight. Autogenerate works by diffing a live
database against an ORM's declared metadata. There is no ORM here — you are writing the DDL yourself,
which means `alembic revision --autogenerate` has nothing to diff and will hand you an empty
migration. Use `alembic revision -m "..."` and write `upgrade()` and `downgrade()` by hand.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from trip_ingest.settings import database_url

config = context.config

# libpq (psycopg) and SQLAlchemy disagree about how to spell a Postgres URL: libpq wants
# `postgresql://`, SQLAlchemy wants a driver — `postgresql+psycopg://` — or it reaches for psycopg2,
# which is not installed. One DSN in the environment; one translation, here.
config.set_main_option(
    "sqlalchemy.url", database_url().replace("postgresql://", "postgresql+psycopg://", 1))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def run_migrations_offline() -> None:
    """Emit SQL to a script without a live connection (`alembic upgrade --sql`)."""
    context.configure(url=config.get_main_option("sqlalchemy.url"),
                      target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
