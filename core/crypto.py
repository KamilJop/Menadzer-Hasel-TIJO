"""Cryptographic facade and orchestrator for key derivation and data encryption."""

from __future__ import annotations

from core.argon2_config import Argon2Config
from core.crypto_constants import (
    AES_256_KEY_SIZE_BYTES,
    AES_GCM_NONCE_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
)
from core.crypto_interfaces import BaseDataEncryptor, BaseKeyDerivator
from core.data_encryptor import DataEncryptor
from core.encrypted_payload import EncryptedPayload
from core.exceptions import (
    CryptoError,
    DecryptionError,
)
from core.key_derivator import KeyDerivator


class CryptoEngine:
    """Unified cryptographic facade orchestrating Key Derivation and Data Encryption services."""

    _default_derivator: KeyDerivator = KeyDerivator()
    _default_encryptor: DataEncryptor = DataEncryptor()

    def __init__(
        self,
        key_derivator: BaseKeyDerivator | None = None,
        data_encryptor: BaseDataEncryptor | None = None,
    ) -> None:
        """Initializes the facade with injectable derivator and encryptor providers.

        Args:
            key_derivator: Key derivation provider implementing BaseKeyDerivator.
            data_encryptor: Data encryption provider implementing BaseDataEncryptor.
        """
        self.key_derivator = key_derivator or self._default_derivator
        self.data_encryptor = data_encryptor or self._default_encryptor

    @classmethod
    def generate_salt(cls, length: int = DEFAULT_SALT_SIZE_BYTES) -> bytes:
        """Generates random salt bytes delegating to KeyDerivator.

        Args:
            length: Salt length in bytes.

        Returns:
            Random salt bytes.
        """
        return cls._default_derivator.generate_salt(length)

    @classmethod
    def generate_nonce(cls, length: int = AES_GCM_NONCE_SIZE_BYTES) -> bytes:
        """Generates unique nonce bytes delegating to DataEncryptor.

        Args:
            length: Nonce length in bytes.

        Returns:
            Random nonce bytes.
        """
        return cls._default_encryptor.generate_nonce(length)

    @classmethod
    def derive_key(
        cls,
        password: str | bytes,
        salt: bytes,
        config: Argon2Config | None = None,
    ) -> bytes:
        """Derives a symmetric key from a master password.

        Args:
            password: User password as a string or raw bytes.
            salt: Cryptographic salt bytes.
            config: Optional Argon2Config containing cost parameters.

        Returns:
            Derived 32-byte key.
        """
        return cls._default_derivator.derive_key(password, salt, config)

    @classmethod
    def encrypt_payload(
        cls,
        data: bytes,
        key: bytes,
        salt: bytes,
        nonce: bytes | None = None,
        associated_data: bytes | None = None,
    ) -> EncryptedPayload:
        """Encrypts data and bundles ciphertext, nonce, and salt into an EncryptedPayload.

        Args:
            data: Plaintext binary payload.
            key: 32-byte derived symmetric key.
            salt: Salt bytes used to derive the key.
            nonce: Optional 12-byte nonce.
            associated_data: Optional authenticated data.

        Returns:
            EncryptedPayload containing ciphertext, nonce, and salt.
        """
        ciphertext, active_nonce = cls._default_encryptor.encrypt(
            data=data,
            key=key,
            nonce=nonce,
            associated_data=associated_data,
        )
        return EncryptedPayload(
            ciphertext=ciphertext,
            nonce=active_nonce,
            salt=salt,
        )

    @classmethod
    def decrypt_payload(
        cls,
        payload: EncryptedPayload,
        key: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Decrypts an EncryptedPayload using its encapsulated ciphertext and nonce.

        Args:
            payload: EncryptedPayload holding ciphertext and nonce.
            key: 32-byte derived symmetric key.
            associated_data: Optional authenticated data.

        Raises:
            CryptoError: If payload is not an EncryptedPayload instance.
            DecryptionError: If tag verification fails or data is corrupted.

        Returns:
            Decrypted plaintext bytes.
        """
        if not isinstance(payload, EncryptedPayload):
            raise CryptoError("Payload must be an instance of EncryptedPayload.")

        return cls._default_encryptor.decrypt(
            ciphertext=payload.ciphertext,
            key=key,
            nonce=payload.nonce,
            associated_data=associated_data,
        )

    @classmethod
    def encrypt(
        cls,
        data: bytes,
        key: bytes,
        nonce: bytes | None = None,
        salt: bytes | None = None,
        associated_data: bytes | None = None,
    ) -> EncryptedPayload:
        """Convenience wrapper creating an EncryptedPayload.

        Args:
            data: Plaintext data to encrypt.
            key: 32-byte symmetric key.
            nonce: Optional 12-byte nonce.
            salt: Optional salt (generated if omitted).
            associated_data: Optional authenticated data.

        Returns:
            EncryptedPayload with ciphertext, nonce, and salt.
        """
        active_salt = salt if salt is not None else cls.generate_salt()
        return cls.encrypt_payload(
            data=data,
            key=key,
            salt=active_salt,
            nonce=nonce,
            associated_data=associated_data,
        )

    @classmethod
    def decrypt(
        cls,
        payload: EncryptedPayload,
        key: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Convenience wrapper decrypting an EncryptedPayload.

        Args:
            payload: EncryptedPayload holding ciphertext and nonce.
            key: 32-byte symmetric key.
            associated_data: Optional authenticated data.

        Returns:
            Decrypted plaintext bytes.
        """
        return cls.decrypt_payload(payload=payload, key=key, associated_data=associated_data)

    @classmethod
    def encrypt_text(
        cls,
        text: str,
        key: bytes,
        salt: bytes | None = None,
        associated_data: bytes | None = None,
    ) -> EncryptedPayload:
        """Encrypts a UTF-8 text string into an EncryptedPayload.

        Args:
            text: Plaintext string to encrypt.
            key: 32-byte symmetric key.
            salt: Optional salt to bundle with payload.
            associated_data: Optional authenticated data.

        Raises:
            TypeError: If text is not a str.

        Returns:
            EncryptedPayload containing ciphertext, nonce, and salt.
        """
        if not isinstance(text, str):
            raise TypeError(f"Expected text to be a str, got {type(text).__name__}.")
        return cls.encrypt(
            data=text.encode("utf-8"),
            key=key,
            salt=salt,
            associated_data=associated_data,
        )

    @classmethod
    def decrypt_text(
        cls,
        payload: EncryptedPayload,
        key: bytes,
        associated_data: bytes | None = None,
    ) -> str:
        """Decrypts an EncryptedPayload into a UTF-8 string.

        Args:
            payload: EncryptedPayload holding ciphertext and nonce.
            key: 32-byte symmetric key.
            associated_data: Optional authenticated data.

        Raises:
            DecryptionError: If decryption or UTF-8 decoding fails.

        Returns:
            Decrypted plaintext string.
        """
        plaintext_bytes = cls.decrypt(payload=payload, key=key, associated_data=associated_data)
        try:
            return plaintext_bytes.decode("utf-8")
        except UnicodeDecodeError as err:
            raise DecryptionError(f"Failed to decode decrypted payload as UTF-8: {err}") from err


__all__ = [
    "CryptoEngine",
    "DataEncryptor",
    "KeyDerivator",
]
