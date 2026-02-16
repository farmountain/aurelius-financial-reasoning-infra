import { useEffect, useState } from 'react';
import { useWebSocket } from '../context/WebSocketContext';

export const useRealtimeStrategies = () => {
  const [strategies, setStrategies] = useState([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('strategy_created', (data) => {
      const incoming = Array.isArray(data?.strategies) ? data.strategies : (data ? [data] : []);
      setStrategies(prev => {
        const merged = [...prev];
        incoming.forEach((item) => {
          const index = merged.findIndex(s => s.id === item.id);
          if (index >= 0) {
            merged[index] = item;
          } else {
            merged.push(item);
          }
        });
        return merged;
      });
    });

    return unsubscribe;
  }, [subscribe]);

  return strategies;
};

export const useRealtimeBacktests = () => {
  const [backtests, setBacktests] = useState([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('backtest_completed', (data) => {
      setBacktests(prev => {
        const index = prev.findIndex(b => b.id === data.backtest_id || b.backtest_id === data.backtest_id);
        if (index >= 0) {
          return [...prev.slice(0, index), data, ...prev.slice(index + 1)];
        }
        return [...prev, data];
      });
    });

    return unsubscribe;
  }, [subscribe]);

  return backtests;
};

export const useRealtimeDashboard = () => {
  const [stats, setStats] = useState({
    active_strategies: 0,
    running_backtests: 0,
    gates_passed: 0,
    gates_failed: 0,
    recent_backtests: [],
  });
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribers = [
      subscribe('backtest_started', () => {
        setStats(prev => ({ ...prev, running_backtests: (prev.running_backtests || 0) + 1 }));
      }),
      subscribe('backtest_completed', (data) => {
        setStats(prev => ({
          ...prev,
          running_backtests: Math.max((prev.running_backtests || 1) - 1, 0),
          recent_backtests: [data, ...(prev.recent_backtests || [])].slice(0, 5),
        }));
      }),
      subscribe('gate_verified', (data) => {
        setStats(prev => ({
          ...prev,
          gates_passed: (prev.gates_passed || 0) + (data?.passed ? 1 : 0),
          gates_failed: (prev.gates_failed || 0) + (data?.passed ? 0 : 1),
        }));
      }),
    ];

    return () => {
      unsubscribers.forEach((unsubscribe) => unsubscribe?.());
    };
  }, [subscribe]);

  return stats;
};

export const useRealtimeReflexionEvents = (onIterationCreated) => {
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('reflexion_iteration_created', (data) => {
      if (typeof onIterationCreated === 'function') {
        onIterationCreated(data);
      }
    });

    return unsubscribe;
  }, [onIterationCreated, subscribe]);
};

export const useRealtimeBacktestProgress = (backtestId) => {
  const [progress, setProgress] = useState(null);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('backtest_started', (data) => {
      setProgress(data);
    });

    return unsubscribe;
  }, [backtestId, subscribe]);

  return progress;
};
