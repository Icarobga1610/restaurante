from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tab_id = Column(Integer, ForeignKey("tabs.id"), nullable=True)
    table_id = Column(Integer, ForeignKey("restaurant_tables.id"), nullable=True)
    status = Column(String(30), default="open")
    # open, confirmed, in_preparation, ready, delivered, cancelled, invoiced, paid
    order_type = Column(String(30), default="mesa")
    # mesa, balcao, retirada, delivery, conta_mensal
    delivery_address_id = Column(Integer, ForeignKey("delivery_addresses.id"), nullable=True)
    delivery_fee = Column(Float, default=0.0)
    delivery_status = Column(String(30), nullable=True)
    # recebido, em_preparo, pronto, saiu_para_entrega, entregue, cancelado
    delivery_person_name = Column(String(150), nullable=True)
    estimated_delivery_time = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    preparation_time_seconds = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    total = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship("Client")
    user = relationship("User")
    tab = relationship("Tab")
    table = relationship("RestaurantTable")
    delivery_address = relationship("DeliveryAddress")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(150), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
