import os
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai
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
    "Your primary goal is to gather detailed information about the patient's symptoms, well-being, and vitals. "
    "Always ask targeted, open-ended follow-up questions to elicit more specific and comprehensive information about their health. "
    "If the patient describes symptoms related to visible physical conditions such as 'wound', 'rash', 'burn', 'cut', 'bruise', 'swelling', 'skin discoloration', or 'lesion', "
    "politely and clearly ask the patient to upload a photo of the affected area for a more accurate assessment. "
    "Provide basic, reassuring, and general health advice if appropriate, but always prioritize gathering information and requesting images when relevant. "
    "Crucially, you must never provide medical diagnoses, prescribe treatments, or offer specific medical advice. "
    "Maintain a supportive, informative, and professional tone throughout the conversation. "
    "After each patient message, consider if any new symptoms are mentioned and if an image is necessary for clarification."
)

# Initialize Gemini models
gemini_model = genai.GenerativeModel('gemini-pro', system_instruction=SYSTEM_INSTRUCTION)
gemini_vision_model = genai.GenerativeModel('gemini-pro-vision')

async def get_chatbot_response(patient_message: str, patient_id: PyObjectId, db: AsyncIOMotorClient, image_path: Optional[str] = None) -> Tuple[str, bool, str]:
    """
    Generates an AI chatbot response using Google Gemini model, incorporating chat history and image analysis.
    Returns the AI response, whether an image is required, and an AI summary of the interaction.
    """
    requires_image = False
    ai_summary = ""
    image_analysis_description = None
    critical_alert_triggered = False

    try:
        # Fetch recent chat history for context
        recent_chat_cursor = db.chat_messages.find({"patient_id": patient_id}).sort("timestamp", 1).limit(10)
        recent_chat_history_raw = [msg async for msg in recent_chat_cursor]
        
        # Format chat history for Gemini's start_chat
        conversation_history = []
        for chat_entry in recent_chat_history_raw:
            # Ensure roles are correctly set for Gemini API
            role = "user" if chat_entry['sender'] == "patient" else "model"
            conversation_history.append({"role": role, "parts": [chat_entry['message']]})
        
        # Prepare content for Gemini
        content_parts = [patient_message]

        # If an image is provided, analyze it first and add to content parts
        if image_path:
            image_analysis_result = await analyze_image_with_gemini_vision(image_path)
            image_analysis_description = image_analysis_result['description']
            content_parts.insert(0, f"Patient uploaded an image. Image analysis: {image_analysis_description}. ")
            
            # Check if image analysis indicates critical condition
            if image_analysis_result.get('doctor_review_recommended', False) or image_analysis_result.get('severity_score', 0) > 7:
                critical_alert_triggered = True

        # Start a chat session with the history
        chat_session = gemini_model.start_chat(history=conversation_history)
        
        # Send the latest patient message (and image analysis if present)
        response = chat_session.send_message(content_parts)

        ai_response_text = response.text

        # Check if the AI's response or the patient's message indicates a need for an image
        patient_message_lower = patient_message.lower()
        ai_response_lower = ai_response_text.lower()
        
        keywords_for_image = ["wound", "rash", "burn", "cut", "bruise", "swelling", "skin discoloration", "lesion", "photo", "picture", "image"]
        if any(keyword in patient_message_lower for keyword in keywords_for_image) or \
           any(keyword in ai_response_lower for keyword in keywords_for_image):
            requires_image = True
            # Refine AI's request for image if it's a generic one
            if "upload a photo" in ai_response_lower and not any(kw in ai_response_lower for kw in ["wound", "rash", "burn", "cut", "bruise", "swelling"]):
                ai_response_text += " Please upload a photo of the affected area for a better assessment."

        # Check for critical symptoms in patient message
        critical_keywords = ["severe pain", "chest pain", "difficulty breathing", "high fever", "unconscious", "bleeding heavily", "severe headache", "stroke", "heart attack", "emergency"]
        if any(keyword in patient_message_lower for keyword in critical_keywords):
            critical_alert_triggered = True
            ai_response_text += " I'm concerned about your symptoms. Please contact your doctor immediately or go to the emergency room if symptoms worsen."

        # Generate a summary of the current interaction for the doctor
        full_interaction_text = f"Patient: {patient_message}\nAI: {ai_response_text}"
        if image_analysis_description:
            full_interaction_text += f"\nImage Analysis: {image_analysis_description}"
        ai_summary = await summarize_conversation_for_doctor(full_interaction_text)
        
        # If critical alert is triggered, create an alert in the database
        if critical_alert_triggered:
            alert = Alert(
                patient_id=patient_id,
                alert_type="critical_symptoms",
                message="Critical symptoms detected in patient communication. Immediate doctor review recommended.",
                severity="critical",
                resolved=False,
                timestamp=datetime.utcnow()
            )
            await db.alerts.insert_one(alert.model_dump(by_alias=True, exclude=["id"]))
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        ai_response_text = "I'm sorry, I'm having trouble connecting to the AI at the moment. Please try again later."
        requires_image = False
        ai_summary = f"AI summary unavailable due to error: {e}"

    # Log symptoms based on AI's understanding or keywords
    extracted_symptoms = await extract_symptoms_from_message(patient_message)
    if extracted_symptoms:
        for symptom_desc in extracted_symptoms:
            symptom_log = SymptomLog(
                patient_id=patient_id,
                symptom_description=symptom_desc,
                severity=random.randint(1, 10), # Mock severity, could be AI-determined or from a more advanced model
                timestamp=datetime.utcnow()
            )
            await db.symptom_logs.insert_one(symptom_log.model_dump(by_alias=True, exclude=["id"]))

    return ai_response_text, requires_image, ai_summary

async def summarize_conversation_for_doctor(conversation_text: str) -> str:
    """
    Summarizes a given conversation text concisely for a doctor using Google Gemini model.
    """
    try:
        response = gemini_model.generate_content(
            f"Summarize the following patient-AI interaction concisely for a doctor, highlighting key symptoms, concerns, and AI actions: {conversation_text}"
        )
        summary = response.text
    except Exception as e:
        print(f"Error summarizing with Gemini API: {e}")
        summary = f"AI summary unavailable for interaction: '{conversation_text}'"
    return summary.strip()

async def extract_symptoms_from_message(message: str) -> List[str]:
    """
    Uses Gemini to extract a list of symptoms from a patient's message.
    """
    try:
        response = gemini_model.generate_content(
            f"From the following patient message, extract a comma-separated list of distinct symptoms mentioned. "
            f"If no symptoms are clearly mentioned, respond with 'None'.\nMessage: \"{message}\""
        )
        symptoms_raw = response.text.strip()
        if symptoms_raw.lower() == 'none' or not symptoms_raw:
            return []
        return [s.strip() for s in symptoms_raw.split(',') if s.strip()]
    except Exception as e:
        print(f"Error extracting symptoms with Gemini API: {e}")
        return []

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

async def analyze_image_with_gemini_vision(image_path: str) -> Dict[str, Any]:
    """
    Analyzes an image for wound assessment using Google Gemini Vision model.
    """
    try:
        # Read the image file
        with open(image_path, "rb") as f:
            image_data = f.read()

        image_part = {
            "mime_type": "image/jpeg",  # Assuming JPEG, adjust if other formats are supported
            "data": image_data
        }

        prompt_parts = [
            image_part,
            "Analyze this image for any signs of wounds, rashes, burns, cuts, bruises, or swelling. "
            "Provide a concise description of your findings, including location, type, and estimated severity (on a scale of 1-10 if applicable). "
            "Also, suggest if a doctor's immediate review is recommended based on the visual evidence. "
            "Format the response as a JSON object with keys: 'wound_detected' (boolean), 'severity_score' (int, 1-10, or null), 'description' (string), 'doctor_review_recommended' (boolean)."
        ]

        response = gemini_vision_model.generate_content(prompt_parts)
        
        # Attempt to parse the response as JSON
        try:
            analysis_result = json.loads(response.text)
        except json.JSONDecodeError:
            print(f"Warning: Gemini Vision response was not valid JSON: {response.text}")
            analysis_result = {
                "wound_detected": False,
                "severity_score": None,
                "description": f"AI image analysis: Could not parse AI response. Raw response: {response.text}",
                "doctor_review_recommended": False
            }
        
        return analysis_result

    except Exception as e:
        print(f"Error analyzing image with Gemini Vision API: {e}")
        return {
            "wound_detected": False,
            "severity_score": None,
            "description": f"AI image analysis failed due to error: {e}",
            "doctor_review_recommended": False
        }