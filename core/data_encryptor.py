"""Data encryption service implementing AES-256-GCM authenticated encryption."""

from __future__ import annotations

import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.crypto_constants import (
    AES_256_KEY_SIZE_BYTES,
    AES_GCM_NONCE_SIZE_BYTES,
)
from core.crypto_interfaces import BaseDataEncryptor
from core.exceptions import (
    CryptoError,
    DecryptionError,
    InvalidKeyError,
)


class DataEncryptor(BaseDataEncryptor):
    """Encrypts and decrypts binary payloads using AES-256-GCM AEAD."""

    def generate_nonce(self, length: int = AES_GCM_NONCE_SIZE_BYTES) -> bytes:
        """Generates a cryptographically strong unique nonce for encryption.

        Args:
            length: Nonce length in bytes (must be exactly 12 bytes).

        Raises:
            CryptoError: If requested length is not exactly 12 bytes.

        Returns:
            Cryptographically secure unique nonce bytes.
        """
        if length != AES_GCM_NONCE_SIZE_BYTES:
            raise CryptoError(
                f"Nonce length must be exactly {AES_GCM_NONCE_SIZE_BYTES} bytes, got {length}."
            )
        return secrets.token_bytes(length)

    def encrypt(
        self,
        data: bytes,
        key: bytes,
        nonce: bytes | None = None,
        associated_data: bytes | None = None,
    ) -> tuple[bytes, bytes]:
        """Encrypts data using AES-256-GCM with optional associated data.

        Args:
            data: Plaintext binary payload to encrypt.
            key: 32-byte symmetric encryption key.
            nonce: Optional 12-byte initialization vector (generated if omitted).
            associated_data: Optional authenticated unencrypted data (AAD).

        Raises:
            InvalidKeyError: If key length is not exactly 32 bytes.
            CryptoError: If nonce length is invalid or encryption fails.

        Returns:
            Tuple of (ciphertext_with_tag, nonce).
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != AES_256_KEY_SIZE_BYTES:
            raise InvalidKeyError(
                f"Key must be exactly {AES_256_KEY_SIZE_BYTES} bytes, got "
                f"{len(key) if isinstance(key, (bytes, bytearray)) else type(key).__name__}."
            )

        if nonce is None:
            active_nonce = self.generate_nonce()
        else:
            if not isinstance(nonce, (bytes, bytearray)) or len(nonce) != AES_GCM_NONCE_SIZE_BYTES:
                raise CryptoError(
                    f"Nonce must be exactly {AES_GCM_NONCE_SIZE_BYTES} bytes, got "
                    f"{len(nonce) if isinstance(nonce, (bytes, bytearray)) else type(nonce).__name__}."
                )
            active_nonce = bytes(nonce)

        try:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(active_nonce, data, associated_data)
            return ciphertext, active_nonce
        except Exception as err:
            raise CryptoError(f"Encryption failed: {err}") from err

    def decrypt(
        self,
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Decrypts and verifies AES-256-GCM ciphertext.

        Args:
            ciphertext: Encrypted binary data including authentication tag.
            key: 32-byte symmetric encryption key.
            nonce: 12-byte initialization vector used during encryption.
            associated_data: Optional authenticated data that must match encryption.

        Raises:
            InvalidKeyError: If key length is not exactly 32 bytes.
            CryptoError: If nonce length is invalid.
            DecryptionError: If tag verification fails or data is corrupted.

        Returns:
            Decrypted plaintext bytes.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != AES_256_KEY_SIZE_BYTES:
            raise InvalidKeyError(
                f"Key must be exactly {AES_256_KEY_SIZE_BYTES} bytes, got "
                f"{len(key) if isinstance(key, (bytes, bytearray)) else type(key).__name__}."
            )

        if not isinstance(nonce, (bytes, bytearray)) or len(nonce) != AES_GCM_NONCE_SIZE_BYTES:
            raise CryptoError(
                f"Nonce must be exactly {AES_GCM_NONCE_SIZE_BYTES} bytes, got "
                f"{len(nonce) if isinstance(nonce, (bytes, bytearray)) else type(nonce).__name__}."
            )

        try:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(bytes(nonce), bytes(ciphertext), associated_data)
        except InvalidTag as err:
            raise DecryptionError(
                "Decryption failed: Authentication tag verification failed or data is corrupted."
            ) from err
        except Exception as err:
            raise DecryptionError(f"Decryption failed: {err}") from err


__all__ = ["DataEncryptor"]
