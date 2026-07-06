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


class DeliveryPlatform(Base):
    __tablename__ = "delivery_platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    slug = Column(String(80), nullable=False, unique=True, index=True)
    active = Column(Boolean, default=True, nullable=False)
    api_base_url = Column(String(255), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    settings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    orders = relationship("DeliveryOrder", back_populates="platform", cascade="all, delete-orphan")


class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("delivery_platforms.id"), nullable=False)
    external_order_id = Column(String(120), nullable=True, index=True)
    client_name = Column(String(180), nullable=True)
    client_phone = Column(String(60), nullable=True)
    address = Column(Text, nullable=True)
    payment_method = Column(String(80), nullable=True)
    subtotal = Column(Float, default=0.0, nullable=False)
    delivery_fee = Column(Float, default=0.0, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    raw_payload = Column(Text, nullable=True)
    received_at = Column(DateTime, default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    platform = relationship("DeliveryPlatform", back_populates="orders")
    items = relationship("DeliveryPlatformItem", back_populates="order", cascade="all, delete-orphan")


class DeliveryPlatformItem(Base):
    __tablename__ = "delivery_platform_items"

    id = Column(Integer, primary_key=True, index=True)
    delivery_order_id = Column(Integer, ForeignKey("delivery_orders.id"), nullable=False)
    external_item_id = Column(String(120), nullable=True)
    product_id = Column(Integer, nullable=True)
    product_name = Column(String(180), nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    order = relationship("DeliveryOrder", back_populates="items")
