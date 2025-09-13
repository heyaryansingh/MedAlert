# MedAlert AI - Post-Surgery Helper

An AI-powered post-surgery monitoring system that helps patients communicate with healthcare providers through an intelligent chatbot.

## Features

- **AI Chatbot**: Patients can chat with an AI assistant that asks open-ended questions about their symptoms
- **Image Upload**: Patients can upload images of wounds, rashes, or other visible symptoms for AI analysis
- **Critical Symptom Detection**: AI automatically flags critical symptoms and creates alerts for doctors
- **Doctor Dashboard**: Doctors receive notifications and can review patient data, chat history, and AI-generated summaries
- **Checkup Completion**: When patients finish their checkup, all data is automatically sent to their assigned doctor

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB (local or cloud)
- Google Gemini API key

### Environment Setup

1. Create a `.env` file in the `backend` directory with:
```
DATABASE_URL=mongodb://localhost:27017/medalertdb
GEMINI_API_KEY=your_gemini_api_key_here
```

### Quick Start (Windows)

1. Run the startup script:
```bash
startup.bat
```

This will:
- Install Python dependencies
- Generate simulated data
- Start the FastAPI backend on port 8000
- Start the React frontend on port 5173

### Manual Setup

#### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Generate simulated data:
```bash
python -m backend.utils.data_generator
```

3. Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

#### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

## Usage

### For Patients

1. Open the patient dashboard
2. Chat with the AI about your symptoms
3. Upload images when requested by the AI
4. Click "Checkup Done" when finished - this sends all data to your doctor

### For Doctors

1. Open the doctor dashboard
2. View notifications for new patient checkups
3. Review patient data, chat history, and AI summaries
4. Add notes, prescriptions, and schedule appointments
5. Mark notifications as resolved

## API Endpoints

### Patient Endpoints
- `POST /api/patient/chatbot_message` - Send message to AI chatbot
- `POST /api/patient/upload_image` - Upload image for analysis
- `POST /api/patient/generate_notes` - Complete checkup and send data to doctor
- `GET /api/patient/chat_history` - Get chat history
- `GET /api/patient/get_alerts` - Get patient alerts

### Doctor Endpoints
- `GET /api/doctor/get_patients` - Get all patients
- `GET /api/doctor/get_patient_data/{patient_id}` - Get detailed patient data
- `GET /api/doctor/get_notifications` - Get doctor notifications
- `POST /api/doctor/mark_alert_resolved` - Mark alert as resolved
- `POST /api/doctor/add_notes` - Add doctor notes
- `POST /api/doctor/prescribe` - Prescribe medication
- `POST /api/doctor/schedule_appointment` - Schedule appointment

## Technology Stack

- **Backend**: FastAPI, MongoDB, Google Gemini AI
- **Frontend**: React, TypeScript, Vite
- **AI**: Google Gemini Pro for text, Gemini Pro Vision for images
- **Database**: MongoDB with Motor (async driver)

## Key Features Implemented

✅ AI chatbot responds to patient messages  
✅ Image upload and analysis  
✅ Critical symptom flagging  
✅ Doctor notification system  
✅ Checkup completion workflow  
✅ AI-generated conversation summaries  
✅ Doctor dashboard with patient management  

## Notes

- The system uses mock patient and doctor IDs for demo purposes
- Image analysis requires a valid Google Gemini API key
- MongoDB should be running locally or provide a cloud connection string
- The AI chatbot is configured to ask follow-up questions and request images when appropriate
