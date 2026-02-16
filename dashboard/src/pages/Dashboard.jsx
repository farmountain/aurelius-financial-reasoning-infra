import { useState, useEffect } from 'react';
import { strategiesAPI, backtestsAPI, gatesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { CheckCircle, XCircle, Layers, Activity, AlertTriangle } from 'lucide-react';
import { useRealtimeDashboard } from '../hooks/useRealtime';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalStrategies: 0,
    recentBacktests: [],
    gateStats: { passed: 0, failed: 0, total: 0 },
    readiness: { averageScore: 0, bands: { Green: 0, Amber: 0, Red: 0 }, topBlockers: [] },
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
      const readinessScores = [];
      const bandCounts = { Green: 0, Amber: 0, Red: 0 };
      const blockerCounts = new Map();

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

        const readiness = payload.readiness || null;
        if (readiness && typeof readiness.score === 'number') {
          readinessScores.push(readiness.score);
        }
        const band = readiness?.band;
        if (bandCounts[band] !== undefined) {
          bandCounts[band] += 1;
        }
        const blockers = Array.isArray(readiness?.top_blockers) ? readiness.top_blockers : [];
        blockers.slice(0, 3).forEach((blocker) => {
          blockerCounts.set(blocker, (blockerCounts.get(blocker) || 0) + 1);
        });
      });

      const averageScore = readinessScores.length > 0
        ? readinessScores.reduce((acc, value) => acc + value, 0) / readinessScores.length
        : 0;

      const topBlockers = Array.from(blockerCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([name]) => name);

      setStats({
        totalStrategies: strategies.length,
        recentBacktests: backtests.slice(0, 5),
        gateStats: {
          passed,
          failed,
          total: gateStatuses.filter((result) => result.status === 'fulfilled').length,
        },
        readiness: {
          averageScore,
          bands: bandCounts,
          topBlockers,
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

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Promotion Readiness</h2>
            <p className="text-xs text-gray-400">Canonical scorecard summary across strategies</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400">Average Score</p>
            <p className="text-2xl font-bold text-white">{stats.readiness.averageScore.toFixed(1)}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4 text-sm">
          <div className="p-3 rounded border border-green-700 bg-green-900/20 text-green-300">Green: {stats.readiness.bands.Green}</div>
          <div className="p-3 rounded border border-yellow-700 bg-yellow-900/20 text-yellow-300">Amber: {stats.readiness.bands.Amber}</div>
          <div className="p-3 rounded border border-red-700 bg-red-900/20 text-red-300">Red: {stats.readiness.bands.Red}</div>
        </div>

        <div className="text-xs text-gray-300">
          <p className="font-semibold mb-2 flex items-center gap-2"><AlertTriangle className="w-4 h-4" />Top blockers</p>
          {stats.readiness.topBlockers.length === 0 ? (
            <p className="text-gray-400">No blockers currently surfaced.</p>
          ) : (
            stats.readiness.topBlockers.map((item) => <p key={item}>• {item}</p>)
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
