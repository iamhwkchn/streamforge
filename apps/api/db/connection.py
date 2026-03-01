import asyncpg
from core.config import settings

class Database:
    pool: asyncpg.Pool = None

db = Database()

async def connect_to_db():
    print("Connecting to standard Postgres database...")
    db.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
    print("Connected to Postgres.")

async def close_db_connection():
    if db.pool:
        print("Closing Postgres connection...")
        await db.pool.close()
        print("Closed Postgres connection.")

async def get_db_pool() -> asyncpg.Pool:
    return db.pool
