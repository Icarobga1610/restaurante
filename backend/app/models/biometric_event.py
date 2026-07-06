from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BiometricEvent(Base):
    """Audit trail for all biometric operations — enrollment, verification, consent changes."""
    __tablename__ = "biometric_events"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("biometric_profiles.id"), nullable=False, index=True)
    # Event type: "enroll", "verify_success", "verify_fail", "consent_granted", "consent_revoked", "profile_disabled"
    event_type = Column(String(50), nullable=False)
    # Success/failure indicator
    success = Column(Boolean, default=True)
    # Match score (0.0 - 1.0) for verification events
    match_score = Column(Integer, nullable=True)
    # Human-readable detail
    detail = Column(Text, nullable=True)
    # Which user performed the operation
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    # IP / device
    ip_address = Column(String(45), nullable=True)
    device_info = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    profile = relationship("BiometricProfile", back_populates="events")
    performer = relationship("User")
