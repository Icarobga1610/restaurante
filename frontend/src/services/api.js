import axios from 'axios';
import { toast } from 'react-toastify';

const apiBase = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: apiBase,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth / permission errors centrally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const detail = error?.response?.data?.detail;
    if (status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return Promise.reject(error);
    }
    if (status === 403) {
      toast.error('Sem autorização para essa ação.');
      return Promise.reject(error);
    }
    if (detail) {
      toast.error(detail);
      return Promise.reject(error);
    }
    toast.error('Erro inesperado.');
    return Promise.reject(error);
  }
);

export default api;

// === Auth ===
export const auth = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/users/me'),
  getRoles: () => api.get('/auth/roles'),
  createUser: (data) => api.post('/auth/users', data),
};

// === Clients ===
export const clients = {
  list: (params) => api.get('/clients', { params }),
  get: (id) => api.get(`/clients/${id}`),
  create: (data) => api.post('/clients', data),
  update: (id, data) => api.put(`/clients/${id}`, data),
  delete: (id) => api.delete(`/clients/${id}`),
};

// === Products ===
export const products = {
  list: (params) => api.get('/products', { params }),
  get: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
};

// === Orders ===
export const orders = {
  list: (params) => api.get('/orders', { params }),
  get: (id) => api.get(`/orders/${id}`),
  create: (data) => api.post('/orders', data),
  update: (id, data) => api.put(`/orders/${id}`, data),
  addSignature: (orderId, data) => api.post(`/orders/${orderId}/signature`, data),
  verifyBiometry: (orderId, clientId) => api.post('/biometrics/verify-identity', { client_id: clientId, monthly_account_id: orderId }),
};

// === Monthly Accounts ===
export const monthlyAccounts = {
  list: (params) => api.get('/monthly-accounts', { params }),
  get: (id) => api.get(`/monthly-accounts/${id}`),
  create: (data) => api.post('/monthly-accounts', data),
  close: (id, data) => api.post(`/monthly-accounts/${id}/close`, data || {}),
  biometricVerify: (id) => api.post(`/monthly-accounts/${id}/biometric-verify`, {}),
  pay: (id, data) => api.post(`/monthly-accounts/${id}/pay`, data || {}),
};

// === Biometrics ===
export const biometrics = {
  enroll: (data) => api.post('/biometrics/enroll', data),
  verify: (data) => api.post('/biometrics/verify', data),
  verifyIdentity: (data) => api.post('/biometrics/verify-identity', data),
  profiles: {
    list: (params) => api.get('/biometrics/profiles', { params }),
    get: (id) => api.get(`/biometrics/profiles/${id}`),
    disable: (id, data) => api.post(`/biometrics/profiles/${id}/disable`, data),
  },
  events: (params) => api.get('/biometrics/events', { params }),
  consent: (params) => api.get('/biometrics/consent', { params }),
};

// === Signatures (legacy — kept for historical data access) ===
export const signatures = {
  list: (params) => api.get('/signatures', { params }),
  get: (id) => api.get(`/signatures/${id}`),
};

// === Dashboard ===
export const dashboard = {
  get: (params) => api.get('/dashboard', { params }),
};

// === Insights ===
export const insights = {
  refresh: () => api.get('/insights/refresh'),
  active: () => api.get('/insights/active'),
  topProductsDay: () => api.get('/insights/seasonality/top-products-day'),
  topProductsMonth: () => api.get('/insights/seasonality/top-products-month'),
  peakHours: () => api.get('/insights/seasonality/peak-hours'),
  topClients: () => api.get('/insights/seasonality/top-clients'),
  categoryConsumption: () => api.get('/insights/seasonality/category-consumption'),
};

// === Audit ===
export const audit = {
  list: (params) => api.get('/audit', { params }),
};
