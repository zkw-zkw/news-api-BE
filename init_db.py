"""Initialize all database tables."""
import asyncio
from config.db_conf import async_engine
from models.news import Base as NewsBase
from models.users import Base as UsersBase
from models.favorite import Base as FavoriteBase
from models.history import Base as HistoryBase


async def init():
    print("Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(NewsBase.metadata.create_all)
        await conn.run_sync(UsersBase.metadata.create_all)
        await conn.run_sync(FavoriteBase.metadata.create_all)
        await conn.run_sync(HistoryBase.metadata.create_all)
    print("All tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init())
