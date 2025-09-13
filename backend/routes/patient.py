from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from datetime import datetime
import shutil

from backend.models import Vital, ImageUpload, ChatMessage, Alert, PyObjectId, ConversationSummary, DoctorNote, Patient
from backend.main import get_database # Assuming get_database is implemented in main.py
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

@router.post("/patient/chatbot_message", response_model=ChatMessage)
async def chatbot_message(
    message: ChatMessage,
    patient_id: PyObjectId = Depends(get_current_patient_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Receives a patient message (and optional image_url), processes it with AI, and responds.
    Also logs the conversation.
    """
    message.patient_id = patient_id
    message.timestamp = datetime.utcnow()
    message.sender = "patient"

    # Log patient message
    await db.chat_messages.insert_one(message.model_dump(by_alias=True, exclude=["id"]))

    try:
        # Get AI response, image requirement, and AI summary
        ai_response_text, requires_image, ai_summary = await get_chatbot_response(message.message, patient_id, db, message.image_url)

        ai_message = ChatMessage(
            patient_id=patient_id,
            sender="ai",
            message=ai_response_text,
            ai_summary=ai_summary,
            requires_image_upload=requires_image,
            timestamp=datetime.utcnow(),
            image_url=None # AI responses typically don't have images, but explicitly set to None
        )
        new_ai_msg = await db.chat_messages.insert_one(ai_message.model_dump(by_alias=True, exclude=["id"]))
        created_ai_message = await db.chat_messages.find_one({"_id": new_ai_msg.inserted_id})
        
        if not created_ai_message:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created AI message.")
        
        ai_message = ChatMessage(**created_ai_message)
        print(f"AI Message successfully created and retrieved: {ai_message.model_dump_json()}")
    except Exception as e:
        print(f"Error in chatbot_message endpoint: {e}")
        # Return a generic error message from AI if something goes wrong
        ai_message = ChatMessage(
            patient_id=patient_id,
            sender="ai",
            message="I'm sorry, I encountered an error while processing your request. Please try again.",
            ai_summary=f"Error: {e}",
            requires_image_upload=False,
            timestamp=datetime.utcnow(),
            image_url=None
        )
        # Attempt to save this error message to the chat history
        await db.chat_messages.insert_one(ai_message.model_dump(by_alias=True, exclude=["id"]))
        # Still return a 200 OK so frontend can display the error message

    # Update or create ConversationSummary for the patient
    existing_summary = await db.conversation_summaries.find_one({"patient_id": patient_id})
    if existing_summary:
        await db.conversation_summaries.update_one(
            {"patient_id": patient_id},
            {"$set": {"summary_text": ai_summary, "last_updated": datetime.utcnow()}}
        )
    else:
        new_summary = ConversationSummary(
            patient_id=patient_id,
            summary_text=ai_summary,
            last_updated=datetime.utcnow()
        )
        await db.conversation_summaries.insert_one(new_summary.model_dump(by_alias=True, exclude=["id"]))

    # If AI requests an image, create an alert for the patient
    if requires_image:
        alert = Alert(
            patient_id=patient_id,
            alert_type="image_request",
            message="The AI chatbot has requested an image related to your symptoms. Please upload one.",
            severity="medium",
            resolved=False,
            timestamp=datetime.utcnow(),
            chat_message_id=ai_message.id # Link alert to the AI message that requested the image
        )
        await db.alerts.insert_one(alert.model_dump(by_alias=True, exclude=["id"]))

    return JSONResponse(
        status_code=200,
        content={
            "_id": str(ai_message.id),
            "sender": ai_message.sender,
            "message": ai_message.message,
            "timestamp": ai_message.timestamp.isoformat(),
            "requires_image_upload": ai_message.requires_image_upload,
            "image_url": ai_message.image_url # This will be None for AI messages, but included for consistency
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

@router.get("/patient/chat_history", response_model=List[ChatMessage])
async def get_patient_chat_history(
    patient_id: PyObjectId = Depends(get_current_patient_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Returns the chat history for the current patient.
    """
    chat_messages_cursor = db.chat_messages.find({"patient_id": patient_id}).sort("timestamp", 1)
    chat_messages = []
    async for m in chat_messages_cursor:
        # Ensure sender is "ai" for AI messages, even if old entries used "model"
        if m.get('sender') == 'model':
            m['sender'] = 'ai'
        chat_messages.append(ChatMessage(**m))
    return chat_messages

@router.post("/patient/generate_notes")
async def generate_doctor_notes(
    patient_id: PyObjectId = Depends(get_current_patient_id),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Generates AI notes for the doctor based on the patient's chat history.
    """
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
    
    if new_note.inserted_id:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "AI notes generated and sent to doctor successfully.", "note_id": str(new_note.inserted_id)}
        )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate and store AI notes.")