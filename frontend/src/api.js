import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach mock analyst token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sentinelx_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: async (username = 'analyst', password = 'sentinelx123') => {
    const res = await api.post('/auth/login', { username, password });
    if (res.data?.access_token) {
      localStorage.setItem('sentinelx_token', res.data.access_token);
    }
    return res.data;
  },
};

export const transactionAPI = {
  list: async (params = {}) => {
    const res = await api.get('/transactions', { params });
    return res.data;
  },
  getById: async (id) => {
    const res = await api.get(`/transactions/${id}`);
    return res.data;
  },
  submit: async (data) => {
    const res = await api.post('/transactions', data);
    return res.data;
  },
};

export const riskAPI = {
  getSummary: async () => {
    const res = await api.get('/risk/summary');
    return res.data;
  },
  predict: async (data, saveToDb = false) => {
    const res = await api.post(`/predict?save_to_db=${saveToDb}`, data);
    return res.data;
  },
};

export const alertAPI = {
  list: async (params = {}) => {
    const res = await api.get('/alerts', { params });
    return res.data;
  },
  getById: async (id) => {
    const res = await api.get(`/alerts/${id}`);
    return res.data;
  },
  updateStatus: async (id, status, remarks = '') => {
    const res = await api.patch(`/alerts/${id}/status`, { status, remarks });
    return res.data;
  },
  assign: async (id, assigned_to) => {
    const res = await api.post(`/alerts/${id}/assign`, { assigned_to });
    return res.data;
  },
};

export const investigationAPI = {
  create: async (data) => {
    const res = await api.post('/investigations', data);
    return res.data;
  },
  list: async (params = {}) => {
    const res = await api.get('/investigations', { params });
    return res.data;
  },
};

export const modelAPI = {
  list: async () => {
    const res = await api.get('/models');
    return res.data;
  },
  getMetrics: async () => {
    const res = await api.get('/models/metrics');
    return res.data;
  },
  retrain: async () => {
    const res = await api.post('/models/retrain');
    return res.data;
  },
};

export const graphAPI = {
  getNetwork: async (limit = 120) => {
    const res = await api.get(`/graph/network?limit=${limit}`);
    return res.data;
  },
};

export const simulatorAPI = {
  trigger: async (forceFraud = false, count = 1) => {
    const res = await api.post(`/simulator/trigger?force_fraud=${forceFraud}&count=${count}`);
    return res.data;
  },
  toggle: async (active, interval = 3.0) => {
    const res = await api.post(`/simulator/toggle?active=${active}&interval_seconds=${interval}`);
    return res.data;
  },
  getStatus: async () => {
    const res = await api.get('/simulator/status');
    return res.data;
  },
};

export default api;
