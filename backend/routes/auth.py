"""Authentication routes for MedAlert healthcare monitoring system.

This module provides login endpoints for patients and doctors. Authentication
is handled via email/password validation with JWT token generation (mocked
for hackathon demo).

Routes:
    POST /patient/login: Authenticate a patient user
    POST /doctor/login: Authenticate a doctor user

Security Notes:
    - Password hashing not yet implemented (TODO for production)
    - JWT tokens are mocked; implement proper signing for production

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
    token: str # Placeholder for JWT token

@router.post("/patient/login", response_model=AuthResponse)
async def patient_login(request: LoginRequest, db: AsyncIOMotorClient = Depends(get_database)):
    """
    Authenticates a patient user.
    In a real application, password would be hashed and compared.
    A JWT token would be generated upon successful login.
    """
    patient = await db.patients.find_one({"email": request.email})

    if not patient or patient["password"] != request.password:
        # TODO(security): Replace plaintext comparison with secure hash verification
        # using bcrypt or argon2: verify_password(request.password, patient["password_hash"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO(security): Implement proper JWT generation with:
    # - Secure secret key from environment
    # - Token expiration (e.g., 15 min access, 7 day refresh)
    # - User claims (id, role, permissions)
    token = "mock_patient_jwt_token"

    return AuthResponse(
        message="Patient login successful",
        user_id=str(patient["_id"]),
        role="patient",
        token=token
    )

@router.post("/doctor/login", response_model=AuthResponse)
async def doctor_login(request: LoginRequest, db: AsyncIOMotorClient = Depends(get_database)):
    """
    Authenticates a doctor user.
    In a real application, password would be hashed and compared.
    A JWT token would be generated upon successful login.
    """
    doctor = await db.doctors.find_one({"email": request.email})

    if not doctor or doctor["password"] != request.password:
        # TODO(security): Replace plaintext comparison with secure hash verification
        # using bcrypt or argon2: verify_password(request.password, doctor["password_hash"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO(security): Implement proper JWT generation with:
    # - Secure secret key from environment
    # - Token expiration (e.g., 15 min access, 7 day refresh)
    # - User claims (id, role, permissions)
    token = "mock_doctor_jwt_token"

    return AuthResponse(
        message="Doctor login successful",
        user_id=str(doctor["_id"]),
        role="doctor",
        token=token
    )
