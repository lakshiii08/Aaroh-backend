import asyncio
import re
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging import logger

class MongoManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    is_mock: bool = False

    @classmethod
    async def connect(cls):
        """Connects to MongoDB with automatic fallback to AsyncMongoMockClient if server is unavailable."""
        if cls.db is not None:
            return cls.db

        try:
            safe_uri = re.sub(r"://[^@/]+@", "://***:***@", settings.MONGODB_URI)
            logger.info(f"Connecting to MongoDB at {safe_uri}...")
            real_client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
            )
            # Test ping
            await real_client.admin.command("ping")
            cls.client = real_client
            cls.db = cls.client[settings.MONGODB_DATABASE]
            cls.is_mock = False
            logger.info(f"Connected to MongoDB database: {settings.MONGODB_DATABASE}")
        except Exception as e:
            if settings.MONGODB_USE_MOCK_FALLBACK:
                logger.warning(
                    f"MongoDB connection failed ({e}). Falling back to in-memory AsyncMongoMockClient for authentication."
                )
                from mongomock_motor import AsyncMongoMockClient
                cls.client = AsyncMongoMockClient()
                cls.db = cls.client[settings.MONGODB_DATABASE]
                cls.is_mock = True
                logger.info(f"Initialized in-memory MongoDB database: {settings.MONGODB_DATABASE}")
            else:
                logger.error(f"MongoDB connection error: {e}")
                raise

        await cls._init_indexes()
        return cls.db

    @classmethod
    async def _init_indexes(cls):
        """Creates unique indexes for scoped roll numbers, emails, and school codes."""
        if cls.db is None:
            return
        try:
            # users collection
            users_col = cls.db["users"]
            await users_col.create_index("email", unique=True, sparse=True)
            await users_col.create_index("user_id", unique=True)
            
            # students collection: unique roll_number scoped to school_id and grade_level
            students_col = cls.db["students"]
            await students_col.create_index(
                [("school_id", 1), ("grade_level", 1), ("roll_number", 1)],
                unique=True,
            )
            await students_col.create_index("student_id", unique=True)

            # schools collection
            schools_col = cls.db["schools"]
            await schools_col.create_index("school_id", unique=True)

            # sessions collection
            sessions_col = cls.db["sessions"]
            await sessions_col.create_index("token_jti", unique=True)
            logger.info("MongoDB identity indexes initialized successfully.")
        except Exception as idx_err:
            logger.warning(f"Note on MongoDB index initialization: {idx_err}")

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB client disconnected.")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            # If called before async event loop starts, initialize synchronously if mock
            if settings.MONGODB_USE_MOCK_FALLBACK:
                from mongomock_motor import AsyncMongoMockClient
                cls.client = AsyncMongoMockClient()
                cls.db = cls.client[settings.MONGODB_DATABASE]
                cls.is_mock = True
            else:
                raise RuntimeError("MongoDB is not connected. Call MongoManager.connect() first.")
        return cls.db

async def get_mongo_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency for injecting MongoDB database."""
    if MongoManager.db is None:
        await MongoManager.connect()
    return MongoManager.db
