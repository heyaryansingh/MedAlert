import React, { useState, useEffect } from 'react';

interface Patient {
  _id: string;
  name: string;
  email: string;
  risk_score?: number;
}

interface PatientDetailData {
  patient_profile: Patient;
  risk_score: number;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const SimplifiedDoctorDashboard: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientData, setPatientData] = useState<PatientDetailData | null>(null);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/get_patients`);
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
      const response = await fetch(`${API_BASE_URL}/get_patient_data/${patientId}`);
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

  return (
    <div className="doctor-dashboard">
      <h2>Simplified Doctor Dashboard</h2>

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
          <p><strong>Current AI Risk Score:</strong> {patientData.risk_score !== undefined ? patientData.risk_score : 'N/A'}</p>
        </div>
      )}
    </div>
  );
};

export default SimplifiedDoctorDashboard;