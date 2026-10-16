from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging

logger = logging.getLogger("agroguard.database")

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    def connect_db(cls):
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        cls.db = cls.client[settings.DATABASE_NAME]
        logger.info("Successfully connected to MongoDB")

    @classmethod
    def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            logger.info("MongoDB connection closed")

def get_database():
    if Database.db is None:
        Database.connect_db()
    return Database.db
