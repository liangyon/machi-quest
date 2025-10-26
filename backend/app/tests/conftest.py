"""
Test fixtures and configuration for pytest.

Provides reusable fixtures for database, HTTP client, and test data.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import hmac
import hashlib
import json

from app.main import app
from app.db.database import Base
from app.core.dependencies import get_db
from app.core.config import settings

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    
    Creates tables, yields session, then drops tables.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create FastAPI test client with test database.
    
    Overrides the get_db dependency to use test database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def webhook_secret():
    """Webhook secret for signing test payloads."""
    return settings.GITHUB_WEBHOOK_SECRET or "test-webhook-secret"


@pytest.fixture
def mock_push_payload():
    """
    Mock GitHub push event payload.
    
    Returns a complete push event with 2 commits.
    """
    return {
        "ref": "refs/heads/main",
        "before": "0000000000000000000000000000000000000000",
        "after": "abc123def456abc123def456abc123def456abc1",
        "repository": {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "owner": {
                "login": "testuser",
                "id": 987654321
            }
        },
        "pusher": {
            "name": "testuser",
            "email": "test@example.com"
        },
        "sender": {
            "login": "testuser",
            "id": 987654321,
            "avatar_url": "https://avatars.githubusercontent.com/u/987654321"
        },
        "commits": [
            {
                "id": "abc123def456abc123def456abc123def456abc1",
                "message": "Test commit 1",
                "timestamp": "2025-10-26T13:00:00-07:00",
                "url": "https://github.com/testuser/test-repo/commit/abc123",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "username": "testuser"
                },
                "committer": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "username": "testuser"
                },
                "added": ["new_file.py"],
                "removed": [],
                "modified": []
            },
            {
                "id": "def789ghi012def789ghi012def789ghi012def7",
                "message": "Test commit 2",
                "timestamp": "2025-10-26T13:05:00-07:00",
                "url": "https://github.com/testuser/test-repo/commit/def789",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "username": "testuser"
                },
                "committer": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "username": "testuser"
                },
                "added": [],
                "removed": ["old_file.py"],
                "modified": ["existing_file.py"]
            }
        ]
    }


def generate_github_signature(payload: dict, secret: str) -> str:
    """
    Generate GitHub webhook signature.
    
    Args:
        payload: The webhook payload dict
        secret: Webhook secret
        
    Returns:
        Signature string in format "sha256=<hex>"
    """
    payload_bytes = json.dumps(payload).encode('utf-8')
    mac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


@pytest.fixture
def signed_webhook_headers(mock_push_payload, webhook_secret):
    """
    Generate valid webhook headers with signature.
    
    Returns headers dict ready for HTTP request.
    """
    signature = generate_github_signature(mock_push_payload, webhook_secret)
    
    return {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "12345678-1234-1234-1234-123456789abc",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }


@pytest.fixture
def duplicate_delivery_id():
    """
    Delivery ID for testing duplicates.
    
    Use this same ID multiple times to simulate GitHub retries.
    """
    return "duplicate-test-id-12345"
