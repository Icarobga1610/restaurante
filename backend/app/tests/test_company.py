"""Tests for corporate member management and grouped monthly billing."""

from datetime import datetime


def test_company_can_link_existing_client(client, auth_header):
    company = client.post(
        "/api/companies",
        json={
            "legal_name": "Acme Corporate Ltda",
            "trade_name": "Acme",
            "document": "12345678000191",
            "monthly_limit": 10000,
            "payment_day": 10,
        },
        headers=auth_header,
    )
    assert company.status_code == 201
    company_data = company.json()
    assert company_data["member_count"] == 0

    person = client.post(
        "/api/clients",
        json={"name": "Pessoa da Acme", "phone": "11999998888"},
        headers=auth_header,
    )
    assert person.status_code == 201

    linked = client.post(
        f"/api/companies/{company_data['id']}/members/{person.json()['id']}",
        headers=auth_header,
    )
    assert linked.status_code == 200
    assert linked.json()["company_id"] == company_data["id"]
    assert len(client.get(f"/api/companies/{company_data['id']}/members", headers=auth_header).json()) == 1


def test_company_account_can_close_and_pay(client, auth_header):
    company = client.post(
        "/api/companies",
        json={
            "legal_name": "Billing Company Ltda",
            "document": "98765432000199",
        },
        headers=auth_header,
    ).json()
    period = datetime.now()
    account = client.post(
        "/api/company-monthly-accounts",
        json={"company_id": company["id"], "month": period.month, "year": period.year},
        headers=auth_header,
    )
    assert account.status_code == 201
    account_id = account.json()["id"]

    closed = client.post(f"/api/company-monthly-accounts/{account_id}/close", headers=auth_header)
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert closed.json()["total"] == 0

    paid = client.post(
        f"/api/company-monthly-accounts/{account_id}/pay",
        json={"payment_method": "pix"},
        headers=auth_header,
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
