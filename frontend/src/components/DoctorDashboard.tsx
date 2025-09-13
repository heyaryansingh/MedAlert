import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

interface Patient {
  _id: string;
  name: string;
  email: string;
  risk_score?: number;
  date_of_birth?: string; // Added missing property
  contact_number?: string; // Added missing property
  address?: string; // Added missing property
}

interface Vital {
  timestamp: string;
  heart_rate?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  temperature?: number;
  oxygen_saturation?: number;
}

interface SymptomLog {
  timestamp: string;
  symptom_description: string;
  severity?: number;
}

interface ChatMessage {
  sender: 'patient' | 'ai';
  message: string;
  timestamp: string;
  image_url?: string;
}

interface Alert {
  alert_type: string;
  message: string;
  severity: string;
  timestamp: string;
}

interface DoctorNote {
  _id: string;
  patient_id: string;
  doctor_id: string;
  timestamp: string;
  note_content: string;
}

interface Prescription {
  _id: string;
  patient_id: string;
  doctor_id: string;
  timestamp: string;
  medication_name: string;
  dosage: string;
  instructions: string;
  start_date: string;
  end_date: string;
}

interface Appointment {
  _id: string;
  patient_id: string;
  doctor_id: string;
  timestamp: string;
  appointment_time: string;
  reason: string;
  status: string;
}

interface ImageUpload {
  _id: string;
  patient_id: string;
  timestamp: string;
  image_url: string;
  description?: string;
  ai_analysis_summary?: string;
}

interface PatientDetailData {
  patient_profile: Patient;
  vitals: Vital[];
  symptom_logs: SymptomLog[];
  chat_history: ChatMessage[];
  alerts: Alert[];
  doctor_notes: DoctorNote[];
  prescriptions: Prescription[];
  appointments: Appointment[];
  image_uploads: ImageUpload[];
  risk_score: number;
  ai_symptom_summary: string;
}

interface NewPrescriptionForm {
  medication_name: string;
  dosage: string;
  instructions: string;
  start_date: string;
  end_date: string;
}

interface NewAppointmentForm {
  appointment_time: string;
  reason: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const DoctorDashboard: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientData, setPatientData] = useState<PatientDetailData | null>(null);
  const [newNote, setNewNote] = useState<string>('');
  const [newPrescription, setNewPrescription] = useState<NewPrescriptionForm>({
    medication_name: '',
    dosage: '',
    instructions: '',
    start_date: new Date().toISOString().split('T'), // YYYY-MM-DD
    end_date: new Date().toISOString().split('T'),   // YYYY-MM-DD
  });
  const [newAppointment, setNewAppointment] = useState<NewAppointmentForm>({
    appointment_time: new Date().toISOString().slice(0, 16), // YYYY-MM-DDTHH:MM
    reason: '',
  });

  // Mock doctor ID for demo purposes
  // const doctorId = '650d7f3e7b1f8c9d0e1f2a3c'; // This variable is not used in the current implementation but kept for future use.

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/doctor/get_patients`);
        if (response.ok) {
          const fetchedPatients = await response.json();
          setPatients(fetchedPatients);
        }
      } catch (error) {
        console.error('Error fetching patients:', error);
      }
    };
    fetchPatients();
  }, []);

  const fetchPatientData = async (patientId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/doctor/get_patient_data/${patientId}`);
      if (response.ok) {
        const data = await response.json();
        setPatientData(data);
      }
    } catch (error) {
      console.error('Error fetching patient data:', error);
    }
  };

  const handlePatientSelect = (patient: Patient) => {
    setSelectedPatient(patient);
    fetchPatientData(patient._id);
  };

  const handleAddNote = async () => {
    if (!selectedPatient || newNote.trim() === '') return;
    try {
      const response = await fetch(`${API_BASE_URL}/doctor/add_notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: selectedPatient._id, note_content: newNote }),
      });
      if (response.ok) {
        setNewNote('');
        fetchPatientData(selectedPatient._id); // Refresh patient data
      } else {
        console.error('Failed to add note');
      }
    } catch (error) {
      console.error('Error adding note:', error);
    }
  };

  const handlePrescribe = async () => {
    if (!selectedPatient || !newPrescription.medication_name) return;
    try {
      const response = await fetch(`${API_BASE_URL}/doctor/prescribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: selectedPatient._id, ...newPrescription }),
      });
      if (response.ok) {
        setNewPrescription({
          medication_name: '',
          dosage: '',
          instructions: '',
          start_date: new Date().toISOString().split('T'),
          end_date: new Date().toISOString().split('T'),
        });
        fetchPatientData(selectedPatient._id); // Refresh patient data
      } else {
        console.error('Failed to add prescription');
      }
    } catch (error) {
      console.error('Error adding prescription:', error);
    }
  };

  const handleScheduleAppointment = async () => {
    if (!selectedPatient || !newAppointment.appointment_time) return;
    try {
      const response = await fetch(`${API_BASE_URL}/doctor/schedule_appointment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: selectedPatient._id, ...newAppointment }),
      });
      if (response.ok) {
        setNewAppointment({
          appointment_time: new Date().toISOString().slice(0, 16),
          reason: '',
        });
        fetchPatientData(selectedPatient._id); // Refresh patient data
      } else {
        console.error('Failed to schedule appointment');
      }
    } catch (error) {
      console.error('Error scheduling appointment:', error);
    }
  };

  const renderVitalsChart = (vitalsData: Vital[], vitalKey: keyof Vital, title: string, unit: string) => {
    const dates = vitalsData.map(v => new Date(v.timestamp));
    const values = vitalsData.map(v => v[vitalKey]).filter((v): v is number => v !== undefined && v !== null);

    if (values.length === 0) return null;

    return (
      <Plot
        data={[
          {
            x: dates,
            y: values as number[], // Cast to number[] after filtering
            type: 'scatter',
            mode: 'lines+markers',
            marker: { color: 'red' },
          },
        ]}
        layout={{
          title: title,
          xaxis: { title: 'Date' },
          yaxis: { title: unit },
          autosize: true,
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '300px' }}
      />
    );
  };

  return (
    <div className="doctor-dashboard">
      <h2>Doctor Dashboard</h2>

      <div className="patient-list-section">
        <h3>My Patients</h3>
        <ul>
          {patients.map((patient) => (
            <li key={patient._id} onClick={() => handlePatientSelect(patient)} className={selectedPatient?._id === patient._id ? 'selected' : ''}>
              {patient.name} ({patient.email}) - Risk Score: {patient.risk_score !== undefined ? patient.risk_score : 'N/A'}
            </li>
          ))}
        </ul>
      </div>

      {selectedPatient && patientData && (
        <div className="patient-details-section">
          <h3>Patient Details: {selectedPatient.name}</h3>
          <p><strong>Email:</strong> {selectedPatient.email}</p>
          <p><strong>Date of Birth:</strong> {patientData.patient_profile.date_of_birth || 'N/A'}</p>
          <p><strong>Contact:</strong> {patientData.patient_profile.contact_number || 'N/A'}</p>
          <p><strong>Address:</strong> {patientData.patient_profile.address || 'N/A'}</p>
          <p><strong>Current AI Risk Score:</strong> {patientData.risk_score !== undefined ? patientData.risk_score : 'N/A'}</p>
          <p><strong>AI Symptom Summary:</strong> {patientData.ai_symptom_summary}</p>

          <h4>Vitals Trends</h4>
          {renderVitalsChart(patientData.vitals, 'heart_rate', 'Heart Rate (bpm)', 'BPM')}
          {renderVitalsChart(patientData.vitals, 'blood_pressure_systolic', 'Systolic Blood Pressure (mmHg)', 'mmHg')}
          {renderVitalsChart(patientData.vitals, 'blood_pressure_diastolic', 'Diastolic Blood Pressure (mmHg)', 'mmHg')}
          {renderVitalsChart(patientData.vitals, 'temperature', 'Temperature (°C)', '°C')}
          {renderVitalsChart(patientData.vitals, 'oxygen_saturation', 'Oxygen Saturation (%)', '%')}

          <h4>Symptom Logs</h4>
          {patientData.symptom_logs.length === 0 ? (
            <p>No symptom logs.</p>
          ) : (
            <ul>
              {patientData.symptom_logs.map((symptom: SymptomLog, index: number) => (
                <li key={index}>
                  {new Date(symptom.timestamp).toLocaleString()}: {symptom.symptom_description} (Severity: {symptom.severity || 'N/A'})
                </li>
              ))}
            </ul>
          )}

          <h4>Chat History</h4>
          {patientData.chat_history.length === 0 ? (
            <p>No chat history.</p>
          ) : (
            <div className="chat-window">
              {patientData.chat_history.map((msg: ChatMessage, index: number) => (
                <div key={index} className={`chat-message ${msg.sender}`}>
                  <strong>{msg.sender === 'patient' ? 'Patient' : 'AI'}:</strong> {msg.message}
                  {msg.image_url && <img src={msg.image_url} alt="Uploaded" style={{ maxWidth: '100px', display: 'block' }} />}
                  <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          )}

          <h4>Image Uploads</h4>
          {patientData.image_uploads.length === 0 ? (
            <p>No image uploads.</p>
          ) : (
            <div className="image-gallery">
              {patientData.image_uploads.map((image: ImageUpload, index: number) => (
                <div key={index} className="image-item">
                  <img src={image.image_url} alt={image.description} style={{ maxWidth: '150px' }} />
                  <p>{image.description} ({new Date(image.timestamp).toLocaleDateString()})</p>
                  {image.ai_analysis_summary && <p><strong>AI Analysis:</strong> {image.ai_analysis_summary}</p>}
                </div>
              ))}
            </div>
          )}

          <h4>Doctor Notes</h4>
          <textarea
            placeholder="Add a new note..."
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
          />
          <button onClick={handleAddNote}>Add Note</button>
          {patientData.doctor_notes.length === 0 ? (
            <p>No doctor notes.</p>
          ) : (
            <ul>
              {patientData.doctor_notes.map((note: DoctorNote, index: number) => (
                <li key={index}>
                  {new Date(note.timestamp).toLocaleString()}: {note.note_content}
                </li>
              ))}
            </ul>
          )}

          <h4>Prescriptions</h4>
          <div>
            <input type="text" placeholder="Medication Name" value={newPrescription.medication_name} onChange={(e) => setNewPrescription({ ...newPrescription, medication_name: e.target.value })} />
            <input type="text" placeholder="Dosage" value={newPrescription.dosage} onChange={(e) => setNewPrescription({ ...newPrescription, dosage: e.target.value })} />
            <input type="text" placeholder="Instructions" value={newPrescription.instructions} onChange={(e) => setNewPrescription({ ...newPrescription, instructions: e.target.value })} />
            <label>Start Date:</label>
            <input type="date" value={newPrescription.start_date} onChange={(e) => setNewPrescription({ ...newPrescription, start_date: e.target.value })} />
            <label>End Date:</label>
            <input type="date" value={newPrescription.end_date} onChange={(e) => setNewPrescription({ ...newPrescription, end_date: e.target.value })} />
            <button onClick={handlePrescribe}>Prescribe</button>
          </div>
          {patientData.prescriptions.length === 0 ? (
            <p>No prescriptions.</p>
          ) : (
            <ul>
              {patientData.prescriptions.map((p: Prescription, index: number) => (
                <li key={index}>
                  <strong>{p.medication_name}</strong> - {p.dosage} ({new Date(p.start_date).toLocaleDateString()} to {new Date(p.end_date).toLocaleDateString()})
                  <p>Instructions: {p.instructions}</p>
                </li>
              ))}
            </ul>
          )}

          <h4>Appointments</h4>
          <div>
            <label>Appointment Time:</label>
            <input type="datetime-local" value={newAppointment.appointment_time} onChange={(e) => setNewAppointment({ ...newAppointment, appointment_time: e.target.value })} />
            <input type="text" placeholder="Reason" value={newAppointment.reason} onChange={(e) => setNewAppointment({ ...newAppointment, reason: e.target.value })} />
            <button onClick={handleScheduleAppointment}>Schedule Appointment</button>
          </div>
          {patientData.appointments.length === 0 ? (
            <p>No appointments.</p>
          ) : (
            <ul>
              {patientData.appointments.map((a: Appointment, index: number) => (
                <li key={index}>
                  {new Date(a.appointment_time).toLocaleString()}: {a.reason} (Status: {a.status})
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default DoctorDashboard;