from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class KitchenOrder(Base):
    """Pedido na cozinha — cada item de pedido vira uma ordem de produção."""
    __tablename__ = "kitchen_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(150), nullable=False)
    quantity = Column(Float, default=1.0)
    status = Column(String(30), default="received")
    # received, in_preparation, ready, delivered, cancelled
    notes = Column(Text, nullable=True)
    preparation_time_seconds = Column(Integer, nullable=True)  # tempo real de preparo
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    order = relationship("Order")
    product = relationship("Product")
    assignee = relationship("User")
    events = relationship("KitchenOrderEvent", back_populates="kitchen_order", cascade="all, delete-orphan")


class KitchenOrderEvent(Base):
    """Evento/status change de um pedido de cozinha."""
    __tablename__ = "kitchen_order_events"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_order_id = Column(Integer, ForeignKey("kitchen_orders.id"), nullable=False)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    kitchen_order = relationship("KitchenOrder", back_populates="events")
    performer = relationship("User")
