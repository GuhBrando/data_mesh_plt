import asyncpg


async def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database using asyncpg.
    """
    return await asyncpg.connect(
        user="your_username",
        password="your_password",
        database="your_database",
        host="localhost",
        port=5432,
    )
