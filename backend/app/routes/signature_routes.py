from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.signature import Signature
from app.schemas.schemas import SignatureOut
from app.auth.auth import get_current_user

router = APIRouter(prefix="/api/signatures", tags=["Signatures"])


@router.get("", response_model=list[SignatureOut])
def list_signatures(
    client_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Signature).options(
        joinedload(Signature.client),
        joinedload(Signature.user),
    )
    if client_id:
        query = query.filter(Signature.client_id == client_id)
    return query.order_by(Signature.signed_at.desc()).offset(skip).limit(limit).all()


@router.get("/{signature_id}", response_model=SignatureOut)
def get_signature(
    signature_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    sig = db.query(Signature).options(
        joinedload(Signature.client),
        joinedload(Signature.user),
    ).filter(Signature.id == signature_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signature not found")
    return sig
