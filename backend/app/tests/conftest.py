"""Pytest fixtures for integration tests."""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# TestClient shares a single client host, so the per-host auth rate limit would
# throttle the suite. Disable it for tests (must be set before importing app).
os.environ["AUTH_RATE_LIMIT_ENABLED"] = "false"

from app.database import Base, get_db
from app.main import app
from app.models.user import User, Role
from app.models.client import Client
from app.models.product import Product
from app.auth.auth import hash_password

# Use SQLite by default; switch to Postgres with USE_POSTGRES_TESTS=true
_raw_test_db = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://restaurante:restaurante@localhost:5432/restaurante"
    if os.getenv("USE_POSTGRES_TESTS", "false").lower() == "true"
    else "sqlite:///./test_restaurante.db",
)
# psycopg v3 works with postgresql+psycopg dialect
TEST_DATABASE_URL = _raw_test_db.replace("postgresql://", "postgresql+psycopg://")
if TEST_DATABASE_URL.startswith("postgres"):
    engine = create_engine(TEST_DATABASE_URL)
else:
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency with test DB."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db_session_factory():
    """Return the test sessionmaker so fixtures can open short-lived sessions."""
    return TestingSessionLocal


@pytest.fixture(autouse=True)
def setup_database(db_session_factory):
    """Create tables before each test and drop them after.

    Also seeds the default payment methods, since several endpoints
    (e.g. monthly-account payment) depend on them existing.
    """
    Base.metadata.create_all(bind=engine)
    session = db_session_factory()
    try:
        from app.models.payment_method import PaymentMethod
        if session.query(PaymentMethod).count() == 0:
            session.add_all([
                PaymentMethod(code="pix", name="Pix", is_default=True, is_active=True),
                PaymentMethod(code="cash", name="Dinheiro", is_active=True),
                PaymentMethod(code="debit", name="Cartão de Débito", is_active=True),
                PaymentMethod(code="credit", name="Cartão de Crédito", is_active=True),
                PaymentMethod(code="transfer", name="Transferência", is_active=True),
            ])
            session.commit()
    finally:
        session.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(setup_database):
    """Provide a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Provide a TestClient with overridden database dependency."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def roles(db):
    """Create default roles."""
    role_list = [
        Role(name="admin", description="Admin"),
        Role(name="attendant", description="Attendant"),
        Role(name="financial", description="Financial"),
    ]
    for r in role_list:
        db.add(r)
    db.commit()
    for r in role_list:
        db.refresh(r)
    return {r.name: r for r in role_list}


@pytest.fixture
def admin_user(db, roles):
    """Create an admin user and return credentials."""
    user = User(
        username="admin_test",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        full_name="Admin Test",
        role_id=roles["admin"].id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"username": "admin_test", "password": "admin123", "user": user}


@pytest.fixture
def attendant_user(db, roles):
    """Create an attendant user."""
    user = User(
        username="attendant_test",
        email="attendant@test.com",
        password_hash=hash_password("attendant123"),
        full_name="Attendant Test",
        role_id=roles["attendant"].id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"username": "attendant_test", "password": "attendant123", "user": user}


@pytest.fixture
def financial_user(db, roles):
    """Create a financial user."""
    user = User(
        username="financial_test",
        email="financial@test.com",
        password_hash=hash_password("financial123"),
        full_name="Financial Test",
        role_id=roles["financial"].id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"username": "financial_test", "password": "financial123", "user": user}


@pytest.fixture
def admin_token(client, admin_user):
    """Get an auth token for the admin user."""
    response = client.post(
        "/api/auth/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def attendant_token(client, attendant_user):
    """Get an auth token for the attendant user."""
    response = client.post(
        "/api/auth/login",
        json={"username": attendant_user["username"], "password": attendant_user["password"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def financial_token(client, financial_user):
    """Get an auth token for the financial user."""
    response = client.post(
        "/api/auth/login",
        json={"username": financial_user["username"], "password": financial_user["password"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_header(admin_token):
    """Return authorization header with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_client(db):
    """Create a sample client in the database."""
    client = Client(
        name="Test Client",
        document="12345678901",
        phone="11999999999",
        company_sector="Tech",
        status="active",
        monthly_limit=1000.0,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@pytest.fixture
def sample_product(db):
    """Create a sample product in the database."""
    product = Product(
        name="Test Product",
        category="Bebidas",
        price=10.50,
        estimated_cost=5.00,
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product