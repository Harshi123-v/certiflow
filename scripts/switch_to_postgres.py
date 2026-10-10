import sys
import getpass
from pathlib import Path
from urllib.parse import quote_plus
import psycopg2

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def setup_postgres(password: str = None, host: str = "localhost", port: int = 5432, user: str = "postgres", dbname: str = "certiflow_db"):
    if not password:
        password = getpass.getpass(f"Enter password for PostgreSQL user '{user}': ")

    print(f"\n1. Testing connection to PostgreSQL at {host}:{port} with user '{user}'...")
    try:
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
        conn.autocommit = True
        cur = conn.cursor()
        print(" -> [OK] Connected to PostgreSQL server successfully!")

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if not cur.fetchone():
            print(f"2. Creating database '{dbname}'...")
            cur.execute(f'CREATE DATABASE "{dbname}"')
            print(f" -> [OK] Database '{dbname}' created successfully!")
        else:
            print(f"2. Database '{dbname}' already exists.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("Please verify your PostgreSQL password and try again.")
        return False

    # 3. Update .env file
    env_file = BASE_DIR / ".env"
    escaped_password = quote_plus(password)
    pg_url = f"postgresql+psycopg2://{user}:{escaped_password}@{host}:{port}/{dbname}"

    lines = []
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        found = False
        for line in content.splitlines():
            if line.strip().startswith("DATABASE_URL="):
                lines.append(f'DATABASE_URL="{pg_url}"')
                found = True
            else:
                lines.append(line)
        if not found:
            lines.append(f'DATABASE_URL="{pg_url}"')
    else:
        lines = [f'DATABASE_URL="{pg_url}"']

    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("3. Updated .env with PostgreSQL connection string:")
    print(f"   DATABASE_URL=\"postgresql+psycopg2://{user}:*****@{host}:{port}/{dbname}\"")

    # 4. Initialize tables using SQLAlchemy
    print("4. Initializing SQLAlchemy tables in PostgreSQL...")
    from app.core.config import settings
    # Force settings reload
    settings.DATABASE_URL = pg_url
    from app.db.database import engine, Base
    Base.metadata.create_all(bind=engine)
    print(" -> [OK] Tables 'generation_jobs' and 'certificate_records' created in PostgreSQL!")

    print("\n" + "="*70)
    print(" SUCCESS! CertiFlow is now running with PostgreSQL!")
    print(f" All job data and certificates will now be stored in '{dbname}'.")
    print("="*70 + "\n")
    return True

if __name__ == "__main__":
    pwd = sys.argv[1] if len(sys.argv) > 1 else None
    setup_postgres(password=pwd)
