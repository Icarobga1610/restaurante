from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Promotion(Base):
    """Promoção ativa no restaurante."""
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    promotion_type = Column(String(30), nullable=False)
    # produto, categoria, combo, horario, dia_semana, geral
    discount_type = Column(String(30), nullable=False)
    # percentual, valor_fixo, preco_fixo
    discount_value = Column(Float, nullable=False)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    day_of_week = Column(Integer, nullable=True)  # 0=domingo, 1=segunda, etc
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Coupon(Base):
    """Cupom de desconto."""
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    discount_type = Column(String(30), nullable=False)
    # percentual, valor_fixo
    discount_value = Column(Float, nullable=False)
    max_uses = Column(Integer, default=0)
    current_uses = Column(Integer, default=0)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ComboItem(Base):
    """Item que compõe um combo."""
    __tablename__ = "combo_items"

    id = Column(Integer, primary_key=True, index=True)
    combo_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, default=1.0)
    created_at = Column(DateTime, default=func.now())

    combo_product = relationship("Product", foreign_keys=[combo_product_id])
    product = relationship("Product", foreign_keys=[product_id])


class DiscountLog(Base):
    """Registro de descontos aplicados em pedidos."""
    __tablename__ = "discount_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    discount_type = Column(String(30), nullable=False)
    # manual, cupom, promocao, cortesia
    discount_value = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    order = relationship("Order")
    user = relationship("User")
    coupon = relationship("Coupon")
    promotion = relationship("Promotion")
