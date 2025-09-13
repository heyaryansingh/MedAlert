import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables from .env file
load_dotenv()

# Import models
from backend.models import (
    Patient, Doctor, User, Vital, SymptomLog, ChatMessage, Alert,
    DoctorNote, Prescription, Appointment, ImageUpload, PyObjectId
)
from backend.routes import auth # Import the auth router
from backend.routes import patient # Import the patient router
from backend.routes import doctor # Import the doctor router

app = FastAPI(
    title="MedAlert AI Backend",
    description="API for patient monitoring and doctor support system.",
    version="0.1.0",
)

# Include routers
app.include_router(auth.router, tags=["Authentication"], prefix="/api")
app.include_router(patient.router, tags=["Patient"], prefix="/api")
app.include_router(doctor.router, tags=["Doctor"], prefix="/api")

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_DETAILS = os.getenv("DATABASE_URL")
if not MONGO_DETAILS:
    raise ValueError("DATABASE_URL environment variable not set.")

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.medalertdb # Database name

# Collections
patients_collection = database.patients
doctors_collection = database.doctors
vitals_collection = database.vitals
symptom_logs_collection = database.symptom_logs
chat_messages_collection = database.chat_messages
alerts_collection = database.alerts
doctor_notes_collection = database.doctor_notes
prescriptions_collection = database.prescriptions
appointments_collection = database.appointments
image_uploads_collection = database.image_uploads

@app.on_event("startup")
async def startup_db_client():
    """Connects to MongoDB on application startup."""
    app.mongodb_client = client
    app.mongodb = database
    print("Connected to MongoDB.")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Closes MongoDB connection on application shutdown."""
    app.mongodb_client.close()
    print("Disconnected from MongoDB.")

@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint for the MedAlert AI API."""
    return {"message": "Welcome to MedAlert AI API!"}

# Dependency to get the database client
async def get_database() -> AsyncIOMotorClient:
    """Dependency that provides the MongoDB database client."""
    return database