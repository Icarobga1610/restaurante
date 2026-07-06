"""Demo-mode biometric reader.

Simulates fingerprint capture for development/testing when no physical reader is available.
In production, swap this out for a real SDK implementation.
"""

import hashlib
import secrets
import time
from typing import Optional, Tuple

from app.biometric_bridge.base import BiometricReader


class DemoBiometricReader(BiometricReader):
    """Simulates a biometric fingerprint reader for development/demo purposes."""

    # Demo mode always "succeeds" with simulated data
    _connected: bool = True
    _reader_name: str = "DemoReader v1.0 (simulated)"
    _capture_delay: float = 0.8  # Simulate processing time

    def enroll(self, timeout_seconds: int = 30) -> Tuple[bool, Optional[str], Optional[str]]:
        """Simulate fingerprint enrollment.

        Returns a SHA-256 hash derived from random data + a static prefix,
        simulating what a real SDK would return as an encrypted template token.
        """
        time.sleep(self._capture_delay)

        # Simulate SDK returning an encrypted template hash
        random_seed = secrets.token_hex(32)
        # In a real SDK, this would be the encrypted template output
        raw_template = f"demo_template_{random_seed}"
        encrypted_hash = hashlib.sha256(raw_template.encode()).hexdigest()

        device_info = "demo_device_fingerprint_simulator"

        return (True, encrypted_hash, device_info)

    def verify(
        self, stored_template: str, timeout_seconds: int = 30
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Simulate fingerprint verification against a stored template.

        In demo mode, verification always succeeds with a high confidence score.
        This simulates a real SDK verifying the live fingerprint against the
        stored encrypted template on-device.
        """
        time.sleep(self._capture_delay)

        # Demo mode: always matches with high confidence
        # In production, the real SDK would perform on-device matching
        # against the encrypted template and return score + match result
        confidence = 92  # 92% confidence in demo mode
        is_match = True
        detail = "Biometria compatível (modo demo)"

        return (is_match, confidence, detail)

    def cancel(self) -> None:
        """Cancel any pending operation — no-op in demo mode."""
        pass

    @property
    def is_connected(self) -> bool:
        return self._connected

    @is_connected.setter
    def is_connected(self, value: bool):
        self._connected = value

    @property
    def reader_name(self) -> str:
        return self._reader_name

    def generate_template_hash(self, raw_template: str) -> str:
        """Generate a deterministic SHA-256 hash from a raw template string.

        This is what ensures we never store raw fingerprint data —
        only a derived cryptographic hash.
        """
        return hashlib.sha256(f"restaurante_{raw_template}_biometric".encode()).hexdigest()
