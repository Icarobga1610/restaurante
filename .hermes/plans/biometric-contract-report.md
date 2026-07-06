# Biometric Contract Report

## 1) Simulation vs Hardware
- `BiometricService.enroll_client` and `verify_client` are **simulated by default**.
- `BiometricService` creates `DemoBiometricReader()` when no reader is injected (`self.reader = reader or DemoBiometricReader()`).
- `DemoBiometricReader`:
  - `enroll()`: sleeps ~0.8s, returns `(True, sha256_hex, "demo_device_fingerprint_simulator")`.
  - `verify()`: sleeps ~0.8s, always succeeds with a fixed **92% confidence** score.
- Hardware is optional via abstraction: swap in a concrete `BiometricReader` implementation. No real SDK implementation exists in this repo yet.

## 2) Payloads and Return Values

### `POST /api/biometrics/enroll`
- **Auth**: required; roles `admin` or `financial` only.
- **Payload**: `{ "client_id": <int> }`
- **Success 200** (`BiometricProfileOut`):
  - `id`, `client_id`, `client_name`, `algorithm`, `fingers_enrolled`, `is_active`, `last_used_at`, `created_at`
- **400 cases**:
  - Client not found / not active
  - Active biometric profile already exists
  - Reader capture failure
- **Service return**: `(True, profile, "Digital cadastrada com sucesso")` or `(False, None, reason)`

### `POST /api/biometrics/verify`
- **Auth**: required; roles `admin` or `financial` only.
- **Payload**: `{ "client_id": <int>, "monthly_account_id": <int> }`
- **Pre-checks in route**:
  - client exists
  - monthly account exists and belongs to client
  - account status is `closed` or `confirmed_by_biometrics`
- **Success 200** (`BiometricVerifyResult`):
  - `success=True`, `message`, `account_id`, `status="confirmed_by_biometrics"`, `match_score=92`
- **400 cases**:
  - No active biometric profile
  - Consent missing for purpose `verification`
  - Decrypt error
  - Reader verify failure
  - Account not in correct status
- **Service return**: `(True, "confirmed_by_biometrics", message)` or `(False, None, reason)`

### `POST /api/monthly-accounts/{id}/biometric-verify`
- **Auth**: required; roles `admin` or `financial` only.
- **Body**: none
- **Success 200**:
  - `{ "success": true, "message": "...", "account_id": ..., "status": "confirmed_by_biometrics" }`
- **404**: account not found.
- **400**: account wrong status OR any biometric business error.
- **Notable path for the earlier smoke-test 400**: it happens if:
  - account status != `closed`/`confirmed_by_biometrics`
  - OR client has no active biometric profile
  - OR consent revoked
  - OR card read/verify failed

## 3) What causes `"Cliente não possui cadastro biométrico"`
- Returned by `BiometricService.verify_client` when no active `BiometricProfile` exists for the client:
  - `self.db.query(BiometricProfile).filter(BiometricProfile.client_id == client_id, BiometricProfile.is_active == True).first()` is `None`.

This surfaces through both `/api/biometrics/verify` and `/api/monthly-accounts/{id}/biometric-verify` as `400`.

## 4) `/verify-identity` Note
- **`/verify-identity` is not implemented** anywhere in this backend. No route, schema, or service method for that path was found.

## 5) Gaps / Integration Notes
- **Demo default**: without DI wiring, verification always succeeds with a fake 92% score; not suitable for real identity checks.
- **Missing real reader**: no concrete `BiometricReader` SDK implementation exists yet, only `DemoBiometricReader`.
- **Hardcoded demo score in `/verify`**: route always returns `match_score=92` instead of the actual reader result from `verify_client`.
- **Mode switch not config-driven**: use of demo vs real reader depends on manual DI injection, not an environment/flag.
- **No `/verify-identity` endpoint**: if the frontend or tests expect it, that contract is missing.
