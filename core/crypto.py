"""Cryptographic operations including Argon2id key derivation and AES-256-GCM encryption."""

from __future__ import annotations

import os
import secrets

from argon2.exceptions import Argon2Error
from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.argon2_config import (
    AES_256_KEY_SIZE_BYTES,
    AES_GCM_NONCE_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
    Argon2Config,
)
from core.encrypted_payload import EncryptedPayload
from core.exceptions import (
    CryptoError,
    DecryptionError,
    InvalidKeyError,
    InvalidPasswordError,
)


class CryptoEngine:
    """Core cryptographic engine implementing Argon2id KDF and AES-256-GCM AEAD."""

    DEFAULT_CONFIG: Argon2Config = Argon2Config()

    @staticmethod
    def generate_salt(length: int = DEFAULT_SALT_SIZE_BYTES) -> bytes:
        """Generates cryptographically strong random salt bytes.

        Args:
            length: Length in bytes of the salt (default: 16 bytes).

        Raises:
            CryptoError: If requested length is less than 16 bytes.

        Returns:
            Randomly generated salt bytes.
        """
        if length < DEFAULT_SALT_SIZE_BYTES:
            raise CryptoError(
                f"Salt length must be at least {DEFAULT_SALT_SIZE_BYTES} bytes, got {length}."
            )
        return secrets.token_bytes(length)

    @staticmethod
    def generate_nonce(length: int = AES_GCM_NONCE_SIZE_BYTES) -> bytes:
        """Generates a cryptographically strong unique nonce for AES-GCM.

        Args:
            length: Nonce length in bytes (standard: 12 bytes).

        Raises:
            CryptoError: If requested length is not exactly 12 bytes.

        Returns:
            Randomly generated nonce bytes.
        """
        if length != AES_GCM_NONCE_SIZE_BYTES:
            raise CryptoError(
                f"AES-GCM nonce length must be exactly {AES_GCM_NONCE_SIZE_BYTES} bytes, got {length}."
            )
        return os.urandom(length)

    @classmethod
    def derive_key(
        cls,
        password: str | bytes,
        salt: bytes,
        config: Argon2Config | None = None,
    ) -> bytes:
        """Derives a 256-bit symmetric encryption key using Argon2id.

        Args:
            password: User password as a UTF-8 string or raw bytes.
            salt: Cryptographic salt bytes (at least 16 bytes).
            config: Optional Argon2Config containing cost parameters.

        Raises:
            InvalidPasswordError: If password is empty or not a valid string/bytes.
            CryptoError: If salt length is invalid or key derivation fails.

        Returns:
            Derived symmetric key bytes (32 bytes).
        """
        if not password:
            raise InvalidPasswordError("Password cannot be empty.")
        if not isinstance(password, (str, bytes)):
            raise InvalidPasswordError("Password must be a str or bytes instance.")

        if not isinstance(salt, (bytes, bytearray)) or len(salt) < DEFAULT_SALT_SIZE_BYTES:
            raise CryptoError(
                f"Salt must be at least {DEFAULT_SALT_SIZE_BYTES} bytes, got {len(salt) if isinstance(salt, (bytes, bytearray)) else type(salt).__name__}."
            )

        active_config = config or cls.DEFAULT_CONFIG
        secret_bytes = password.encode("utf-8") if isinstance(password, str) else password

        try:
            return hash_secret_raw(
                secret=secret_bytes,
                salt=bytes(salt),
                time_cost=active_config.time_cost,
                memory_cost=active_config.memory_cost,
                parallelism=active_config.parallelism,
                hash_len=active_config.hash_len,
                type=Type.ID,
            )
        except Argon2Error as err:
            raise CryptoError(f"Key derivation failed: {err}") from err

    @classmethod
    def encrypt(
        cls,
        data: bytes,
        key: bytes,
        nonce: bytes | None = None,
        salt: bytes | None = None,
        associated_data: bytes | None = None,
    ) -> EncryptedPayload:
        """Encrypts data using AES-256-GCM with associated authenticated data.

        Args:
            data: Plaintext binary payload to encrypt.
            key: 32-byte derived symmetric key.
            nonce: Optional 12-byte nonce (freshly generated if omitted).
            salt: Optional cryptographic salt (freshly generated if omitted).
            associated_data: Optional authenticated unencrypted data (AAD).

        Raises:
            InvalidKeyError: If key is not 32 bytes in length.
            CryptoError: If provided nonce or salt is invalid, or encryption fails.

        Returns:
            EncryptedPayload containing ciphertext, nonce, and derivation salt.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != AES_256_KEY_SIZE_BYTES:
            raise InvalidKeyError(
                f"AES-256 key must be exactly {AES_256_KEY_SIZE_BYTES} bytes, got {len(key) if isinstance(key, (bytes, bytearray)) else type(key).__name__}."
            )

        if nonce is None:
            active_nonce = cls.generate_nonce()
        else:
            if not isinstance(nonce, (bytes, bytearray)) or len(nonce) != AES_GCM_NONCE_SIZE_BYTES:
                raise CryptoError(
                    f"Nonce must be exactly {AES_GCM_NONCE_SIZE_BYTES} bytes, got {len(nonce) if isinstance(nonce, (bytes, bytearray)) else type(nonce).__name__}."
                )
            active_nonce = bytes(nonce)

        if salt is None:
            active_salt = cls.generate_salt()
        else:
            if not isinstance(salt, (bytes, bytearray)) or len(salt) < DEFAULT_SALT_SIZE_BYTES:
                raise CryptoError(
                    f"Salt must be at least {DEFAULT_SALT_SIZE_BYTES} bytes, got {len(salt) if isinstance(salt, (bytes, bytearray)) else type(salt).__name__}."
                )
            active_salt = bytes(salt)

        try:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(active_nonce, data, associated_data)
            return EncryptedPayload(
                ciphertext=ciphertext,
                nonce=active_nonce,
                salt=active_salt,
            )
        except Exception as err:
            raise CryptoError(f"Encryption failed: {err}") from err

    @classmethod
    def decrypt(
        cls,
        payload: EncryptedPayload,
        key: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Decrypts and verifies an AES-256-GCM EncryptedPayload.

        Args:
            payload: EncryptedPayload holding ciphertext and nonce.
            key: 32-byte derived symmetric key.
            associated_data: Optional authenticated data that must match what was used for encryption.

        Raises:
            InvalidKeyError: If key is not 32 bytes in length.
            CryptoError: If payload or nonce parameters are invalid.
            DecryptionError: If authentication tag verification fails or data is corrupted.

        Returns:
            Decrypted plaintext bytes.
        """
        if not isinstance(payload, EncryptedPayload):
            raise CryptoError("Payload must be an instance of EncryptedPayload.")

        if not isinstance(key, (bytes, bytearray)) or len(key) != AES_256_KEY_SIZE_BYTES:
            raise InvalidKeyError(
                f"AES-256 key must be exactly {AES_256_KEY_SIZE_BYTES} bytes, got {len(key) if isinstance(key, (bytes, bytearray)) else type(key).__name__}."
            )

        if len(payload.nonce) != AES_GCM_NONCE_SIZE_BYTES:
            raise CryptoError(
                f"Nonce must be exactly {AES_GCM_NONCE_SIZE_BYTES} bytes, got {len(payload.nonce)}."
            )

        try:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(payload.nonce, payload.ciphertext, associated_data)
        except InvalidTag as err:
            raise DecryptionError(
                "Decryption failed: Authentication tag verification failed or data is corrupted."
            ) from err
        except Exception as err:
            raise DecryptionError(f"Decryption failed: {err}") from err

    @classmethod
    def encrypt_text(
        cls,
        text: str,
        key: bytes,
        salt: bytes | None = None,
        associated_data: bytes | None = None,
    ) -> EncryptedPayload:
        """Convenience method to encrypt a UTF-8 string payload.

        Args:
            text: Plaintext string to encrypt.
            key: 32-byte derived symmetric key.
            salt: Optional salt to bundle with payload.
            associated_data: Optional authenticated unencrypted data.

        Returns:
            EncryptedPayload containing encrypted string bytes.
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
        """Convenience method to decrypt an EncryptedPayload into a UTF-8 string.

        Args:
            payload: EncryptedPayload holding ciphertext and nonce.
            key: 32-byte derived symmetric key.
            associated_data: Optional authenticated data.

        Raises:
            DecryptionError: If decryption or UTF-8 decoding fails.

        Returns:
            Decrypted plaintext UTF-8 string.
        """
        plaintext_bytes = cls.decrypt(payload=payload, key=key, associated_data=associated_data)
        try:
            return plaintext_bytes.decode("utf-8")
        except UnicodeDecodeError as err:
            raise DecryptionError(f"Failed to decode decrypted payload as UTF-8: {err}") from err
