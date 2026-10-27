"""Key derivation service implementing password-to-key derivation using Argon2id."""

from __future__ import annotations

import secrets

from argon2.exceptions import Argon2Error
from argon2.low_level import Type, hash_secret_raw

from core.argon2_config import Argon2Config
from core.crypto_constants import DEFAULT_SALT_SIZE_BYTES
from core.crypto_interfaces import BaseKeyDerivator
from core.exceptions import CryptoError, InvalidPasswordError


class KeyDerivator(BaseKeyDerivator):
    """Derives symmetric encryption keys from passwords using Argon2id."""

    DEFAULT_CONFIG: Argon2Config = Argon2Config()

    def generate_salt(self, length: int = DEFAULT_SALT_SIZE_BYTES) -> bytes:
        """Generates cryptographically strong random salt bytes.

        Args:
            length: Length in bytes of the salt (minimum 16 bytes).

        Raises:
            CryptoError: If requested length is less than 16 bytes.

        Returns:
            Cryptographically secure random salt bytes.
        """
        if length < DEFAULT_SALT_SIZE_BYTES:
            raise CryptoError(
                f"Salt length must be at least {DEFAULT_SALT_SIZE_BYTES} bytes, got {length}."
            )
        return secrets.token_bytes(length)

    def derive_key(
        self,
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
                f"Salt must be at least {DEFAULT_SALT_SIZE_BYTES} bytes, got "
                f"{len(salt) if isinstance(salt, (bytes, bytearray)) else type(salt).__name__}."
            )

        active_config = config or self.DEFAULT_CONFIG
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


__all__ = ["KeyDerivator"]
