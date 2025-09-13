import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai
from dotenv import load_dotenv

from backend.models import PyObjectId, ChatMessage, SymptomLog, Vital, ImageUpload, Alert

# Load environment variables
load_dotenv()

from dotenv import load_dotenv

from backend.models import PyObjectId, ChatMessage, SymptomLog, Vital, ImageUpload, Alert

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

# System instruction for the Gemini model
SYSTEM_INSTRUCTION = (
    "You are MedAlert AI, an empathetic and helpful patient monitoring chatbot. "
    "Your goal is to gather detailed information about the patient's symptoms and vitals. "
    "Upon the patient's first message after the initial greeting, ask a targeted follow-up question to get more specific information about their well-being. "
    "Ask open-ended questions. If symptoms like 'wound', 'rash', or 'swelling' are mentioned, "
    "politely ask the patient to upload a photo. Provide basic, reassuring advice if appropriate, "
    "but always prioritize gathering information. Do not provide medical diagnoses or treatment plans."
)

# Initialize Gemini model with system instruction
gemini_model = genai.GenerativeModel('gemini-pro', system_instruction=SYSTEM_INSTRUCTION)

async def get_chatbot_response(patient_message: str, patient_id: PyObjectId, db: AsyncIOMotorClient) -> Tuple[str, bool, str]:
    """
    Generates an AI chatbot response using Google Gemini model.
    Also simulates prompting for an image based on keywords.
    Returns the AI response, whether an image is required, and an AI summary of the interaction.
    """
    requires_image = False
    ai_summary = ""
    
    # Check for keywords that might require an image
    patient_message_lower = patient_message.lower()
    if "wound" in patient_message_lower or "bandage" in patient_message_lower or "rash" in patient_message_lower or "swelling" in patient_message_lower:
        requires_image = True

    try:
        # Fetch recent chat history for context
        recent_chat_cursor = db.chat_messages.find({"patient_id": patient_id}).sort("timestamp", 1).limit(10) # Increased limit for more context
        recent_chat_history_raw = [msg async for msg in recent_chat_cursor]
        
        # Format chat history for Gemini's start_chat
        conversation_history = []
        for chat_entry in recent_chat_history_raw:
            if chat_entry['sender'] == "patient":
                conversation_history.append({"role": "user", "parts": [chat_entry['message']]})
            else: # Assuming 'model' for AI responses
                conversation_history.append({"role": "model", "parts": [chat_entry['message']]})
        
        # Start a chat session with the history
        chat_session = gemini_model.start_chat(history=conversation_history)
        
        # Send the latest patient message
        response = await chat_session.send_message_async(patient_message)

        ai_response_text = response.text

        # Generate a summary of the current interaction for the doctor
        full_interaction_text = f"Patient: {patient_message}\nAI: {ai_response_text}"
        ai_summary = await summarize_conversation_for_doctor(full_interaction_text)
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        ai_response_text = "I'm sorry, I'm having trouble connecting to the AI at the moment. Please try again later."
        requires_image = False # If AI fails, don't request image
        ai_summary = f"AI summary unavailable due to error: {e}"

    # Simulate logging symptom if a relevant keyword is found (can be enhanced with AI analysis)
    if any(keyword in patient_message_lower for keyword in ["fever", "pain", "headache", "nausea", "tired", "dizzy", "cough", "rash", "swelling", "sore throat", "diarrhea", "constipation", "stress", "anxiety", "mood", "depressed", "wound"]):
        symptom_log = SymptomLog(
            patient_id=patient_id,
            symptom_description=patient_message,
            severity=random.randint(1, 10), # Mock severity, could be AI-determined
            timestamp=datetime.utcnow()
        )
        await db.symptom_logs.insert_one(symptom_log.model_dump(by_alias=True, exclude=["id"]))

    return ai_response_text, requires_image, ai_summary

async def summarize_conversation_for_doctor(conversation_text: str) -> str:
    """
    Summarizes a given conversation text concisely for a doctor using Google Gemini model.
    """
    try:
        response = await gemini_model.generate_content_async(
            f"Summarize the following patient-AI interaction concisely for a doctor, highlighting key symptoms, concerns, and AI actions: {conversation_text}"
        )
        summary = response.text
    except Exception as e:
        print(f"Error summarizing with Gemini API: {e}")
        summary = f"AI summary unavailable for interaction: '{conversation_text}'"
    return summary.strip()

async def analyze_vitals_for_risk(vitals: Vital) -> Optional[str]:
    """
    Mocks AI analysis of vitals for risk assessment.
    In a real scenario, this could use a more sophisticated rule-based system or ML model.
    """
    risk_message = None
    if vitals.heart_rate and (vitals.heart_rate > 100 or vitals.heart_rate < 60):
        risk_message = "Abnormal heart rate detected."
    if vitals.blood_pressure_systolic and vitals.blood_pressure_diastolic:
        if vitals.blood_pressure_systolic > 140 or vitals.blood_pressure_diastolic > 90:
            risk_message = "Elevated blood pressure detected."
        elif vitals.blood_pressure_systolic < 90 or vitals.blood_pressure_diastolic < 60:
            risk_message = "Low blood pressure detected."
    if vitals.temperature and vitals.temperature > 38.0:
        risk_message = "Elevated temperature detected (fever)."
    if vitals.oxygen_saturation and vitals.oxygen_saturation < 95.0:
        risk_message = "Low oxygen saturation detected."
    return risk_message

async def analyze_image_for_wound(image_path: str) -> Dict[str, Any]:
    """
    Mocks AI analysis of an image for wound assessment using a pretrained CNN model.
    In a real scenario, this would involve loading and running a PyTorch/TensorFlow model.
    For the demo, it simulates a result.
    """
    # Placeholder for actual CNN model inference
    # Example:
    # from PIL import Image
    # import torch
    # from torchvision import transforms
    # model = load_pretrained_cnn_model()
    # image = Image.open(image_path).convert('RGB')
    # preprocess = transforms.Compose([...])
    # input_tensor = preprocess(image)
    # output = model(input_tensor)
    # prediction = interpret_output(output)

    analysis_result = {
        "wound_detected": random.choice([True, False]),
        "severity_score": random.randint(1, 10),
        "description": "Simulated AI image analysis: "
    }
    if analysis_result["wound_detected"]:
        analysis_result["description"] += f"Wound detected with severity {analysis_result['severity_score']}/10. "
        if analysis_result["severity_score"] > 7:
            analysis_result["description"] += "Suggest immediate doctor review."
        else:
            analysis_result["description"] += "Monitor closely."
    else:
        analysis_result["description"] += "No obvious wound detected."
    return analysis_result

async def get_patient_risk_score(patient_id: PyObjectId, db: AsyncIOMotorClient) -> float:
    """
    Calculates a patient's overall risk score based on vitals, symptoms, and image analysis.
    Combines mock AI analysis results.
    """
    # Fetch recent vitals (e.g., last 24 hours)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    recent_vitals_cursor = db.vitals.find({"patient_id": patient_id, "timestamp": {"$gte": one_day_ago}})
    recent_vitals = [Vital(**v) async for v in recent_vitals_cursor]

    # Fetch recent symptom logs
    recent_symptoms_cursor = db.symptom_logs.find({"patient_id": patient_id, "timestamp": {"$gte": one_day_ago}})
    recent_symptoms = [SymptomLog(**s) async for s in recent_symptoms_cursor]

    # Fetch recent image uploads with AI analysis
    recent_images_cursor = db.image_uploads.find({"patient_id": patient_id, "timestamp": {"$gte": one_day_ago}, "ai_analysis_summary": {"$ne": None}})
    recent_images = [ImageUpload(**img) async for img in recent_images_cursor]

    risk_factors = 0
    # Simple risk calculation for demo
    for vital in recent_vitals:
        if await analyze_vitals_for_risk(vital):
            risk_factors += 1

    for symptom in recent_symptoms:
        if symptom.severity and symptom.severity > 5:
            risk_factors += 0.5 * (symptom.severity / 10)

    for image in recent_images:
        if image.ai_analysis_summary and "wound detected" in image.ai_analysis_summary.lower() and "severity" in image.ai_analysis_summary.lower():
            # Extract severity from summary (mock parsing)
            try:
                severity_str = image.ai_analysis_summary.split("severity ").split("/")
                severity = int(severity_str)
                risk_factors += 0.7 * (severity / 10)
            except (IndexError, ValueError):
                pass # Ignore if parsing fails

    # Normalize risk score to a 0-10 scale for simplicity
    # This is a very basic mock; real risk scoring would be more complex
    max_possible_risk_factors = 5 # Arbitrary max for normalization
    risk_score = min(10.0, (risk_factors / max_possible_risk_factors) * 10)
    return round(risk_score, 2)