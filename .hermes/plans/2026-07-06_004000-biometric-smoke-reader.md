# Biometric Fingerprint Integration: Smoke Tests + Reader Validation

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add a reliable biometric smoke-test that uses real `client_id` flow, and validate the fingerprint reader integration path in the app—both in demo/simulated mode and, if supported by the environment, with a real reader.

**Architecture:** Keep the existing backend biometric service interface; add a backend smoke test under `/tests` and a frontend validation script that exercises enrollment/verification through the browser without changing production behavior. Reader validation requires USB/device path checks and optional integration confirmation.

**Tech Stack:** FastAPI, pytest, SQLAlchemy, React, Vite, node fetch/playwright for browser automation. Hardware validation via OS utilities (`lsusb`, `udevadm`, etc.).

---

## Current Context / Assumptions

- Backend biometric endpoints exist under `/api/biometrics/*`: `/enroll`, `/verify`, `/verify-identity`, `/profiles`, `/events`, `/consent`.
- `/biometrics/enroll` expects `client_id` and creates an active `BiometricProfile`.
- `/monthly-accounts/{id}/biometric-verify` expects the account to be in `closed` or `confirmed_by_biometrics` state; it calls `BiometricService.verify_client(...)`.
- Blocking issue observed: earlier smoke tests sent `{}` to `/monthly-accounts/{id}/biometric-verify` and got `400: Cliente não possui cadastro biométrico`. That indicates the service requires a real enrolled profile unless in demo fallback; more investigation is needed.
- Frontend has `/biometric` page and enrollment UI in client registration when `is_account_client=true`.
- The project currently has SQLite-based tests and optional Postgres via `USE_POSTGRES_TESTS=true`. Prefer Postgres for smoke tests to match production behavior.

## Proposed Approach

1. Inspect `BiometricService` to understand demo mode, reader SDK stubs, and how `/verify` behaves when no profile exists.
2. Add a backend smoke test that mimics the exact production payloads: create client → mark as account client → create monthly account → add order → close account → enroll → verify → pay.
3. Add a frontend validation script tested against `http://2.25.175.234:5173` (or local Vite preview) that exercises the biometric page flow.
4. Provide a hardware validation checklist and script probing local reader availability (USB, ttyACM, etc.), plus notes for wiring a real reader into `BiometricService`.

## Files Likely To Change

- `backend/app/services/biometric_service.py`
- `backend/tests/test_biometric_smoke.py`
- `frontend/src/pages/BiometricVerify.jsx`
- `frontend/src/app/biometric-validation.js`
- `scripts/check-fingerprint-reader.sh`

## Step-by-Step Plan

### Task 1: Inspect BiometricService contract

**Objective:** Confirm demo mode behavior, required fields, and how enrollment/verification should be called.

**Files:**
- Read: `backend/app/services/biometric_service.py`
- Read: `backend/app/routes/biometric_routes.py`

**Step 1:** Read `backend/app/services/biometric_service.py`.

Validation: author can state whether `enroll_client` is simulated or requires hardware, and what `verify_client` returns when no profile exists.

### Task 2: Add backend biometric smoke test

**Objective:** Automated pytest that exercises the full account-client biometric flow with real database rows.

**Files:**
- Create: `backend/tests/test_biometric_smoke.py`
- Modify: none required if helper clients/products already available via existing test factories/fixtures

**Step 1:** Check existing test patterns and utils (`tests/`, `backend/tests/conftest.py`, `tests/factories`).

**Step 2:** Write failing test that posts to `/auth/login`, creates a client with `is_account_client=true`, creates a monthly account, closes it, enrolls biometrics, verifies biometrics, then pays the account.

**Step 3:** Run the test. Expected: FAIL around the first assertion that is not initialized.

**Step 4:** Implement the minimal sequence in the test file using `client` fixture and request helper.

**Step 5:** Run again with `USE_POSTGRES_TESTS=true` to confirm production DB behavior. Expected: PASS.

### Task 3: Add frontend integration validation script

**Objective:** Non-UI automation validation for `/api/biometrics` and account closing path from browser entrypoint.

**Files:**
- Create: `frontend/src/app/biometric-validation.js`
- Modify: none runtime; optional `frontend/package.json` scripts entry

**Step 1:** Read `frontend/package.json` to see existing scripts/proxy setup.

**Step 2:** Create `frontend/src/app/biometric-validation.js` exporting async functions:
- `fetchCsrfToken()` from dev server cookies if needed by auth.
- `login(username, password)` using `/api/auth/login`.
- `createAccountClient(name, phone)` using `/api/clients`.
- `enrollBiometric(clientId)` using `/api/biometrics/enroll`.
- `createAccount(clientId, month, year)`, `closeAccount(accountId)`, `verifyBiometric(clientId, accountId)`, `payAccount(accountId)`.

**Step 3:** Add script entry `biometric:validate` that runs Node to execute these steps against `5173` with its proxy.

**Verification:** `npm run biometric:validate` succeeds; each function returns JSON with expected status.

### Task 4: Validate fingerprint reader availability on host

**Objective:** Determine if this Linux host exposes any fingerprint device that a webapp/binary could use.

**Files:**
- Create: `scripts/check-fingerprint-reader.sh`

**Step 1:** Inspect `/sys/class/input` for `uinput` and biometric devices, `lsusb` for reader vendors, `dmesg` for USB biometric events, `v4l-ctl`/`fpcmock` if relevant.

**Step 2:** Script checks and prints:
- Connected USB devices
- Input devices containing `finger` or `biometric`
- Any `/dev/bus/usb` readers

**Step 3:** Run script. Provide output path.

**Step 4:** Document expected integration points in `BiometricService` for real SDK.

### Task 5: Document reader integration requirements

**Objective:** Define how to plug a real reader into `BiometricService` vs demo mode.

**Files:**
- Modify: `backend/app/services/biometric_service.py`
- Create: `docs/fingerprint-reader-integration.md`

**Step 1:** Check whether `BiometricService` currently raises or returns simulated matches when no reader is attached.

**Step 2:** Write integration doc with:
- Demo mode flags
- Expected interface changes for adding a library
- How to confirm enrollment/verification via real reader in dev
- Known-knowns about hardware support on Linux

**Step 3:** Update `BiometricService` to log a distinct warning when reader is unavailable and fallback to demo, without changing default behavior.

Validation: re-run Task 2 smoke test and ensure same pass state.

## Tests / Validation

- `cd /root/restaurante/backend && USE_POSTGRES_TESTS=true pytest tests/test_biometric_smoke.py -v`
- `cd /root/restaurante/frontend && npm run biometric:validate`
- `bash scripts/check-fingerprint-reader.sh`

## Risks, Tradeoffs, and Open Questions

- Real biometric SDK integration is out of scope if no reader is available; plan keeps demo mode intact.
- Biometric verification endpoint may restrict demo; if so, backend fallback path must be explicit.
- Frontend validation script depends on dev server cookies/proxy; may need `localhost` instead of external IP depending on `vite.config.js`.
- Hardware validation is inform-only unless a physical reader is present; script is read-only and will not mutate state.
