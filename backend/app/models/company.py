from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    legal_name = Column(String(200), nullable=False, index=True)
    trade_name = Column(String(150), nullable=True, index=True)
    document = Column(String(20), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True)
    address = Column(String(255), nullable=True)
    monthly_limit = Column(Float, nullable=True)
    payment_day = Column(Integer, nullable=True)
    status = Column(String(20), default="active", index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    members = relationship("Client", back_populates="company")
    monthly_accounts = relationship("CompanyMonthlyAccount", back_populates="company")
