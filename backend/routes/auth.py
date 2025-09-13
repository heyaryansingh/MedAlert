from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional

from backend.models import Patient, Doctor, User
from backend.dependencies import get_database

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Placeholder for JWT token generation
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Placeholder for JWT token generation
    token = "mock_doctor_jwt_token"

    return AuthResponse(
        message="Doctor login successful",
        user_id=str(doctor["_id"]),
        role="doctor",
        token=token
    )
