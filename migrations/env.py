import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import models from api service
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.app.database import Base
import api.app.models  # noqa — registers models on Base

config = context.config

# Allow DATABASE_URL env var to override alembic.ini
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,          # detect column type changes
            compare_server_default=True # detect default value changes
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()