from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.utils import utcnow
from app.database import get_db
from app.models.user import User
from app.models.restaurant_table import RestaurantTable
from app.schemas.schemas import TableCreate, TableUpdate, TableOut
from app.auth.auth import get_current_user

router = APIRouter(prefix="/api/tables", tags=["Tables"])

@router.get("", response_model=list[TableOut])
def list_tables(status: Optional[str] = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(RestaurantTable)
    if status: q = q.filter(RestaurantTable.status == status)
    return q.order_by(RestaurantTable.number).all()

@router.get("/{table_id}", response_model=TableOut)
def get_table(table_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    t = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not t: raise HTTPException(404, "Table not found")
    return TableOut(id=t.id, number=t.number, capacity=t.capacity, status=t.status,
        client_id=t.client_id, client_name=t.client.name if t.client else None,
        opened_at=t.opened_at, closed_at=t.closed_at, notes=t.notes,
        created_at=t.created_at, updated_at=t.updated_at)

@router.post("", response_model=TableOut, status_code=201)
def create_table(data: TableCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin",): raise HTTPException(403, "Only admins can manage tables")
    existing = db.query(RestaurantTable).filter(RestaurantTable.number == data.number).first()
    if existing: raise HTTPException(400, f"Table #{data.number} already exists")
    t = RestaurantTable(**data.model_dump()); db.add(t); db.commit(); db.refresh(t)
    return get_table(t.id, db, current_user)

@router.put("/{table_id}", response_model=TableOut)
def update_table(table_id: int, data: TableUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin",): raise HTTPException(403, "Only admins can update tables")
    t = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not t: raise HTTPException(404, "Table not found")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(t, k, v)
    if data.status == "occupied" and not t.opened_at: t.opened_at = utcnow()
    if data.status == "free": t.client_id = None; t.opened_at = None; t.closed_at = None
    db.commit(); db.refresh(t); return get_table(t.id, db, current_user)

@router.post("/{table_id}/open")
def open_table(table_id: int, client_id: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not t: raise HTTPException(404, "Table not found")
    if t.status != "free": raise HTTPException(400, f"Table is {t.status}")
    t.status = "occupied"; t.client_id = client_id; t.opened_at = utcnow()
    db.commit(); return {"message": f"Table #{t.number} opened", "table_id": table_id}

@router.post("/{table_id}/close")
def close_table(table_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not t: raise HTTPException(404, "Table not found")
    t.status = "free"; t.client_id = None; t.closed_at = utcnow()
    db.commit(); return {"message": f"Table #{t.number} closed"}
