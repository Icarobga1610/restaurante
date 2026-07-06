import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

# Auth config
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password supporting both legacy SHA256 and modern bcrypt."""
    if not password_hash:
        return False
    if password_hash.startswith("$2"):
        return pwd_context.verify(password, password_hash)
    # Legacy sha256$salt$hash fallback
    if "$" not in password_hash:
        return False
    salt, hsh = password_hash.split("$", 1)
    return hsh == hashlib.sha256((salt + password).encode()).hexdigest()


def create_access_token(user_id: int, username: str, role_id: int) -> str:
    """Create a standard HS256 JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role_id": role_id,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_legacy_token(token: str):
    """Decode legacy custom token format: user_id|username|role_id|exp|nonce|sig."""
    try:
        parts = token.split("|")
        if len(parts) != 6:
            return None
        user_id, username, role_id, exp_str, nonce, sig = parts
        expected_sig = hashlib.sha256(
            (f"{user_id}|{username}|{role_id}|{exp_str}|{nonce}" + SECRET_KEY).encode()
        ).hexdigest()[:16]
        if sig != expected_sig:
            return None
        exp = float(exp_str)
        if datetime.now(timezone.utc).timestamp() > exp:
            return None
        return {"user_id": int(user_id), "username": username, "role_id": int(role_id)}
    except Exception:
        return None


def decode_access_token(token: str):
    """Decode JWT token or legacy custom token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id": int(payload["sub"]),
            "username": payload.get("username", ""),
            "role_id": int(payload.get("role_id", 0)),
        }
    except JWTError:
        legacy = _decode_legacy_token(token)
        if legacy:
            return legacy
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        role_name = getattr(current_user.role, "name", None)
        if role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker
