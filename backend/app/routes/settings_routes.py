from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.schemas import RestaurantSettingsUpdate, RestaurantSettingsOut
from app.auth.auth import get_current_user
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=RestaurantSettingsOut)
def get_settings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = SettingsService(db)
    settings = service.get_settings()
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    return settings


@router.post("", response_model=RestaurantSettingsOut)
def create_settings(
    data: RestaurantSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SettingsService(db)
    filtered = {k: v for k, v in data.model_dump(exclude_none=True).items() if v is not None}
    settings = service.create_or_update(
        filtered,
        user_id=current_user.id,
        username=current_user.username,
    )
    return settings


@router.put("", response_model=RestaurantSettingsOut)
def update_settings(
    data: RestaurantSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SettingsService(db)
    filtered = {k: v for k, v in data.model_dump(exclude_none=True).items() if v is not None}
    if not filtered:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    settings = service.create_or_update(
        filtered,
        user_id=current_user.id,
        username=current_user.username,
    )
    return settings
