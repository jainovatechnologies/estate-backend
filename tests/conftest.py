import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import fastapi_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.sources = MagicMock()
    db.content_chunks = MagicMock()
    db.chat_sessions = MagicMock()
    db.chat_messages = MagicMock()
    db.ingestion_runs = MagicMock()

    db.sources.find_one = AsyncMock(return_value=None)
    db.sources.count_documents = AsyncMock(return_value=12)
    db.sources.update_one = AsyncMock(return_value=MagicMock(upserted_id="123"))

    db.content_chunks.count_documents = AsyncMock(return_value=45)
    db.content_chunks.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))
    db.content_chunks.insert_many = AsyncMock(return_value=MagicMock(inserted_ids=["c1", "c2"]))

    db.chat_sessions.find_one = AsyncMock(return_value=None)
    db.chat_sessions.insert_one = AsyncMock(return_value=MagicMock(inserted_id="s1"))
    db.chat_sessions.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    db.chat_messages.insert_one = AsyncMock(return_value=MagicMock(inserted_id="m1"))
    db.ingestion_runs.insert_one = AsyncMock(return_value=MagicMock(inserted_id="r1"))
    db.ingestion_runs.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    db.ingestion_runs.find_one = AsyncMock(return_value=None)

    return db


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
