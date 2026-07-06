from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BiometricProfile(Base):
    """Stores biometric enrollment data — only encrypted template/token/hash, never raw image."""
    __tablename__ = "biometric_profiles"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True, index=True)
    # Encrypted template hash / token returned by the SDK or demo mode
    encrypted_template = Column(Text, nullable=False)
    # Algorithm used: "demo_sha256" for demo, or future "sdk_v1", "sdk_v2", etc.
    algorithm = Column(String(50), nullable=False, default="demo_sha256")
    # Number of fingers enrolled (1-10)
    fingers_enrolled = Column(Integer, default=1)
    # Device / SDK identifier
    device_id = Column(String(255), nullable=True)
    # Active flag – can be disabled without losing data
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship("Client")
    consents = relationship("BiometricConsent", back_populates="profile", cascade="all, delete-orphan")
    events = relationship("BiometricEvent", back_populates="profile", cascade="all, delete-orphan")
