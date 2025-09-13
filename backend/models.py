from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# Custom ObjectId type for Pydantic
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        field_schema.update(type="string")

# --- User Models ---
class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    email: EmailStr
    password: str # In a real app, this would be hashed
    role: str # "patient" or "doctor"

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Patient(User):
    name: str
    date_of_birth: str
    contact_number: Optional[str] = None
    address: Optional[str] = None
    doctor_id: Optional[PyObjectId] = None # Doctor assigned to this patient

class Doctor(User):
    name: str
    specialization: str
    contact_number: Optional[str] = None

# --- Patient Data Models ---
class Vital(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    # Add more vitals as needed

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class SymptomLog(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symptom_description: str
    severity: Optional[int] = Field(None, ge=1, le=10) # 1-10 scale
    # Additional fields for symptoms

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChatMessage(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender: str # "patient" or "ai"
    message: str
    image_url: Optional[str] = None # URL to uploaded image if any

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Alert(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    alert_type: str # e.g., "high_risk_vitals", "wound_deterioration", "symptom_escalation"
    message: str
    severity: str # "low", "medium", "high", "critical"
    resolved: bool = False

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DoctorNote(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    doctor_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    note_content: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Prescription(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    doctor_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    medication_name: str
    dosage: str
    instructions: str
    start_date: datetime
    end_date: datetime

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Appointment(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    doctor_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    appointment_time: datetime
    reason: str
    status: str # "scheduled", "completed", "cancelled"

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ImageUpload(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    patient_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    image_url: str # URL to the uploaded image (e.g., S3 bucket, local storage)
    description: Optional[str] = None
    ai_analysis_summary: Optional[str] = None # AI-generated summary of the image

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}