import pytest
import asyncio
import os
from datetime import datetime


TEST_DB_PATH = "./test_subscriptions.db"


@pytest.fixture(scope="function")
async def test_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    import backend.db.database as db_module

    original_path = db_module.DATABASE_PATH
    db_module.DATABASE_PATH = TEST_DB_PATH

    from backend.db.database import init_db

    await init_db()

    yield

    db_module.DATABASE_PATH = original_path
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
def sample_subscription_data():
    return {
        "name": "Test Newsletter",
        "email": "newsletter@example.com",
        "domain": "example.com",
        "unsubscribe_url": "https://example.com/unsubscribe",
        "description": "A test newsletter",
    }


@pytest.fixture(scope="function")
def sample_email_data():
    return {
        "subscription_id": "test-sub-id",
        "gmail_message_id": "test-msg-123",
        "subject": "Weekly Update",
        "snippet": "This is a test email snippet...",
        "body_preview": "This is the full body preview of the email...",
        "date": datetime.utcnow(),
    }


@pytest.fixture(scope="module")
def api_client():
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        yield client
