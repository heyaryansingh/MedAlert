from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from datetime import datetime
import shutil
import os
from pydantic import BaseModel

from backend.models import Vital, ImageUpload, ChatMessage, Alert, PyObjectId, ConversationSummary, DoctorNote, Patient
from backend.dependencies import get_database
from backend.ai.chatbot_logic import get_chatbot_response, summarize_conversation_for_doctor # Placeholder for AI functions

router = APIRouter()

# Placeholder for authentication dependency
# In a real app, this would validate a JWT token and return the current user's ID
async def get_current_patient_id():
    """
    Placeholder for a dependency that returns the current authenticated patient's ID.
    For hackathon demo, we might mock this or use a simple header.
    """
    # For demo purposes, let's assume a patient ID is passed in a header or is hardcoded
    # In a real app, this would involve decoding a JWT token
    mock_patient_id = "650d7f3e7b1f8c9d0e1f2a3b" # Example patient ID
    return PyObjectId(mock_patient_id)

@router.post("/patient/log_vitals", response_model=Vital)
async def log_vitals(
    vitals: Vital,
    patient_id: PyObjectId = Depends(get_current_patient_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Allows a patient to log their daily vitals.
    """
    vitals.patient_id = patient_id
    vitals.timestamp = datetime.utcnow() # Ensure timestamp is current

    new_vital = await db.vitals.insert_one(vitals.model_dump(by_alias=True, exclude=["id"]))
    created_vital = await db.vitals.find_one({"_id": new_vital.inserted_id})

    if created_vital:
        return Vital(**created_vital)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to log vitals")

@router.post("/patient/upload_image")
async def upload_image(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    patient_id: PyObjectId = Depends(get_current_patient_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Allows a patient to upload an image (e.g., wound/bandage photos).
    Images will be saved locally for the hackathon demo. In a real app,
    these would be uploaded to cloud storage like AWS S3 or Google Cloud Storage.
    """
    # Create a directory to store images if it doesn't exist
    upload_dir = f"simulated_data/patient_images/{str(patient_id)}"
    os.makedirs(upload_dir, exist_ok=True)

    file_location = f"{upload_dir}/{file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload image: {e}")

    image_upload = ImageUpload(
        patient_id=patient_id,
        image_url=file_location,
        description=description,
        timestamp=datetime.utcnow()
    )

    new_image_upload = await db.image_uploads.insert_one(image_upload.model_dump(by_alias=True, exclude=["id"]))
    created_image = await db.image_uploads.find_one({"_id": new_image_upload.inserted_id})

    if created_image:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "Image uploaded successfully", "image_id": str(created_image["_id"]), "image_url": file_location}
        )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record image upload in DB")

class ChatbotMessageRequest(BaseModel):
    patient_id: str
    message: str

@router.post("/patient/chatbot_message")
async def chatbot_message(request: ChatbotMessageRequest):
    """
    Receives a patient message and responds with AI-generated response.
    Works in demo mode without database.
    """
    try:
        # Simple AI responses for demo
        message_lower = request.message.lower()
        
        if any(word in message_lower for word in ["pain", "hurt", "ache"]):
            ai_response = "I understand you're experiencing pain. Can you tell me more about where the pain is located and how severe it is on a scale of 1-10?"
            requires_image = False
        elif any(word in message_lower for word in ["wound", "cut", "injury", "scar"]):
            ai_response = "I'd like to see the wound to better assess it. Could you please upload a photo of the affected area?"
            requires_image = True
        elif any(word in message_lower for word in ["fever", "temperature", "hot"]):
            ai_response = "A fever can be concerning after surgery. What's your current temperature? Have you taken any medication for it?"
            requires_image = False
        elif any(word in message_lower for word in ["bleeding", "blood"]):
            ai_response = "Bleeding after surgery needs immediate attention. Is the bleeding heavy or just spotting? Please contact your doctor immediately if it's heavy."
            requires_image = False
        elif any(word in message_lower for word in ["swelling", "swollen", "puffy"]):
            ai_response = "Swelling is common after surgery but should be monitored. Where is the swelling located? Is it getting worse or better?"
            requires_image = True
        elif any(word in message_lower for word in ["nausea", "sick", "vomit"]):
            ai_response = "Nausea can be a side effect of medications or anesthesia. Are you able to keep fluids down? When did this start?"
            requires_image = False
        elif any(word in message_lower for word in ["dizzy", "lightheaded", "faint"]):
            ai_response = "Feeling dizzy can be concerning. Are you experiencing this when standing up or all the time? Have you been drinking enough fluids?"
            requires_image = False
        elif any(word in message_lower for word in ["sleep", "tired", "fatigue"]):
            ai_response = "Fatigue is normal during recovery. How many hours of sleep are you getting? Are you able to rest comfortably?"
            requires_image = False
        else:
            ai_response = "Thank you for sharing that with me. Can you tell me more about your symptoms? How are you feeling overall today?"
            requires_image = False
        
        # Check for critical symptoms
        critical_keywords = ["severe pain", "chest pain", "difficulty breathing", "high fever", "unconscious", "bleeding heavily", "severe headache", "stroke", "heart attack", "emergency"]
        if any(keyword in message_lower for keyword in critical_keywords):
            ai_response += " I'm concerned about your symptoms. Please contact your doctor immediately or go to the emergency room if symptoms worsen."

        return JSONResponse(
            status_code=200,
            content={
                "_id": "demo_message_id",
                "sender": "ai",
                "message": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
                "requires_image_upload": requires_image,
                "image_url": None
            }
        )
        
    except Exception as e:
        print(f"Error in chatbot_message endpoint: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "_id": "error_message_id",
                "sender": "ai",
                "message": "I'm sorry, I'm having trouble processing your message right now. Please try again.",
                "timestamp": datetime.utcnow().isoformat(),
                "requires_image_upload": False,
                "image_url": None
            }
        )

@router.get("/patient/get_alerts", response_model=List[Alert])
async def get_alerts(
    patient_id: PyObjectId = Depends(get_current_patient_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Returns AI-generated instructions or alerts for the patient.
    """
    alerts_cursor = db.alerts.find({"patient_id": patient_id, "resolved": False}).sort("timestamp", -1)
    alerts = [Alert(**alert) async for alert in alerts_cursor]
    return alerts

@router.get("/patient/chat_history")
async def get_patient_chat_history():
    """
    Returns mock chat history for demo purposes.
    """
    return [
        {
            "_id": "demo_1",
            "sender": "ai",
            "message": "Hello! I am MedAlert AI. How are you feeling today?",
            "timestamp": datetime.utcnow().isoformat(),
            "image_url": None
        }
    ]

@router.post("/patient/generate_notes")
async def generate_doctor_notes(
    request: ChatbotMessageRequest,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Generates AI notes for the doctor based on the patient's chat history.
    This is called when the patient clicks "Checkup Done".
    """
    patient_id = PyObjectId(request.patient_id)
    
    # Fetch all chat messages for the patient
    chat_history_cursor = db.chat_messages.find({"patient_id": patient_id}).sort("timestamp", 1)
    chat_history = [ChatMessage(**msg) async for msg in chat_history_cursor]

    if not chat_history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No chat history found for this patient.")

    # Concatenate chat messages into a single string for summarization
    full_conversation_text = "\n".join([
        f"{'Patient' if msg.sender == 'patient' else 'AI'}: {msg.message}"
        for msg in chat_history
    ])

    # Generate a comprehensive summary/note using the AI
    ai_generated_note_content = await summarize_conversation_for_doctor(full_conversation_text)

    # Fetch the patient to get their assigned doctor_id
    patient = await db.patients.find_one({"_id": patient_id})
    if not patient or not patient.get("doctor_id"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient or assigned doctor not found.")
    
    doctor_id = PyObjectId(patient["doctor_id"])

    # Create and store the DoctorNote
    doctor_note = DoctorNote(
        patient_id=patient_id,
        doctor_id=doctor_id,
        note_content=ai_generated_note_content,
        timestamp=datetime.utcnow()
    )

    new_note = await db.doctor_notes.insert_one(doctor_note.model_dump(by_alias=True, exclude=["id"]))
    
    # Create a notification alert for the doctor
    notification_alert = Alert(
        patient_id=patient_id,
        alert_type="patient_checkup_complete",
        message=f"Patient {patient.get('name', 'Unknown')} has completed their checkup. New AI-generated notes are available for review.",
        severity="medium",
        resolved=False,
        timestamp=datetime.utcnow(),
        doctor_id=doctor_id
    )
    await db.alerts.insert_one(notification_alert.model_dump(by_alias=True, exclude=["id"]))
    
    if new_note.inserted_id:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "AI notes generated and sent to doctor successfully.", "note_id": str(new_note.inserted_id)}
        )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate and store AI notes.")