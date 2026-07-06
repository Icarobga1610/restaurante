"""Tests for product CRUD operations."""


def test_create_product(client, auth_header):
    """Test creating a new product."""
    response = client.post(
        "/api/products",
        json={
            "name": "X-Burguer Especial",
            "category": "Lanches",
            "price": 25.90,
            "estimated_cost": 12.00,
            "is_active": True,
            "notes": "Produto mais vendido",
        },
        headers=auth_header,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "X-Burguer Especial"
    assert data["category"] == "Lanches"
    assert data["price"] == 25.9
    assert data["estimated_cost"] == 12.0
    assert data["is_active"] is True
    assert "id" in data


def test_create_product_minimal(client, auth_header):
    """Test creating a product with only required fields."""
    response = client.post(
        "/api/products",
        json={"name": "Coca-Cola", "category": "Bebidas", "price": 8.00},
        headers=auth_header,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Coca-Cola"
    assert data["price"] == 8.0
    assert data["is_active"] is True  # default


def test_list_products(client, auth_header):
    """Test listing products."""
    client.post(
        "/api/products",
        json={"name": "Produto A", "category": "Lanches", "price": 15.0},
        headers=auth_header,
    )
    client.post(
        "/api/products",
        json={"name": "Produto B", "category": "Bebidas", "price": 7.0},
        headers=auth_header,
    )
    response = client.get("/api/products", headers=auth_header)
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_list_products_filter_by_category(client, auth_header):
    """Test filtering products by category."""
    client.post(
        "/api/products",
        json={"name": "Hamburguer", "category": "Lanches", "price": 20.0},
        headers=auth_header,
    )
    client.post(
        "/api/products",
        json={"name": "Suco", "category": "Bebidas", "price": 10.0},
        headers=auth_header,
    )
    response = client.get("/api/products?category=Bebidas", headers=auth_header)
    assert response.status_code == 200
    for p in response.json():
        assert p["category"] == "Bebidas"


def test_get_product(client, auth_header):
    """Test getting a product by ID."""
    created = client.post(
        "/api/products",
        json={"name": "Produto Teste", "category": "Sobremesas", "price": 12.0},
        headers=auth_header,
    ).json()
    response = client.get(f"/api/products/{created['id']}", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["name"] == "Produto Teste"


def test_get_product_not_found(client, auth_header):
    """Test getting non-existent product returns 404."""
    response = client.get("/api/products/99999", headers=auth_header)
    assert response.status_code == 404


def test_update_product(client, auth_header):
    """Test updating a product."""
    created = client.post(
        "/api/products",
        json={"name": "Produto Original", "category": "Lanches", "price": 18.0},
        headers=auth_header,
    ).json()
    response = client.put(
        f"/api/products/{created['id']}",
        json={"name": "Produto Alterado", "price": 22.0},
        headers=auth_header,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Produto Alterado"
    assert data["price"] == 22.0


def test_deactivate_product(client, auth_header):
    """Test deactivating a product."""
    created = client.post(
        "/api/products",
        json={"name": "Produto Ativo", "category": "Lanches", "price": 15.0},
        headers=auth_header,
    ).json()
    response = client.delete(f"/api/products/{created['id']}", headers=auth_header)
    assert response.status_code == 200
    # Verify it's now inactive
    get_resp = client.get(f"/api/products/{created['id']}", headers=auth_header)
    assert get_resp.json()["is_active"] is False


def test_create_product_with_seasonality(client, auth_header):
    """Test creating a product with seasonality metadata."""
    response = client.post(
        "/api/products",
        json={
            "name": "Sorvete de Chocolate",
            "category": "Sobremesas",
            "price": 15.0,
            "seasonality": {"type": "seasonal", "months": [11, 12, 1, 2]},
        },
        headers=auth_header,
    )
    assert response.status_code == 201
    assert response.json()["seasonality"] == {"type": "seasonal", "months": [11, 12, 1, 2]}
