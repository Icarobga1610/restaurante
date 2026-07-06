from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    category = Column(String(80), nullable=False)
    # pratos, bebidas, sobremesas, lanches, combos, adicionais, promocoes
    price = Column(Float, nullable=False)
    estimated_cost = Column(Float, nullable=True)
    estimated_margin = Column(Float, nullable=True)
    avg_prep_time_minutes = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_seasonal = Column(Boolean, default=False)
    availability = Column(String(30), default="always")  # always, limited, seasonal
    seasonality = Column(JSON, nullable=True)  # {"type": "seasonal", "months": [1,2,3], "days": [0,1,...]}
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
