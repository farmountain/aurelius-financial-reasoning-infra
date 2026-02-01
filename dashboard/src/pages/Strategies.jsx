import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { strategiesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import { Layers, Plus, TrendingUp } from 'lucide-react';
import StrategyGenerationModal from '../components/StrategyGenerationModal';

const Strategies = () => {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [actionError, setActionError] = useState(null);

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await strategiesAPI.list(100, 0);
      setStrategies(data);
    } catch (err) {
      setError(err.message || 'Failed to load strategies');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (payload) => {
    setIsGenerating(true);
    setActionError(null);
    try {
      await strategiesAPI.generate(payload);
      setIsModalOpen(false);
      await loadStrategies();
    } catch (err) {
      setActionError(err.message || 'Failed to generate strategy');
    } finally {
      setIsGenerating(false);
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

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Strategies</h1>
          <p className="text-gray-400">Manage and monitor your trading strategies</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          Generate Strategy
        </button>
      </div>

      {actionError && (
        <div className="p-4 bg-red-900/20 border border-red-800 rounded-lg text-red-300">
          {actionError}
        </div>
      )}

      {strategies.length === 0 ? (
        <EmptyState
          title="No Strategies Yet"
          description="Generate your first strategy to get started with quantitative trading"
          icon={Layers}
          action={
            <button className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors">
              Generate Strategy
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {strategies.map((strategy) => (
            <StrategyCard key={strategy.id} strategy={strategy} />
          ))}
        </div>
      )}

      <StrategyGenerationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleGenerate}
        loading={isGenerating}
      />
    </div>
  );
};

const StrategyCard = ({ strategy }) => {
  return (
    <Link
      to={`/strategies/${strategy.id}`}
      className="block p-6 bg-gray-800 rounded-lg border border-gray-700 hover:border-primary-500 transition-colors"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1">{strategy.name}</h3>
          <p className="text-sm text-gray-400">{strategy.strategy_type}</p>
        </div>
        <div className="flex items-center space-x-1">
          <TrendingUp className="w-4 h-4 text-primary-400" />
          <span className="text-sm font-medium text-primary-400">
            {(strategy.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Created</span>
          <span className="text-white">
            {new Date(strategy.created_at).toLocaleDateString()}
          </span>
        </div>
        {strategy.parameters && (
          <div className="pt-2 border-t border-gray-700">
            <span className="text-gray-400 text-xs">Parameters:</span>
            <div className="mt-1 text-xs text-gray-300 max-h-20 overflow-y-auto">
              {JSON.stringify(strategy.parameters, null, 2).substring(0, 100)}...
            </div>
          </div>
        )}
      </div>
    </Link>
  );
};

export default Strategies;
