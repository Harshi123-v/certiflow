import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure certiflow root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.database import Base, get_db
from app.core.config import settings
from app.services.storage_service import storage_service
from app.main import app

# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup temporary storage directory and create database tables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_storage = Path(temp_dir)
        old_storage = storage_service.base_dir
        storage_service.base_dir = temp_storage
        
        # Initialize tables
        Base.metadata.create_all(bind=test_engine)
        
        yield
        
        # Teardown
        Base.metadata.drop_all(bind=test_engine)
        storage_service.base_dir = old_storage

@pytest.fixture
def db_session():
    """Yields an isolated database session per test with rollback/clean table states."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session, monkeypatch):
    """Provides a TestClient with overridden get_db dependency and sync background tasks."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Also patch SessionLocal in generation_service so background tasks use the test engine
    monkeypatch.setattr("app.services.generation_service.SessionLocal", lambda: db_session)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
