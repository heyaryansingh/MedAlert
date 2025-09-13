# MedAlert AI

MedAlert AI is a patient monitoring and doctor support system designed for hackathon demonstration. It leverages AI to provide an interactive patient chatbot, analyze symptoms and images, and offer doctors a comprehensive dashboard for patient management.

## Project Overview

- **Patient Monitoring:** Patients can log daily vitals, symptoms, and upload images of wounds/bandages.
- **Interactive AI Chatbot:** An AI-powered chatbot guides patients through symptom input, requests images when necessary, and provides alerts for potential health risks based on vitals and symptoms.
- **Doctor Support System:** Doctors have access to a dashboard displaying real-time patient updates, AI-analyzed symptom summaries, uploaded images, notes, prescriptions, and appointment scheduling.

## Repository Structure

- [`backend/`](backend/)
  - [`main.py`](backend/main.py) (FastAPI application)
  - [`models.py`](backend/models.py) (MongoDB schema definitions)
  - [`routes/`](backend/routes/) (Patient and Doctor API endpoints)
  - [`ai/`](backend/ai/) (Chatbot logic, image analysis, risk scoring)
  - [`utils/`](backend/utils/) (Synthetic data generator, helper functions)
- [`frontend/`](frontend/)
  - React (Vite) or Streamlit application
  - Components for patient chatbot, vitals logging, dashboard, doctor interface
- [`simulated_data/`](simulated_data/)
  - JSON patient profiles, sample chat logs, example vitals, sample images of wounds/bandages
- [`README.md`](README.md) (This file)
- [`requirements.txt`](requirements.txt) (Python dependencies for backend)
- [`package.json`](package.json) (Node.js dependencies for frontend)
- `startup.sh` (or `startup.bat` for Windows) (Script to populate MongoDB and launch apps)

## Setup and Installation

### Prerequisites

- Python 3.8+
- Node.js (LTS recommended)
- MongoDB Atlas account (or local MongoDB instance)

### Backend Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure MongoDB Atlas connection string in a `.env` file (e.g., `DATABASE_URL="mongodb+srv://user:pass@cluster.mongodb.net/MedAlertDB?retryWrites=true&w=majority"`).

### Frontend Setup

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Configure backend API endpoint in a `.env` file (e.g., `VITE_API_URL="http://localhost:8000"`).

### Running the Demo

A `startup.sh` (or `startup.bat`) script will be provided to:
1. Populate MongoDB with simulated data.
2. Start the FastAPI backend.
3. Start the React/Streamlit frontend.

More detailed instructions will be added here once the components are implemented.

## Demo Workflow

1. **Load Simulated Data:** The startup script will automatically populate the database.
2. **Patient Interaction:**
   - Access the patient UI.
   - Interact with the AI chatbot to report vitals and symptoms.
   - The AI will prompt for image uploads if necessary.
3. **Doctor Review:**
   - Access the doctor UI.
   - View AI-summarized patient information, uploaded images, risk scores, and trends.
   - Add notes, prescribe medication, and schedule appointments.
4. **Visualizations:** Dashboards will display vitals trends, risk scores, and patient chat summaries.

## Technologies Used

- **Backend:** Python, FastAPI, MongoDB Atlas
- **Frontend:** React (with Vite) or Streamlit, Plotly/D3.js
- **AI:** GPT/OpenAI API, Pretrained CNN (PyTorch/TensorFlow)

## Contributing

This project is designed for a hackathon. Contributions are welcome for further development!