import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const API_V1_PREFIX = '/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid - clear auth and redirect
      localStorage.removeItem('auth_token');
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
    return Promise.reject(error);
  }
);

// Strategies API
export const strategiesAPI = {
  generate: async (data) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/strategies/generate`, data);
    return response.data?.strategies || [];
  },
  list: async (limit = 100, skip = 0) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/strategies/`, { params: { limit, skip } });
    return response.data?.strategies || [];
  },
  get: async (strategyId) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/strategies/${strategyId}`);
    const payload = response.data || {};
    return {
      id: payload.strategy_id,
      created_at: payload.created_at,
      status: payload.status,
      ...(payload.strategy || {}),
    };
  },
};

// Backtests API
export const backtestsAPI = {
  run: async (strategyId, data) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/backtests/run`, {
      strategy_id: strategyId,
      ...data,
    });
    return response.data;
  },
  list: async (strategyId = null, limit = 100, skip = 0) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/backtests/`, {
      params: { strategy_id: strategyId, limit, skip },
    });
    return (response.data?.backtests || []).map((item) => ({
      id: item.backtest_id,
      strategy_id: item.strategy_id,
      status: item.status,
      start_date: item.start_date,
      end_date: item.end_date,
      created_at: item.completed_at,
      results: item.metrics,
      duration_seconds: item.duration_seconds,
    }));
  },
  get: async (backtestId) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/backtests/${backtestId}`);
    return response.data;
  },
};

// Validations API
export const validationsAPI = {
  run: async (strategyId, data) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/validation/run`, {
      strategy_id: strategyId,
      ...data,
    });
    return response.data;
  },
  list: async (strategyId = null, limit = 100, skip = 0) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/validation/`, {
      params: { strategy_id: strategyId, limit, skip },
    });
    return response.data?.validations || [];
  },
  get: async (validationId) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/validation/${validationId}`);
    return response.data;
  },
};

// Gates API
export const gatesAPI = {
  runDev: async (strategyId, data = {}) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/gates/dev-gate`, {
      strategy_id: strategyId,
      ...data,
    });
    return response.data;
  },
  runCRV: async (strategyId, data = {}) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/gates/crv-gate`, {
      strategy_id: strategyId,
      ...data,
    });
    return response.data;
  },
  runProduct: async (strategyId, data = {}) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/gates/product-gate`, {
      strategy_id: strategyId,
      ...data,
    });
    return response.data;
  },
  getStatus: async (strategyId) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/gates/${strategyId}/status`);
    return response.data;
  },
};

// Reflexion API
export const reflexionAPI = {
  run: async (strategyId, data) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/reflexion/${strategyId}/run`, data || {});
    return response.data;
  },
  getHistory: async (strategyId) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/reflexion/${strategyId}/history`);
    return response.data || [];
  },
};

// Orchestrator API
export const orchestratorAPI = {
  run: async (data) => {
    const response = await apiClient.post(`${API_V1_PREFIX}/orchestrator/runs`, data);
    return response.data;
  },
  getStatus: async (runId) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/orchestrator/runs/${runId}`);
    return response.data;
  },
  list: async (limit = 50, skip = 0) => {
    const response = await apiClient.get(`${API_V1_PREFIX}/orchestrator/runs`, { params: { limit, skip } });
    return response.data?.runs || [];
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default apiClient;
