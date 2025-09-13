import { Routes, Route, Link } from 'react-router-dom';
import './App.css';
import PatientChatbot from './components/PatientChatbot';
import DoctorDashboard from './components/DoctorDashboard';

const HomePage = () => (
  <div>
    <h1>Welcome to MedAlert AI</h1>
    <nav>
      <ul>
        <li>
          <Link to="/patient/dashboard">Patient Dashboard</Link>
        </li>
        <li>
          <Link to="/doctor/dashboard">Doctor Dashboard</Link>
        </li>
      </ul>
    </nav>
  </div>
);

const PatientDashboard = () => (
  <div>
    <PatientChatbot />
    <Link to="/">Back to Home</Link>
  </div>
);

const DoctorDashboardComponent = () => (
  <div>
    <DoctorDashboard />
    <Link to="/">Back to Home</Link>
  </div>
);

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/patient/dashboard" element={<PatientDashboard />} />
        <Route path="/doctor/dashboard" element={<DoctorDashboardComponent />} />
      </Routes>
    </div>
  );
}

export default App;
