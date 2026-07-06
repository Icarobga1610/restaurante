from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DeliveryAddress(Base):
    """Endereço de entrega do cliente."""
    __tablename__ = "delivery_addresses"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    label = Column(String(100), nullable=True)  # Casa, Trabalho, etc
    street = Column(String(200), nullable=False)
    number = Column(String(20), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=False, default="São Paulo")
    state = Column(String(50), nullable=False, default="SP")
    reference = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship("Client")


class DeliveryEvent(Base):
    """Evento de rastreamento de entrega."""
    __tablename__ = "delivery_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    order = relationship("Order")
    user = relationship("User")
