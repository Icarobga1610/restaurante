from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class RestaurantSettings(Base):
    """Configurações gerais do restaurante."""
    __tablename__ = "restaurant_settings"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_name = Column(String(200), nullable=False, default="Meu Restaurante")
    cnpj = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    opening_hours = Column(String(255), nullable=True)
    service_fee_percent = Column(Float, default=0.0)
    delivery_fee_default = Column(Float, default=0.0)
    default_monthly_limit = Column(Float, default=500.0)
    default_due_days = Column(Integer, default=30)
    logo_url = Column(String(255), nullable=True)
    cancellation_policy = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
