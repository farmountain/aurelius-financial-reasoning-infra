import { useState, useEffect } from 'react';
import { reflexionAPI, strategiesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { RefreshCw } from 'lucide-react';

const Reflexion = () => {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [reflexionHistory, setReflexionHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      loadReflexionHistory(selectedStrategy.id);
    }
  }, [selectedStrategy]);

  const loadStrategies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await strategiesAPI.list(100, 0);
      setStrategies(data);
      if (data.length > 0) {
        setSelectedStrategy(data[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load strategies');
    } finally {
      setLoading(false);
    }
  };

  const loadReflexionHistory = async (strategyId) => {
    try {
      const data = await reflexionAPI.getHistory(strategyId);
      setReflexionHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      setReflexionHistory([]);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadStrategies} />;
  }

  if (strategies.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="No Strategies Yet"
          description="Create strategies to track reflexion improvements"
          icon={RefreshCw}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Reflexion</h1>
        <p className="text-gray-400">Strategy improvement iterations and feedback loops</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Strategy List */}
        <div className="lg:col-span-1 bg-gray-800 rounded-lg border border-gray-700 p-4 max-h-[calc(100vh-200px)] overflow-y-auto">
          <h2 className="text-lg font-semibold text-white mb-4">Strategies</h2>
          <div className="space-y-2">
            {strategies.map((strategy) => (
              <button
                key={strategy.id}
                onClick={() => setSelectedStrategy(strategy)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedStrategy?.id === strategy.id
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-900/50 text-gray-300 hover:bg-gray-900'
                }`}
              >
                <p className="font-medium text-sm">{strategy.name}</p>
                <p className="text-xs opacity-75 mt-1">
                  Iterations: {reflexionHistory.length}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Reflexion Details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedStrategy && (
            <>
              <ReflexionSummary
                strategy={selectedStrategy}
                history={reflexionHistory}
              />
              {reflexionHistory.length > 0 && (
                <>
                  <ReflexionChart data={reflexionHistory} />
                  <ReflexionHistory history={reflexionHistory} />
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const ReflexionSummary = ({ strategy, history }) => {
  const improvements = history.length > 0
    ? history.reduce((acc, h) => acc + (h.improvement_score || 0), 0)
    : 0;

  const latestImprovement = history.length > 0 ? history[0] : null;

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Reflexion Summary</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <MetricCard
          label="Total Iterations"
          value={history.length}
        />
        <MetricCard
          label="Cumulative Improvement"
          value={improvements.toFixed(2)}
          positive={improvements > 0}
        />
        <MetricCard
          label="Latest Iteration"
          value={latestImprovement ? latestImprovement.iteration_num : 'N/A'}
        />
      </div>
      {latestImprovement && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="text-sm">
            <span className="text-gray-400">Latest Improvements:</span>
            <div className="mt-2 space-y-1">
              {latestImprovement.improvements && Array.isArray(latestImprovement.improvements) ? (
                latestImprovement.improvements.slice(0, 3).map((imp, idx) => (
                  <p key={idx} className="text-white text-xs">
                    • {imp}
                  </p>
                ))
              ) : (
                <p className="text-gray-400 text-xs">No improvements recorded</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ReflexionChart = ({ data }) => {
  const chartData = data.map((item, index) => ({
    iteration: item.iteration_num || index + 1,
    score: item.improvement_score || 0,
  })).reverse();

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Improvement Trend</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="iteration" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" />
          <Tooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
            labelStyle={{ color: '#9CA3AF' }}
          />
          <Legend />
          <Line type="monotone" dataKey="score" stroke="#F59E0B" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const ReflexionHistory = ({ history }) => {
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Iteration History</h2>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {history.map((item, index) => (
          <div
            key={index}
            className="p-4 bg-gray-900/50 rounded-lg border border-gray-700"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-medium text-white">
                  Iteration {item.iteration_num || index + 1}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown date'}
                </p>
              </div>
              <span className={`text-sm font-medium px-2 py-1 rounded ${
                item.improvement_score && item.improvement_score > 0
                  ? 'bg-green-900/30 text-green-400'
                  : 'bg-gray-700 text-gray-400'
              }`}>
                {item.improvement_score?.toFixed(2) || '0.00'}
              </span>
            </div>
            {item.feedback && (
              <p className="text-xs text-gray-300 mt-2">{item.feedback}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const MetricCard = ({ label, value, positive }) => (
  <div className="p-4 bg-gray-900/50 rounded-lg">
    <p className="text-xs text-gray-400 mb-1">{label}</p>
    <p className={`text-xl font-bold ${positive ? 'text-green-400' : positive === false ? 'text-red-400' : 'text-white'}`}>
      {value}
    </p>
  </div>
);

export default Reflexion;
