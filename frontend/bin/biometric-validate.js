import axios from 'axios';

const API_BASE = 'http://localhost:8030';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' }
});

async function authedRequest(method, path, payload, token) {
  const response = await api.request({
    method,
    url: path.replace(/^\/+/, ''),
    data: payload,
    headers: { Authorization: `Bearer ${token}` },
    validateStatus: () => true,
  });
  return { ok: response.status >= 200 && response.status < 300, status: response.status, body: response.data };
}

let token = null;
const results = {};

try {
  results.login = await authedRequest('POST', '/api/auth/login', { username: 'admin', password: 'admin123' }, token);
  token = results.login.body?.access_token;

  if (!token) {
    throw new Error('Admin login failed');
  }

  results.createAccountClient = await authedRequest('POST', '/api/clients', {
    name: `Test Client ${Date.now()}`,
    phone: '11999990000'
  }, token);

  const clientId = results.createAccountClient.body?.id;
  results.clientId = clientId;

  if (clientId) {
    results.enrollBiometric = await authedRequest('POST', '/api/biometrics/enroll', { client_id: clientId }, token);
    results.createAccount = await authedRequest('POST', '/api/monthly-accounts', { client_id: clientId, month: new Date().getMonth() + 1, year: new Date().getFullYear() }, token);

    const accountId = results.createAccount.body?.id;
    results.accountId = accountId;

    if (accountId) {
      results.closeAccount = await authedRequest('POST', `/api/monthly-accounts/${accountId}/close`, {}, token);
      results.verifyBiometric = await authedRequest('POST', `/api/monthly-accounts/${accountId}/biometric-verify`, { client_id: clientId, monthly_account_id: accountId }, token);
      results.payAccount = await authedRequest('POST', `/api/monthly-accounts/${accountId}/pay`, { payment_method: 'pix' }, token);
    }
  }
} catch (error) {
  results.error = { message: error.message, stack: error.stack };
}

console.log(JSON.stringify(results, null, 2));
