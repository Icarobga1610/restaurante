from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, Role
from app.schemas.schemas import LoginRequest, TokenResponse, UserCreate, UserOut, RoleOut
from app.auth.auth import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        # Log failed attempt
        AuditService(db).log(
            action="login_failed",
            entity_type="user",
            username=req.username,
            ip_address=request.client.host if request.client else None,
            details="Failed login attempt",
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")

    token = create_access_token(user.id, user.username, user.role_id)

    AuditService(db).log(
        action="login",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else None,
        details="User logged in",
    )

    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            role_id=user.role_id,
            role_name=user.role.name if user.role else None,
        ),
    )


@router.post("/users", response_model=UserOut)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users")

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role_id=data.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    AuditService(db).log(
        action="create",
        entity_type="user",
        entity_id=user.id,
        user_id=current_user.id,
        username=current_user.username,
        details=f"Created user {user.username}",
    )

    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role_id=user.role_id,
        role_name=user.role.name if user.role else None,
    )


@router.get("/users/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        role_id=current_user.role_id,
        role_name=current_user.role.name if current_user.role else None,
    )


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return roles
