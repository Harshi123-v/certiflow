import logging
from urllib.parse import urlparse, urlunparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

logger = logging.getLogger("certiflow.db")

# Dialect-specific options
connect_args = {}
engine_kwargs = {"pool_pre_ping": True, "echo": False}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif settings.DATABASE_URL.startswith("postgresql"):
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_postgres_database_exists():
    """
    If using PostgreSQL and target database does not exist,
    connect to the default 'postgres' database and create it.
    """
    if not settings.DATABASE_URL.startswith("postgresql"):
        return

    try:
        parsed = urlparse(settings.DATABASE_URL)
        target_db = parsed.path.lstrip("/")
        if not target_db or target_db == "postgres":
            return

        # Maintenance DB connection URL (to default 'postgres' DB)
        maintenance_url = urlunparse(parsed._replace(path="/postgres"))
        m_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
        with m_engine.connect() as conn:
            check_sql = text("SELECT 1 FROM pg_database WHERE datname = :dbname")
            exists = conn.execute(check_sql, {"dbname": target_db}).scalar()
            if not exists:
                logger.info(f"Target PostgreSQL database '{target_db}' does not exist. Creating...")
                conn.execute(text(f'CREATE DATABASE "{target_db}"'))
                logger.info(f"Database '{target_db}' created successfully.")
        m_engine.dispose()
    except Exception as e:
        logger.warning(f"Could not auto-create database (might already exist or lack permission): {e}")

def ensure_postgres_schema_compatibility():
    """Ensure existing columns like send_emails or email_sent don't block inserts."""
    if not settings.DATABASE_URL.startswith("postgresql"):
        return
    try:
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("ALTER TABLE generation_jobs ALTER COLUMN send_emails DROP NOT NULL;"))
            conn.execute(text("ALTER TABLE generation_jobs ALTER COLUMN send_emails SET DEFAULT false;"))
            conn.execute(text("ALTER TABLE certificate_records ALTER COLUMN email_sent DROP NOT NULL;"))
            conn.execute(text("ALTER TABLE certificate_records ALTER COLUMN email_sent SET DEFAULT false;"))
    except Exception:
        pass

def init_db():
    """Initialize database tables."""
    if settings.DATABASE_URL.startswith("postgresql"):
        ensure_postgres_database_exists()
    Base.metadata.create_all(bind=engine)
    if settings.DATABASE_URL.startswith("postgresql"):
        ensure_postgres_schema_compatibility()

