"""Tests for monthly account operations: creation, closing, total calculation, payment."""
import pytest
from datetime import datetime
from app.utils import utcnow


def test_create_monthly_account(client, admin_token, sample_client):
    """Test creating a monthly account."""
    now = utcnow()
    response = client.post(
        "/api/monthly-accounts",
        json={
            "client_id": sample_client.id,
            "month": now.month,
            "year": now.year,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == sample_client.id
    assert data["month"] == now.month
    assert data["year"] == now.year
    assert data["status"] == "open"
    assert data["total"] == 0.0


def test_create_duplicate_monthly_account(client, admin_token, sample_client):
    """Test creating a duplicate monthly account fails."""
    now = utcnow()
    client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_close_monthly_account(client, admin_token, financial_token, sample_client, sample_product):
    """Test closing a monthly account calculates total from orders."""
    now = utcnow()

    # Create orders for the client in the current month
    client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 2,
                    "unit_price": 25.0,
                    "total": 50.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 3,
                    "unit_price": 10.0,
                    "total": 30.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Create monthly account
    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # Close the account (requires financial or admin)
    response = client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={"notes": "Fechamento mensal de testes"},
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "closed"
    assert data["total"] == pytest.approx(80.0)  # 50 + 30
    assert data["notes"] == "Fechamento mensal de testes"
    assert data["closed_by_name"] is not None


def test_monthly_total_calculation(client, admin_token, financial_token, sample_client, sample_product):
    """Test that monthly total correctly sums all orders."""
    now = utcnow()

    # Create 3 orders with different values
    amounts = [45.0, 32.50, 78.20]
    for amt in amounts:
        client.post(
            "/api/orders",
            json={
                "client_id": sample_client.id,
                "items": [
                    {
                        "product_id": sample_product.id,
                        "product_name": sample_product.name,
                        "quantity": 1,
                        "unit_price": amt,
                        "total": amt,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    response = client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == pytest.approx(sum(amounts))


def test_close_open_account_only(client, admin_token, financial_token, sample_client):
    """Test that closing an already closed account fails."""
    now = utcnow()

    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # Close once
    client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )

    # Try closing again
    response = client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 400
    assert "already" in response.json()["detail"]


def test_pay_monthly_account(client, admin_token, financial_token, sample_client, sample_product):
    """Test paying a confirmed_by_biometrics monthly account."""
    now = utcnow()

    # Create order
    client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 1,
                    "unit_price": 100.0,
                    "total": 100.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Create and close account
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

    # Confirm with biometrics (instead of old signature)
    # First enroll
    client.post(
        "/api/biometrics/enroll",
        json={"client_id": sample_client.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Then verify
    client.post(
        f"/api/monthly-accounts/{account['id']}/biometric-verify",
        json={},
        headers={"Authorization": f"Bearer {financial_token}"},
    )

    # Pay
    response = client.post(
        f"/api/monthly-accounts/{account['id']}/pay",
        json={"payment_method": "pix"},
        headers={"Authorization": f"Bearer {financial_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "paid"
    assert response.json()["paid_by_name"] is not None


def test_attendant_cannot_close_account(client, attendant_token, sample_client):
    """Test that an attendant cannot close a monthly account (permissions)."""
    now = utcnow()
    account = client.post(
        "/api/monthly-accounts",
        json={"client_id": sample_client.id, "month": now.month, "year": now.year},
        headers={"Authorization": f"Bearer {attendant_token}"},
    ).json()

    response = client.post(
        f"/api/monthly-accounts/{account['id']}/close",
        json={},
        headers={"Authorization": f"Bearer {attendant_token}"},
    )
    assert response.status_code == 403
