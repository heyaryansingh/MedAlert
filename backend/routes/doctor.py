from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from datetime import datetime

from backend.models import (
    Patient, Vital, SymptomLog, ChatMessage, Alert, DoctorNote,
    Prescription, Appointment, ImageUpload, PyObjectId, ConversationSummary
)
from backend.main import get_database # Assuming get_database is implemented in main.py
from backend.ai.chatbot_logic import analyze_vitals_for_risk, analyze_image_for_wound, get_patient_risk_score # Import AI functions

router = APIRouter()

# Placeholder for authentication dependency
# In a real app, this would validate a JWT token and return the current doctor's ID
async def get_current_doctor_id():
    """
    Placeholder for a dependency that returns the current authenticated doctor's ID.
    For hackathon demo, we might mock this or use a simple header.
    """
    # For demo purposes, let's assume a doctor ID is passed in a header or is hardcoded
    mock_doctor_id = "650d7f3e7b1f8c9d0e1f2a3c" # Example doctor ID
    return PyObjectId(mock_doctor_id)

@router.get("/doctor/get_patients", response_model=List[Patient])
async def get_patients(
    doctor_id: PyObjectId = Depends(get_current_doctor_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Returns a list of all patients assigned to the current doctor, including their risk scores.
    For demo, returns all patients.
    """
    patients_cursor = db.patients.find({}) # In a real app, filter by doctor_id
    patients = []
    async for patient_data in patients_cursor:
        patient = Patient(**patient_data)
        # Calculate risk score for each patient
        patient.risk_score = await get_patient_risk_score(patient.id, db)
        patients.append(patient)
    return patients

@router.get("/doctor/get_patient_data/{patient_id}", response_model=dict)
async def get_patient_data(
    patient_id: str,
    doctor_id: PyObjectId = Depends(get_current_doctor_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Returns comprehensive data for a specific patient, including vitals, symptom summaries,
    images, risk scores, chat history, notes, prescriptions, and appointments.
    """
    patient_obj_id = PyObjectId(patient_id)
    patient = await db.patients.find_one({"_id": patient_obj_id})
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    vitals_cursor = db.vitals.find({"patient_id": patient_obj_id}).sort("timestamp", -1)
    vitals = [Vital(**v) async for v in vitals_cursor]

    symptom_logs_cursor = db.symptom_logs.find({"patient_id": patient_obj_id}).sort("timestamp", -1)
    symptom_logs = [SymptomLog(**s) async for s in symptom_logs_cursor]

    chat_messages_cursor = db.chat_messages.find({"patient_id": patient_obj_id}).sort("timestamp", 1)
    chat_messages = [ChatMessage(**m) async for m in chat_messages_cursor]

    alerts_cursor = db.alerts.find({"patient_id": patient_obj_id}).sort("timestamp", -1)
    alerts = [Alert(**a) async for a in alerts_cursor]

    doctor_notes_cursor = db.doctor_notes.find({"patient_id": patient_obj_id}).sort("timestamp", -1)
    doctor_notes = [DoctorNote(**n) async for n in doctor_notes_cursor]

    prescriptions_cursor = db.prescriptions.find({"patient_id": patient_obj_id}).sort("timestamp", -1)
    prescriptions = [Prescription(**p) async for p in prescriptions_cursor]

    appointments_cursor = db.appointments.find({"patient_id": patient_obj_id}).sort("appointment_time", -1)
    appointments = [Appointment(**a) async for a in appointments_cursor]

    image_uploads_cursor = db.image_uploads.find({"patient_id": patient_obj_id}).sort("timestamp", -1)
    image_uploads = [ImageUpload(**img) async for img in image_uploads_cursor]

    # AI-generated summaries and risk score
    risk_score = await get_patient_risk_score(patient_obj_id, db)
    symptom_summary = "No recent symptoms."
    # Fetch conversation summary
    conversation_summary = await db.conversation_summaries.find_one({"patient_id": patient_obj_id})
    
    return {
        "patient_profile": Patient(**patient),
        "vitals": vitals,
        "symptom_logs": symptom_logs,
        "chat_history": chat_messages,
        "alerts": alerts,
        "doctor_notes": doctor_notes,
        "prescriptions": prescriptions,
        "appointments": appointments,
        "image_uploads": image_uploads,
        "risk_score": risk_score,
        "conversation_summary": ConversationSummary(**conversation_summary) if conversation_summary else None
    }

class AddNoteRequest(BaseModel):
    patient_id: str
    note_content: str

@router.post("/doctor/add_notes", response_model=DoctorNote)
async def add_notes(
    request: AddNoteRequest,
    doctor_id: PyObjectId = Depends(get_current_doctor_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Allows a doctor to add notes for a specific patient.
    """
    patient_obj_id = PyObjectId(request.patient_id)
    note = DoctorNote(
        patient_id=patient_obj_id,
        doctor_id=doctor_id,
        note_content=request.note_content,
        timestamp=datetime.utcnow()
    )
    new_note = await db.doctor_notes.insert_one(note.model_dump(by_alias=True, exclude=["id"]))
    created_note = await db.doctor_notes.find_one({"_id": new_note.inserted_id})

    if created_note:
        return DoctorNote(**created_note)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add note")

class PrescribeRequest(BaseModel):
    patient_id: str
    medication_name: str
    dosage: str
    instructions: str
    start_date: datetime
    end_date: datetime

@router.post("/doctor/prescribe", response_model=Prescription)
async def prescribe(
    request: PrescribeRequest,
    doctor_id: PyObjectId = Depends(get_current_doctor_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Allows a doctor to prescribe medication for a patient.
    """
    patient_obj_id = PyObjectId(request.patient_id)
    prescription = Prescription(
        patient_id=patient_obj_id,
        doctor_id=doctor_id,
        medication_name=request.medication_name,
        dosage=request.dosage,
        instructions=request.instructions,
        start_date=request.start_date,
        end_date=request.end_date,
        timestamp=datetime.utcnow()
    )
    new_prescription = await db.prescriptions.insert_one(prescription.model_dump(by_alias=True, exclude=["id"]))
    created_prescription = await db.prescriptions.find_one({"_id": new_prescription.inserted_id})

    if created_prescription:
        return Prescription(**created_prescription)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add prescription")

class ScheduleAppointmentRequest(BaseModel):
    patient_id: str
    appointment_time: datetime
    reason: str

@router.post("/doctor/schedule_appointment", response_model=Appointment)
async def schedule_appointment(
    request: ScheduleAppointmentRequest,
    doctor_id: PyObjectId = Depends(get_current_doctor_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Allows a doctor to schedule an appointment for a patient.
    """
    patient_obj_id = PyObjectId(request.patient_id)
    appointment = Appointment(
        patient_id=patient_obj_id,
        doctor_id=doctor_id,
        appointment_time=request.appointment_time,
        reason=request.reason,
        status="scheduled",
        timestamp=datetime.utcnow()
    )
    new_appointment = await db.appointments.insert_one(appointment.model_dump(by_alias=True, exclude=["id"]))
    created_appointment = await db.appointments.find_one({"_id": new_appointment.inserted_id})

    if created_appointment:
        return Appointment(**created_appointment)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to schedule appointment")

class DoctorCommentRequest(BaseModel):
    chat_message_id: str
    comment_content: str

@router.post("/doctor/add_chat_comment", response_model=ChatMessage)
async def add_chat_comment(
    request: DoctorCommentRequest,
    doctor_id: PyObjectId = Depends(get_current_doctor_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Allows a doctor to add a comment to a specific chat message.
    """
    chat_message_obj_id = PyObjectId(request.chat_message_id)
    
    updated_message = await db.chat_messages.find_one_and_update(
        {"_id": chat_message_obj_id},
        {"$set": {"doctor_comment": request.comment_content}},
        return_document=True
    )

    if updated_message:
        return ChatMessage(**updated_message)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat message not found")

class TriggerAlertRequest(BaseModel):
    patient_id: str
    alert_type: str
    message: str
    severity: str
    chat_message_id: Optional[str] = None

@router.post("/doctor/trigger_alert", response_model=Alert)
async def trigger_alert(
    request: TriggerAlertRequest,
    doctor_id: PyObjectId = Depends(get_current_doctor_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Allows a doctor to manually trigger an alert for a patient.
    """
    patient_obj_id = PyObjectId(request.patient_id)
    
    alert = Alert(
        patient_id=patient_obj_id,
        alert_type=request.alert_type,
        message=request.message,
        severity=request.severity,
        resolved=False,
        timestamp=datetime.utcnow(),
        doctor_id=doctor_id,
        chat_message_id=PyObjectId(request.chat_message_id) if request.chat_message_id else None
    )
    new_alert = await db.alerts.insert_one(alert.model_dump(by_alias=True, exclude=["id"]))
    created_alert = await db.alerts.find_one({"_id": new_alert.inserted_id})

    if created_alert:
        # Optionally, update the linked chat message to mark that an alert was triggered
        if request.chat_message_id:
            await db.chat_messages.update_one(
                {"_id": PyObjectId(request.chat_message_id)},
                {"$set": {"alert_triggered": True}}
            )
        return Alert(**created_alert)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to trigger alert")

# Extend Patient model to include risk_score for doctor view
# This is a temporary solution for the demo to display risk_score in the patient list
# A more robust solution would involve a dedicated DTO or a computed property in the frontend
Patient.model_fields['risk_score'] = Optional[float]