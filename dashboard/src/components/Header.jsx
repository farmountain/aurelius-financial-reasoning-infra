import { useState, useEffect } from 'react';
import { Activity, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { healthAPI } from '../services/api';

const Header = () => {
  const [health, setHealth] = useState(null);
  const { user, logout } = useAuth();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await healthAPI.check();
        setHealth(data);
      } catch (error) {
        console.error('Health check failed:', error);
        setHealth({ status: 'error' });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-gray-900 border-b border-gray-800">
      <h2 className="text-lg font-semibold text-white">Quant Reasoning Model</h2>
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <Activity className={`w-4 h-4 ${health?.status === 'healthy' ? 'text-green-500' : 'text-red-500'}`} />
          <span className="text-sm text-gray-300">
            {health?.status === 'healthy' ? 'API Connected' : 'API Disconnected'}
          </span>
        </div>
        <div className="flex items-center space-x-3 pl-6 border-l border-gray-700">
          <div className="text-right">
            <p className="text-sm font-medium text-white">{user?.name || user?.email}</p>
            <p className="text-xs text-gray-400">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
