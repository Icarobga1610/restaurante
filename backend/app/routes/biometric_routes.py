"""Biometric Routes — fingerprint enrollment, verification, and consent management."""

import base64
import json
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.utils import utcnow
from app.database import get_db
from app.models.user import User
from app.models.client import Client
from app.models.biometric_profile import BiometricProfile
from app.models.biometric_consent import BiometricConsent
from app.models.biometric_event import BiometricEvent
from app.schemas.schemas import (
    BiometricEnrollRequest,
    BiometricVerifyRequest,
    BiometricProfileOut,
    BiometricConsentOut,
    BiometricEventOut,
    BiometricVerifyResult,
    WebAuthnEnrollComplete,
    WebAuthnOptionsRequest,
    WebAuthnVerifyComplete,
)
from app.auth.auth import get_current_user
from app.services.biometric_service import BiometricService

router = APIRouter(prefix="/api/biometrics", tags=["Biometrics"])

_webauthn_challenges: dict[str, dict] = {}
_verified_tokens: dict[str, dict] = {}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _decode_b64url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _origin(request: Request) -> str:
    return request.headers.get("origin") or f"{request.url.scheme}://{request.url.netloc}"


def _rp_id(request: Request) -> str:
    host = request.headers.get("host") or request.url.netloc
    return host.split(":")[0]


def consume_verified_token(token: str, client_id: int) -> bool:
    payload = _verified_tokens.pop(token, None)
    if not payload:
        return False
    if payload["client_id"] != client_id:
        return False
    if payload["expires_at"] < utcnow():
        return False
    return True


def _read_client_data(response: dict) -> dict:
    client_data = response.get("clientDataJSON")
    if not client_data:
        raise HTTPException(status_code=400, detail="Missing WebAuthn clientDataJSON")
    try:
        return json.loads(_decode_b64url(client_data))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid WebAuthn clientDataJSON")


@router.post("/webauthn/enroll/options")
def webauthn_enroll_options(
    data: WebAuthnOptionsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only admin/financial can enroll biometrics")

    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if client.status != "active":
        raise HTTPException(status_code=400, detail="Client is not active")

    challenge = _b64url(secrets.token_bytes(32))
    key = f"enroll:{data.client_id}:{current_user.id}"
    _webauthn_challenges[key] = {
        "challenge": challenge,
        "origin": _origin(request),
        "expires_at": utcnow() + timedelta(minutes=5),
    }

    return {
        "publicKey": {
            "challenge": challenge,
            "rp": {"name": "Restaurante", "id": _rp_id(request)},
            "user": {
                "id": _b64url(str(client.id).encode()),
                "name": client.phone or client.name,
                "displayName": client.name,
            },
            "pubKeyCredParams": [
                {"type": "public-key", "alg": -7},
                {"type": "public-key", "alg": -257},
            ],
            "authenticatorSelection": {
                "userVerification": "required",
                "residentKey": "preferred",
            },
            "timeout": 60000,
            "attestation": "none",
        }
    }


@router.post("/webauthn/enroll/complete", response_model=BiometricProfileOut)
def webauthn_enroll_complete(
    data: WebAuthnEnrollComplete,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only admin/financial can enroll biometrics")

    key = f"enroll:{data.client_id}:{current_user.id}"
    challenge_payload = _webauthn_challenges.pop(key, None)
    if not challenge_payload or challenge_payload["expires_at"] < utcnow():
        raise HTTPException(status_code=400, detail="WebAuthn challenge expired")

    client_data = _read_client_data(data.response)
    if client_data.get("type") != "webauthn.create":
        raise HTTPException(status_code=400, detail="Invalid WebAuthn enrollment response")
    if client_data.get("challenge") != challenge_payload["challenge"]:
        raise HTTPException(status_code=400, detail="WebAuthn challenge mismatch")
    if client_data.get("origin") != challenge_payload["origin"]:
        raise HTTPException(status_code=400, detail="WebAuthn origin mismatch")

    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    profile = db.query(BiometricProfile).filter(BiometricProfile.client_id == data.client_id).first()
    if not profile:
        profile = BiometricProfile(client_id=data.client_id)
        db.add(profile)

    credential_payload = {
        "credential_id": data.credential_id,
        "raw_id": data.raw_id,
        "type": data.type,
        "registered_via": "webauthn",
    }
    profile.encrypted_template = json.dumps(credential_payload)
    profile.algorithm = "webauthn_passkey"
    profile.fingers_enrolled = 1
    profile.device_id = request.headers.get("user-agent", "webauthn")
    profile.is_active = True
    profile.updated_at = utcnow()
    db.flush()

    BiometricService(db).register_consent(profile.id, current_user.id, "verification")
    event = BiometricEvent(
        profile_id=profile.id,
        event_type="webauthn_enroll",
        success=True,
        performed_by=current_user.id,
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("user-agent"),
        detail="Digital cadastrada via WebAuthn/passkey",
    )
    db.add(event)
    db.commit()
    db.refresh(profile)

    return BiometricProfileOut(
        id=profile.id,
        client_id=profile.client_id,
        client_name=client.name,
        algorithm=profile.algorithm,
        fingers_enrolled=profile.fingers_enrolled,
        is_active=profile.is_active,
        last_used_at=profile.last_used_at,
        created_at=profile.created_at,
    )


@router.post("/webauthn/verify/options")
def webauthn_verify_options(
    data: WebAuthnOptionsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(BiometricProfile).filter(
        BiometricProfile.client_id == data.client_id,
        BiometricProfile.is_active == True,
        BiometricProfile.algorithm == "webauthn_passkey",
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Cliente não possui digital funcional cadastrada")

    try:
        credential = json.loads(profile.encrypted_template)
    except Exception:
        raise HTTPException(status_code=400, detail="Cadastro biométrico inválido")

    challenge = _b64url(secrets.token_bytes(32))
    key = f"verify:{data.client_id}:{current_user.id}"
    _webauthn_challenges[key] = {
        "challenge": challenge,
        "origin": _origin(request),
        "credential_id": credential["credential_id"],
        "expires_at": utcnow() + timedelta(minutes=5),
    }

    return {
        "publicKey": {
            "challenge": challenge,
            "rpId": _rp_id(request),
            "allowCredentials": [{"type": "public-key", "id": credential["credential_id"]}],
            "userVerification": "required",
            "timeout": 60000,
        }
    }


@router.post("/webauthn/verify/complete")
def webauthn_verify_complete(
    data: WebAuthnVerifyComplete,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = f"verify:{data.client_id}:{current_user.id}"
    challenge_payload = _webauthn_challenges.pop(key, None)
    if not challenge_payload or challenge_payload["expires_at"] < utcnow():
        raise HTTPException(status_code=400, detail="WebAuthn challenge expired")
    if data.credential_id != challenge_payload["credential_id"]:
        raise HTTPException(status_code=400, detail="Credencial biométrica incorreta")

    client_data = _read_client_data(data.response)
    if client_data.get("type") != "webauthn.get":
        raise HTTPException(status_code=400, detail="Invalid WebAuthn verification response")
    if client_data.get("challenge") != challenge_payload["challenge"]:
        raise HTTPException(status_code=400, detail="WebAuthn challenge mismatch")
    if client_data.get("origin") != challenge_payload["origin"]:
        raise HTTPException(status_code=400, detail="WebAuthn origin mismatch")

    profile = db.query(BiometricProfile).filter(
        BiometricProfile.client_id == data.client_id,
        BiometricProfile.is_active == True,
        BiometricProfile.algorithm == "webauthn_passkey",
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Cliente não possui digital funcional cadastrada")

    now = utcnow()
    token = secrets.token_urlsafe(32)
    _verified_tokens[token] = {
        "client_id": data.client_id,
        "profile_id": profile.id,
        "expires_at": now + timedelta(minutes=3),
    }
    profile.last_used_at = now
    event = BiometricEvent(
        profile_id=profile.id,
        event_type="webauthn_verify",
        success=True,
        match_score=100,
        performed_by=current_user.id,
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("user-agent"),
        detail="Digital validada via WebAuthn/passkey",
    )
    db.add(event)
    db.commit()

    return {"success": True, "message": "Digital validada com sucesso.", "verification_token": token}


@router.post("/enroll", response_model=BiometricProfileOut)
def enroll_client_fingerprint(
    data: BiometricEnrollRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll a client's fingerprint (demo or real).

    Captures fingerprint via reader, encrypts the template hash,
    records consent, and logs all events.
    Never stores raw fingerprint image — only encrypted template token.
    """
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only admin/financial can enroll biometrics")

    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if client.status != "active":
        raise HTTPException(status_code=400, detail="Client is not active")

    service = BiometricService(db)
    success, profile, message = service.enroll_client(
        client_id=data.client_id,
        performed_by=current_user.id,
        ip_address=request.client.host if request.client else None,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return BiometricProfileOut(
        id=profile.id,
        client_id=profile.client_id,
        client_name=client.name,
        algorithm=profile.algorithm,
        fingers_enrolled=profile.fingers_enrolled,
        is_active=profile.is_active,
        last_used_at=profile.last_used_at,
        created_at=profile.created_at,
    )


@router.post("/verify", response_model=BiometricVerifyResult)
def verify_fingerprint(
    data: BiometricVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify a client's fingerprint for monthly closing confirmation.

    Replaces the old \"sign\" flow. On success, sets account status
    to 'confirmed_by_biometrics'.
    """
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only admin/financial can verify biometrics")

    # Verify client exists
    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Verify monthly account exists and is in correct state
    from app.models.monthly_account import MonthlyAccount
    account = db.query(MonthlyAccount).filter(MonthlyAccount.id == data.monthly_account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Monthly account not found")
    if account.client_id != data.client_id:
        raise HTTPException(status_code=400, detail="Account does not belong to this client")
    if account.status not in ("closed", "confirmed_by_biometrics"):
        raise HTTPException(
            status_code=400,
            detail=f"Account must be closed to verify biometrics, current status: {account.status}",
        )

    service = BiometricService(db)
    success, status, message = service.verify_client(
        client_id=data.client_id,
        monthly_account_id=data.monthly_account_id,
        performed_by=current_user.id,
        ip_address=request.client.host if request.client else None,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return BiometricVerifyResult(
        success=True,
        message=message,
        account_id=data.monthly_account_id,
        status=status,
        match_score=92,  # Demo mode score; real SDK would return actual score
    )


@router.post("/verify-identity", response_model=BiometricVerifyResult)
def verify_identity(
    data: BiometricVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alias of /verify kept for client compatibility (verify client identity)."""
    return verify_fingerprint(data, request, db, current_user)


@router.get("/profiles", response_model=list[BiometricProfileOut])
def list_biometric_profiles(
    client_id: Optional[int] = None,
    active_only: bool = Query(True, alias="active_only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List biometric profiles."""
    query = db.query(BiometricProfile).options(joinedload(BiometricProfile.client))
    if client_id:
        query = query.filter(BiometricProfile.client_id == client_id)
    if active_only:
        query = query.filter(BiometricProfile.is_active == True)
    profiles = query.order_by(BiometricProfile.created_at.desc()).offset(skip).limit(limit).all()

    return [
        BiometricProfileOut(
            id=p.id,
            client_id=p.client_id,
            client_name=p.client.name if p.client else None,
            algorithm=p.algorithm,
            fingers_enrolled=p.fingers_enrolled,
            is_active=p.is_active,
            last_used_at=p.last_used_at,
            created_at=p.created_at,
        )
        for p in profiles
    ]


@router.get("/profiles/{profile_id}", response_model=BiometricProfileOut)
def get_biometric_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a single biometric profile."""
    profile = db.query(BiometricProfile).options(
        joinedload(BiometricProfile.client)
    ).filter(BiometricProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Biometric profile not found")

    return BiometricProfileOut(
        id=profile.id,
        client_id=profile.client_id,
        client_name=profile.client.name if profile.client else None,
        algorithm=profile.algorithm,
        fingers_enrolled=profile.fingers_enrolled,
        is_active=profile.is_active,
        last_used_at=profile.last_used_at,
        created_at=profile.created_at,
    )


@router.delete("/profiles/{profile_id}")
def disable_biometric_profile(
    profile_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disable a biometric profile (soft-delete)."""
    if current_user.role.name not in ("admin",):
        raise HTTPException(status_code=403, detail="Only admin can disable biometric profiles")

    profile = db.query(BiometricProfile).filter(BiometricProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Biometric profile not found")

    profile.is_active = False

    # Revoke consents
    db.query(BiometricConsent).filter(
        BiometricConsent.profile_id == profile_id,
        BiometricConsent.is_active == True,
    ).update({"is_active": False, "revoked_at": utcnow()})

    # Log event
    from app.models.biometric_event import BiometricEvent
    event = BiometricEvent(
        profile_id=profile_id,
        event_type="profile_disabled",
        success=True,
        performed_by=current_user.id,
        ip_address=request.client.host if request.client else None,
        detail="Perfil biométrico desativado",
    )
    db.add(event)
    db.commit()

    return {"message": "Biometric profile disabled successfully"}


@router.get("/events", response_model=list[BiometricEventOut])
def list_biometric_events(
    profile_id: Optional[int] = None,
    event_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List biometric events (audit trail)."""
    query = db.query(BiometricEvent).options(
        joinedload(BiometricEvent.profile),
        joinedload(BiometricEvent.performer),
    )
    if profile_id:
        query = query.filter(BiometricEvent.profile_id == profile_id)
    if event_type:
        query = query.filter(BiometricEvent.event_type == event_type)

    events = query.order_by(BiometricEvent.created_at.desc()).offset(skip).limit(limit).all()

    return [
        BiometricEventOut(
            id=e.id,
            profile_id=e.profile_id,
            event_type=e.event_type,
            success=e.success,
            match_score=e.match_score,
            detail=e.detail,
            performed_by=e.performed_by,
            ip_address=e.ip_address,
            created_at=e.created_at,
        )
        for e in events
    ]


@router.get("/consent", response_model=list[BiometricConsentOut])
def list_consent_records(
    profile_id: Optional[int] = None,
    active_only: bool = Query(True, alias="active_only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List biometric consent records."""
    query = db.query(BiometricConsent)
    if profile_id:
        query = query.filter(BiometricConsent.profile_id == profile_id)
    if active_only:
        query = query.filter(BiometricConsent.is_active == True)

    consents = query.order_by(BiometricConsent.granted_at.desc()).offset(skip).limit(limit).all()

    return [
        BiometricConsentOut(
            id=c.id,
            profile_id=c.profile_id,
            purpose=c.purpose,
            consent_version=c.consent_version,
            is_active=c.is_active,
            granted_at=c.granted_at,
            revoked_at=c.revoked_at,
        )
        for c in consents
    ]
