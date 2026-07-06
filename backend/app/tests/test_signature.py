"""Legacy digital signature tests — DEPRECATED.

The signature/canvas flow has been replaced by biometric (fingerprint) verification.
These tests are kept for reference but will always be skipped.
"""
import pytest
from datetime import datetime
from app.utils import utcnow

pytestmark = pytest.mark.skip(reason="Signature flow replaced by biometric verification")

SAMPLE_SIGNATURE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def _setup_account(client, admin_token, financial_token, sample_client, sample_product):
    now = utcnow()
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
    return account


def test_sign_monthly_account(client, admin_token, financial_token, sample_client, sample_product):
    account = _setup_account(client, admin_token, financial_token, sample_client, sample_product)
    response = client.post(
        f"/api/monthly-accounts/{account['id']}/sign",
        json={
            "monthly_account_id": account["id"],
            "client_id": sample_client.id,
            "signature_data": SAMPLE_SIGNATURE,
            "signed_value": 50.0,
            "device_info": "Mozilla/5.0 Test Browser",
        },
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 200


def test_signature_updates_account_status(client, admin_token, financial_token, sample_client, sample_product):
    pass  # Deprecated


def test_signature_verification_hash(client, admin_token, financial_token, sample_client, sample_product):
    pass  # Deprecated


def test_signature_linked_to_closing(client, admin_token, financial_token, sample_client, sample_product):
    pass  # Deprecated


def test_sign_uncosed_account_fails(client, admin_token, financial_token, sample_client):
    pass  # Deprecated


def test_attendant_cannot_sign(client, attendant_token, admin_token, financial_token, sample_client, sample_product):
    pass  # Deprecated
