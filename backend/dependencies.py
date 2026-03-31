"""
FastAPI dependency injection for database access.

This module provides async dependencies for accessing the MongoDB database
through the Motor async driver.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.main import database


async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency that provides the MongoDB database instance.

    This is an async generator that yields the database connection.
    Use with FastAPI's Depends() for automatic injection.

    Returns:
        AsyncIOMotorDatabase: The MongoDB database instance for async operations.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncIOMotorDatabase = Depends(get_database)):
            return await db.items.find().to_list(100)
    """
    return database