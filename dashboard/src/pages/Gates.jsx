import { useState, useEffect } from 'react';
import { strategiesAPI, gatesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import { Shield, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const Gates = () => {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [gateStatus, setGateStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      loadGateStatus(selectedStrategy.id);
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

  const loadGateStatus = async (strategyId) => {
    try {
      const data = await gatesAPI.getStatus(strategyId);
      setGateStatus(data);
    } catch (err) {
      setGateStatus(null);
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
          description="Create strategies to run gate checks"
          icon={Shield}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Gates</h1>
        <p className="text-gray-400">Dev, CRV, and Product gate verification</p>
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
                <p className="text-xs opacity-75 mt-1">{strategy.strategy_type}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Gate Status */}
        <div className="lg:col-span-2 space-y-6">
          {selectedStrategy && (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-white">Gate Status</h2>
                  <p className="text-gray-400 text-sm">{selectedStrategy.name}</p>
                </div>
              </div>

              {gateStatus ? (
                <div className="space-y-4">
                  <ReadinessPanel readiness={gateStatus.readiness} />
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <GateCard
                      title="Dev Gate"
                      gate={gateStatus.dev_gate}
                      fallbackPassed={gateStatus.dev_gate_passed}
                    />
                    <GateCard
                      title="CRV Gate"
                      gate={gateStatus.crv_gate}
                      fallbackPassed={gateStatus.crv_gate_passed}
                    />
                    <GateCard
                      title="Product Gate"
                      gate={gateStatus.product_gate}
                      fallbackPassed={gateStatus.production_ready}
                    />
                  </div>
                </div>
              ) : (
                <p className="text-gray-400">No gate results found for this strategy</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const GateCard = ({ title, gate, fallbackPassed = null }) => {
  const resolvedPassed = gate?.passed;
  const hasGateResult = resolvedPassed !== undefined && resolvedPassed !== null;
  const hasFallback = fallbackPassed !== undefined && fallbackPassed !== null;

  if (!hasGateResult && !hasFallback) {
    return (
      <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
        <h3 className="text-sm font-medium text-gray-300 mb-2">{title}</h3>
        <p className="text-xs text-gray-500">Not run</p>
      </div>
    );
  }

  const passed = hasGateResult ? Boolean(resolvedPassed) : Boolean(fallbackPassed);
  const gateResults = gate?.results || null;

  return (
    <div className={`p-4 rounded-lg border ${passed ? 'bg-green-900/20 border-green-700' : 'bg-red-900/20 border-red-700'}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-white">{title}</h3>
        {passed ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <XCircle className="w-5 h-5 text-red-400" />
        )}
      </div>
      <p className={`text-xs ${passed ? 'text-green-400' : 'text-red-400'}`}>
        {passed ? 'Passed' : 'Failed'}
      </p>
      {gateResults && (
        <div className="mt-2 text-xs text-gray-400">
          {Object.entries(gateResults).slice(0, 3).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span>{key}</span>
              <span>{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ReadinessPanel = ({ readiness }) => {
  if (!readiness || typeof readiness !== 'object') {
    return (
      <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
        <div className="flex items-center gap-2 text-gray-300 text-sm">
          <AlertTriangle className="w-4 h-4" />
          Promotion readiness not yet available.
        </div>
      </div>
    );
  }

  const band = readiness.band || 'Unknown';
  const score = typeof readiness.score === 'number' ? readiness.score.toFixed(1) : 'N/A';
  const maturity = readiness.maturity_label || 'unknown';
  const blockers = Array.isArray(readiness.top_blockers) ? readiness.top_blockers : [];
  const actions = Array.isArray(readiness.next_actions) ? readiness.next_actions : [];

  const bandClasses = {
    Green: 'bg-green-900/20 border-green-700 text-green-300',
    Amber: 'bg-yellow-900/20 border-yellow-700 text-yellow-300',
    Red: 'bg-red-900/20 border-red-700 text-red-300',
    Unknown: 'bg-gray-900/50 border-gray-700 text-gray-300',
  };

  return (
    <div className={`p-4 rounded-lg border ${bandClasses[band] || bandClasses.Unknown}`}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div>
          <p className="text-xs uppercase tracking-wide opacity-80">Promotion Readiness</p>
          <p className="text-lg font-semibold">{band} ({score})</p>
        </div>
        <div className="text-sm opacity-90">
          <span className="mr-2">Maturity:</span>
          <span className="font-semibold">{maturity}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        <div>
          <p className="font-semibold mb-1">Top blockers</p>
          {blockers.length === 0 ? (
            <p className="opacity-80">No blockers</p>
          ) : (
            blockers.slice(0, 3).map((item) => <p key={item}>• {item}</p>)
          )}
        </div>
        <div>
          <p className="font-semibold mb-1">Recommended actions</p>
          {actions.length === 0 ? (
            <p className="opacity-80">No immediate action</p>
          ) : (
            actions.slice(0, 3).map((item, idx) => <p key={`${idx}-${item}`}>• {item}</p>)
          )}
        </div>
      </div>
    </div>
  );
};

export default Gates;
