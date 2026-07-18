from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CompanyMonthlyAccount(Base):
    __tablename__ = "company_monthly_accounts"
    __table_args__ = (UniqueConstraint("company_id", "month", "year", name="uq_company_monthly_accounts_period"),)

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    total = Column(Float, default=0.0)
    due_date = Column(Date, nullable=True)
    status = Column(String(30), default="open", index=True)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    payment_method = Column(String(50), nullable=True)
    notes = Column(String(500), nullable=True)
    over_limit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    company = relationship("Company", back_populates="monthly_accounts")
    closer = relationship("User", foreign_keys=[closed_by])
    payer = relationship("User", foreign_keys=[paid_by])
    items = relationship(
        "CompanyMonthlyAccountItem",
        back_populates="account",
        cascade="all, delete-orphan",
    )


class CompanyMonthlyAccountItem(Base):
    __tablename__ = "company_monthly_account_items"

    id = Column(Integer, primary_key=True, index=True)
    company_monthly_account_id = Column(
        Integer,
        ForeignKey("company_monthly_accounts.id"),
        nullable=False,
    )
    monthly_account_id = Column(Integer, ForeignKey("monthly_accounts.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client_total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    account = relationship("CompanyMonthlyAccount", back_populates="items")
    monthly_account = relationship("MonthlyAccount")
    client = relationship("Client")


class CompanyPayment(Base):
    __tablename__ = "company_payments"

    id = Column(Integer, primary_key=True, index=True)
    company_monthly_account_id = Column(
        Integer,
        ForeignKey("company_monthly_accounts.id"),
        nullable=False,
    )
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    paid_at = Column(DateTime, default=func.now())
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    account = relationship("CompanyMonthlyAccount")
    company = relationship("Company")
    user = relationship("User")
