import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import StrategyDetail from './pages/StrategyDetail';
import Backtests from './pages/Backtests';
import Validations from './pages/Validations';
import Gates from './pages/Gates';
import Reflexion from './pages/Reflexion';
import Orchestrator from './pages/Orchestrator';

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-900">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto bg-gray-900">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/strategies/:id" element={<StrategyDetail />} />
              <Route path="/backtests" element={<Backtests />} />
              <Route path="/validations" element={<Validations />} />
              <Route path="/gates" element={<Gates />} />
              <Route path="/reflexion" element={<Reflexion />} />
              <Route path="/orchestrator" element={<Orchestrator />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

const PlaceholderPage = ({ title }) => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center">
      <h1 className="text-3xl font-bold text-white mb-2">{title}</h1>
      <p className="text-gray-400">Coming soon</p>
    </div>
  </div>
);

export default App;
