"""Encrypted payload container with base64 serialization."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Any

from core.crypto_constants import (
    AES_GCM_NONCE_SIZE_BYTES,
    AES_GCM_TAG_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
)
from core.exceptions import CryptoError


@dataclass(frozen=True)
class EncryptedPayload:
    """Immutable container holding ciphertext, AEAD nonce, and KDF derivation salt.

    Attributes:
        ciphertext: Encrypted binary data including authentication tag (AEAD).
        nonce: Initialization vector (12 bytes for AES-GCM).
        salt: Cryptographic salt used during key derivation (minimum 16 bytes).
    """

    ciphertext: bytes
    nonce: bytes
    salt: bytes

    def __post_init__(self) -> None:
        """Validates payload field sizes upon construction.

        Raises:
            CryptoError: If ciphertext, nonce, or salt sizes are invalid.
        """
        if not isinstance(self.nonce, (bytes, bytearray)) or len(self.nonce) != AES_GCM_NONCE_SIZE_BYTES:
            raise CryptoError(
                f"Nonce must be exactly {AES_GCM_NONCE_SIZE_BYTES} bytes, got "
                f"{len(self.nonce) if isinstance(self.nonce, (bytes, bytearray)) else type(self.nonce).__name__}."
            )

        if not isinstance(self.salt, (bytes, bytearray)) or len(self.salt) < DEFAULT_SALT_SIZE_BYTES:
            raise CryptoError(
                f"Salt must be at least {DEFAULT_SALT_SIZE_BYTES} bytes, got "
                f"{len(self.salt) if isinstance(self.salt, (bytes, bytearray)) else type(self.salt).__name__}."
            )

        if not isinstance(self.ciphertext, (bytes, bytearray)) or len(self.ciphertext) < AES_GCM_TAG_SIZE_BYTES:
            raise CryptoError(
                f"Ciphertext must be at least {AES_GCM_TAG_SIZE_BYTES} bytes (including AEAD tag), got "
                f"{len(self.ciphertext) if isinstance(self.ciphertext, (bytes, bytearray)) else type(self.ciphertext).__name__}."
            )

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
                ciphertext=base64.b64decode(data["ciphertext"], validate=True),
                nonce=base64.b64decode(data["nonce"], validate=True),
                salt=base64.b64decode(data["salt"], validate=True),
            )
        except (KeyError, ValueError, TypeError, binascii.Error) as err:
            raise CryptoError(f"Failed to deserialize encrypted payload: {err}") from err
