import axios from 'axios';

const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:5173';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

async function request(method, path, payload) {
  const response = await api.request({
    method,
    url: path.replace(/^\/+/, ''),
    data: payload,
    validateStatus: () => true,
  });
  return { ok: response.status >= 200 && response.status < 300, status: response.status, body: response.data };
}

export async function fetchCsrfToken() {
  return request('GET', '/api/auth/csrf');
}

export async function login(username, password) {
  return request('POST', '/api/auth/login', { username, password });
}

export async function createAccountClient(name, phone) {
  return request('POST', '/api/clients', { name, phone });
}

export async function enrollBiometric(clientId) {
  return request('POST', '/api/biometrics/enroll', { client_id: clientId });
}

export async function createAccount(clientId, month, year) {
  return request('POST', '/api/monthly-accounts', { client_id: clientId, month, year });
}

export async function closeAccount(accountId) {
  return request('POST', `/api/monthly-accounts/${encodeURIComponent(accountId)}/close`, {});
}

export async function verifyBiometric(clientId, accountId) {
  return request('POST', `/api/monthly-accounts/${encodeURIComponent(accountId)}/biometric-verify`, {
    client_id: clientId,
    monthly_account_id: accountId,
  });
}

export async function payAccount(accountId) {
  return request('POST', `/api/monthly-accounts/${encodeURIComponent(accountId)}/pay`, {});
}

export default { fetchCsrfToken, login, createAccountClient, enrollBiometric, createAccount, closeAccount, verifyBiometric, payAccount };
