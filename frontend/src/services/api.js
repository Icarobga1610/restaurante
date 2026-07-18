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

// Response interceptor: centralize auth/permission handling AND transparently
// refresh the access token on 401 (rotating the server-side refresh token).
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config || {};
    const status = error?.response?.status;

    // Try a single token refresh on 401, then retry the original request.
    if (status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh');
      if (refreshToken) {
        originalRequest._retry = true;
        try {
          // Imported lazily to avoid a circular dependency at module load.
          const { auth } = await import('../services/api');
          const resp = await auth.refresh(refreshToken);
          const { access_token } = resp.data;
          localStorage.setItem('token', access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch {
          // Refresh failed: treat as a real logout.
        }
      }
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('refresh');
      window.dispatchEvent(new Event('auth:unauthorized'));
      return Promise.reject(error);
    }

    if (status === 403) {
      toast.error('Sem autorização para essa ação.');
      return Promise.reject(error);
    }
    const detail = error?.response?.data?.detail;
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
  refresh: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }, { _retry: true }),
  logout: (refreshToken) => api.post('/auth/logout', { refresh_token: refreshToken }, { _retry: true }),
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

// === Companies / corporate billing ===
export const companies = {
  list: (params) => api.get('/companies', { params }),
  get: (id) => api.get(`/companies/${id}`),
  create: (data) => api.post('/companies', data),
  update: (id, data) => api.put(`/companies/${id}`, data),
  members: (id) => api.get(`/companies/${id}/members`),
  linkMember: (companyId, clientId) => api.post(`/companies/${companyId}/members/${clientId}`),
  unlinkMember: (companyId, clientId) => api.delete(`/companies/${companyId}/members/${clientId}`),
};

export const companyAccounts = {
  list: (params) => api.get('/company-monthly-accounts', { params }),
  get: (id) => api.get(`/company-monthly-accounts/${id}`),
  create: (data) => api.post('/company-monthly-accounts', data),
  close: (id) => api.post(`/company-monthly-accounts/${id}/close`),
  pay: (id, data) => api.post(`/company-monthly-accounts/${id}/pay`, data),
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
  webauthn: {
    enrollOptions: (data) => api.post('/biometrics/webauthn/enroll/options', data),
    enrollComplete: (data) => api.post('/biometrics/webauthn/enroll/complete', data),
    verifyOptions: (data) => api.post('/biometrics/webauthn/verify/options', data),
    verifyComplete: (data) => api.post('/biometrics/webauthn/verify/complete', data),
  },
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

// === Stock / Ingredients ===
export const stock = {
  items: {
    list: (params) => api.get('/stock/items', { params }),
    get: (id) => api.get(`/stock/items/${id}`),
    create: (data) => api.post('/stock/items', data),
    update: (id, data) => api.put(`/stock/items/${id}`, data),
  },
  movements: {
    list: (params) => api.get('/stock/movements', { params }),
    create: (data) => api.post('/stock/movements', data),
  },
  alerts: {
    lowStock: () => api.get('/stock/alerts/low-stock'),
    expiring: (params) => api.get('/stock/alerts/expiring', { params }),
  },
};

// === Recipes / Technical Sheets ===
export const recipes = {
  list: () => api.get('/recipes'),
  get: (id) => api.get(`/recipes/${id}`),
  create: (data) => api.post('/recipes', data),
  update: (id, data) => api.put(`/recipes/${id}`, data),
  recalculate: (id) => api.post(`/recipes/${id}/recalculate`),
};

// === Promotions ===
export const promotions = {
  list: (params) => api.get('/promotions/promotions', { params }),
  coupons: (params) => api.get('/promotions/coupons', { params }),
};

// === Finance ===
export const finance = {
  ledger: (params) => api.get('/finance/ledger', { params }),
};

// === Payment Methods ===
export const paymentMethods = {
  list: (params) => api.get('/payment-methods', { params }),
  getDefault: () => api.get('/payment-methods/default'),
  create: (data) => api.post('/payment-methods', data),
  update: (id, data) => api.put(`/payment-methods/${id}`, data),
  setDefault: (id) => api.post(`/payment-methods/${id}/default`),
};

// === Delivery ===
export const delivery = {
  platforms: {
    list: (params) => api.get('/delivery/platforms', { params }),
    create: (data) => api.post('/delivery/platforms', data),
    get: (slug) => api.get(`/delivery/platforms/${slug}`),
  },
  orders: {
    list: (params) => api.get('/delivery/orders', { params }),
    get: (id) => api.get(`/delivery/orders/${id}`),
    create: (data) => api.post('/delivery/orders/incoming', data),
    ack: (id) => api.post(`/delivery/orders/${id}/ack`),
    cancel: (id) => api.post(`/delivery/orders/${id}/cancel`),
    convert: (id) => api.post(`/delivery/orders/${id}/convert-order`),
  },
  webhooks: {
    send: (slug, data) => api.post(`/delivery/webhook/${slug}`, data),
  },
};

// === Audit ===
export const audit = {
  list: (params) => api.get('/audit', { params }),
};
