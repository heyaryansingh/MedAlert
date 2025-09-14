# Creator: Aryan Singh, JHU

# MedAlert AI

MedAlert AI is a patient monitoring and doctor support system designed for post operation or checkup monitoring. It leverages AI to provide an interactive patient chatbot, analyze symptoms and images, and offer doctors a comprehensive dashboard for patient management.

# Inspiration

In the past, one of my own family members was in a car crash and needed surgery on her femur. A month after the surgery due to repeated complaints, doctors discovered that the dull pain she felt at times was an allergic reaction to the tungsten implant she got. She has had 11 surgeries (each with their own mishaps) since then and two total hip replacements to go back to "normal". Now, my mom walks just fine, without a limp and without constant pain. But nobody else should have to suffer from post-operational neglect. I made MedAlert to help fight this glaring issue in modern healthcare.

# Features
- **Redesigned Patient Dashboard:** A clean, intuitive chat-based interface for patients to easily communicate symptoms, log well-being updates, and interact with the AI.
- **Enhanced Interactive AI Chatbot:** The AI chatbot is designed to be straightforward and focused on gathering precise patient details without obfuscation. It intelligently guides patients through symptom input, asks targeted follow-up questions, and explicitly requests image uploads when visible conditions (like wounds, rashes, burns, etc.) are mentioned for better assessment. The AI's responses are immediately displayed on the patient's screen.
- **Multiple Chat Sessions:** The system supports multiple chat sessions, allowing patients to initiate new conversations at different times of the day, providing a continuous log of their health journey.
- **Patient Image Uploads:** Patients can easily upload photos of affected areas (e.g., wounds, rashes) directly within the chat. These images are analyzed by the AI and made available for doctor review, enabling better monitoring of physical conditions.
- **Doctor Support System with Actionable Alerts:** Doctors have access to a comprehensive dashboard displaying real-time patient updates, AI-analyzed symptom summaries, uploaded images, and vitals. Crucially, doctor actions such as prescribing medication, scheduling appointments, or sending specific questions to the patient now appear as clear, easily viewable alerts directly on the patient's dashboard, ensuring timely communication and action.

## Repository Structure

- [`backend/`](backend/)
  - [`main.py`](backend/main.py) (FastAPI application entry point)
  - [`models.py`](backend/models.py) (MongoDB schema definitions)
  - [`routes/`](backend/routes/) (Patient, Doctor, and Authentication API endpoints)
  - [`ai/`](backend/ai/) (Chatbot logic, image analysis, risk scoring)
  - [`utils/`](backend/utils/) (Synthetic data generator, helper functions)
  - [`dependencies.py`](backend/dependencies.py) (Database dependency injection)
- [`frontend/`](frontend/)
  - React (Vite) application
  - Components for patient chatbot, dashboard, doctor interface
- [`simulated_data/`](simulated_data/)
  - JSON patient profiles, sample chat logs, example vitals, sample images of wounds/bandages
- [`README.md`](README.md) (This file)
- [`requirements.txt`](requirements.txt) (Python dependencies for backend)
- [`package.json`](package.json) (Node.js dependencies for frontend)
- ['medalert.html'] - main html file for webapp.
- ['chatbot_logic.py] - main chatbot logic system
- [`.\start_medalert.bat`] for Windows (Script to populate MongoDB and launch apps)

## Setup and Installation

### Prerequisites

- Python 3.12 (or compatible version for Pydantic v1.x)
- Node.js (LTS recommended)
- MongoDB Atlas account (or local MongoDB instance)
- all additional requirements can be found in requirements.txt

## Running the Demo

1.  **Load Simulated Data:** Requirements can be found in requirements.txt and downloaded with pip. Navigate to MedAlert copied repo folder and run .\start_medalert.bat to open the webapp.
2.  **Patient Interaction (via Redesigned Dashboard):**
    *   Access the patient UI in your browser.
    *   Interact with the AI chatbot to report symptoms, ask questions, and provide updates on your well-being.
    *   The AI will provide straightforward responses and may prompt for image uploads if you describe visible conditions like wounds or rashes.
    *   Upload images of affected areas directly through the chat interface.
    *   You can initiate multiple chat sessions throughout the day, and the history will be maintained.
3.  **Doctor Review (via Doctor Dashboard):**
    *   Access the doctor UI.
    *   Doctors can view AI-summarized patient information, uploaded images, risk scores, and vitals trends.
    *   The AI will provide notes (without rewording important specifics) of each opened chat as well as a cumulative notes page. It will categorize important information and give a possible follow up response from the doctor.
    *   Doctors can perform actions like adding notes, prescribing medication, scheduling appointments, or sending specific questions. These actions will appear as alerts on the patient's dashboard.

## Technologies Used

-   **Backend:** Python, FastAPI, MongoDB Atlas, Google Gemini API
-   **Frontend:** React (with Vite), NodeJS, Javascript
-   **AI:** Google Gemini (for conversational AI and image analysis). Trained specifically to act as a doctor assistant, with minimal obfuscation/explanation of details to not dilute patient inputs.

## Contributing

This project is designed for a hackathon. Contributions are welcome for further development!
