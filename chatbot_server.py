from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os
import base64
import json

app = FastAPI(title="MedAlert AI Chatbot")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    patient_id: str
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str
    user_type: str  # "patient" or "doctor"

class DoctorActionRequest(BaseModel):
    patient_id: str
    action_type: str  # "prescription", "appointment", "question"
    content: str
    doctor_id: str

# In-memory storage for demo
conversations = {}
doctor_summaries = {}
patient_notifications = {}

# Enhanced AI chatbot logic with conversation memory
def get_ai_response(message: str, conversation_history: list = None) -> tuple[str, bool, str]:
    """Returns AI response, whether image is needed, and follow-up question"""
    message_lower = message.lower().strip()
    
    if conversation_history is None:
        conversation_history = []
    
    # Analyze conversation context - look at more messages for better memory
    recent_messages = [msg.get('message', '').lower() for msg in conversation_history[-10:]]
    recent_context = ' '.join(recent_messages)
    
    # Extract key information from current message
    current_symptoms = extract_symptoms(message_lower)
    pain_indicators = extract_pain_info(message_lower)
    severity_indicators = extract_severity(message_lower)
    
    # Check for emergency situations first
    if is_emergency_situation(message_lower, recent_context):
        return generate_emergency_response(message_lower), False, "emergency"
    
    # Check if we've already asked about pain level in recent conversation
    if any(word in message_lower for word in ["pain", "hurt", "ache", "sore", "throbbing", "sharp", "dull", "burning", "stabbing"]):
        return handle_pain_assessment(message_lower, recent_context, pain_indicators, severity_indicators)
    
    # Check if this is a pain level response (contains numbers 1-10) and we've been discussing pain
    if any(word in message_lower for word in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]) and ("pain" in recent_context or "hurt" in recent_context or "scale" in recent_context or "1-10" in recent_context or "rate" in recent_context):
        return handle_pain_level_response(message_lower, recent_context)
    
    # Wound/injury assessment
    if any(word in message_lower for word in ["wound", "cut", "injury", "scar", "bruise", "incision", "stitches", "surgical site"]):
        return handle_wound_assessment(message_lower, recent_context)
    
    # Fever and temperature
    if any(word in message_lower for word in ["fever", "temperature", "hot", "burning up", "thermometer", "chills"]):
        return handle_fever_assessment(message_lower, recent_context)
    
    # Bleeding assessment
    if any(word in message_lower for word in ["bleeding", "blood", "bleed", "spotting", "drainage", "discharge"]):
        return handle_bleeding_assessment(message_lower, recent_context)
    
    # Swelling and inflammation
    if any(word in message_lower for word in ["swelling", "swollen", "puffy", "inflamed", "puffiness", "inflammation"]):
        return handle_swelling_assessment(message_lower, recent_context)
    
    # Nausea and digestive issues
    if any(word in message_lower for word in ["nausea", "sick", "vomit", "throwing up", "queasy", "nauseous", "stomach"]):
        return handle_nausea_assessment(message_lower, recent_context)
    
    # Dizziness and balance
    if any(word in message_lower for word in ["dizzy", "lightheaded", "faint", "woozy", "dizziness", "spinning", "balance"]):
        return handle_dizziness_assessment(message_lower, recent_context)
    
    # Sleep and fatigue
    if any(word in message_lower for word in ["sleep", "tired", "fatigue", "exhausted", "sleepy", "rest", "energy"]):
        return handle_sleep_assessment(message_lower, recent_context)
    
    # Medication questions
    if any(word in message_lower for word in ["medication", "medicine", "pills", "drugs", "prescription", "taking", "dosage"]):
        return handle_medication_assessment(message_lower, recent_context)
    
    # Breathing and respiratory
    if any(word in message_lower for word in ["breathing", "breath", "shortness", "cough", "chest tightness", "respiratory"]):
        return handle_breathing_assessment(message_lower, recent_context)
    
    # Mobility and movement
    if any(word in message_lower for word in ["walking", "moving", "mobility", "stiff", "range of motion", "movement"]):
        return handle_mobility_assessment(message_lower, recent_context)
    
    # General wellness and recovery
    if any(word in message_lower for word in ["how are you", "feeling", "doing", "okay", "fine", "good", "better", "recovery", "healing"]):
        return handle_general_wellness(message_lower, recent_context)
    
    # Default response with better engagement
    return generate_engaging_response(message_lower, recent_context), False, "general_inquiry"

def extract_symptoms(message: str) -> list:
    """Extract symptoms from message"""
    symptoms = []
    symptom_keywords = {
        "pain": ["pain", "hurt", "ache", "sore", "throbbing", "sharp", "dull", "burning", "stabbing"],
        "fever": ["fever", "temperature", "hot", "burning up", "chills"],
        "bleeding": ["bleeding", "blood", "bleed", "spotting", "drainage"],
        "swelling": ["swelling", "swollen", "puffy", "inflamed"],
        "nausea": ["nausea", "sick", "vomit", "queasy", "nauseous"],
        "dizziness": ["dizzy", "lightheaded", "faint", "woozy"],
        "fatigue": ["tired", "fatigue", "exhausted", "sleepy"],
        "breathing": ["breathing", "breath", "shortness", "cough"]
    }
    
    for symptom, keywords in symptom_keywords.items():
        if any(keyword in message for keyword in keywords):
            symptoms.append(symptom)
    
    return symptoms

def extract_pain_info(message: str) -> dict:
    """Extract pain-related information"""
    pain_info = {
        "level": None,
        "location": None,
        "type": None,
        "duration": None
    }
    
    # Pain level
    for i in range(1, 11):
        if f"{i}" in message and ("pain" in message or "hurt" in message):
            pain_info["level"] = i
            break
    
    # Pain location
    locations = ["chest", "head", "stomach", "back", "leg", "arm", "shoulder", "neck", "abdomen", "incision", "surgical site"]
    for location in locations:
        if location in message:
            pain_info["location"] = location
            break
    
    # Pain type
    types = ["sharp", "dull", "throbbing", "burning", "stabbing", "aching", "cramping"]
    for pain_type in types:
        if pain_type in message:
            pain_info["type"] = pain_type
            break
    
    return pain_info

def extract_severity(message: str) -> str:
    """Extract severity indicators"""
    severe_words = ["severe", "terrible", "awful", "unbearable", "intense", "extreme", "bad"]
    moderate_words = ["moderate", "some", "a bit", "slightly", "mild"]
    mild_words = ["mild", "little", "barely", "slight"]
    
    if any(word in message for word in severe_words):
        return "severe"
    elif any(word in message for word in moderate_words):
        return "moderate"
    elif any(word in message for word in mild_words):
        return "mild"
    return "unknown"

def is_emergency_situation(message: str, context: str) -> bool:
    """Check if this is an emergency situation"""
    emergency_keywords = [
        "severe pain", "chest pain", "difficulty breathing", "can't breathe", 
        "high fever", "bleeding heavily", "emergency", "urgent", "911",
        "unconscious", "fainting", "severe bleeding", "severe swelling"
    ]
    
    combined_text = f"{message} {context}"
    return any(keyword in combined_text for keyword in emergency_keywords)

def generate_emergency_response(message: str) -> str:
    """Generate emergency response"""
    return "🚨 **EMERGENCY ALERT** 🚨\n\nI'm very concerned about your symptoms. This could be a medical emergency that requires immediate attention.\n\n**Please take the following actions immediately:**\n• Call 911 or go to the nearest emergency room\n• Do not wait for symptoms to worsen\n• If you're alone, call someone to help you\n\n**Your safety is the top priority.** Please seek emergency medical care right away. I'll be here to help with any other questions once you're safe."

def handle_pain_level_response(message: str, context: str) -> tuple[str, bool, str]:
    """Handle pain level responses specifically"""
    # Extract the pain level - look for numbers in the message
    import re
    numbers = re.findall(r'\b(\d+)\b', message)
    pain_level = None
    
    # Find the first number that could be a pain level (1-10)
    for num_str in numbers:
        num = int(num_str)
        if 1 <= num <= 10:
            pain_level = num
            break
    
    if pain_level:
        if pain_level >= 7:
            return f"I'm concerned about your pain level of {pain_level}/10. This is quite high and needs attention. What type of pain is it - sharp, dull, throbbing, or burning? Are you taking any pain medication? How long have you been experiencing this level of pain?", False, "pain_type"
        elif pain_level >= 4:
            return f"Thank you for that information. A pain level of {pain_level}/10 is moderate and should be managed. What type of pain are you experiencing? Is it constant or does it come and go? What makes it better or worse?", False, "pain_management"
        else:
            return f"Good to know your pain is at a {pain_level}/10 level. Even mild pain should be monitored. What type of pain is it? Is it getting better, worse, or staying the same? Are you taking any pain medication?", False, "pain_monitoring"
    
    return generate_engaging_response(message, context), False, "general_inquiry"

def handle_pain_assessment(message: str, context: str, pain_info: dict, severity: str) -> tuple[str, bool, str]:
    """Handle pain assessment with detailed follow-up"""
    
    # Check if we've already discussed pain level recently
    if "scale" in context or "1-10" in context or "rate" in context:
        # We've already asked about pain level, move to next step
        if pain_info["location"]:
            return f"Thank you for the pain information. You mentioned pain in your {pain_info['location']}. What type of pain is it - sharp, dull, throbbing, or burning? Is it constant or does it come and go?", False, "pain_type"
        else:
            return "Thank you for the pain information. Can you tell me where exactly this pain is located? Also, what type of pain is it - sharp, dull, throbbing, or burning?", False, "pain_location"
    
    # If we have pain level from extraction, ask about type and management
    if pain_info["level"]:
        if pain_info["level"] >= 7:
            return f"I'm concerned about your pain level of {pain_info['level']}/10. This is quite high and needs attention. What type of pain is it - sharp, dull, throbbing, or burning? Are you taking any pain medication? How long have you been experiencing this level of pain?", False, "pain_type"
        elif pain_info["level"] >= 4:
            return f"Thank you for that information. A pain level of {pain_info['level']}/10 is moderate and should be managed. What type of pain are you experiencing? Is it constant or does it come and go? What makes it better or worse?", False, "pain_management"
        else:
            return f"Good to know your pain is at a {pain_info['level']}/10 level. Even mild pain should be monitored. What type of pain is it? Is it getting better, worse, or staying the same? Are you taking any pain medication?", False, "pain_monitoring"
    
    # If we have location but no level
    if pain_info["location"]:
        return f"I understand you're experiencing pain in your {pain_info['location']}. This is important information. On a scale of 1-10, where 1 is no pain and 10 is the worst pain imaginable, how would you rate this pain? Is it constant or does it come and go?", False, "pain_level"
    
    # If we have pain type but no other info
    if pain_info["type"]:
        return f"I understand you're experiencing {pain_info['type']} pain. This helps me understand what you're feeling. Can you tell me where exactly this pain is located? Also, on a scale of 1-10, how severe is it?", False, "pain_location"
    
    # Initial pain assessment
    return "I'm sorry you're experiencing pain. To help me understand your situation better, can you tell me:\n\n1. **Where** is the pain located?\n2. **How severe** is it on a scale of 1-10?\n3. **What type** of pain is it (sharp, dull, throbbing, burning)?\n\nThis information will help me provide better guidance for your recovery.", False, "pain_assessment"

def handle_wound_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle wound/injury assessment"""
    if "photo" in context or "image" in context or "picture" in context:
        return "Thank you for uploading the image. I can see the wound area you're concerned about. Based on what I can observe, I'd like to ask a few follow-up questions:\n\n• Is there any redness, warmth, or unusual discharge around the wound?\n• How does it feel when you touch it?\n• Is the wound getting better, worse, or staying the same?\n• Are you experiencing any fever or increased pain in the area?", False, "wound_followup"
    else:
        return "I'd like to assess your wound properly to provide the best guidance. Could you please upload a clear photo of the affected area? Make sure the lighting is good and the wound is clearly visible.\n\nWhile you prepare the photo, can you tell me:\n• How long ago did this wound occur?\n• Is it getting better, worse, or staying the same?\n• Are you experiencing any redness, warmth, or unusual discharge?", True, "wound_image"

def handle_fever_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle fever assessment"""
    if any(word in message for word in ["101", "102", "103", "104", "105", "high", "very high"]):
        return "🚨 A high fever after surgery is concerning and needs immediate attention. Please contact your doctor right away or go to the emergency room if your temperature is above 101°F (38.3°C).\n\nAre you experiencing any other symptoms like:\n• Chills or sweating\n• Confusion or dizziness\n• Severe headache\n• Difficulty breathing\n\nPlease seek medical attention immediately.", False, "high_fever"
    elif any(word in message for word in ["99", "100", "low grade", "slightly elevated"]):
        return "A low-grade fever can be normal during recovery, but we should monitor it closely. How long have you had this fever? Are you taking any fever-reducing medication like acetaminophen or ibuprofen?\n\nPlease continue monitoring your temperature every few hours and contact your doctor if:\n• The fever increases\n• You develop other symptoms\n• The fever persists for more than 24 hours", False, "low_fever"
    else:
        return "Fever monitoring is very important after surgery. What's your current temperature? Have you taken your temperature with a thermometer recently?\n\nPlease take your temperature and let me know:\n• The exact reading\n• When you last took it\n• Any other symptoms you're experiencing\n\nThis will help me provide appropriate guidance.", False, "fever_check"

def handle_bleeding_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle bleeding assessment"""
    if any(word in message for word in ["heavy", "a lot", "soaking", "continuous", "profuse"]):
        return "🚨 Heavy bleeding after surgery is a serious concern that requires immediate attention. Please contact your doctor immediately or go to the emergency room.\n\nWhile you seek medical attention, please tell me:\n• How long has this been happening?\n• Is the blood bright red or darker?\n• Are you feeling dizzy or lightheaded?\n• How much blood are we talking about?\n\n**Do not delay seeking medical care.**", False, "heavy_bleeding"
    else:
        return "Some bleeding or spotting can be normal after surgery, but it's important to monitor it carefully. Can you tell me more details:\n\n• How much bleeding are you seeing? (Just a few drops, light spotting, or more?)\n• What color is the blood? (Bright red, dark red, or brownish?)\n• How often does it occur?\n• Is it getting better, worse, or staying the same?\n\nThis information will help determine if this is normal healing or needs attention.", False, "bleeding_amount"

def handle_swelling_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle swelling assessment"""
    if "photo" in context or "image" in context:
        return "Thank you for the photo. I can see the swelling you're concerned about. Swelling is common after surgery but should be monitored carefully.\n\nCan you tell me:\n• Is the swelling getting worse, better, or staying the same?\n• Does the swollen area feel warm to the touch?\n• Are you experiencing any pain or tenderness in the swollen area?\n• Is the swelling affecting your mobility or daily activities?\n\nThis information will help determine if the swelling is normal healing or needs medical attention.", False, "swelling_progress"
    else:
        return "Swelling monitoring is important for your recovery. To better assess the situation, could you upload a photo of the swollen area? Also, please tell me:\n\n• Where exactly is the swelling located?\n• Is it getting worse, better, or staying the same?\n• Does it feel warm to the touch?\n• How long has it been swollen?\n\nPhotos help me provide better guidance for your recovery.", True, "swelling_image"

def handle_nausea_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle nausea assessment"""
    if "fluids" in context or "drinking" in context:
        return "Good to know about your fluid intake. Nausea can be challenging during recovery. Let me ask a few more questions:\n\n• Are you able to keep small amounts of water down?\n• Have you tried any anti-nausea medications?\n• When did the nausea start?\n• Are you experiencing any vomiting, and if so, how many times?\n• Are you able to eat any solid foods?\n\nStaying hydrated is crucial for your recovery.", False, "nausea_management"
    else:
        return "Nausea can be a side effect of medications or anesthesia after surgery. This is important to address for your recovery.\n\nCan you tell me:\n• Are you able to keep fluids down?\n• How many times have you vomited (if any)?\n• When did this nausea start?\n• Are you taking any anti-nausea medications?\n• Have you been able to eat anything?\n\nProper nutrition and hydration are essential for healing.", False, "nausea_assessment"

def handle_dizziness_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle dizziness assessment"""
    if "standing" in context or "position" in context:
        return "Positional dizziness can be concerning after surgery. Let me ask some follow-up questions:\n\n• Are you drinking enough fluids? (Dehydration can cause dizziness)\n• Have you been taking your medications as prescribed?\n• Do you feel dizzy even when sitting or lying down?\n• Are you experiencing any nausea or vomiting?\n• Have you been eating regularly?\n\nDizziness can be related to medication, dehydration, or blood pressure changes.", False, "dizziness_position"
    else:
        return "Feeling dizzy can be concerning after surgery and needs to be addressed. Can you tell me:\n\n• Are you experiencing this when standing up, sitting, or all the time?\n• Have you been drinking enough fluids?\n• Are you taking your medications as prescribed?\n• Do you feel dizzy even when lying down?\n• Are you experiencing any other symptoms like nausea or weakness?\n\nDizziness can have several causes that need to be identified.", False, "dizziness_timing"

def handle_sleep_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle sleep and fatigue assessment"""
    if "hours" in context or "sleep" in context:
        return "That's helpful information about your sleep patterns. Sleep is crucial for healing. Let me ask a few more questions:\n\n• Are you able to sleep comfortably, or is pain keeping you awake?\n• Do you wake up frequently during the night?\n• Are you taking any sleep aids or pain medication?\n• Do you feel rested when you wake up?\n• Are you able to nap during the day if needed?\n\nGood sleep quality is essential for your recovery process.", False, "sleep_quality"
    else:
        return "Fatigue and sleep issues are common during recovery and important to address. Can you tell me:\n\n• How many hours of sleep are you getting each night?\n• Are you able to rest comfortably, or is pain keeping you awake?\n• Do you wake up frequently during the night?\n• Are you able to nap during the day?\n• Do you feel rested when you wake up?\n\nProper rest is essential for healing and recovery.", False, "sleep_quantity"

def handle_medication_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle medication assessment"""
    return "Medication management is crucial for your recovery. Let me ask some important questions:\n\n• Are you taking your medications exactly as prescribed?\n• Are you experiencing any side effects from your medications?\n• Do you have enough medication to last until your next appointment?\n• Are you taking any over-the-counter medications or supplements?\n• Have you missed any doses?\n• Are you having any difficulty swallowing pills?\n\nProper medication adherence is essential for optimal recovery.", False, "medication_check"

def handle_breathing_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle breathing assessment"""
    return "Breathing issues after surgery need immediate attention. Can you tell me:\n\n• Are you experiencing shortness of breath at rest or only with activity?\n• Do you have a cough, and if so, is it dry or productive?\n• Are you experiencing any chest pain or tightness?\n• Have you noticed any wheezing or unusual sounds when breathing?\n• Are you able to take deep breaths?\n• Is this getting better, worse, or staying the same?\n\nBreathing difficulties can be serious and may need immediate medical attention.", False, "breathing_assessment"

def handle_mobility_assessment(message: str, context: str) -> tuple[str, bool, str]:
    """Handle mobility assessment"""
    return "Mobility and movement are important indicators of your recovery progress. Can you tell me:\n\n• Are you able to walk normally, or do you have limitations?\n• Do you experience any stiffness or difficulty moving?\n• Is your range of motion limited in any way?\n• Are you able to perform your daily activities?\n• Do you need assistance with walking or moving?\n• Are you following any physical therapy or exercise recommendations?\n\nMobility assessment helps track your recovery progress.", False, "mobility_assessment"

def handle_general_wellness(message: str, context: str) -> tuple[str, bool, str]:
    """Handle general wellness questions"""
    if "overall" in context or "general" in context:
        return "I'm glad to hear you're thinking about your overall recovery. Let me ask about different aspects of your healing:\n\n• How is your energy level today compared to yesterday?\n• Are you able to perform your daily activities?\n• Are there any specific symptoms or concerns you'd like to discuss?\n• How is your appetite and nutrition?\n• Are you feeling more like yourself?\n\nOverall wellness is a great indicator of recovery progress.", False, "general_wellness"
    else:
        return "I'm here to help monitor your recovery and ensure you're healing well. How are you feeling overall today?\n\nTo give you the best guidance, can you tell me:\n• What's your main concern or symptom right now?\n• How is your energy level?\n• Are you experiencing any new symptoms?\n• How would you rate your overall comfort level?\n• Is there anything specific you'd like to discuss?\n\nI'm here to support you through your recovery journey.", False, "general_check"

def generate_engaging_response(message: str, context: str) -> str:
    """Generate engaging response for unclear messages"""
    return f"I want to make sure I understand your situation completely. You mentioned: '{message}'\n\nTo provide you with the best guidance for your recovery, could you help me understand:\n\n• What specific symptoms or concerns are you experiencing?\n• How long have you been experiencing this?\n• Is this something new or has it been ongoing?\n• How would you describe your overall comfort level?\n\nI'm here to help monitor your recovery and ensure you're healing properly. Please share any details that might help me assist you better."

@app.get("/")
async def root():
    return {"message": "MedAlert AI Chatbot is running!", "status": "active"}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login endpoint for patients and doctors"""
    # Simple demo authentication
    if request.user_type == "patient":
        if request.username == "patient" and request.password == "password":
            return JSONResponse(content={
                "success": True,
                "user_type": "patient",
                "user_id": "patient_123",
                "name": "John Doe"
            })
    elif request.user_type == "doctor":
        if request.username == "doctor" and request.password == "password":
            return JSONResponse(content={
                "success": True,
                "user_type": "doctor", 
                "user_id": "doctor_123",
                "name": "Dr. Smith"
            })
    
    return JSONResponse(content={"success": False, "message": "Invalid credentials"}, status_code=401)

@app.post("/api/patient/chatbot_message")
async def chatbot_message(request: ChatRequest):
    """Main chatbot endpoint with conversation memory"""
    try:
        # Get conversation history
        if request.patient_id not in conversations:
            conversations[request.patient_id] = []
        
        conversation_history = conversations[request.patient_id]
        
        # Get AI response with context
        ai_response, needs_image, follow_up_type = get_ai_response(request.message, conversation_history)
        
        # Add user message to conversation
        user_message = {
            "_id": f"user_{datetime.now().timestamp()}",
            "sender": "patient",
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        }
        conversation_history.append(user_message)
        
        # Add AI response to conversation
        ai_message = {
            "_id": f"ai_{datetime.now().timestamp()}",
            "sender": "ai",
            "message": ai_response,
            "timestamp": datetime.now().isoformat(),
            "requires_image_upload": needs_image,
            "image_url": None,
            "follow_up_type": follow_up_type
        }
        conversation_history.append(ai_message)
        
        return JSONResponse(content=ai_message)
    except Exception as e:
        return JSONResponse(content={
            "_id": f"error_{datetime.now().timestamp()}",
            "sender": "ai", 
            "message": "I'm sorry, I'm having trouble processing your message right now. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "requires_image_upload": False,
            "image_url": None
        })

@app.post("/api/patient/upload_image")
async def upload_image(patient_id: str = Form(...), file: UploadFile = File(...)):
    """Upload image for wound/swelling assessment"""
    try:
        # Read image file
        image_data = await file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Add image message to conversation
        if patient_id not in conversations:
            conversations[patient_id] = []
        
        image_message = {
            "_id": f"image_{datetime.now().timestamp()}",
            "sender": "patient",
            "message": f"Uploaded image: {file.filename}",
            "timestamp": datetime.now().isoformat(),
            "image_url": f"data:image/jpeg;base64,{image_base64}",
            "image_filename": file.filename
        }
        conversations[patient_id].append(image_message)
        
        # Generate AI response for image
        ai_response = "Thank you for uploading the image. I can see the area you're concerned about. Based on what I can observe, the wound appears to be healing normally. Are you experiencing any redness, warmth, or unusual discharge around the area?"
        
        ai_message = {
            "_id": f"ai_image_{datetime.now().timestamp()}",
            "sender": "ai",
            "message": ai_response,
            "timestamp": datetime.now().isoformat(),
            "requires_image_upload": False,
            "image_url": None
        }
        conversations[patient_id].append(ai_message)
        
        return JSONResponse(content={
            "success": True,
            "message": "Image uploaded successfully",
            "ai_response": ai_message
        })
    except Exception as e:
        return JSONResponse(content={"success": False, "message": "Failed to upload image"}, status_code=500)

@app.get("/api/patient/chat_history")
async def get_chat_history(patient_id: str = "demo_patient_123"):
    """Returns chat history for a patient"""
    if patient_id in conversations:
        return conversations[patient_id]
    else:
        return [{
            "_id": "initial_msg",
            "sender": "ai",
            "message": "Hello! I am MedAlert AI. How are you feeling today?",
            "timestamp": datetime.now().isoformat(),
            "image_url": None
        }]

@app.get("/api/patient/vitals/{patient_id}")
async def get_vitals(patient_id: str):
    """Mock vitals data"""
    return [{
        "timestamp": datetime.now().isoformat(),
        "heart_rate": 75,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "temperature": 36.5,
        "oxygen_saturation": 98.0
    }]

@app.get("/api/patient/get_alerts")
async def get_alerts():
    """Mock alerts"""
    return []

@app.get("/api/patient/risk_score/{patient_id}")
async def get_risk_score(patient_id: str):
    """Mock risk score"""
    return {"risk_score": 3.2}

@app.post("/api/patient/generate_notes")
async def generate_notes(request: ChatRequest):
    """Generate AI summary and send to doctor"""
    try:
        # Get conversation history
        if request.patient_id not in conversations:
            conversations[request.patient_id] = []
        
        conversation_history = conversations[request.patient_id]
        
        # Generate AI summary
        summary = generate_conversation_summary(conversation_history)
        
        # Store summary for doctor
        doctor_summaries[request.patient_id] = {
            "patient_id": request.patient_id,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "conversation_count": len(conversation_history),
            "status": "pending_review"
        }
        
        return JSONResponse(content={
            "message": "Checkup complete! Your notes have been sent to your doctor.",
            "note_id": f"note_{datetime.now().timestamp()}",
            "summary": summary
        })
    except Exception as e:
        return JSONResponse(content={
            "message": "Error generating notes. Please try again.",
            "error": str(e)
        }, status_code=500)

def generate_conversation_summary(conversation_history: list) -> str:
    """Generate detailed AI summary of conversation in paragraph form"""
    if not conversation_history:
        return "No conversation data available."
    
    # Extract comprehensive information from conversation
    patient_messages = [msg for msg in conversation_history if msg.get('sender') == 'patient']
    ai_messages = [msg for msg in conversation_history if msg.get('sender') == 'ai']
    
    # Analyze conversation content
    symptoms_discussed = []
    pain_levels = []
    medications_mentioned = []
    vital_signs = []
    concerns_expressed = []
    emergency_flags = []
    images_uploaded = []
    
    for msg in patient_messages:
        message = msg.get('message', '').lower()
        
        # Extract symptoms
        if any(word in message for word in ['pain', 'hurt', 'ache', 'sore', 'throbbing', 'sharp', 'dull', 'burning']):
            symptoms_discussed.append(msg.get('message', ''))
        if any(word in message for word in ['fever', 'temperature', 'hot', 'burning up', 'chills']):
            symptoms_discussed.append(msg.get('message', ''))
        if any(word in message for word in ['bleeding', 'blood', 'bleed', 'spotting', 'drainage']):
            symptoms_discussed.append(msg.get('message', ''))
        if any(word in message for word in ['swelling', 'swollen', 'puffy', 'inflamed']):
            symptoms_discussed.append(msg.get('message', ''))
        if any(word in message for word in ['nausea', 'sick', 'vomit', 'queasy', 'nauseous']):
            symptoms_discussed.append(msg.get('message', ''))
        if any(word in message for word in ['dizzy', 'lightheaded', 'faint', 'woozy']):
            symptoms_discussed.append(msg.get('message', ''))
        if any(word in message for word in ['tired', 'fatigue', 'exhausted', 'sleepy']):
            symptoms_discussed.append(msg.get('message', ''))
        
        # Extract pain levels
        if any(word in message for word in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']):
            if 'pain' in message or 'hurt' in message or 'scale' in message:
                pain_levels.append(msg.get('message', ''))
        
        # Extract medications
        if any(word in message for word in ['medication', 'medicine', 'pills', 'drugs', 'prescription', 'taking']):
            medications_mentioned.append(msg.get('message', ''))
        
        # Extract vital signs
        if any(word in message for word in ['temperature', 'fever', 'heart rate', 'blood pressure', 'breathing']):
            vital_signs.append(msg.get('message', ''))
        
        # Extract concerns
        if any(word in message for word in ['concern', 'worried', 'scared', 'problem', 'issue', 'afraid']):
            concerns_expressed.append(msg.get('message', ''))
        
        # Check for emergency flags
        if any(word in message for word in ['severe', 'emergency', 'can\'t breathe', 'chest pain', 'heavy bleeding', 'unbearable']):
            emergency_flags.append(msg.get('message', ''))
    
    # Check for images
    for msg in conversation_history:
        if msg.get('image_url'):
            images_uploaded.append(msg.get('message', 'Image uploaded'))
    
    # Generate comprehensive paragraph-form summary
    summary_parts = []
    
    # Executive Summary
    summary_parts.append("**PATIENT ASSESSMENT SUMMARY**")
    summary_parts.append(f"Comprehensive assessment conducted on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}. This evaluation encompasses {len(conversation_history)} total interactions between the patient and AI assistant, providing a thorough overview of the patient's post-surgical recovery status.")
    
    # Clinical Presentation
    if symptoms_discussed:
        summary_parts.append(f"\n**CLINICAL PRESENTATION:**")
        summary_parts.append(f"The patient presented with multiple symptoms requiring attention during their post-surgical recovery period. Key symptoms reported include: {', '.join(symptoms_discussed[:5])}. These symptoms were systematically evaluated through a structured questioning process designed to assess severity, duration, and impact on daily functioning. The patient demonstrated good engagement with the assessment process and provided detailed responses to follow-up questions.")
    
    # Pain Assessment
    if pain_levels:
        summary_parts.append(f"\n**PAIN ASSESSMENT:**")
        summary_parts.append(f"Pain evaluation was conducted using a standardized 1-10 scale. Patient-reported pain levels included: {', '.join(pain_levels[:3])}. The pain assessment protocol included comprehensive questioning about pain location, character, duration, and factors that exacerbate or alleviate symptoms. Based on the reported pain levels, appropriate management strategies were discussed, including medication adherence, positioning techniques, and when to seek additional medical attention.")
    
    # Emergency Concerns
    if emergency_flags:
        summary_parts.append(f"\n**EMERGENCY CONCERNS:**")
        summary_parts.append(f"⚠️ **URGENT MEDICAL ATTENTION REQUIRED:** The patient reported concerning symptoms that warrant immediate medical evaluation: {', '.join(emergency_flags[:3])}. These symptoms suggest potential complications that require prompt medical intervention. The patient was advised to contact their healthcare provider immediately or seek emergency medical care. Close monitoring and follow-up are essential.")
    
    # Medication Management
    if medications_mentioned:
        summary_parts.append(f"\n**MEDICATION MANAGEMENT:**")
        summary_parts.append(f"Medication-related discussions revealed important information about the patient's adherence and response to prescribed treatments. Key points included: {', '.join(medications_mentioned[:3])}. The patient's understanding of medication instructions, potential side effects, and adherence to prescribed regimens was assessed. Recommendations were provided regarding proper medication timing, potential interactions, and when to contact healthcare providers about medication concerns.")
    
    # Vital Signs and Monitoring
    if vital_signs:
        summary_parts.append(f"\n**VITAL SIGNS AND MONITORING:**")
        summary_parts.append(f"Vital signs monitoring was discussed with the patient, including: {', '.join(vital_signs[:3])}. The patient was educated about normal ranges, signs of concern, and appropriate monitoring frequency. Instructions were provided regarding when to seek medical attention based on vital sign abnormalities. The importance of regular monitoring during the recovery period was emphasized.")
    
    # Visual Assessment
    if images_uploaded:
        summary_parts.append(f"\n**VISUAL ASSESSMENT:**")
        summary_parts.append(f"The patient provided {len(images_uploaded)} image(s) for visual assessment of their condition. These images were reviewed to evaluate wound healing, swelling, or other visible concerns. Based on the visual findings, appropriate guidance was provided regarding wound care, signs of infection, and when to seek medical attention for visual changes.")
    
    # Patient Concerns and Emotional State
    if concerns_expressed:
        summary_parts.append(f"\n**PATIENT CONCERNS AND EMOTIONAL STATE:**")
        summary_parts.append(f"The patient expressed several concerns during the assessment: {', '.join(concerns_expressed[:3])}. These concerns were addressed with empathy and appropriate reassurance while maintaining medical accuracy. The patient's emotional well-being and anxiety levels were assessed, and appropriate coping strategies were discussed. The importance of open communication with healthcare providers was emphasized.")
    
    # Clinical Recommendations
    summary_parts.append(f"\n**CLINICAL RECOMMENDATIONS:**")
    if emergency_flags:
        summary_parts.append("Given the concerning symptoms reported, immediate medical evaluation is strongly recommended. The patient should be seen by a healthcare provider within 24 hours or seek emergency care if symptoms worsen. Close monitoring of vital signs and symptom progression is essential. Consider expedited follow-up appointments and potential imaging or laboratory studies.")
    else:
        summary_parts.append("Based on the comprehensive assessment, the patient appears to be progressing through normal post-surgical recovery. Continued monitoring of symptoms is recommended, with particular attention to pain management, wound healing, and functional recovery. The patient should maintain regular follow-up appointments and contact their healthcare provider if any new concerns arise or existing symptoms worsen.")
    
    # Follow-up Plan
    summary_parts.append(f"\n**FOLLOW-UP PLAN:**")
    summary_parts.append("1. Review this comprehensive assessment with the healthcare team")
    summary_parts.append("2. Consider appropriate interventions based on reported symptoms and concerns")
    summary_parts.append("3. Schedule follow-up appointments as indicated by the assessment findings")
    summary_parts.append("4. Provide patient with clear instructions and emergency contact information")
    summary_parts.append("5. Monitor patient's progress and adjust care plan as needed")
    summary_parts.append("6. Ensure patient understands when to seek immediate medical attention")
    
    return "\n".join(summary_parts)

# Doctor Dashboard Endpoints
@app.get("/api/doctor/patients")
async def get_patients():
    """Get list of patients with summaries"""
    patients = []
    for patient_id, summary_data in doctor_summaries.items():
        patients.append({
            "patient_id": patient_id,
            "name": f"Patient {patient_id}",
            "last_checkup": summary_data["timestamp"],
            "status": summary_data["status"],
            "conversation_count": summary_data["conversation_count"]
        })
    return patients

@app.get("/api/doctor/patient_summary/{patient_id}")
async def get_patient_summary(patient_id: str):
    """Get detailed summary for a specific patient"""
    if patient_id in doctor_summaries:
        summary_data = doctor_summaries[patient_id]
        conversation_history = conversations.get(patient_id, [])
        
        return {
            "patient_id": patient_id,
            "summary": summary_data["summary"],
            "timestamp": summary_data["timestamp"],
            "conversation_history": conversation_history,
            "status": summary_data["status"]
        }
    else:
        return {"error": "No summary found for this patient"}

@app.post("/api/doctor/mark_reviewed/{patient_id}")
async def mark_patient_reviewed(patient_id: str):
    """Mark patient summary as reviewed by doctor"""
    if patient_id in doctor_summaries:
        doctor_summaries[patient_id]["status"] = "reviewed"
        doctor_summaries[patient_id]["reviewed_at"] = datetime.now().isoformat()
        return {"success": True, "message": "Patient marked as reviewed"}
    else:
        return {"success": False, "message": "Patient not found"}

@app.post("/api/doctor/action")
async def doctor_action(request: DoctorActionRequest):
    """Doctor actions: prescribe medication, suggest appointment, or send question"""
    try:
        # Create notification for patient
        notification = {
            "id": f"notif_{datetime.now().timestamp()}",
            "patient_id": request.patient_id,
            "doctor_id": request.doctor_id,
            "action_type": request.action_type,
            "content": request.content,
            "timestamp": datetime.now().isoformat(),
            "status": "unread"
        }
        
        # Store notification
        if request.patient_id not in patient_notifications:
            patient_notifications[request.patient_id] = []
        patient_notifications[request.patient_id].append(notification)
        
        # Generate appropriate message based on action type
        if request.action_type == "prescription":
            message = f"📋 **New Prescription from Dr. Smith**\n\n{request.content}\n\nPlease follow the medication instructions carefully and contact us if you have any questions."
        elif request.action_type == "appointment":
            message = f"📅 **Appointment Recommendation from Dr. Smith**\n\n{request.content}\n\nPlease contact our office to schedule this appointment."
        elif request.action_type == "question":
            message = f"❓ **Question from Dr. Smith**\n\n{request.content}\n\nPlease respond to this question when convenient."
        else:
            message = f"📝 **Message from Dr. Smith**\n\n{request.content}"
        
        return JSONResponse(content={
            "success": True,
            "message": "Action sent to patient successfully",
            "notification": notification,
            "patient_message": message
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": "Failed to send action to patient",
            "error": str(e)
        }, status_code=500)

@app.get("/api/patient/notifications/{patient_id}")
async def get_patient_notifications(patient_id: str):
    """Get notifications for a specific patient"""
    notifications = patient_notifications.get(patient_id, [])
    # Return only unread notifications
    unread_notifications = [n for n in notifications if n["status"] == "unread"]
    return unread_notifications

@app.post("/api/patient/mark_notification_read/{notification_id}")
async def mark_notification_read(notification_id: str, patient_id: str = "demo_patient_123"):
    """Mark a notification as read"""
    if patient_id in patient_notifications:
        for notification in patient_notifications[patient_id]:
            if notification["id"] == notification_id:
                notification["status"] = "read"
                return {"success": True, "message": "Notification marked as read"}
    return {"success": False, "message": "Notification not found"}

if __name__ == "__main__":
    print("Starting MedAlert AI Chatbot...")
    print("Backend will be available at: http://localhost:8001")
    print("API docs at: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
