"""Biometric Routes — fingerprint enrollment, verification, and consent management."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional

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
)
from app.auth.auth import get_current_user
from app.services.biometric_service import BiometricService

router = APIRouter(prefix="/api/biometrics", tags=["Biometrics"])


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
