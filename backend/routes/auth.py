"""Authentication routes for MedAlert healthcare monitoring system.

This module provides login endpoints for patients and doctors. Authentication
is handled via email/password validation with bcrypt hashing and signed
JWT token generation.

Routes:
    POST /patient/login: Authenticate a patient user
    POST /doctor/login: Authenticate a doctor user

Security:
    - Passwords verified using bcrypt via passlib
    - JWT tokens signed with HS256 and configurable expiration
    - Supports both legacy plaintext passwords (auto-upgrades to hash) and
      bcrypt hashes for backward compatibility during migration

Example:
    >>> import httpx
    >>> response = httpx.post(
    ...     "http://localhost:8000/patient/login",
    ...     json={"email": "patient@example.com", "password": "secret"}
    ... )
    >>> response.json()
    {'message': 'Patient login successful', 'user_id': '...', 'role': 'patient', 'token': '...'}
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

from backend.models import Patient, Doctor, User
from backend.dependencies import get_database
from backend.utils.auth_security import (
    verify_password,
    hash_password,
    create_access_token,
)

router = APIRouter()

class LoginRequest(BaseModel):
    """Request model for user authentication."""
    email: EmailStr  # Validates email format automatically
    password: str

    @field_validator('password')
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        """Ensure password is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v

class AuthResponse(BaseModel):
    message: str
    user_id: str
    role: str
    token: str


def _check_password(plain_password: str, stored_password: str) -> bool:
    """Verify password supporting both bcrypt hashes and legacy plaintext.

    If the stored password is a bcrypt hash (starts with $2b$), uses
    secure hash verification. Otherwise falls back to plaintext comparison
    for backward compatibility with existing accounts.
    """
    if stored_password.startswith("$2b$"):
        return verify_password(plain_password, stored_password)
    # Legacy plaintext comparison for unmigrated accounts
    return plain_password == stored_password


async def _upgrade_password_hash(
    collection, user_id, plain_password: str
) -> None:
    """Upgrade a legacy plaintext password to bcrypt hash in-place.

    Called after successful plaintext login to transparently migrate
    the account to secure password storage.
    """
    hashed = hash_password(plain_password)
    await collection.update_one(
        {"_id": user_id},
        {"$set": {"password": hashed}},
    )


@router.post("/patient/login", response_model=AuthResponse)
async def patient_login(request: LoginRequest, db: AsyncIOMotorClient = Depends(get_database)):
    """Authenticate a patient user with bcrypt password verification and JWT."""
    patient = await db.patients.find_one({"email": request.email})

    if not patient or not _check_password(request.password, patient["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Auto-upgrade plaintext passwords to bcrypt on successful login
    if not patient["password"].startswith("$2b$"):
        await _upgrade_password_hash(db.patients, patient["_id"], request.password)

    token = create_access_token(
        data={"sub": str(patient["_id"]), "role": "patient"}
    )

    return AuthResponse(
        message="Patient login successful",
        user_id=str(patient["_id"]),
        role="patient",
        token=token
    )

@router.post("/doctor/login", response_model=AuthResponse)
async def doctor_login(request: LoginRequest, db: AsyncIOMotorClient = Depends(get_database)):
    """Authenticate a doctor user with bcrypt password verification and JWT."""
    doctor = await db.doctors.find_one({"email": request.email})

    if not doctor or not _check_password(request.password, doctor["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Auto-upgrade plaintext passwords to bcrypt on successful login
    if not doctor["password"].startswith("$2b$"):
        await _upgrade_password_hash(db.doctors, doctor["_id"], request.password)

    token = create_access_token(
        data={"sub": str(doctor["_id"]), "role": "doctor"}
    )

    return AuthResponse(
        message="Doctor login successful",
        user_id=str(doctor["_id"]),
        role="doctor",
        token=token
    )
