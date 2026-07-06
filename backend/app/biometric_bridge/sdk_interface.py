"""SDK Interface for future biometric reader integration.

This module provides the structure for integrating with real fingerprint
reader hardware via USB/SDK. Currently a placeholder — extend when hardware is available.

Supported reader types (planned):
- USB fingerprint scanners (e.g., DigitalPersona, Futronic, Secugen)
- Mobile biometric SDKs (Android/iOS fingerprint APIs)
- WebAuthn / FIDO2 authenticators
"""

from typing import Optional, Tuple

from app.biometric_bridge.base import BiometricReader


class SDKBiometricReader(BiometricReader):
    """Integration with a real fingerprint reader SDK.

    TODO: Implement when hardware is available.
    Steps to integrate:
    1. Install vendor SDK and Python bindings
    2. Implement enroll() calling the SDK's capture API
    3. Implement verify() calling the SDK's match/verify API
    4. Ensure the SDK returns an encrypted template (not raw image)
    5. Use generate_template_hash() to derive the stored token
    """

    _connected: bool = False
    _reader_name: str = "SDK Reader (not connected)"
    _sdk_initialized: bool = False

    def __init__(self, sdk_path: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the SDK reader.

        Args:
            sdk_path: Path to the vendor SDK library (.so/.dll/.dylib)
            api_key: Optional API key for cloud-based biometric services
        """
        self._sdk_path = sdk_path
        self._api_key = api_key
        # TODO: Initialize vendor SDK here
        # Example:
        #   self._sdk = load_vendor_sdk(sdk_path)
        #   self._sdk.initialize(api_key)
        #   self._connected = self._sdk.is_reader_connected()

    def enroll(self, timeout_seconds: int = 30) -> Tuple[bool, Optional[str], Optional[str]]:
        """Capture fingerprint using the vendor SDK.

        Returns (success, encrypted_template_hash, device_info).
        """
        # TODO: Implement with vendor SDK
        # Example:
        #   result = self._sdk.capture_fingerprint(timeout=timeout_seconds)
        #   if result.success:
        #       encrypted = self.generate_template_hash(result.template)
        #       return (True, encrypted, f"sdk_v1:{result.device_id}")
        raise NotImplementedError("SDK reader not yet implemented. Use DemoBiometricReader.")

    def verify(
        self, stored_template: str, timeout_seconds: int = 30
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Verify fingerprint against a stored template using the vendor SDK."""
        # TODO: Implement with vendor SDK
        # Example:
        #   result = self._sdk.verify_fingerprint(
        #       template=stored_template,
        #       timeout=timeout_seconds
        #   )
        #   return (result.match, result.confidence, result.detail)
        raise NotImplementedError("SDK reader not yet implemented. Use DemoBiometricReader.")

    def cancel(self) -> None:
        """Cancel any pending capture/verification operation."""
        # TODO: Implement with vendor SDK
        # self._sdk.cancel()
        pass

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def reader_name(self) -> str:
        return self._reader_name

    def generate_template_hash(self, raw_template: str) -> str:
        """Generate a deterministic hash from raw SDK template data.

        Uses SHA-256 to ensure we never store raw fingerprint data.
        The hash is what gets encrypted and stored in the database.
        """
        import hashlib
        return hashlib.sha256(f"restaurante_sdk_{raw_template}".encode()).hexdigest()
