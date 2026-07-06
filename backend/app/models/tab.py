from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Tab(Base):
    """Comanda — pode estar vinculada a uma mesa ou a um cliente."""
    __tablename__ = "tabs"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("restaurant_tables.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total = Column(Float, default=0.0)
    status = Column(String(30), default="open")  # open, closed, cancelled, paid, sent_to_monthly
    notes = Column(Text, nullable=True)
    opened_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    table = relationship("RestaurantTable", back_populates="tabs")
    client = relationship("Client")
    user = relationship("User")
    items = relationship("TabItem", back_populates="tab", cascade="all, delete-orphan")


class TabItem(Base):
    """Item de uma comanda."""
    __tablename__ = "tab_items"

    id = Column(Integer, primary_key=True, index=True)
    tab_id = Column(Integer, ForeignKey("tabs.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(150), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    tab = relationship("Tab", back_populates="items")
    product = relationship("Product")
