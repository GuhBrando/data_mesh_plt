import os

from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("ADMIN_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "data_mesh_plt")
