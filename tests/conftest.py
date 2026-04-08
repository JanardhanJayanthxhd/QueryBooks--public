import os

# Set test environment variables BEFORE any src imports
os.environ.setdefault("POSTGRESQL_DB_NAME", "testdb")
os.environ.setdefault("POSTGRESQL_PORT", "5432")
os.environ.setdefault("POSTGRESQL_HOST", "localhost")
os.environ.setdefault("POSTGRESQL_PWD", "testpwd")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")
os.environ.setdefault("OPENAI_EMBEDDING_MODEL", "text-embedding-large-3")
os.environ.setdefault("OLLAMA_MODEL", "mistral:7b")
os.environ.setdefault("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# In-memory SQLite database for testing
@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory SQLite database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from src.models.base import Base
    import src.models.user  # noqa: F401
    import src.models.cache  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a database session for testing"""
    testing_session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = testing_session_local()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(test_db_engine, test_db_session):
    """Create a TestClient with database dependency override"""
    from src.api.main import app
    from src.core.database import get_db

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with patch("src.core.config.engine", test_db_engine):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()


# Test user fixtures
@pytest.fixture
def test_user_data():
    """Provides sample user data for registration"""
    return {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "securepassword123",
    }


@pytest.fixture
def test_user(test_db_session, test_user_data):
    """Create and return a test user in the database"""
    from src.core.utility import hash_password
    from src.models.user import User

    user = User(
        name=test_user_data["name"],
        email=test_user_data["email"],
        password_hash=hash_password(test_user_data["password"]),
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Generate a valid JWT token for the test user"""
    from src.core.jwt import create_access_token

    token = create_access_token(
        data={"email": test_user.email, "id": test_user.id}, expires_delta=None
    )
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Return authorization headers with Bearer token"""
    return {"Authorization": f"Bearer {auth_token}"}


# Mock file fixtures
@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file for upload testing"""
    return b"%PDF-1.4 mock pdf content"
