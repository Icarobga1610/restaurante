"""Abstract base class for all biometric reader implementations."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BiometricReader(ABC):
    """Abstract interface for fingerprint reader integration.

    All implementations (demo, SDK, USB) must inherit from this class.
    """

    @abstractmethod
    def enroll(self, timeout_seconds: int = 30) -> Tuple[bool, Optional[str], Optional[str]]:
        """Capture a fingerprint and return (success, encrypted_template_hash, device_info).

        - success: True if capture succeeded
        - encrypted_template_hash: The encrypted template/token/hash (never the raw image)
        - device_info: Optional string identifying the reader/device
        """
        ...

    @abstractmethod
    def verify(self, stored_template: str, timeout_seconds: int = 30) -> Tuple[bool, Optional[int], Optional[str]]:
        """Verify a fingerprint against a stored template.

        Returns (success, match_score_0_to_100, detail).
        - success: True if fingerprint matches
        - match_score: Confidence score 0-100 (None if not applicable)
        - detail: Human-readable result detail
        """
        ...

    @abstractmethod
    def cancel(self) -> None:
        """Cancel any pending capture/verification operation."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the reader hardware is connected and ready."""
        ...

    @property
    @abstractmethod
    def reader_name(self) -> str:
        """Human-readable name of the reader implementation."""
        ...

    @abstractmethod
    def generate_template_hash(self, raw_template: str) -> str:
        """Generate a deterministic hash/token from raw SDK template data.

        This ensures we never store raw fingerprint data — only a derived token.
        """
        ...
