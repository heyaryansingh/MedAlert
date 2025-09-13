import random
from datetime import datetime, timedelta
from typing import List, Dict
from faker import Faker
from bson import ObjectId

from backend.models import (
    Patient, Doctor, Vital, SymptomLog, ChatMessage, Alert,
    DoctorNote, Prescription, Appointment, ImageUpload, PyObjectId
)

fake = Faker()

def generate_fake_patient(doctor_id: Optional[PyObjectId] = None) -> Patient:
    """Generates a single fake patient profile."""
    return Patient(
        id=PyObjectId(),
        email=fake.email(),
        password="password123", # Mock password
        role="patient",
        name=fake.name(),
        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
        contact_number=fake.phone_number(),
        address=fake.address(),
        doctor_id=doctor_id
    )

def generate_fake_doctor() -> Doctor:
    """Generates a single fake doctor profile."""
    return Doctor(
        id=PyObjectId(),
        email=fake.email(),
        password="password123", # Mock password
        role="doctor",
        name=fake.name(),
        specialization=random.choice(["Cardiology", "Dermatology", "General Practice", "Pediatrics", "Oncology"]),
        contact_number=fake.phone_number()
    )

def generate_fake_vitals(patient_id: PyObjectId, num_entries: int = 10) -> List[Vital]:
    """Generates fake vital logs for a patient."""
    vitals = []
    for i in range(num_entries):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 30), hours=random.randint(1, 23), minutes=random.randint(1, 59))
        vitals.append(Vital(
            id=PyObjectId(),
            patient_id=patient_id,
            timestamp=timestamp,
            heart_rate=random.randint(60, 100),
            blood_pressure_systolic=random.randint(110, 140),
            blood_pressure_diastolic=random.randint(70, 90),
            temperature=round(random.uniform(36.5, 37.5), 1),
            oxygen_saturation=round(random.uniform(95.0, 99.9), 1)
        ))
    return vitals

def generate_fake_symptom_logs(patient_id: PyObjectId, num_entries: int = 5) -> List[SymptomLog]:
    """Generates fake symptom logs for a patient."""
    symptoms = []
    common_symptoms = [
        "headache", "fever", "cough", "sore throat", "fatigue",
        "nausea", "dizziness", "chest pain", "rash", "wound discomfort"
    ]
    for i in range(num_entries):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 15), hours=random.randint(1, 23), minutes=random.randint(1, 59))
        symptoms.append(SymptomLog(
            id=PyObjectId(),
            patient_id=patient_id,
            timestamp=timestamp,
            symptom_description=random.choice(common_symptoms),
            severity=random.randint(1, 10)
        ))
    return symptoms

def generate_fake_chat_messages(patient_id: PyObjectId, num_entries: int = 10) -> List[ChatMessage]:
    """Generates fake chat messages between a patient and AI."""
    messages = []
    patient_prompts = [
        "I have a headache today.",
        "My temperature feels a bit high.",
        "There's a new wound on my arm.",
        "I'm feeling very tired.",
        "My blood pressure was 130/85.",
        "I have a persistent cough.",
        "Feeling dizzy when I stand up.",
        "My heart rate is a bit fast.",
        "I'm worried about this rash.",
        "Just wanted to check in."
    ]
    ai_responses = [
        "Thank you for letting me know. Can you describe the headache?",
        "Please log your temperature. How high is it?",
        "Could you upload a photo of the wound?",
        "How long have you been feeling tired?",
        "Thank you for logging your BP.",
        "Is your cough dry or productive?",
        "Are you experiencing dizziness often?",
        "Please log your heart rate in the vitals section.",
        "Can you describe the rash? Is it itchy?",
        "Thanks for the update. Anything else?"
    ]

    for i in range(num_entries // 2):
        timestamp_patient = datetime.utcnow() - timedelta(days=random.randint(1, 7), hours=random.randint(1, 23), minutes=random.randint(1, 59))
        messages.append(ChatMessage(
            id=PyObjectId(),
            patient_id=patient_id,
            timestamp=timestamp_patient,
            sender="patient",
            message=random.choice(patient_prompts)
        ))
        timestamp_ai = timestamp_patient + timedelta(minutes=random.randint(1, 5))
        messages.append(ChatMessage(
            id=PyObjectId(),
            patient_id=patient_id,
            timestamp=timestamp_ai,
            sender="ai",
            message=random.choice(ai_responses)
        ))
    return sorted(messages, key=lambda x: x.timestamp)

def generate_fake_image_uploads(patient_id: PyObjectId, num_entries: int = 2) -> List[ImageUpload]:
    """Generates fake image upload entries."""
    images = []
    for i in range(num_entries):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 10), hours=random.randint(1, 23), minutes=random.randint(1, 59))
        images.append(ImageUpload(
            id=PyObjectId(),
            patient_id=patient_id,
            timestamp=timestamp,
            image_url=f"simulated_data/patient_images/{str(patient_id)}/wound_sample_{i+1}.jpg",
            description=f"Sample wound image {i+1}",
            ai_analysis_summary=f"Simulated AI analysis: Wound detected with severity {random.randint(3, 9)}/10."
        ))
    return images

def generate_fake_doctor_notes(patient_id: PyObjectId, doctor_id: PyObjectId, num_entries: int = 3) -> List[DoctorNote]:
    """Generates fake doctor notes for a patient."""
    notes = []
    for i in range(num_entries):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 20), hours=random.randint(1, 23), minutes=random.randint(1, 59))
        notes.append(DoctorNote(
            id=PyObjectId(),
            patient_id=patient_id,
            doctor_id=doctor_id,
            timestamp=timestamp,
            note_content=f"Patient presented with {fake.word()} symptoms. Advised rest and hydration. Follow-up in a week. (Note {i+1})"
        ))
    return notes

def generate_fake_prescriptions(patient_id: PyObjectId, doctor_id: PyObjectId, num_entries: int = 2) -> List[Prescription]:
    """Generates fake prescriptions for a patient."""
    prescriptions = []
    for i in range(num_entries):
        start_date = datetime.utcnow() - timedelta(days=random.randint(0, 10))
        end_date = start_date + timedelta(days=random.randint(7, 30))
        prescriptions.append(Prescription(
            id=PyObjectId(),
            patient_id=patient_id,
            doctor_id=doctor_id,
            timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
            medication_name=fake.word().capitalize() + "ol",
            dosage=f"{random.randint(100, 500)}mg {random.choice(['once', 'twice'])} daily",
            instructions="Take with food.",
            start_date=start_date,
            end_date=end_date
        ))
    return prescriptions

def generate_fake_appointments(patient_id: PyObjectId, doctor_id: PyObjectId, num_entries: int = 2) -> List[Appointment]:
    """Generates fake appointments for a patient."""
    appointments = []
    for i in range(num_entries):
        appointment_time = datetime.utcnow() + timedelta(days=random.randint(-5, 10), hours=random.randint(9, 17), minutes=random.choice([0, 15, 30, 45]))
        appointments.append(Appointment(
            id=PyObjectId(),
            patient_id=patient_id,
            doctor_id=doctor_id,
            timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 5)),
            appointment_time=appointment_time,
            reason=f"Follow-up for {fake.word()} condition.",
            status=random.choice(["scheduled", "completed", "cancelled"])
        ))
    return appointments

def generate_all_simulated_data(num_patients: int = 3, num_doctors: int = 1) -> Dict:
    """Generates a complete set of simulated data for the demo."""
    doctors = [generate_fake_doctor() for _ in range(num_doctors)]
    patients = [generate_fake_patient(doctor_id=doctors[0].id) for _ in range(num_patients)] # Assign all patients to the first doctor for simplicity

    all_data = {
        "doctors": [d.model_dump(by_alias=True) for d in doctors],
        "patients": [p.model_dump(by_alias=True) for p in patients],
        "vitals": [],
        "symptom_logs": [],
        "chat_messages": [],
        "image_uploads": [],
        "doctor_notes": [],
        "prescriptions": [],
        "appointments": []
    }

    for patient in patients:
        all_data["vitals"].extend([v.model_dump(by_alias=True) for v in generate_fake_vitals(patient.id)])
        all_data["symptom_logs"].extend([s.model_dump(by_alias=True) for s in generate_fake_symptom_logs(patient.id)])
        all_data["chat_messages"].extend([m.model_dump(by_alias=True) for m in generate_fake_chat_messages(patient.id)])
        all_data["image_uploads"].extend([img.model_dump(by_alias=True) for img in generate_fake_image_uploads(patient.id)])
        
        # Assign notes, prescriptions, appointments to the first doctor for simplicity
        if doctors:
            all_data["doctor_notes"].extend([n.model_dump(by_alias=True) for n in generate_fake_doctor_notes(patient.id, doctors[0].id)])
            all_data["prescriptions"].extend([p.model_dump(by_alias=True) for p in generate_fake_prescriptions(patient.id, doctors[0].id)])
            all_data["appointments"].extend([a.model_dump(by_alias=True) for a in generate_fake_appointments(patient.id, doctors[0].id)])

    return all_data

if __name__ == "__main__":
    # Example usage:
    simulated_data = generate_all_simulated_data(num_patients=2, num_doctors=1)
    import json
    # Convert ObjectId to string for JSON serialization
    def convert_objectid_to_str(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    # Save to JSON files in simulated_data directory
    os.makedirs("../../simulated_data", exist_ok=True)
    with open("../../simulated_data/patients.json", "w") as f:
        json.dump(simulated_data["patients"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/doctors.json", "w") as f:
        json.dump(simulated_data["doctors"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/vitals.json", "w") as f:
        json.dump(simulated_data["vitals"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/symptom_logs.json", "w") as f:
        json.dump(simulated_data["symptom_logs"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/chat_messages.json", "w") as f:
        json.dump(simulated_data["chat_messages"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/image_uploads.json", "w") as f:
        json.dump(simulated_data["image_uploads"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/doctor_notes.json", "w") as f:
        json.dump(simulated_data["doctor_notes"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/prescriptions.json", "w") as f:
        json.dump(simulated_data["prescriptions"], f, indent=4, default=convert_objectid_to_str)
    with open("../../simulated_data/appointments.json", "w") as f:
        json.dump(simulated_data["appointments"], f, indent=4, default=convert_objectid_to_str)

    print("Simulated data generated and saved to simulated_data/ directory.")