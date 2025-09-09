import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    # Einfacher Sync-Client für Demo
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
