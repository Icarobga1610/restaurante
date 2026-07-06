"""Biometric Service

Handles biometric enrollment, verification, consent management, and encryption.
Uses the biometric_bridge for reader abstraction (demo or real SDK).
"""

import os
import hashlib
from base64 import b64encode, b64decode
from datetime import datetime
from app.utils import utcnow
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session

from app.biometric_bridge.demo import DemoBiometricReader
from app.biometric_bridge.base import BiometricReader
from app.models.biometric_profile import BiometricProfile
from app.models.biometric_consent import BiometricConsent
from app.models.biometric_event import BiometricEvent
from app.models.monthly_account import MonthlyAccount
from app.models.client import Client
from app.services.audit_service import AuditService


class BiometricService:
    """Service layer for biometric operations with encryption and audit logging."""

    # Derive encryption key from app secret key
    _fernet: Fernet = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get or create a Fernet encryption instance derived from the app secret."""
        if cls._fernet is None:
            secret = os.getenv("SECRET_KEY", "default-dev-key-change-in-production")
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"restaurante_biometric_salt_v1",
                iterations=100_000,
            )
            key = b64encode(kdf.derive(secret.encode())).decode()
            cls._fernet = Fernet(key.encode())
        return cls._fernet

    def __init__(self, db: Session, reader: Optional[BiometricReader] = None):
        self.db = db
        self.reader = reader or DemoBiometricReader()
        self.audit = AuditService(db)

    # ── Encryption ──────────────────────────────────────────────

    @staticmethod
    def encrypt_data(plaintext: str) -> str:
        """Encrypt biometric data using Fernet symmetric encryption."""
        f = BiometricService._get_fernet()
        return f.encrypt(plaintext.encode()).decode()

    @staticmethod
    def decrypt_data(ciphertext: str) -> str:
        """Decrypt biometric data."""
        f = BiometricService._get_fernet()
        return f.decrypt(ciphertext.encode()).decode()

    # ── Consent Management ──────────────────────────────────────

    def register_consent(
        self,
        profile_id: int,
        purpose: str = "both",
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
        performed_by: Optional[int] = None,
    ) -> BiometricConsent:
        """Register explicit client consent for biometric data processing."""
        # Revoke any previous active consent for this profile
        self.db.query(BiometricConsent).filter(
            BiometricConsent.profile_id == profile_id,
            BiometricConsent.is_active == True,
        ).update({"is_active": False, "revoked_at": utcnow()})

        consent = BiometricConsent(
            profile_id=profile_id,
            purpose=purpose,
            consent_version="1.0",
            ip_address=ip_address,
            device_info=device_info,
            is_active=True,
        )
        self.db.add(consent)
        self.db.flush()

        self.audit.log(
            action="consent_granted",
            entity_type="biometric_consent",
            entity_id=consent.id,
            user_id=performed_by,
            ip_address=ip_address,
            details=f"Consent granted for biometric profile #{profile_id}, purpose: {purpose}",
        )
        return consent

    def revoke_consent(
        self,
        profile_id: int,
        performed_by: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Revoke all active consent for a biometric profile."""
        updated = self.db.query(BiometricConsent).filter(
            BiometricConsent.profile_id == profile_id,
            BiometricConsent.is_active == True,
        ).update({"is_active": False, "revoked_at": utcnow()})

        if updated:
            self.audit.log(
                action="consent_revoked",
                entity_type="biometric_consent",
                entity_id=profile_id,
                user_id=performed_by,
                ip_address=ip_address,
                details=f"Consent revoked for biometric profile #{profile_id}",
            )
        return updated > 0

    def check_consent(self, profile_id: int, purpose: str = "verification") -> bool:
        """Check if a profile has active consent for the given purpose."""
        consent = self.db.query(BiometricConsent).filter(
            BiometricConsent.profile_id == profile_id,
            BiometricConsent.is_active == True,
            BiometricConsent.purpose.in_([purpose, "both"]),
        ).first()
        return consent is not None

    # ── Enrollment ──────────────────────────────────────────────

    def enroll_client(
        self,
        client_id: int,
        performed_by: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[BiometricProfile], str]:
        """Enroll a client's fingerprint (demo or real).

        Uses the biometric reader to capture a fingerprint template,
        encrypts the template hash, and stores it.

        Never stores raw fingerprint image — only an encrypted template token/hash.
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return (False, None, "Cliente não encontrado")

        # Check if already enrolled
        existing = self.db.query(BiometricProfile).filter(
            BiometricProfile.client_id == client_id,
            BiometricProfile.is_active == True,
        ).first()
        if existing:
            return (False, None, "Cliente já possui cadastro biométrico ativo")

        # Capture fingerprint via the reader
        success, encrypted_template, device_info = self.reader.enroll()
        if not success or not encrypted_template:
            return (False, None, "Falha na captura da digital")

        # Generate the stored hash (never store raw SDK template)
        stored_hash = self.reader.generate_template_hash(encrypted_template)

        # Encrypt the stored hash before saving
        encrypted_stored = self.encrypt_data(stored_hash)

        # Create profile
        profile = BiometricProfile(
            client_id=client_id,
            encrypted_template=encrypted_stored,
            algorithm="demo_sha256" if "demo" in self.reader.reader_name.lower() else "sdk_v1",
            fingers_enrolled=1,
            device_id=device_info,
            is_active=True,
        )
        self.db.add(profile)
        self.db.flush()

        # Auto-register consent
        self.register_consent(
            profile_id=profile.id,
            purpose="both",
            ip_address=ip_address,
            device_info=device_info,
            performed_by=performed_by,
        )

        # Log event
        event = BiometricEvent(
            profile_id=profile.id,
            event_type="enroll",
            success=True,
            performed_by=performed_by,
            ip_address=ip_address,
            detail="Digital cadastrada com sucesso",
        )
        self.db.add(event)
        self.db.flush()

        self.audit.log(
            action="biometric_enroll",
            entity_type="biometric_profile",
            entity_id=profile.id,
            user_id=performed_by,
            ip_address=ip_address,
            details=f"Biometric enrollment for client #{client_id}",
        )

        self.db.commit()
        self.db.refresh(profile)
        return (True, profile, "Digital cadastrada com sucesso")

    # ── Verification ────────────────────────────────────────────

    def verify_client(
        self,
        client_id: int,
        monthly_account_id: int,
        performed_by: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], str]:
        """Verify a client's fingerprint for monthly closing confirmation.

        Replaces the old "sign" flow with biometric verification.
        On success, sets the account status to "confirmed_by_biometrics".
        Does NOT override the original closed_at timestamp.
        """
        # Find active profile
        profile = self.db.query(BiometricProfile).filter(
            BiometricProfile.client_id == client_id,
            BiometricProfile.is_active == True,
        ).first()
        if not profile:
            return (False, None, "Cliente não possui cadastro biométrico")

        # Check consent
        if not self.check_consent(profile.id, "verification"):
            return (False, None, "Consentimento biométrico não autorizado")

        # Decrypt the stored template
        try:
            stored_template = self.decrypt_data(profile.encrypted_template)
        except Exception:
            return (False, None, "Erro ao descriptografar template biométrico")

        # Verify fingerprint via the reader
        success, score, detail = self.reader.verify(stored_template)
        if not success:
            # Log failure
            event = BiometricEvent(
                profile_id=profile.id,
                event_type="verify_fail",
                success=False,
                match_score=score,
                detail=detail or "Digital não reconhecida",
                performed_by=performed_by,
                ip_address=ip_address,
            )
            self.db.add(event)
            self.db.flush()
            self.db.commit()
            return (False, None, detail or "Digital não reconhecida")

        # Success — update the monthly account
        account = self.db.query(MonthlyAccount).filter(MonthlyAccount.id == monthly_account_id).first()
        if not account:
            return (False, None, "Conta mensal não encontrada")
        if account.status not in ("closed", "confirmed_by_biometrics"):
            return (False, None, f"Conta precisa estar fechada para confirmação biométrica, status atual: {account.status}")

        now = utcnow()

        # Update account status — never override the original closed_at
        account.status = "confirmed_by_biometrics"
        account.biometric_verification_id = profile.id
        account.biometric_verified_at = now
        account.updated_at = now

        # Update profile
        profile.last_used_at = now

        # Log success event
        event = BiometricEvent(
            profile_id=profile.id,
            event_type="verify_success",
            success=True,
            match_score=score,
            detail=detail or "Digital verificada com sucesso",
            performed_by=performed_by,
            ip_address=ip_address,
        )
        self.db.add(event)

        self.audit.log(
            action="biometric_verify",
            entity_type="monthly_account",
            entity_id=monthly_account_id,
            user_id=performed_by,
            ip_address=ip_address,
            details=f"Biometric verification for client #{client_id} on account #{monthly_account_id} — score: {score}%",
        )

        self.db.commit()
        return (True, "confirmed_by_biometrics", "Digital verificada com sucesso! Conta confirmada por biometria.")

    def verify_identity(
        self,
        client_id: int,
        performed_by: Optional[int] = None,
        ip_address: Optional[str] = None,
        detail_context: Optional[str] = None,
    ) -> Tuple[bool, Optional[int], str]:
        """Verify a client's fingerprint without changing account/payment status."""
        profile = self.db.query(BiometricProfile).filter(
            BiometricProfile.client_id == client_id,
            BiometricProfile.is_active == True,
        ).first()
        if not profile:
            return (False, None, "Cliente não possui cadastro biométrico")

        if not self.check_consent(profile.id, "verification"):
            return (False, None, "Consentimento biométrico não autorizado")

        try:
            stored_template = self.decrypt_data(profile.encrypted_template)
        except Exception:
            return (False, None, "Erro ao descriptografar template biométrico")

        success, score, detail = self.reader.verify(stored_template)
        event = BiometricEvent(
            profile_id=profile.id,
            event_type="identity_verify_success" if success else "identity_verify_fail",
            success=success,
            match_score=score,
            detail=detail_context or detail or ("Digital verificada" if success else "Digital não reconhecida"),
            performed_by=performed_by,
            ip_address=ip_address,
        )
        self.db.add(event)

        if not success:
            self.db.flush()
            return (False, profile.id, detail or "Digital não reconhecida")

        profile.last_used_at = utcnow()
        self.audit.log(
            action="biometric_identity_verify",
            entity_type="client",
            entity_id=client_id,
            user_id=performed_by,
            ip_address=ip_address,
            details=detail_context or f"Biometric identity verification for client #{client_id} — score: {score}%",
        )
        self.db.flush()
        return (True, profile.id, "Digital verificada com sucesso.")
