import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Layers, 
  BarChart3, 
  CheckCircle2, 
  Shield,
  RefreshCw,
  Activity
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Strategies', href: '/strategies', icon: Layers },
    { name: 'Backtests', href: '/backtests', icon: BarChart3 },
    { name: 'Validations', href: '/validations', icon: CheckCircle2 },
    { name: 'Gates', href: '/gates', icon: Shield },
    { name: 'Reflexion', href: '/reflexion', icon: RefreshCw },
    { name: 'Orchestrator', href: '/orchestrator', icon: Activity },
  ];

  return (
    <div className="flex flex-col w-64 bg-gray-900 border-r border-gray-800">
      <div className="flex items-center h-16 px-6 border-b border-gray-800">
        <h1 className="text-xl font-bold text-white">AURELIUS</h1>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`
                flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                ${isActive 
                  ? 'bg-primary-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }
              `}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-800">
        <p className="text-xs text-gray-400">Version 0.1.0</p>
      </div>
    </div>
  );
};

export default Sidebar;
