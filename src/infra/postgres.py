import asyncpg


async def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database using asyncpg.
    """
    return await asyncpg.connect(
        user="admin",
        password="admin_password",
        database="data_mesh_plt",
        host="localhost",
        port=5432,
    )
