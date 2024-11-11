from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
from alembic import context

config = context.config


def run_migrations_online():

    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        echo=True,
    )

    async def do_migrations():
        async with connectable.connect() as connection:
            # This is where Alembic actually runs the migrations
            await connection.run_sync(context.run_migrations)

    asyncio.run(do_migrations())
