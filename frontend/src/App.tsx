import './App.css';
import React, { useState } from 'react';
import PatientChatbot from './components/PatientChatbot';
import SimplifiedDoctorDashboard from './components/SimplifiedDoctorDashboard';

function App() {

  const [userType, setUserType] = useState<'doctor' | 'patient' | null>(null);
  const [loggedIn, setLoggedIn] = useState(false); // State to manage login status

  const handleLogin = (type: 'doctor' | 'patient') => {
    setUserType(type);
    setLoggedIn(true);
  };

  const handleLogout = () => {
    setUserType(null);
    setLoggedIn(false);
  };

  if (!loggedIn) {
    return (
      <div className="App">
        <h1>MedAlert Login</h1>
        <div className="login-container">
          <button onClick={() => handleLogin('doctor')}>Login as Doctor</button>
          <button onClick={() => handleLogin('patient')}>Login as Patient</button>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>MedAlert AI Dashboards</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <div className="dashboards-container">
        {userType === 'doctor' && <SimplifiedDoctorDashboard />}
        {userType === 'patient' && <PatientChatbot />}
      </div>
    </div>
  );
}

export default App;
