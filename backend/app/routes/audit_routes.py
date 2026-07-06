from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.schemas import AuditLogOut
from app.auth.auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)

    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
