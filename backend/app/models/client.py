from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    document = Column(String(20), nullable=True, unique=True)
    phone = Column(String(20), nullable=False)
    company_sector = Column(String(100), nullable=True)
    status = Column(String(20), default="active")  # active / inactive
    monthly_limit = Column(Float, nullable=True)
    is_account_client = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
