from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.client import Client
from app.schemas.schemas import ClientCreate, ClientUpdate, ClientOut
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/clients", tags=["Clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Client)
    if status:
        query = query.filter(Client.status == status)
    if search:
        query = query.filter(
            Client.name.ilike(f"%{search}%") | Client.phone.ilike(f"%{search}%")
        )
    return query.order_by(Client.name).offset(skip).limit(limit).all()


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    data: ClientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin",):
        raise HTTPException(status_code=403, detail="Only admins can create clients")

    if data.document:
        existing = db.query(Client).filter(Client.document == data.document).first()
        if existing:
            raise HTTPException(status_code=400, detail="Document already exists")

    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)

    AuditService(db).log(
        action="create",
        entity_type="client",
        entity_id=client.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Created client {client.name}",
    )

    return client


@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    data: ClientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin",):
        raise HTTPException(status_code=403, detail="Only admins can update clients")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    before = {"name": client.name, "status": client.status, "phone": client.phone}
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(client, key, value)

    db.commit()
    db.refresh(client)

    AuditService(db).log(
        action="update",
        entity_type="client",
        entity_id=client.id,
        user_id=current_user.id,
        username=current_user.username,
        before_state=before,
        after_state={"name": client.name, "status": client.status, "phone": client.phone},
        ip_address=request.client.host if request.client else None,
        details=f"Updated client {client.name}",
    )

    return client


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin",):
        raise HTTPException(status_code=403, detail="Only admins can delete clients")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.status = "inactive"
    db.commit()

    return {"message": "Client deactivated"}
