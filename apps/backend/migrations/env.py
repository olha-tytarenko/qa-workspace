import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.config import get_settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    # Keep loggers the application already created: Alembic also runs in-process
    # (the test suite does this), where disabling them would silence later logging.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def resolve_database_url() -> str:
    # A caller may pass an explicit URL through `Config.attributes` (the test
    # suite does this to migrate the test database). Otherwise the URL comes from
    # settings, resolved lazily so importing this module never needs DATABASE_URL.
    override = config.attributes.get("database_url")
    if override is not None:
        return str(override)
    return get_settings().database_url


def get_database_url() -> str:
    # "%" is escaped because Alembic's config uses ConfigParser interpolation.
    return resolve_database_url().replace("%", "%%")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode, emitting SQL without a connection."""
    context.configure(
        url=resolve_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    config.set_main_option("sqlalchemy.url", get_database_url())

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against an async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
