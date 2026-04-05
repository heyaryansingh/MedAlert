"""MedAlert AI Backend - FastAPI application for patient monitoring and doctor support.

This module initializes the FastAPI application, configures middleware,
establishes MongoDB connections, and registers API routers for authentication,
patient management, and doctor workflows.

Example:
    Run the server with uvicorn:

        $ uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Attributes:
    app: The FastAPI application instance.
    database: The MongoDB database instance (or None in demo mode).
"""

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
    DoctorNote, Prescription, Appointment, ImageUpload, PyObjectId, ConversationSummary
)
from backend.routes import auth # Import the auth router
from backend.routes import patient # Import the patient router
from backend.routes import doctor # Import the doctor router
from backend.dependencies import get_database # Import get_database from dependencies

app = FastAPI(
    title="MedAlert AI Backend",
    description="API for patient monitoring and doctor support system.",
    version="0.1.0",
)

# Include routers
app.include_router(auth.router, tags=["Authentication"], prefix="/api/auth")
app.include_router(patient.router, tags=["Patient"], prefix="/api/patient")
app.include_router(doctor.router, tags=["Doctor"], prefix="/api/doctor")

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_DETAILS = os.getenv("DATABASE_URL", "mongodb://localhost:27017/medalertdb")
if not MONGO_DETAILS:
    print("Warning: DATABASE_URL not set, using default MongoDB connection")

try:
    client = AsyncIOMotorClient(MONGO_DETAILS)
    database = client.medalertdb # Database name
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Warning: Could not connect to MongoDB: {e}")
    print("Running in demo mode without database connection.")
    client = None
    database = None

# Collections
if database:
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
    conversation_summaries_collection = database.conversation_summaries
else:
    # Mock collections for demo mode
    patients_collection = None
    doctors_collection = None
    vitals_collection = None
    symptom_logs_collection = None
    chat_messages_collection = None
    alerts_collection = None
    doctor_notes_collection = None
    prescriptions_collection = None
    appointments_collection = None
    image_uploads_collection = None
    conversation_summaries_collection = None

@app.on_event("startup")
async def startup_db_client():
    """Connects to MongoDB on application startup."""
    if client:
        app.mongodb_client = client
        app.mongodb = database
        print("Connected to MongoDB.")
    else:
        print("Running in demo mode without MongoDB.")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Closes MongoDB connection on application shutdown."""
    if client:
        app.mongodb_client.close()
        print("Disconnected from MongoDB.")

@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint for the MedAlert AI API."""
    return {"message": "Welcome to MedAlert AI API!"}