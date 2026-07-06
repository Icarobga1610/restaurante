"""Tests for client CRUD operations."""
import pytest


def test_create_client(client, auth_header):
    """Test creating a new client."""
    response = client.post(
        "/api/clients",
        json={
            "name": "Empresa Exemplo Ltda",
            "document": "12345678000199",
            "phone": "11988887777",
            "company_sector": "Tecnologia",
            "monthly_limit": 5000.00,
            "notes": "Cliente VIP",
        },
        headers=auth_header,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Empresa Exemplo Ltda"
    assert data["document"] == "12345678000199"
    assert data["phone"] == "11988887777"
    assert data["company_sector"] == "Tecnologia"
    assert data["monthly_limit"] == 5000.0
    assert data["status"] == "active"
    assert "id" in data


def test_create_client_minimal_fields(client, auth_header):
    """Test creating a client with only required fields."""
    response = client.post(
        "/api/clients",
        json={"name": "Cliente Simples", "phone": "11977776666"},
        headers=auth_header,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cliente Simples"
    assert data["phone"] == "11977776666"
    assert data["status"] == "active"
    assert data["monthly_limit"] is None


def test_create_client_duplicate_document(client, auth_header):
    """Test that creating a client with duplicate document fails."""
    client.post(
        "/api/clients",
        json={"name": "Cliente 1", "document": "11122233344", "phone": "11911112222"},
        headers=auth_header,
    )
    response = client.post(
        "/api/clients",
        json={"name": "Cliente 2", "document": "11122233344", "phone": "11933334444"},
        headers=auth_header,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_client_without_auth(client):
    """Test that creating a client without auth fails."""
    response = client.post(
        "/api/clients",
        json={"name": "No Auth", "phone": "11955556666"},
    )
    assert response.status_code == 403


def test_list_clients(client, auth_header):
    """Test listing all clients."""
    # Create two clients
    client.post(
        "/api/clients",
        json={"name": "Alpha", "phone": "11911111111"},
        headers=auth_header,
    )
    client.post(
        "/api/clients",
        json={"name": "Beta", "phone": "11922222222"},
        headers=auth_header,
    )
    response = client.get("/api/clients", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_client_by_id(client, auth_header):
    """Test getting a single client by ID."""
    created = client.post(
        "/api/clients",
        json={"name": "Busca Cliente", "phone": "11933332222"},
        headers=auth_header,
    ).json()
    response = client.get(f"/api/clients/{created['id']}", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["name"] == "Busca Cliente"


def test_get_client_not_found(client, auth_header):
    """Test getting a non-existent client returns 404."""
    response = client.get("/api/clients/99999", headers=auth_header)
    assert response.status_code == 404


def test_update_client(client, auth_header):
    """Test updating a client."""
    created = client.post(
        "/api/clients",
        json={"name": "Original", "phone": "11944445555"},
        headers=auth_header,
    ).json()
    response = client.put(
        f"/api/clients/{created['id']}",
        json={"name": "Updated Name", "monthly_limit": 2000.0},
        headers=auth_header,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["monthly_limit"] == 2000.0


def test_deactivate_client(client, auth_header):
    """Test deactivating a client."""
    created = client.post(
        "/api/clients",
        json={"name": "To Deactivate", "phone": "11955556666"},
        headers=auth_header,
    ).json()
    response = client.delete(f"/api/clients/{created['id']}", headers=auth_header)
    assert response.status_code == 200
    # Verify it's now inactive
    get_resp = client.get(f"/api/clients/{created['id']}", headers=auth_header)
    assert get_resp.json()["status"] == "inactive"
