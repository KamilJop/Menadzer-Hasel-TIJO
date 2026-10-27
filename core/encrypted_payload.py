"""Encrypted payload container with base64 serialization."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from core.exceptions import CryptoError


@dataclass
class EncryptedPayload:
    """Container holding ciphertext, AEAD nonce, and KDF derivation salt.

    Attributes:
        ciphertext: Encrypted binary data including authentication tag (AEAD).
        nonce: Initialization vector (12 bytes for AES-GCM).
        salt: Cryptographic salt used during key derivation.
    """

    ciphertext: bytes
    nonce: bytes
    salt: bytes

    def to_dict(self) -> dict[str, str]:
        """Serializes the binary payload into a base64-encoded dictionary.

        Returns:
            Dictionary with base64 encoded strings for ciphertext, nonce, and salt.
        """
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode("ascii"),
            "nonce": base64.b64encode(self.nonce).decode("ascii"),
            "salt": base64.b64encode(self.salt).decode("ascii"),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EncryptedPayload:
        """Constructs an EncryptedPayload from a base64-encoded dictionary.

        Args:
            data: Dictionary containing 'ciphertext', 'nonce', and 'salt'.

        Raises:
            CryptoError: If decoding fails or required fields are missing.

        Returns:
            EncryptedPayload instance with decoded binary attributes.
        """
        try:
            return cls(
                ciphertext=base64.b64decode(data["ciphertext"]),
                nonce=base64.b64decode(data["nonce"]),
                salt=base64.b64decode(data["salt"]),
            )
        except (KeyError, ValueError, TypeError) as err:
            raise CryptoError(f"Failed to deserialize encrypted payload: {err}") from err
