"""Smoke test for the biometric flow using requests against the running API."""

import os
from datetime import datetime

import pytest
import requests


BASE_URL = os.getenv("RESTAURANTE_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
API = f"{BASE_URL}/api"


def test_biometric_smoke_flow():
    # 1) Login as admin and obtain access token
    login = requests.post(
        f"{API}/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # 2) Create a client with is_account_client=true
    import uuid
    unique_doc = f"test_doc_smoke_{uuid.uuid4().hex[:8]}"
    now = datetime.now()
    client_payload = {
        "name": "Biometric Smoke Client",
        "document": unique_doc,
        "phone": "11999999999",
        "company_sector": "Tech",
        "monthly_limit": 1000.0,
        "is_account_client": True,
        "status": "active",
    }
    client_resp = requests.post(f"{API}/clients", json=client_payload, headers=headers)
    assert client_resp.status_code == 201, client_resp.text
    client_data = client_resp.json()
    client_id = client_data["id"]
    assert client_data["name"] == client_payload["name"]
    assert client_data["status"] == "active"
    assert client_data["document"] == client_payload["document"]

    # 3) Create a monthly account
    account_resp = requests.post(
        f"{API}/monthly-accounts",
        json={"client_id": client_id, "month": now.month, "year": now.year},
        headers=headers,
    )
    assert account_resp.status_code == 201, account_resp.text
    account_data = account_resp.json()
    account_id = account_data["id"]
    assert account_data["status"] == "open"
    assert account_data["client_id"] == client_id

    # 4) Create an order linked to the account/month
    order_resp = requests.post(
        f"{API}/orders",
        json={
            "client_id": client_id,
            "tab_id": account_id,
            "notes": "smoke order",
            "items": [
                {
                    "product_id": 1,
                    "product_name": "Smoke Item",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "total": 10.0,
                }
            ],
        },
        headers=headers,
    )
    assert order_resp.status_code == 201, order_resp.text
    order_data = order_resp.json()
    order_id = order_data["id"]
    assert order_data["client_id"] == client_id

    # Confirm order exists and is linked
    order_get = requests.get(
        f"{API}/orders/{order_id}",
        headers=headers,
    )
    assert order_get.status_code == 200
    assert order_get.json()["id"] == order_id

    # 5) Close the account using admin token
    close_resp = requests.post(
        f"{API}/monthly-accounts/{account_id}/close",
        json={},
        headers=headers,
    )
    assert close_resp.status_code == 200, close_resp.text
    close_data = close_resp.json()
    assert close_data["status"] == "closed"
    assert close_data["id"] == account_id

    # 6) Enroll biometrics for the client
    enroll_resp = requests.post(
        f"{API}/biometrics/enroll",
        json={"client_id": client_id},
        headers=headers,
    )
    assert enroll_resp.status_code == 200, enroll_resp.text
    enroll_data = enroll_resp.json()
    assert enroll_data["client_id"] == client_id
    assert enroll_data["is_active"] is True
    assert enroll_data["algorithm"] == "demo_sha256"
    assert enroll_data["fingers_enrolled"] == 1

    # 7) Verify biometrics for the account using /biometrics/verify
    verify_resp = requests.post(
        f"{API}/biometrics/verify",
        json={"client_id": client_id, "monthly_account_id": account_id},
        headers=headers,
    )
    assert verify_resp.status_code == 200, verify_resp.text
    verify_data = verify_resp.json()
    assert verify_data["success"] is True
    assert verify_data["account_id"] == account_id
    assert verify_data["status"] == "confirmed_by_biometrics"

    # Re-fetch account to confirm persisted status
    account_get = requests.get(
        f"{API}/monthly-accounts/{account_id}",
        headers=headers,
    )
    assert account_get.status_code == 200
    assert account_get.json()["status"] == "confirmed_by_biometrics"
    assert account_get.json()["id"] == account_id

    # 8) Pay the account
    pay_resp = requests.post(
        f"{API}/monthly-accounts/{account_id}/pay",
        json={"payment_method": "pix"},
        headers=headers,
    )
    assert pay_resp.status_code == 200, pay_resp.text
    pay_data = pay_resp.json()
    assert pay_data["status"] == "paid"
    assert pay_data["id"] == account_id
    assert pay_data["paid_by_name"] in {"Administrador", None}
