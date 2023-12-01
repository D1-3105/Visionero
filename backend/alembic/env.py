import pathlib
import sys
from logging.config import fileConfig

import psycopg2
import sqlalchemy
from alembic import context
from asyncpg import InvalidCatalogNameError
from sqlalchemy import text

sys.path.append(pathlib.Path(__file__).parent.parent.parent.absolute().as_posix())

from backend.db.configs import settings_nonpersistent, acreate_session, settings_persistent
from backend.db.setting_pool import DBSettings, BaseORMModel
from backend.shared.configs import db_parameters

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
config.set_main_option('sqlalchemy.url', DBSettings.build_url(db_parameters))

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = BaseORMModel.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


import asyncio


def create_database_if_not_exists(db_parameters):
    """Create the database if it does not exist."""
    main_db_parameters = db_parameters.copy()
    main_db_parameters['dbname'] = 'postgres'
    main_db_parameters['driver'] = 'postgresql+psycopg2'
    settings_main_database = DBSettings.from_cdp(main_db_parameters, False)
    settings_main_database.setup()

    main_conn = settings_main_database.ses().connection()
    main_conn.commit()
    print('DATABASE', db_parameters['dbname'], 'DOES NOT EXIST. CREATING...')
    main_conn.execution_options(
        isolation_level="AUTOCOMMIT"
    ).execute(text(f'CREATE DATABASE {db_parameters["dbname"]};'))
    main_conn.close()


def run_migrations_online():
    mig_parameters = db_parameters.copy()
    mig_parameters['driver'] = 'postgresql+psycopg2'
    db_settings = DBSettings.from_cdp(mig_parameters, False)
    db_settings.setup()
    try:
        connection = db_settings.ses().connection()
    except sqlalchemy.exc.OperationalError as e:
        create_database_if_not_exists(db_parameters)
        connection = db_settings.ses().connection()

    # Run the migrations
    context.configure(connection=connection, target_metadata=target_metadata)

    # Run the migrations
    context.run_migrations()
    connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
