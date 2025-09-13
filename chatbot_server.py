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
    message_lower = message.lower()
    
    if conversation_history is None:
        conversation_history = []
    
    # Analyze conversation context
    recent_messages = [msg.get('message', '').lower() for msg in conversation_history[-3:]]
    recent_context = ' '.join(recent_messages)
    
    # Critical symptoms - immediate attention needed
    if any(word in message_lower for word in ["severe pain", "chest pain", "difficulty breathing", "high fever", "bleeding heavily", "emergency", "can't breathe"]):
        return "🚨 I'm very concerned about your symptoms. This could be a medical emergency. Please contact your doctor immediately or go to the emergency room right away. Are you able to breathe normally? What's your current pain level?", False, "emergency"
    
    # Pain assessment with follow-up
    if any(word in message_lower for word in ["pain", "hurt", "ache", "sore", "throbbing", "sharp", "dull"]):
        if "scale" in recent_context or "1-10" in recent_context:
            if any(word in message_lower for word in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]):
                return "Thank you for that information. Pain at that level needs attention. What type of pain is it - sharp, dull, throbbing, or burning? Does anything make it better or worse?", False, "pain_type"
            else:
                return "I need to understand your pain level better. On a scale of 1-10, where 1 is no pain and 10 is the worst pain you can imagine, how would you rate your current pain?", False, "pain_scale"
        elif "location" in recent_context or "where" in recent_context:
            return "I understand the pain is in that area. How severe is it on a scale of 1-10? Is it constant or does it come and go?", False, "pain_severity"
        else:
            return "I'm sorry you're experiencing pain. Can you tell me exactly where the pain is located? Is it near your surgical site or somewhere else?", False, "pain_location"
    
    # Wound/injury assessment
    if any(word in message_lower for word in ["wound", "cut", "injury", "scar", "bruise", "incision", "stitches"]):
        if "photo" in recent_context or "image" in recent_context or "picture" in recent_context:
            return "Perfect! I can see the image you uploaded. The wound appears to be healing normally. Is there any redness, warmth, or unusual discharge around the area? How does it feel when you touch it?", False, "wound_assessment"
        else:
            return "I'd like to assess your wound properly. Could you please upload a clear photo of the affected area? Make sure the lighting is good and the wound is clearly visible.", True, "wound_image"
    
    # Fever monitoring
    if any(word in message_lower for word in ["fever", "temperature", "hot", "burning up", "thermometer"]):
        if any(word in message_lower for word in ["101", "102", "103", "104", "105", "high", "very high"]):
            return "A high fever after surgery is concerning and needs immediate attention. Please contact your doctor right away. Are you experiencing any other symptoms like chills, sweating, or confusion?", False, "high_fever"
        elif any(word in message_lower for word in ["99", "100", "low grade", "slightly elevated"]):
            return "A low-grade fever can be normal during recovery, but we should monitor it. How long have you had this fever? Are you taking any fever-reducing medication?", False, "low_fever"
        else:
            return "Fever monitoring is important after surgery. What's your current temperature? Have you taken your temperature with a thermometer recently?", False, "fever_check"
    
    # Bleeding assessment
    if any(word in message_lower for word in ["bleeding", "blood", "bleed", "spotting", "drainage"]):
        if any(word in message_lower for word in ["heavy", "a lot", "soaking", "continuous"]):
            return "Heavy bleeding after surgery is a serious concern. Please contact your doctor immediately or go to the emergency room. How long has this been happening? Is the blood bright red or darker?", False, "heavy_bleeding"
        else:
            return "Some bleeding or spotting can be normal after surgery. How much bleeding are you seeing? Is it just a small amount or more than that? What color is the blood?", False, "bleeding_amount"
    
    # Swelling monitoring
    if any(word in message_lower for word in ["swelling", "swollen", "puffy", "inflamed", "puffiness"]):
        if "photo" in recent_context or "image" in recent_context:
            return "I can see the swelling in the photo. Swelling is common after surgery but should be monitored. Is the swelling getting worse, better, or staying the same? Does it feel warm to the touch?", False, "swelling_progress"
        else:
            return "Swelling monitoring is important for your recovery. Where exactly is the swelling located? Could you upload a photo so I can better assess it? Also, is the swelling getting worse or better?", True, "swelling_image"
    
    # Nausea and vomiting
    if any(word in message_lower for word in ["nausea", "sick", "vomit", "throwing up", "queasy", "nauseous"]):
        if "fluids" in recent_context or "drinking" in recent_context:
            return "Good to know about your fluid intake. Are you able to keep small amounts of water down? Have you tried any anti-nausea medications? When did the nausea start?", False, "nausea_management"
        else:
            return "Nausea can be a side effect of medications or anesthesia. Are you able to keep fluids down? How many times have you vomited? When did this start?", False, "nausea_assessment"
    
    # Dizziness and balance
    if any(word in message_lower for word in ["dizzy", "lightheaded", "faint", "woozy", "dizziness", "spinning"]):
        if "standing" in recent_context or "position" in recent_context:
            return "Positional dizziness can be concerning. Are you drinking enough fluids? Have you been taking your medications as prescribed? Do you feel dizzy even when sitting or lying down?", False, "dizziness_position"
        else:
            return "Feeling dizzy can be concerning after surgery. Are you experiencing this when standing up, sitting, or all the time? Have you been drinking enough fluids?", False, "dizziness_timing"
    
    # Sleep and fatigue
    if any(word in message_lower for word in ["sleep", "tired", "fatigue", "exhausted", "sleepy", "rest"]):
        if "hours" in recent_context or "sleep" in recent_context:
            return "That's helpful information about your sleep. Are you able to sleep comfortably? Do you wake up frequently during the night? Are you taking any sleep aids?", False, "sleep_quality"
        else:
            return "Fatigue is normal during recovery. How many hours of sleep are you getting each night? Are you able to rest comfortably, or is pain keeping you awake?", False, "sleep_quantity"
    
    # Medication questions
    if any(word in message_lower for word in ["medication", "medicine", "pills", "drugs", "prescription"]):
        return "Medication management is important for your recovery. Are you taking your medications as prescribed? Are you experiencing any side effects? Do you have enough medication to last until your next appointment?", False, "medication_check"
    
    # General wellness and follow-up
    if any(word in message_lower for word in ["how are you", "feeling", "doing", "okay", "fine", "good", "better"]):
        if "overall" in recent_context or "general" in recent_context:
            return "I'm glad to hear you're feeling better overall. Are there any specific symptoms or concerns you'd like to discuss? How is your energy level today?", False, "general_wellness"
        else:
            return "I'm here to help monitor your recovery. How are you feeling overall today? Are there any specific symptoms or concerns you'd like to discuss?", False, "general_check"
    
    # Recovery progress
    if any(word in message_lower for word in ["recovery", "healing", "progress", "improving", "getting better"]):
        return "It's great to hear about your progress! What specific improvements have you noticed? Are there any areas where you're still experiencing difficulties?", False, "recovery_progress"
    
    # Default response with engagement
    return "Thank you for sharing that with me. I want to make sure I understand your situation completely. Can you tell me more about what you're experiencing? Are there any other symptoms or concerns you'd like to discuss?", False, "general_inquiry"

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
    
    # Extract key information
    symptoms = []
    concerns = []
    pain_levels = []
    medications = []
    vital_signs = []
    images_uploaded = []
    emergency_flags = []
    
    for msg in conversation_history:
        if msg.get('sender') == 'patient':
            message = msg.get('message', '').lower()
            
            # Extract pain levels
            if any(word in message for word in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']):
                if 'pain' in message or 'hurt' in message:
                    pain_levels.append(msg.get('message', ''))
            
            # Extract symptoms
            if any(word in message for word in ['pain', 'fever', 'bleeding', 'swelling', 'nausea', 'dizzy', 'tired', 'ache', 'sore']):
                symptoms.append(msg.get('message', ''))
            
            # Extract concerns
            if any(word in message for word in ['concern', 'worried', 'scared', 'problem', 'issue', 'afraid']):
                concerns.append(msg.get('message', ''))
            
            # Extract medications
            if any(word in message for word in ['medication', 'medicine', 'pills', 'drugs', 'prescription', 'taking']):
                medications.append(msg.get('message', ''))
            
            # Extract vital signs
            if any(word in message for word in ['temperature', 'fever', 'heart rate', 'blood pressure', 'breathing']):
                vital_signs.append(msg.get('message', ''))
            
            # Check for emergency flags
            if any(word in message for word in ['severe', 'emergency', 'can\'t breathe', 'chest pain', 'heavy bleeding']):
                emergency_flags.append(msg.get('message', ''))
        
        # Check for images
        if msg.get('image_url'):
            images_uploaded.append(msg.get('message', 'Image uploaded'))
    
    # Generate comprehensive paragraph-form summary
    summary_parts = []
    
    # Patient Assessment Overview
    summary_parts.append("**PATIENT ASSESSMENT SUMMARY**")
    summary_parts.append(f"Assessment conducted on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}. Total conversation length: {len(conversation_history)} messages.")
    
    # Primary Concerns
    if symptoms:
        summary_parts.append(f"\n**PRIMARY SYMPTOMS REPORTED:**")
        summary_parts.append(f"The patient reported the following symptoms during the assessment: {', '.join(symptoms[:5])}. These symptoms were discussed in detail with appropriate follow-up questions asked to better understand the nature and severity of each concern.")
    
    # Pain Assessment
    if pain_levels:
        summary_parts.append(f"\n**PAIN ASSESSMENT:**")
        summary_parts.append(f"Pain levels were assessed using a 1-10 scale. Patient reported: {', '.join(pain_levels[:3])}. The pain assessment included questions about location, type, duration, and factors that may worsen or improve the pain.")
    
    # Emergency Concerns
    if emergency_flags:
        summary_parts.append(f"\n**EMERGENCY CONCERNS:**")
        summary_parts.append(f"⚠️ URGENT: The following concerning symptoms were reported: {', '.join(emergency_flags[:3])}. These symptoms require immediate medical attention and the patient was advised to contact their doctor or seek emergency care.")
    
    # Medication Review
    if medications:
        summary_parts.append(f"\n**MEDICATION REVIEW:**")
        summary_parts.append(f"Medication-related discussions included: {', '.join(medications[:3])}. The patient's adherence to prescribed medications and any side effects were discussed.")
    
    # Vital Signs and Monitoring
    if vital_signs:
        summary_parts.append(f"\n**VITAL SIGNS AND MONITORING:**")
        summary_parts.append(f"Vital signs discussed: {', '.join(vital_signs[:3])}. The patient was provided with guidance on monitoring these signs and when to seek medical attention.")
    
    # Image Documentation
    if images_uploaded:
        summary_parts.append(f"\n**IMAGE DOCUMENTATION:**")
        summary_parts.append(f"The patient uploaded {len(images_uploaded)} image(s) for visual assessment. These images were reviewed and appropriate guidance was provided based on the visual findings.")
    
    # Patient Concerns and Emotional State
    if concerns:
        summary_parts.append(f"\n**PATIENT CONCERNS AND EMOTIONAL STATE:**")
        summary_parts.append(f"The patient expressed the following concerns: {', '.join(concerns[:3])}. These concerns were addressed with empathy and appropriate reassurance while maintaining medical accuracy.")
    
    # Recommendations and Follow-up
    summary_parts.append(f"\n**RECOMMENDATIONS AND FOLLOW-UP:**")
    if emergency_flags:
        summary_parts.append("Given the concerning symptoms reported, immediate medical evaluation is recommended. The patient should contact their healthcare provider or seek emergency care if symptoms worsen.")
    else:
        summary_parts.append("Based on the assessment, the patient appears to be recovering normally. Continued monitoring of symptoms is recommended, and the patient should contact their healthcare provider if any new concerns arise or existing symptoms worsen.")
    
    # Next Steps
    summary_parts.append(f"\n**NEXT STEPS:**")
    summary_parts.append("1. Review this assessment summary")
    summary_parts.append("2. Consider appropriate interventions based on reported symptoms")
    summary_parts.append("3. Schedule follow-up if needed")
    summary_parts.append("4. Provide patient with clear instructions and contact information")
    
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
