import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { strategiesAPI, backtestsAPI, gatesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { ArrowLeft, Play, CheckCircle, XCircle } from 'lucide-react';

const StrategyDetail = () => {
  const { id } = useParams();
  const [strategy, setStrategy] = useState(null);
  const [backtests, setBacktests] = useState([]);
  const [gates, setGates] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStrategyData();
  }, [id]);

  const loadStrategyData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [strategyData, backtestsData, gatesData] = await Promise.all([
        strategiesAPI.get(id),
        backtestsAPI.list(id, 10, 0),
        gatesAPI.getStatus(id).catch(() => null),
      ]);
      setStrategy(strategyData);
      setBacktests(backtestsData);
      setGates(gatesData);
    } catch (err) {
      setError(err.message || 'Failed to load strategy details');
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
    return <ErrorMessage message={error} onRetry={loadStrategyData} />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center space-x-4">
        <Link
          to="/strategies"
          className="p-2 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-white mb-1">{strategy.name}</h1>
          <p className="text-gray-400">{strategy.strategy_type}</p>
        </div>
        <button className="flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors">
          <Play className="w-4 h-4 mr-2" />
          Run Backtest
        </button>
      </div>

      {/* Strategy Info */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Strategy Details</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Confidence</span>
            <p className="text-white font-medium">{(strategy.confidence * 100).toFixed(1)}%</p>
          </div>
          <div>
            <span className="text-gray-400">Created</span>
            <p className="text-white font-medium">
              {new Date(strategy.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        {strategy.parameters && (
          <div className="mt-4">
            <span className="text-gray-400 text-sm">Parameters</span>
            <pre className="mt-2 p-4 bg-gray-900 rounded text-xs text-gray-300 overflow-x-auto">
              {JSON.stringify(strategy.parameters, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Gate Status */}
      {gates && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Gate Status</h2>
          <div className="grid grid-cols-3 gap-4">
            <GateStatusCard
              name="Dev Gate"
              passed={gates.dev_gate?.passed}
              results={gates.dev_gate?.results}
            />
            <GateStatusCard
              name="CRV Gate"
              passed={gates.crv_gate?.passed}
              results={gates.crv_gate?.results}
            />
            <GateStatusCard
              name="Product Gate"
              passed={gates.product_gate?.passed}
              results={gates.product_gate?.results}
            />
          </div>
        </div>
      )}

      {/* Backtests */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Backtest History</h2>
        {backtests.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No backtests yet</p>
        ) : (
          <div className="space-y-3">
            {backtests.map((backtest) => (
              <BacktestRow key={backtest.id} backtest={backtest} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const GateStatusCard = ({ name, passed, results }) => {
  if (!passed && passed !== false) {
    return (
      <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
        <h3 className="text-sm font-medium text-gray-300 mb-2">{name}</h3>
        <p className="text-xs text-gray-500">Not run</p>
      </div>
    );
  }

  return (
    <div className={`p-4 rounded-lg border ${passed ? 'bg-green-900/20 border-green-700' : 'bg-red-900/20 border-red-700'}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-white">{name}</h3>
        {passed ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <XCircle className="w-5 h-5 text-red-400" />
        )}
      </div>
      <p className={`text-xs ${passed ? 'text-green-400' : 'text-red-400'}`}>
        {passed ? 'Passed' : 'Failed'}
      </p>
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
        <p className="text-white font-medium">
          {backtest.start_date} to {backtest.end_date}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Run at {new Date(backtest.created_at).toLocaleString()}
        </p>
      </div>
      <div className="flex items-center space-x-4">
        {backtest.results && (
          <>
            <div className="text-right">
              <p className="text-xs text-gray-400">Return</p>
              <p className="text-white font-semibold">
                {(backtest.results.total_return * 100).toFixed(2)}%
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-400">Sharpe</p>
              <p className="text-white font-semibold">
                {backtest.results.sharpe_ratio?.toFixed(2) || 'N/A'}
              </p>
            </div>
          </>
        )}
        <span className={`text-sm font-medium ${statusColors[backtest.status]}`}>
          {backtest.status}
        </span>
      </div>
    </div>
  );
};

export default StrategyDetail;
