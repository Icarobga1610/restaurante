import os
import sys
import json
import logging
import uuid
from contextlib import asynccontextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from orjson import dumps as orjson_dumps
from orjson import OPT_NON_STR_KEYS
from orjson import OPT_UTC_Z
from collections import defaultdict
from time import time
from sqlalchemy import inspect, text

from app.utils import utcnow
from app.database import engine, Base, get_db
from app.models.user import User, Role
from app.models.payment_method import PaymentMethod
from app.auth.auth import hash_password

# Import all route modules
from app.routes.auth_routes import router as auth_router
from app.routes.client_routes import router as client_router
from app.routes.product_routes import router as product_router
from app.routes.order_routes import router as order_router
from app.routes.monthly_account_routes import router as monthly_account_router
from app.routes.signature_routes import router as signature_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.insight_routes import router as insight_router
from app.routes.audit_routes import router as audit_router
from app.routes.biometric_routes import router as biometric_router
from app.routes.supplier_routes import router as supplier_router
from app.routes.stock_routes import router as stock_router
from app.routes.recipe_routes import router as recipe_router
from app.routes.purchase_routes import router as purchase_router
from app.routes.table_routes import router as table_router
from app.routes.tab_routes import router as tab_router
from app.routes.cash_routes import router as cash_router
from app.routes.expense_routes import router as expense_router
from app.routes.finance_routes import router as finance_router
from app.routes.payment_method_routes import router as payment_method_router
from app.routes.kitchen_routes import router as kitchen_router
from app.routes.delivery_routes import router as delivery_router


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return orjson_dumps(
            content,
            option=OPT_NON_STR_KEYS | OPT_UTC_Z,
        )


class ProblemResponse(JSONResponse):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, content={"detail": detail})


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = req_id

        def with_request_id(record: logging.LogRecord) -> bool:
            record.request_id = getattr(request.state, "request_id", None)
            return True

        logger.addFilter(with_request_id)
        try:
            response = await call_next(request)
        finally:
            logger.removeFilter(with_request_id)

        response.headers["x-request-id"] = req_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("x-content-type-options", "nosniff")
        response.headers.setdefault("x-frame-options", "DENY")
        response.headers.setdefault("referrer-policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("x-request-id", getattr(request.state, "request_id", ""))
        return response


# Simple in-memory rate limiting sensitive auth endpoints
class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, login_paths=("/api/auth/login",)) -> None:
        super().__init__(app)
        self.login_paths = set(login_paths)
        self.window_seconds = 60
        self.max_requests = 20
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path not in self.login_paths or request.method != "POST":
            return await call_next(request)

        client_host = (request.client.host if request.client else "unknown")
        key = f"{client_host}::{path}"
        now = time()
        window_start = now - self.window_seconds
        hits = self._hits[key]
        hits[:] = [t for t in hits if t > window_start]
        if len(hits) >= self.max_requests:
            logger.warning(
                "Rate limit hit",
                extra={"path": path, "ip": client_host, "request_id": getattr(request.state, "request_id", None)},
            )
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Try again shortly."})
        hits.append(now)
        return await call_next(request)


# Structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        extra_data = getattr(record, "extra", {})
        if isinstance(extra_data, dict):
            log_entry.update({k: v for k, v in extra_data.items() if k not in log_entry})
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("restaurante")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


logger = setup_logging()


def _ensure_incremental_columns() -> None:
    """Add safe additive columns for existing local databases."""
    inspector = inspect(engine)
    existing = {
        table: {column["name"] for column in inspector.get_columns(table)}
        for table in ("clients", "monthly_accounts")
        if inspector.has_table(table)
    }
    statements = []
    if "clients" in existing and "payment_day" not in existing["clients"]:
        statements.append("ALTER TABLE clients ADD COLUMN payment_day INTEGER")
    if "monthly_accounts" in existing and "due_date" not in existing["monthly_accounts"]:
        statements.append("ALTER TABLE monthly_accounts ADD COLUMN due_date DATE")

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application", extra={"event": "startup"})
    Base.metadata.create_all(bind=engine)
    _ensure_incremental_columns()
    _seed_initial_data()
    _seed_payment_methods()
    logger.info("Application started successfully", extra={"event": "startup_complete"})
    yield
    logger.info("Application shutting down", extra={"event": "shutdown"})


app = FastAPI(
    title="Restaurante Conta Mensal - API",
    description="Sistema de gestão de restaurante com controle de conta mensal para clientes",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthRateLimitMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    status = getattr(exc, "status_code", 500)
    detail = str(exc) if status != 500 else "Internal server error. Please check logs."
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
            "status_code": status,
            "error": str(exc),
        },
        exc_info=True,
    )
    return ProblemResponse(status_code=status, detail=detail)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = utcnow()
    response = await call_next(request)
    duration = (utcnow() - start).total_seconds()
    logger.info(
        "HTTP Request",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "ip": request.client.host if request.client else None,
        },
    )
    return response


# Include routers
app.include_router(auth_router)
app.include_router(client_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(monthly_account_router)
app.include_router(signature_router)
app.include_router(dashboard_router)
app.include_router(insight_router)
app.include_router(audit_router)
app.include_router(biometric_router)
app.include_router(supplier_router)
app.include_router(stock_router)
app.include_router(recipe_router)
app.include_router(purchase_router)
app.include_router(table_router)
app.include_router(tab_router)
app.include_router(cash_router)
app.include_router(expense_router)
app.include_router(finance_router)
app.include_router(payment_method_router)
app.include_router(kitchen_router)
app.include_router(delivery_router)

@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "timestamp": utcnow().isoformat()}


def _seed_initial_data():
    """Seed default roles and admin user."""
    from sqlalchemy.orm import Session
    from app.database import SessionLocal

    db: Session = SessionLocal()
    try:
        # Check if roles exist
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            logger.info("Database already has data, skipping seed", extra={"event": "seed_skip"})
            return

        logger.info("Seeding initial data", extra={"event": "seed_start"})

        # Create roles
        roles = [
            Role(name="admin", description="Administrador - acesso total ao sistema"),
            Role(name="attendant", description="Atendente - lançar pedidos e consultar clientes"),
            Role(name="financial", description="Financeiro - fechar contas, assinar, pagamentos"),
        ]
        for role in roles:
            db.add(role)
        db.flush()

        # Create default admin user (password: admin123)
        admin = User(
            username="admin",
            email="admin@restaurante.com",
            password_hash=hash_password("admin123"),
            full_name="Administrador",
            role_id=roles[0].id,
            is_active=True,
        )

        attendant = User(
            username="atendente",
            email="atendente@restaurante.com",
            password_hash=hash_password("atendente123"),
            full_name="Atendente Padrão",
            role_id=roles[1].id,
            is_active=True,
        )

        financial = User(
            username="financeiro",
            email="financeiro@restaurante.com",
            password_hash=hash_password("financeiro123"),
            full_name="Financeiro Padrão",
            role_id=roles[2].id,
            is_active=True,
        )

        db.add_all([admin, attendant, financial])
        db.commit()

        logger.info(
            "Initial data seeded successfully",
            extra={
                "event": "seed_complete",
                "roles": [r.name for r in roles],
                "users": ["admin", "atendente", "financeiro"],
            },
        )
    except Exception:
        db.rollback()
        logger.error("Error seeding initial data", exc_info=True)
    finally:
        db.close()


def _seed_payment_methods():
    """Seed default payment methods."""
    from sqlalchemy.orm import Session
    from app.database import SessionLocal

    db: Session = SessionLocal()
    try:
        if db.query(PaymentMethod).count() > 0:
            return
        db.add_all([
            PaymentMethod(code="pix", name="Pix", is_default=True, is_active=True),
            PaymentMethod(code="cash", name="Dinheiro", is_active=True),
            PaymentMethod(code="debit", name="Cartão de Débito", is_active=True),
            PaymentMethod(code="credit", name="Cartão de Crédito", is_active=True),
            PaymentMethod(code="transfer", name="Transferência", is_active=True),
        ])
        db.commit()
        logger.info("Default payment methods seeded", extra={"event": "payment_methods_seed"})
    except Exception:
        db.rollback()
        logger.error("Error seeding payment methods", exc_info=True)
    finally:
        db.close()
