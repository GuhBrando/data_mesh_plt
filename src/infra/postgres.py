import asyncpg

from src.infra.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


async def get_db_connection():
    """
    FastAPI dependency that yields a database connection
    and closes it after the request.
    """
    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
    )
    try:
        yield conn
    finally:
        await conn.close()
