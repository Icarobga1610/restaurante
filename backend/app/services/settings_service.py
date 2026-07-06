from typing import Optional
from sqlalchemy.orm import Session
from app.models.restaurant_settings import RestaurantSettings
from app.services.audit_service import AuditService


class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def get_settings(self) -> Optional[RestaurantSettings]:
        return self.db.query(RestaurantSettings).first()

    def create_or_update(
        self,
        data: dict,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
    ) -> RestaurantSettings:
        settings = self.get_settings()
        if settings:
            before = {
                "restaurant_name": settings.restaurant_name,
                "service_fee_percent": settings.service_fee_percent,
                "delivery_fee_default": settings.delivery_fee_default,
            }
            for key, value in data.items():
                if hasattr(settings, key) and value is not None:
                    setattr(settings, key, value)
            self.db.commit()
            self.db.refresh(settings)
            self.audit.log(
                action="update",
                entity_type="restaurant_settings",
                entity_id=settings.id,
                user_id=user_id,
                username=username,
                before_state=before,
                after_state=data,
                details="Configurações do restaurante atualizadas",
            )
        else:
            settings = RestaurantSettings(**data)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            self.audit.log(
                action="create",
                entity_type="restaurant_settings",
                entity_id=settings.id,
                user_id=user_id,
                username=username,
                after_state=data,
                details="Configurações iniciais do restaurante criadas",
            )
        return settings

    def get_service_fee_percent(self) -> float:
        settings = self.get_settings()
        return settings.service_fee_percent if settings else 0.0

    def get_delivery_fee_default(self) -> float:
        settings = self.get_settings()
        return settings.delivery_fee_default if settings else 0.0
