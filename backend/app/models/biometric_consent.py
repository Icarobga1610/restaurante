from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BiometricConsent(Base):
    """Records client consent for biometric data collection and processing."""
    __tablename__ = "biometric_consents"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("biometric_profiles.id"), nullable=False)
    # Purpose of consent: "enrollment", "verification", "both"
    purpose = Column(String(50), nullable=False)
    # Consent version / terms accepted
    consent_version = Column(String(20), nullable=True)
    # IP and device info where consent was given
    ip_address = Column(String(45), nullable=True)
    device_info = Column(String(255), nullable=True)
    # Whether consent is still valid
    is_active = Column(Boolean, default=True)
    granted_at = Column(DateTime, default=func.now())
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    profile = relationship("BiometricProfile", back_populates="consents")
