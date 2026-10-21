import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, TEXT
from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        try:
            logger.info("Connecting to MongoDB at %s...", settings.MONGODB_URI.split("@")[-1])
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            cls.db = cls.client[settings.MONGODB_DATABASE]
            await cls.client.admin.command("ping")
            logger.info("Connected to MongoDB database: %s", settings.MONGODB_DATABASE)
            await cls.init_indexes()
        except Exception as e:
            logger.warning("MongoDB initial connection failed: %s. Running in degraded mode until database is available.", e)

    @classmethod
    async def init_indexes(cls) -> None:
        if cls.db is None:
            return
        try:
            await cls.db.sources.create_index([("canonical_url", ASCENDING)], unique=True)
            await cls.db.sources.create_index([("domain", ASCENDING)])
            await cls.db.sources.create_index([("fetch_status", ASCENDING)])
            await cls.db.sources.create_index([("updated_at", ASCENDING)])

            await cls.db.content_chunks.create_index([("chunk_id", ASCENDING)], unique=True)
            await cls.db.content_chunks.create_index([("source_url", ASCENDING)])
            await cls.db.content_chunks.create_index([("domain", ASCENDING)])
            await cls.db.content_chunks.create_index(
                [("title", TEXT), ("content", TEXT)],
                weights={"title": 5, "content": 1},
                name="text_content_search_idx"
            )

            await cls.db.chat_sessions.create_index([("session_id", ASCENDING)], unique=True)
            await cls.db.chat_sessions.create_index([("updated_at", ASCENDING)])

            await cls.db.chat_messages.create_index([("session_id", ASCENDING), ("created_at", ASCENDING)])
            await cls.db.chat_messages.create_index([("message_id", ASCENDING)], unique=True)

            await cls.db.ingestion_runs.create_index([("run_id", ASCENDING)], unique=True)
            await cls.db.ingestion_runs.create_index([("started_at", ASCENDING)])

            logger.info("MongoDB indexes verified.")
        except Exception as e:
            logger.error("Failed to initialize MongoDB indexes: %s", e)

    @classmethod
    async def close(cls) -> None:
        if cls.client:
            logger.info("Closing MongoDB connection pool.")
            cls.client.close()
            cls.client = None
            cls.db = None

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            raise RuntimeError("Database is not connected. Check MONGODB_URI configuration.")
        return cls.db

    @classmethod
    async def is_healthy(cls) -> bool:
        if cls.client is None:
            return False
        try:
            await cls.client.admin.command("ping")
            return True
        except Exception:
            return False


async def get_db() -> AsyncIOMotorDatabase:
    return DatabaseManager.get_database()
