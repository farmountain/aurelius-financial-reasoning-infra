import { useState, useEffect } from 'react';
import { orchestratorAPI, strategiesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import { Activity } from 'lucide-react';
import { useWebSocket } from '../context/WebSocketContext';

const Orchestrator = () => {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startingRun, setStartingRun] = useState(false);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState('');
  const [isGeneratingStrategy, setIsGeneratingStrategy] = useState(false);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    loadOrchestrationRuns();
    // Poll for updates every 10 seconds
    const interval = setInterval(loadOrchestrationRuns, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadOrchestrationRuns = async () => {
    setError(null);
    try {
      const data = await orchestratorAPI.list(100, 0);
      setRuns(Array.isArray(data) ? data : []);
      if (!selectedRun && Array.isArray(data) && data.length > 0) {
        setSelectedRun(data[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load orchestrator runs');
    } finally {
      setLoading(false);
    }
  };

  const loadStrategies = async () => {
    try {
      const data = await strategiesAPI.list(100, 0);
      const list = Array.isArray(data) ? data : [];
      setAvailableStrategies(list);

      if (!selectedStrategyId && list.length > 0) {
        setSelectedStrategyId(list[0].id);
      }
    } catch (err) {
      setAvailableStrategies([]);
    }
  };

  useEffect(() => {
    loadStrategies();
  }, []);

  useEffect(() => {
    const unsubscribeCreated = subscribe('orchestrator_run_created', () => {
      loadOrchestrationRuns();
    });

    const unsubscribeStage = subscribe('orchestrator_stage_updated', (event) => {
      if (!event?.run_id) {
        return;
      }

      setRuns((prevRuns) => prevRuns.map((run) => {
        if (run.id !== event.run_id) {
          return run;
        }

        return {
          ...run,
          current_stage: event.stage,
          stages: {
            ...(run.stages || {}),
            [event.stage]: {
              ...(run.stages?.[event.stage] || {}),
              status: event.status,
              details: event.details || {},
            },
          },
        };
      }));

      setSelectedRun((prev) => {
        if (!prev || prev.id !== event.run_id) {
          return prev;
        }

        return {
          ...prev,
          current_stage: event.stage,
          stages: {
            ...(prev.stages || {}),
            [event.stage]: {
              ...(prev.stages?.[event.stage] || {}),
              status: event.status,
              details: event.details || {},
            },
          },
        };
      });
    });

    return () => {
      unsubscribeCreated?.();
      unsubscribeStage?.();
    };
  }, [subscribe]);

  const generateStrategyForOrchestrator = async () => {
    if (isGeneratingStrategy) {
      return;
    }

    setIsGeneratingStrategy(true);
    setError(null);
    try {
      const generated = await strategiesAPI.generate({
        goal: 'Generate a robust baseline strategy for orchestrator first-run pipeline execution',
        risk_preference: 'moderate',
        max_strategies: 1,
      });

      if (!Array.isArray(generated) || generated.length === 0 || !generated[0]?.id) {
        throw new Error('Strategy generation did not return a usable strategy ID');
      }

      await loadStrategies();
      setSelectedStrategyId(generated[0].id);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to generate strategy');
    } finally {
      setIsGeneratingStrategy(false);
    }
  };

  const startNewRun = async () => {
    if (startingRun) {
      return;
    }

    setStartingRun(true);
    setError(null);
    try {
      const strategyId = selectedStrategyId || availableStrategies[0]?.id || runs[0]?.strategy_id;
      if (!strategyId) {
        throw new Error('No strategy available. Generate one strategy before starting an orchestrator run.');
      }

      const result = await orchestratorAPI.run({
        strategy_id: strategyId,
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        initial_capital: 100000,
        instruments: ['SPY'],
      });

      if (result?.run_id) {
        const runStatus = await orchestratorAPI.getStatus(result.run_id);
        setSelectedRun(runStatus);
      }

      await loadOrchestrationRuns();
      await loadStrategies();
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to start orchestrator run');
    } finally {
      setStartingRun(false);
    }
  };

  if (loading && runs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error && runs.length === 0) {
    return <ErrorMessage message={error} onRetry={loadOrchestrationRuns} />;
  }

  if (runs.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="No Orchestrator Runs"
          description="Start a first end-to-end pipeline run using an existing or newly generated strategy"
          icon={Activity}
          action={
            <div className="space-y-3 w-full max-w-xl">
              <div className="flex flex-col sm:flex-row gap-2">
                <select
                  value={selectedStrategyId}
                  onChange={(e) => setSelectedStrategyId(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm"
                >
                  {availableStrategies.length === 0 && <option value="">No strategy available</option>}
                  {availableStrategies.map((strategy) => (
                    <option key={strategy.id} value={strategy.id}>
                      {strategy.name || strategy.strategy_type || strategy.id}
                    </option>
                  ))}
                </select>
                <button
                  onClick={startNewRun}
                  disabled={startingRun || !selectedStrategyId}
                  className="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-lg transition-colors"
                >
                  {startingRun ? 'Starting...' : 'Start New Run'}
                </button>
              </div>
              <button
                onClick={generateStrategyForOrchestrator}
                disabled={isGeneratingStrategy}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white rounded-lg text-sm transition-colors"
              >
                {isGeneratingStrategy ? 'Generating Strategy...' : 'Generate Strategy for First Run'}
              </button>
            </div>
          }
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Orchestrator</h1>
          <p className="text-gray-400">End-to-end pipeline execution and monitoring</p>
        </div>
        <button
          onClick={startNewRun}
          disabled={startingRun || (!selectedStrategyId && availableStrategies.length === 0)}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-lg transition-colors"
        >
          {startingRun ? 'Starting...' : 'Start New Run'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Runs List */}
        <div className="lg:col-span-1 bg-gray-800 rounded-lg border border-gray-700 p-4 max-h-[calc(100vh-200px)] overflow-y-auto">
          <h2 className="text-lg font-semibold text-white mb-4">Pipeline Runs</h2>
          <div className="space-y-2">
            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => setSelectedRun(run)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedRun?.id === run.id
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-900/50 text-gray-300 hover:bg-gray-900'
                }`}
              >
                <p className="font-medium text-sm">Run {run.run_num || run.id}</p>
                <p className="text-xs opacity-75 mt-1">
                  {run.created_at ? new Date(run.created_at).toLocaleDateString() : 'Unknown date'}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Run Details */}
        <div className="lg:col-span-2">
          {selectedRun ? (
            <RunDetails run={selectedRun} />
          ) : (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 text-center">
              <p className="text-gray-400">Select a run to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const RunDetails = ({ run }) => {
  const stages = [
    { name: 'Generate Strategy', status: run.stages?.generate_strategy?.status || 'pending' },
    { name: 'Run Backtest', status: run.stages?.run_backtest?.status || 'pending' },
    { name: 'Validation', status: run.stages?.validation?.status || 'pending' },
    { name: 'Dev Gate', status: run.stages?.dev_gate?.status || 'pending' },
    { name: 'CRV Gate', status: run.stages?.crv_gate?.status || 'pending' },
    { name: 'Product Gate', status: run.stages?.product_gate?.status || 'pending' },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-900/30 border-green-700 text-green-400';
      case 'running':
        return 'bg-yellow-900/30 border-yellow-700 text-yellow-400';
      case 'failed':
        return 'bg-red-900/30 border-red-700 text-red-400';
      default:
        return 'bg-gray-900/50 border-gray-700 text-gray-400';
    }
  };

  const overallProgress = stages.filter(s => s.status === 'completed').length;
  const progressPercent = Math.round((overallProgress / stages.length) * 100);

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Pipeline Progress</h2>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-400 text-sm">Overall Progress</span>
            <span className="text-white font-medium">{progressPercent}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>

        {/* Stages */}
        <div className="space-y-3">
          {stages.map((stage, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border flex items-center justify-between ${getStatusColor(stage.status)}`}
            >
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <StageIcon status={stage.status} />
                </div>
                <span className="font-medium">{stage.name}</span>
              </div>
              <span className="text-xs capitalize px-2 py-1 bg-black/20 rounded">
                {stage.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Run Info */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Run Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Status</span>
            <p className="text-white font-medium capitalize">{run.status || 'unknown'}</p>
          </div>
          <div>
            <span className="text-gray-400">Started</span>
            <p className="text-white font-medium">
              {run.created_at ? new Date(run.created_at).toLocaleString() : 'Unknown'}
            </p>
          </div>
          {run.strategy_id && (
            <div>
              <span className="text-gray-400">Strategy ID</span>
              <p className="text-white font-medium">{run.strategy_id}</p>
            </div>
          )}
          {run.duration && (
            <div>
              <span className="text-gray-400">Duration</span>
              <p className="text-white font-medium">{run.duration}s</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const StageIcon = ({ status }) => {
  switch (status) {
    case 'completed':
      return (
        <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      );
    case 'running':
      return (
        <svg className="w-5 h-5 text-yellow-400 animate-spin" fill="currentColor" viewBox="0 0 20 20">
          <path d="M4 2a1 1 0 011 1v2.101a7 7 0 012.16-1.283 1 1 0 10-.56 1.933A5 5 0 005 6.65V3a1 1 0 01-1-1z" />
        </svg>
      );
    case 'failed':
      return (
        <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      );
    default:
      return (
        <div className="w-5 h-5 rounded-full border-2 border-gray-400 border-t-gray-600"></div>
      );
  }
};

export default Orchestrator;
