from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RestaurantTable(Base):
    """Mesa do restaurante."""
    __tablename__ = "restaurant_tables"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=False, unique=True)
    capacity = Column(Integer, default=4)
    status = Column(String(30), default="free")  # free, occupied, awaiting_payment, closed
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    opened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship("Client")
    tabs = relationship("Tab", back_populates="table")
