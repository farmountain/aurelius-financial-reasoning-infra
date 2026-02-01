import { useState, useEffect } from 'react';
import { backtestsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { BarChart3 } from 'lucide-react';

const Backtests = () => {
  const [backtests, setBacktests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBacktest, setSelectedBacktest] = useState(null);

  useEffect(() => {
    loadBacktests();
  }, []);

  const loadBacktests = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await backtestsAPI.list(null, 100, 0);
      setBacktests(data);
      if (data.length > 0 && !selectedBacktest) {
        setSelectedBacktest(data[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load backtests');
    } finally {
      setLoading(false);
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
    return <ErrorMessage message={error} onRetry={loadBacktests} />;
  }

  if (backtests.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="No Backtests Yet"
          description="Run your first backtest to analyze strategy performance"
          icon={BarChart3}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Backtests</h1>
        <p className="text-gray-400">Analyze historical performance of your strategies</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Backtest List */}
        <div className="lg:col-span-1 bg-gray-800 rounded-lg border border-gray-700 p-4 max-h-[calc(100vh-200px)] overflow-y-auto">
          <h2 className="text-lg font-semibold text-white mb-4">All Backtests</h2>
          <div className="space-y-2">
            {backtests.map((backtest) => (
              <button
                key={backtest.id}
                onClick={() => setSelectedBacktest(backtest)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedBacktest?.id === backtest.id
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-900/50 text-gray-300 hover:bg-gray-900'
                }`}
              >
                <p className="font-medium text-sm">Strategy {backtest.strategy_id}</p>
                <p className="text-xs opacity-75 mt-1">
                  {backtest.start_date} - {backtest.end_date}
                </p>
                <div className="flex items-center justify-between mt-2">
                  <span className={`text-xs px-2 py-1 rounded ${
                    backtest.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                    backtest.status === 'running' ? 'bg-yellow-900/30 text-yellow-400' :
                    backtest.status === 'failed' ? 'bg-red-900/30 text-red-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>
                    {backtest.status}
                  </span>
                  {backtest.results?.sharpe_ratio && (
                    <span className="text-xs">SR: {backtest.results.sharpe_ratio.toFixed(2)}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Backtest Details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedBacktest && (
            <>
              <BacktestMetrics backtest={selectedBacktest} />
              {selectedBacktest.results && selectedBacktest.results.equity_curve && (
                <BacktestChart data={selectedBacktest.results.equity_curve} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const BacktestMetrics = ({ backtest }) => {
  const metrics = backtest.results || {};

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Performance Metrics</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Return"
          value={metrics.total_return ? `${(metrics.total_return * 100).toFixed(2)}%` : 'N/A'}
          positive={metrics.total_return > 0}
        />
        <MetricCard
          label="Sharpe Ratio"
          value={metrics.sharpe_ratio?.toFixed(2) || 'N/A'}
          positive={metrics.sharpe_ratio > 1}
        />
        <MetricCard
          label="Max Drawdown"
          value={metrics.max_drawdown ? `${(metrics.max_drawdown * 100).toFixed(2)}%` : 'N/A'}
          positive={false}
        />
        <MetricCard
          label="Win Rate"
          value={metrics.win_rate ? `${(metrics.win_rate * 100).toFixed(1)}%` : 'N/A'}
          positive={metrics.win_rate > 0.5}
        />
      </div>
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Period</span>
            <p className="text-white font-medium">{backtest.start_date} to {backtest.end_date}</p>
          </div>
          <div>
            <span className="text-gray-400">Status</span>
            <p className="text-white font-medium capitalize">{backtest.status}</p>
          </div>
        </div>
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

const BacktestChart = ({ data }) => {
  // Transform data for Recharts
  const chartData = data.map((point, index) => ({
    index,
    equity: point,
  }));

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Equity Curve</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="index" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" />
          <Tooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
            labelStyle={{ color: '#9CA3AF' }}
          />
          <Legend />
          <Line type="monotone" dataKey="equity" stroke="#0EA5E9" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Backtests;
