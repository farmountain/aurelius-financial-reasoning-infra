import { useState, useEffect } from 'react';
import { strategiesAPI, backtestsAPI, gatesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { TrendingUp, TrendingDown, CheckCircle, XCircle, Layers, Activity } from 'lucide-react';
import { useRealtimeDashboard } from '../hooks/useRealtime';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalStrategies: 0,
    recentBacktests: [],
    gateStats: { passed: 0, failed: 0, total: 0 },
  });
  const realtimeStats = useRealtimeDashboard();

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    if (
      (realtimeStats?.recent_backtests || []).length > 0 ||
      (realtimeStats?.running_backtests || 0) > 0 ||
      (realtimeStats?.gates_passed || 0) > 0 ||
      (realtimeStats?.gates_failed || 0) > 0
    ) {
      loadDashboardData();
    }
  }, [realtimeStats]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [strategies, backtests] = await Promise.all([
        strategiesAPI.list(100, 0),
        backtestsAPI.list(null, 10, 0),
      ]);

      const gateStatuses = await Promise.allSettled(
        (strategies || []).map((strategy) => gatesAPI.getStatus(strategy.id))
      );

      let passed = 0;
      let failed = 0;
      gateStatuses.forEach((result) => {
        if (result.status !== 'fulfilled') {
          return;
        }

        const payload = result.value || {};
        if (payload.production_ready === true) {
          passed += 1;
        } else {
          failed += 1;
        }
      });

      setStats({
        totalStrategies: strategies.length,
        recentBacktests: backtests.slice(0, 5),
        gateStats: {
          passed,
          failed,
          total: gateStatuses.filter((result) => result.status === 'fulfilled').length,
        },
      });
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
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
    return <ErrorMessage message={error} onRetry={loadDashboardData} />;
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-gray-400">Overview of your quantitative strategies and backtests</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Strategies"
          value={stats.totalStrategies}
          icon={Layers}
          color="blue"
        />
        <StatCard
          title="Active Backtests"
          value={stats.recentBacktests.filter(b => b.status === 'running').length}
          icon={Activity}
          color="purple"
        />
        <StatCard
          title="Gates Passed"
          value={stats.gateStats.passed}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="Gates Failed"
          value={stats.gateStats.failed}
          icon={XCircle}
          color="red"
        />
      </div>

      {/* Recent Backtests */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-6 py-4 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">Recent Backtests</h2>
        </div>
        <div className="p-6">
          {stats.recentBacktests.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No backtests yet</p>
          ) : (
            <div className="space-y-3">
              {stats.recentBacktests.map((backtest) => (
                <BacktestRow key={backtest.id} backtest={backtest} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-900/30 border-blue-700 text-blue-400',
    purple: 'bg-purple-900/30 border-purple-700 text-purple-400',
    green: 'bg-green-900/30 border-green-700 text-green-400',
    red: 'bg-red-900/30 border-red-700 text-red-400',
  };

  return (
    <div className={`p-6 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-300">{title}</span>
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
};

const BacktestRow = ({ backtest }) => {
  const statusColors = {
    completed: 'text-green-400',
    running: 'text-yellow-400',
    failed: 'text-red-400',
    pending: 'text-gray-400',
  };

  return (
    <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg border border-gray-700">
      <div className="flex-1">
        <p className="text-white font-medium">Strategy ID: {backtest.strategy_id}</p>
        <p className="text-sm text-gray-400">
          {backtest.start_date} to {backtest.end_date}
        </p>
      </div>
      <div className="flex items-center space-x-4">
        {backtest.results?.sharpe_ratio && (
          <div className="text-right">
            <p className="text-xs text-gray-400">Sharpe Ratio</p>
            <p className="text-white font-semibold">{backtest.results.sharpe_ratio.toFixed(2)}</p>
          </div>
        )}
        <span className={`text-sm font-medium ${statusColors[backtest.status]}`}>
          {backtest.status}
        </span>
      </div>
    </div>
  );
};

export default Dashboard;
