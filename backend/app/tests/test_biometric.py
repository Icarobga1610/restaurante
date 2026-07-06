"""Tests for biometric enrollment and verification flow (replaces digital signature)."""
import pytest
from datetime import datetime
from app.utils import utcnow

from app.models.biometric_profile import BiometricProfile
from app.models.biometric_consent import BiometricConsent
from app.models.biometric_event import BiometricEvent


def test_biometric_enroll_client(client, admin_token, sample_client):
    """Test enrolling a client's fingerprint (demo mode)."""
    response = client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == sample_client.id
    assert data["is_active"] is True
    assert data["algorithm"] == "demo_sha256"
    assert data["fingers_enrolled"] == 1


def test_biometric_enroll_duplicate_fails(client, admin_token, sample_client):
    """Test that enrolling a client twice fails."""
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "já possui cadastro" in response.json()["detail"]


def test_biometric_enroll_creates_consent_and_event(client, admin_token, sample_client, db):
    """Test that enrollment automatically creates consent record and audit event."""
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Check consent was created
    profile = db.query(BiometricProfile).filter(
        BiometricProfile.client_id == sample_client.id
    ).first()
    assert profile is not None

    consents = db.query(BiometricConsent).filter(
        BiometricConsent.profile_id == profile.id
    ).all()
    assert len(consents) >= 1
    assert consents[0].purpose == "both"
    assert consents[0].is_active is True

    # Check events were created
    events = db.query(BiometricEvent).filter(
        BiometricEvent.profile_id == profile.id
    ).all()
    assert len(events) >= 1
    assert events[0].event_type == "enroll"


def test_biometric_list_profiles(client, admin_token, sample_client):
    """Test listing biometric profiles."""
    # Enroll a client first
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = client.get(
        "/api/biometrics/profiles",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["client_name"] == sample_client.name


def test_biometric_verify_monthly_account(client, admin_token, financial_token, sample_client, sample_product):
    """Test biometric verification for monthly closing (replaces old signature flow)."""
    now = utcnow()

    # Create order
    client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [{
                "product_id": sample_product.id,
                "product_name": sample_product.name,
                "quantity": 1,
                "unit_price": 100.0,
                "total": 100.0,
            }],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Enroll biometrics
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Create and close monthly account
    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )

    # Verify biometrics
    response = client.post(
        f"/api/monthly-accounts/{account['id']}/biometric-verify",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "confirmed_by_biometrics"
    assert data["account_id"] == account["id"]


def test_biometric_verify_updates_account_status(client, admin_token, financial_token, sample_client, sample_product):
    """Test that biometric verification updates account status."""
    now = utcnow()

    # Create order
    client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [{
                "product_id": sample_product.id,
                "product_name": sample_product.name,
                "quantity": 1,
                "unit_price": 50.0,
                "total": 50.0,
            }],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Enroll biometrics
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Create, close, verify
    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )

    client.post(
        f"/api/monthly-accounts/{account['id']}/biometric-verify",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )

    # Check account status
    response = client.get(
        f"/api/monthly-accounts/{account['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.json()["status"] == "confirmed_by_biometrics"
    assert response.json()["biometric_verification_id"] is not None


def test_biometric_verify_unclosed_account_fails(client, admin_token, financial_token, sample_client):
    """Test that verifying an open (unclosed) account fails."""
    now = utcnow()

    # Enroll biometrics first
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    response = client.post(
        f"/api/monthly-accounts/{account['id']}/biometric-verify",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 400
    assert "must be closed" in response.json()["detail"]


def test_biometric_without_enrollment_fails(client, admin_token, financial_token, sample_client):
    """Test that verifying without enrollment fails."""
    now = utcnow()

    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )

    response = client.post(
        f"/api/monthly-accounts/{account['id']}/biometric-verify",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 400
    assert "não possui cadastro biométrico" in response.json()["detail"]


def test_attendant_cannot_enroll_or_verify(client, attendant_token, sample_client):
    """Test that an attendant cannot enroll or verify biometrics."""
    # Try enroll
    response = client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {attendant_token}"},
    )
    assert response.status_code == 403

    # Try verify
    response = client.post(
        "/api/biometrics/verify",
        json={"client_id": sample_client.id, "monthly_account_id": 1},
        headers={"Authorization": f"Bearer {attendant_token}"},
    )
    assert response.status_code == 403


def test_biometric_events_list(client, admin_token, sample_client):
    """Test listing biometric events."""
    # Enroll (creates events)
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = client.get(
        "/api/biometrics/events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert events[0]["event_type"] in ("enroll", "verify_success", "verify_fail")
