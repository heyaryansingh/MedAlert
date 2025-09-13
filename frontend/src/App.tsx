import './App.css';
import SimplifiedPatientDashboard from './components/SimplifiedPatientDashboard';
import SimplifiedDoctorDashboard from './components/SimplifiedDoctorDashboard';

function App() {
  return (
    <div className="App">
      <h1>MedAlert AI Dashboards</h1>
      <div className="dashboards-container">
        <SimplifiedDoctorDashboard />
        <SimplifiedPatientDashboard />
      </div>
    </div>
  );
}

export default App;
