"""Abstract base classes establishing contracts for cryptographic services."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.argon2_config import Argon2Config
from core.crypto_constants import (
    AES_GCM_NONCE_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
)


class BaseKeyDerivator(ABC):
    """Abstract base class establishing the contract for key derivation services."""

    @abstractmethod
    def generate_salt(self, length: int = DEFAULT_SALT_SIZE_BYTES) -> bytes:
        """Generates cryptographically secure random salt bytes.

        Args:
            length: Length in bytes of the salt.

        Returns:
            Cryptographically secure salt bytes.
        """

    @abstractmethod
    def derive_key(
        self,
        password: str | bytes,
        salt: bytes,
        config: Argon2Config | None = None,
    ) -> bytes:
        """Derives a symmetric key from a password and salt.

        Args:
            password: User password as a string or raw bytes.
            salt: Cryptographic salt bytes.
            config: Optional Argon2Config containing cost parameters.

        Returns:
            Derived key bytes.
        """


class BaseDataEncryptor(ABC):
    """Abstract base class establishing the contract for data encryption services."""

    @abstractmethod
    def generate_nonce(self, length: int = AES_GCM_NONCE_SIZE_BYTES) -> bytes:
        """Generates a cryptographically strong unique nonce.

        Args:
            length: Nonce length in bytes.

        Returns:
            Unique nonce bytes.
        """

    @abstractmethod
    def encrypt(
        self,
        data: bytes,
        key: bytes,
        nonce: bytes | None = None,
        associated_data: bytes | None = None,
    ) -> tuple[bytes, bytes]:
        """Encrypts data with an authenticated cipher.

        Args:
            data: Plaintext data bytes to encrypt.
            key: Symmetric key bytes.
            nonce: Optional nonce bytes.
            associated_data: Optional authenticated unencrypted data.

        Returns:
            Tuple containing (ciphertext, nonce).
        """

    @abstractmethod
    def decrypt(
        self,
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Decrypts and authenticates ciphertext.

        Args:
            ciphertext: Encrypted binary data with authentication tag.
            key: Symmetric key bytes.
            nonce: Initialization vector used during encryption.
            associated_data: Optional authenticated data.

        Returns:
            Decrypted plaintext bytes.
        """


__all__ = [
    "BaseDataEncryptor",
    "BaseKeyDerivator",
]
