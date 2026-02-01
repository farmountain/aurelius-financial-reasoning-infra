import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import StrategyDetail from './pages/StrategyDetail';
import Backtests from './pages/Backtests';
import Validations from './pages/Validations';
import Gates from './pages/Gates';
import Reflexion from './pages/Reflexion';
import Orchestrator from './pages/Orchestrator';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Login />} />
        </Routes>
      </Router>
    );
  }

  return (
    <Router>
      <div className="flex h-screen bg-gray-900">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto bg-gray-900">
            <Routes>
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/strategies"
                element={
                  <ProtectedRoute>
                    <Strategies />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/strategies/:id"
                element={
                  <ProtectedRoute>
                    <StrategyDetail />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/backtests"
                element={
                  <ProtectedRoute>
                    <Backtests />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/validations"
                element={
                  <ProtectedRoute>
                    <Validations />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/gates"
                element={
                  <ProtectedRoute>
                    <Gates />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reflexion"
                element={
                  <ProtectedRoute>
                    <Reflexion />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/orchestrator"
                element={
                  <ProtectedRoute>
                    <Orchestrator />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
