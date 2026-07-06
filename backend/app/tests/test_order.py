"""Tests for order creation and management."""
import pytest


def test_create_order(client, auth_header, admin_token, sample_client, sample_product):
    """Test creating an order with items."""
    response = client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "notes": "Pedido de teste",
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 2,
                    "unit_price": sample_product.price,
                    "total": sample_product.price * 2,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == sample_client.id
    assert data["client_name"] == sample_client.name
    assert data["status"] == "confirmed"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_name"] == sample_product.name
    assert data["items"][0]["quantity"] == 2
    assert data["notes"] == "Pedido de teste"


def test_create_order_with_multiple_items(client, admin_token, sample_client, sample_product):
    """Test creating an order with multiple items."""
    # Create another product
    from app.tests.conftest import override_get_db, TestingSessionLocal
    from app.models.product import Product

    db = TestingSessionLocal()
    try:
        prod2 = Product(name="Second Item", category="Porções", price=30.0, is_active=True)
        db.add(prod2)
        db.commit()
        db.refresh(prod2)
        prod2_id = prod2.id
    finally:
        db.close()

    response = client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 1,
                    "unit_price": sample_product.price,
                    "total": sample_product.price,
                },
                {
                    "product_id": prod2_id,
                    "product_name": "Second Item",
                    "quantity": 3,
                    "unit_price": 30.0,
                    "total": 90.0,
                },
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == pytest.approx(sample_product.price + 90.0)


def test_create_order_inactive_client(client, admin_token, sample_client, sample_product):
    """Test creating an order for inactive client fails."""
    # Deactivate client
    client.put(
        f"/api/clients/{sample_client.id}",
        json={"status": "inactive"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 1,
                    "unit_price": 10.0,
                    "total": 10.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"]


def test_create_order_empty_items(client, admin_token, sample_client):
    """Test creating an order without items fails."""
    response = client.post(
        "/api/orders",
        json={"client_id": sample_client.id, "items": []},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "at least one item" in response.json()["detail"]


def test_create_order_nonexistent_client(client, admin_token, sample_product):
    """Test creating an order for a non-existent client fails."""
    response = client.post(
        "/api/orders",
        json={
            "client_id": 99999,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 1,
                    "unit_price": 10.0,
                    "total": 10.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


def test_list_orders(client, admin_token, sample_client, sample_product):
    """Test listing orders."""
    # Create a couple orders
    for i in range(3):
        client.post(
            "/api/orders",
            json={
                "client_id": sample_client.id,
                "items": [
                    {
                        "product_id": sample_product.id,
                        "product_name": sample_product.name,
                        "quantity": 1,
                        "unit_price": 10.0,
                        "total": 10.0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    response = client.get("/api/orders", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_cancel_order(client, admin_token, sample_client, sample_product):
    """Test cancelling an order."""
    created = client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 1,
                    "unit_price": 10.0,
                    "total": 10.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    response = client.put(
        f"/api/orders/{created['id']}",
        json={"status": "cancelled"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_total_calculation(client, admin_token, sample_client, sample_product):
    """Test that order total is correctly calculated."""
    response = client.post(
        "/api/orders",
        json={
            "client_id": sample_client.id,
            "items": [
                {
                    "product_id": sample_product.id,
                    "product_name": sample_product.name,
                    "quantity": 3,
                    "unit_price": 15.50,
                    "total": 46.50,
                },
                {
                    "product_id": sample_product.id,
                    "product_name": "Outro Item",
                    "quantity": 2,
                    "unit_price": 22.30,
                    "total": 44.60,
                },
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["total"] == pytest.approx(46.50 + 44.60)
