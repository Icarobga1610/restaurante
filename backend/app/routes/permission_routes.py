from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User, Role
from app.models.permission import Permission, RolePermission
from app.schemas.schemas import PermissionOut, RolePermissionUpdate
from app.auth.auth import get_current_user
from app.services.permission_service import PermissionService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/permissions", tags=["Permissions"])


@router.get("", response_model=List[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Permission).order_by(Permission.module, Permission.key).all()


@router.get("/my", response_model=List[str])
def my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PermissionService(db)
    return service.get_user_permissions(current_user)


@router.get("/roles/{role_id}", response_model=List[int])
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rps = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    return [rp.permission_id for rp in rps]


@router.put("/roles/{role_id}", response_model=dict)
def update_role_permissions(
    role_id: int,
    data: RolePermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only admin can update permissions
    if current_user.role.name not in ("admin", "dono_gerente", "administrador"):
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar permissões")

    # Delete existing permissions for this role
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

    # Add new permissions
    for perm_id in data.permission_ids:
        rp = RolePermission(role_id=role_id, permission_id=perm_id)
        db.add(rp)

    db.commit()

    role = db.query(Role).filter(Role.id == role_id).first()
    AuditService(db).log(
        action="update", entity_type="role_permissions",
        entity_id=role_id,
        user_id=current_user.id, username=current_user.username,
        details=f"Permissões do perfil '{role.name if role else '#'}' atualizadas",
    )

    return {"role_id": role_id, "permission_ids": data.permission_ids}
