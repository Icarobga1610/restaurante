from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, Role
from app.schemas.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserOut,
    RoleOut,
    RefreshRequest,
    LogoutRequest,
)
from app.auth.auth import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
)
from app.auth.token_store import token_store
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

    access_token = create_access_token(user.id, user.username, user.role_id)
    # Server-side, revocable refresh token stored in Redis.
    refresh_token = token_store.create(user.id)

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
        access_token=access_token,
        refresh_token=refresh_token,
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


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access+refresh pair (rotation)."""
    # We need to know which user the refresh token belongs to. The opaque token
    # is stored as `refresh:{user_id}:{jti}`, so we brute-force the small set of
    # candidate users by checking validity. To keep it cheap, we look up the user
    # id from the token value via a reverse index is overkill; instead we scan
    # known user ids from the DB is wrong. Simpler: the refresh token is the jti,
    # and we stored it under the user id. We can't reverse it without the id, so
    # the client must also send the user id — but the frontend only has the
    # refresh token. Resolution: embed user_id in the opaque token as `jti` is
    # just random; instead we keep a reverse lookup map in Redis updated on create.
    jti = req.refresh_token
    user_id = token_store.lookup_user(jti)
    if user_id is None or not token_store.is_valid(user_id, jti):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        token_store.revoke(user_id, jti)
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Rotate: revoke the used token, issue a fresh pair.
    token_store.revoke(user_id, jti)
    access_token = create_access_token(user.id, user.username, user.role_id)
    new_refresh = token_store.create(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
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


@router.post("/logout")
def logout(req: LogoutRequest, request: Request, db: Session = Depends(get_db)):
    """Revoke a refresh token.

    The refresh token is revoked server-side using its reverse index, so logout
    works even when the short-lived access token has already expired. If a valid
    access token is also present we additionally revoke every refresh token for
    the user (global logout from all devices).
    """
    # Try to identify the user from a (possibly expired) access token, but don't
    # depend on it — the refresh token reverse index is authoritative.
    current_user: User | None = None
    creds = request.headers.get("Authorization", "")
    if creds.startswith("Bearer "):
        try:
            from app.auth.auth import decode_access_token

            payload = decode_access_token(creds[7:])
            if payload:
                current_user = db.query(User).filter(User.id == payload["user_id"]).first()
        except Exception:
            current_user = None

    if req.refresh_token:
        owner_id = token_store.lookup_user(req.refresh_token)
        if owner_id is not None:
            token_store.revoke(owner_id, req.refresh_token)
        # If we also know the authenticated user, revoke all their sessions.
        if current_user:
            token_store.revoke_all(current_user.id)
    elif current_user:
        token_store.revoke_all(current_user.id)

    return {"detail": "Logged out"}


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
