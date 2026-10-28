"""Parsing of client-supplied MongoDB ObjectIds for route handlers."""

from bson import ObjectId
from fastapi import HTTPException, status


def parse_object_id(value: str, field: str = "id") -> ObjectId:
    """Parse a client-supplied ObjectId, rejecting malformed ones with HTTP 400.

    ObjectId("bad") raises bson.errors.InvalidId, which FastAPI would surface
    as a 500 instead of telling the client its input was wrong.
    """
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}: {value!r}"
        )
    return ObjectId(value)
