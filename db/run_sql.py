# db/run_sql.py
import os
import sys
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

try:
    from dotenv import load_dotenv
    load_dotenv()  # lädt .env aus dem Projektroot
except Exception:
    pass  # notfalls ohne .env weiter

def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL ist nicht gesetzt. Lege eine .env an oder exportiere die Variable.\n"
            "Beispiel: postgresql://user:pass@localhost:5432/appdb"
        )
    return url

def run_init_sql():
    # Pfad zu init.sql -> z.B. <project>/db/init.sql
    sql_path = Path(__file__).with_name("init.sql")
    if not sql_path.exists():
        raise FileNotFoundError(f"init.sql nicht gefunden unter: {sql_path}")

    sql_script = sql_path.read_text(encoding="utf-8")

    db_url = get_database_url()
    # Hinweis: Für docker-compose ist host=Service-Name, z.B. db
    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()

def run_example_data_sql():
    # Pfad zu init.sql -> z.B. <project>/db/init.sql
    sql_path = Path(__file__).with_name("example_data.sql")
    if not sql_path.exists():
        raise FileNotFoundError(f"init.sql nicht gefunden unter: {sql_path}")

    sql_script = sql_path.read_text(encoding="utf-8")

    db_url = get_database_url()
    # Hinweis: Für docker-compose ist host=Service-Name, z.B. db
    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()

def run_drop_all_sql():
    # Pfad zu init.sql -> z.B. <project>/db/init.sql
    sql_path = Path(__file__).with_name("drop_all.sql")
    if not sql_path.exists():
        raise FileNotFoundError(f"init.sql nicht gefunden unter: {sql_path}")

    sql_script = sql_path.read_text(encoding="utf-8")

    db_url = get_database_url()
    # Hinweis: Für docker-compose ist host=Service-Name, z.B. db
    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()

if __name__ == "__main__":
    try:
        run_drop_all_sql()
        print("✅ drop_all.sql erfolgreich ausgeführt.")
        run_init_sql()
        print("✅ init.sql erfolgreich ausgeführt.")
        run_example_data_sql()
        print("✅ example_data.sql erfolgreich ausgeführt.")
    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        sys.exit(1)
