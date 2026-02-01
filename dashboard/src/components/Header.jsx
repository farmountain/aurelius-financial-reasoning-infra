import { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { healthAPI } from '../services/api';

const Header = () => {
  const [health, setHealth] = useState(null);

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
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <Activity className={`w-4 h-4 ${health?.status === 'healthy' ? 'text-green-500' : 'text-red-500'}`} />
          <span className="text-sm text-gray-300">
            {health?.status === 'healthy' ? 'API Connected' : 'API Disconnected'}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Header;
