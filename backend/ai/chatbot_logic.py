from motor.motor_asyncio import AsyncIOMotorClient
from backend.models import PyObjectId, ChatMessage, SymptomLog, Vital
from datetime import datetime, timedelta
import random

async def get_chatbot_response(patient_message: str, patient_id: PyObjectId, db: AsyncIOMotorClient) -> (str, bool):
    """
    Mocks an AI chatbot response.
    In a real scenario, this would interact with GPT/OpenAI API.
    It also simulates prompting for an image based on keywords.
    """
    patient_message_lower = patient_message.lower()
    response_text = "Thank you for your update. Is there anything else you'd like to share?"
    requires_image = False

    if "wound" in patient_message_lower or "bandage" in patient_message_lower or "cut" in patient_message_lower:
        response_text = "I understand you're concerned about a wound. Could you please upload a photo of it so the doctor can assess it?"
        requires_image = True
    elif "fever" in patient_message_lower or "temperature" in patient_message_lower:
        response_text = "Please log your temperature in the vitals section. How high is your fever?"
    elif "pain" in patient_message_lower:
        response_text = "Where is the pain located and on a scale of 1 to 10, how severe is it?"
    elif "headache" in patient_message_lower:
        response_text = "How severe is your headache on a scale of 1 to 10? Have you taken any medication?"
    elif "nausea" in patient_message_lower or "vomiting" in patient_message_lower:
        response_text = "Are you experiencing any other symptoms with the nausea/vomiting?"
    elif "blood pressure" in patient_message_lower or "bp" in patient_message_lower:
        response_text = "Please log your blood pressure readings in the vitals section."
    elif "heart rate" in patient_message_lower or "hr" in patient_message_lower:
        response_text = "Please log your heart rate in the vitals section."
    elif "tired" in patient_message_lower or "fatigue" in patient_message_lower:
        response_text = "How long have you been feeling tired? Is it affecting your daily activities?"
    elif "dizzy" in patient_message_lower:
        response_text = "Are you experiencing dizziness when standing up or constantly? Have you had enough to drink today?"
    elif "shortness of breath" in patient_message_lower or "breathing" in patient_message_lower:
        response_text = "Are you experiencing shortness of breath at rest or only with exertion? Please log your oxygen saturation if you have a device."
    elif "chest pain" in patient_message_lower:
        response_text = "Please describe your chest pain. Is it sharp, dull, or crushing? Does it radiate anywhere?"
    elif "rash" in patient_message_lower:
        response_text = "Can you describe the rash? Is it itchy, red, or raised? Please upload an image if possible."
        requires_image = True
    elif "swelling" in patient_message_lower:
        response_text = "Where is the swelling located? Is it painful or red? Please upload an image if possible."
        requires_image = True
    elif "cough" in patient_message_lower:
        response_text = "Is your cough dry or productive? Are you experiencing any other cold or flu-like symptoms?"
    elif "sore throat" in patient_message_lower:
        response_text = "How severe is your sore throat? Is it difficult to swallow?"
    elif "diarrhea" in patient_message_lower:
        response_text = "How many times have you had diarrhea today? Are you experiencing any abdominal pain?"
    elif "constipation" in patient_message_lower:
        response_text = "How long have you been constipated? Have you tried any remedies?"
    elif "sleep" in patient_message_lower or "insomnia" in patient_message_lower:
        response_text = "How has your sleep been recently? Are you having trouble falling asleep or staying asleep?"
    elif "stress" in patient_message_lower or "anxiety" in patient_message_lower:
        response_text = "I understand you're feeling stressed or anxious. Would you like to talk more about what's on your mind?"
    elif "mood" in patient_message_lower or "depressed" in patient_message_lower:
        response_text = "How has your mood been lately? It's important to talk about these feelings."
    elif "medication" in patient_message_lower or "prescription" in patient_message_lower:
        response_text = "Are you having any issues with your medication or do you need a refill?"
    elif "appointment" in patient_message_lower:
        response_text = "Are you looking to schedule an appointment or do you have questions about an existing one?"
    elif "hello" in patient_message_lower or "hi" in patient_message_lower:
        response_text = "Hello! How are you feeling today? Please tell me about any symptoms or updates."
    elif "thank you" in patient_message_lower or "thanks" in patient_message_lower:
        response_text = "You're welcome! I'm here to help. Is there anything else I can assist you with?"
    elif "goodbye" in patient_message_lower or "bye" in patient_message_lower:
        response_text = "Goodbye! Take care and don't hesitate to reach out if you need anything."
    else:
        response_text = "I'm not sure I understand. Could you please rephrase or provide more details?"

    # Simulate logging symptom if a relevant keyword is found
    if any(keyword in patient_message_lower for keyword in ["fever", "pain", "headache", "nausea", "tired", "dizzy", "cough", "rash", "swelling", "sore throat", "diarrhea", "constipation", "stress", "anxiety", "mood", "depressed"]):
        symptom_log = SymptomLog(
            patient_id=patient_id,
            symptom_description=patient_message,
            severity=random.randint(1, 10), # Mock severity
            timestamp=datetime.utcnow()
        )
        await db.symptom_logs.insert_one(symptom_log.model_dump(by_alias=True, exclude=["id"]))

    return response_text, requires_image

async def analyze_patient_message(patient_message: str) -> dict:
    """
    Mocks AI analysis of a patient message for summarization.
    In a real scenario, this would use GPT/OpenAI API.
    """
    # Simple keyword-based summary for demo
    summary = f"Patient reported: '{patient_message}'. "
    if "pain" in patient_message.lower():
        summary += "Possible pain complaint. "
    if "fever" in patient_message.lower():
        summary += "Possible fever. "
    if "wound" in patient_message.lower() or "bandage" in patient_message.lower():
        summary += "Wound/bandage mentioned. "
    return {"summary": summary.strip()}

async def analyze_vitals_for_risk(vitals: Vital) -> Optional[str]:
    """
    Mocks AI analysis of vitals for risk assessment.
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

async def analyze_image_for_wound(image_path: str) -> dict:
    """
    Mocks AI analysis of an image for wound assessment.
    In a real scenario, this would use a pretrained CNN model.
    """
    # Simulate some analysis
    analysis_result = {
        "wound_detected": random.choice([True, False]),
        "severity_score": random.randint(1, 10),
        "description": "Simulated AI analysis: "
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
    Mocks calculation of a patient's overall risk score.
    This would combine vitals, symptoms, and image analysis.
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
                severity_str = image.ai_analysis_summary.split("severity ")[1].split("/")[0]
                severity = int(severity_str)
                risk_factors += 0.7 * (severity / 10)
            except (IndexError, ValueError):
                pass # Ignore if parsing fails

    # Normalize risk score to a 0-10 scale for simplicity
    # This is a very basic mock; real risk scoring would be more complex
    max_possible_risk_factors = 5 # Arbitrary max for normalization
    risk_score = min(10.0, (risk_factors / max_possible_risk_factors) * 10)
    return round(risk_score, 2)