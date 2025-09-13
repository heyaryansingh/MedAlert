from motor.motor_asyncio import AsyncIOMotorClient
from backend.main import database # Import the initialized database client from main

async def get_database() -> AsyncIOMotorClient:
    """Dependency that provides the MongoDB database client."""
    return database