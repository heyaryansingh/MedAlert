from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List, Optional
import os

app = FastAPI(
    title="MedAlert AI Backend",
    description="API for patient monitoring and doctor support system.",
    version="0.1.0",
)

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple request models
class ChatbotMessageRequest(BaseModel):
    patient_id: str
    message: str

@app.get("/")
async def read_root():
    """Root endpoint for the MedAlert AI API."""
    return {"message": "Welcome to MedAlert AI API!", "status": "running"}

@app.post("/api/patient/chatbot_message")
async def chatbot_message(request: ChatbotMessageRequest):
    """
    Receives a patient message and responds with AI-generated response.
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "requires_image_upload": False,
                "image_url": None
            }
        )

@app.get("/api/patient/chat_history")
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

@app.get("/api/patient/vitals/{patient_id}")
async def get_patient_vitals(patient_id: str):
    """Mock vitals data"""
    return [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "heart_rate": 75,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "temperature": 36.5,
            "oxygen_saturation": 98.0
        }
    ]

@app.get("/api/patient/get_alerts")
async def get_patient_alerts():
    """Mock alerts data"""
    return []

@app.get("/api/patient/risk_score/{patient_id}")
async def get_patient_risk_score(patient_id: str):
    """Mock risk score"""
    return {"risk_score": 3.2}

@app.post("/api/patient/generate_notes")
async def generate_doctor_notes(request: ChatbotMessageRequest):
    """Mock notes generation"""
    return JSONResponse(
        status_code=200,
        content={"message": "AI notes generated and sent to doctor successfully.", "note_id": "demo_note_id"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
