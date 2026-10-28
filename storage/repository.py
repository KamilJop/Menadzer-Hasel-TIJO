"""Encrypted vault repository coordinating serialization, encryption, and persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.argon2_config import Argon2Config
from core.crypto import CryptoEngine
from core.encrypted_payload import EncryptedPayload
from core.exceptions import (
    CryptoError,
    DecryptionError,
    InvalidPasswordError,
    StorageError,
    VaultCorruptedError,
    VaultNotFoundError,
)
from core.vault import Vault
from storage.file_writer import FileWriter
from storage.interfaces import BaseFileWriter, BaseVaultRepository


class VaultRepository(BaseVaultRepository):
    """Coordinates vault serialization, authenticated encryption, and safe file persistence."""

    DEFAULT_FORMAT_VERSION: int = 1

    def __init__(
        self,
        default_path: str | Path | None = None,
        crypto_engine: CryptoEngine | None = None,
        kdf_config: Argon2Config | None = None,
        file_writer: BaseFileWriter | None = None,
    ) -> None:
        """Initializes the repository with optional default path and injectable dependencies.

        Args:
            default_path: Optional default file path used when no explicit path is passed to operations.
            crypto_engine: Cryptographic facade (defaults to default CryptoEngine).
            kdf_config: Optional Argon2 parameters (defaults to Argon2Config standard presets).
            file_writer: Safe file writer provider (defaults to FileWriter).
        """
        self._default_path: Path | None = Path(default_path).resolve() if default_path is not None else None
        self._crypto_engine: CryptoEngine = crypto_engine if crypto_engine is not None else CryptoEngine()
        self._kdf_config: Argon2Config | None = kdf_config
        self._file_writer: BaseFileWriter = file_writer if file_writer is not None else FileWriter()

    @property
    def default_path(self) -> Path | None:
        """Configured default vault file path.

        Returns:
            Resolved Path instance or None if no default was set.
        """
        return self._default_path

    def exists(self, file_path: str | Path | None = None) -> bool:
        """Checks whether the vault file exists and is a regular file.

        Args:
            file_path: Optional path to verify (defaults to configured default path).

        Returns:
            True if file exists and is a regular file, False otherwise.
        """
        resolved = self._resolve_path(file_path)
        return resolved.is_file()

    def save(
        self,
        vault: Vault,
        password: str | bytes,
        file_path: str | Path | None = None,
    ) -> Path:
        """Serializes, encrypts, and safely persists vault contents.

        Args:
            vault: Vault instance to encrypt and store.
            password: Master password string or bytes.
            file_path: Optional destination path (defaults to repository default_path).

        Raises:
            TypeError: If vault is not an instance of Vault.
            ValueError: If password is empty.
            CryptoError: If encryption or key derivation fails.
            StorageError: If disk writing fails.

        Returns:
            Resolved Path of the saved vault file.
        """
        if not isinstance(vault, Vault):
            raise TypeError(f"Expected Vault instance, got {type(vault).__name__}.")

        self._validate_password(password)
        dest_path = self._resolve_path(file_path)

        vault_dict = vault.to_dict()
        plaintext_bytes = json.dumps(vault_dict, ensure_ascii=False).encode("utf-8")

        salt = self._crypto_engine.generate_salt()
        key = self._crypto_engine.derive_key(
            password=password,
            salt=salt,
            config=self._kdf_config,
        )

        payload = self._crypto_engine.encrypt_payload(
            data=plaintext_bytes,
            key=key,
            salt=salt,
        )

        container: dict[str, Any] = {
            "version": self.DEFAULT_FORMAT_VERSION,
            **payload.to_dict(),
        }
        json_bytes = json.dumps(container, indent=2).encode("utf-8")

        self._file_writer.write_bytes(dest_path, json_bytes)
        return dest_path

    def load(
        self,
        password: str | bytes,
        file_path: str | Path | None = None,
    ) -> Vault:
        """Loads and decrypts a vault file from disk.

        Args:
            password: Master password string or bytes.
            file_path: Optional vault file path (defaults to repository default_path).

        Raises:
            ValueError: If password is empty.
            VaultNotFoundError: If the vault file does not exist.
            VaultCorruptedError: If file content or container structure is invalid.
            InvalidPasswordError: If decryption fails due to wrong password or tampered data.
            StorageError: If reading the file from disk fails.

        Returns:
            Reconstructed Vault instance populated with entries.
        """
        self._validate_password(password)
        target_path = self._resolve_path(file_path)

        if not target_path.is_file():
            raise VaultNotFoundError(f"Vault file not found at: {target_path}")

        try:
            raw_bytes = target_path.read_bytes()
        except OSError as err:
            raise StorageError(f"Failed to read vault file from '{target_path}': {err}") from err

        try:
            container = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise VaultCorruptedError(f"Vault file at '{target_path}' contains invalid JSON: {err}") from err

        if not isinstance(container, dict):
            raise VaultCorruptedError(f"Vault container at '{target_path}' must be a JSON object.")

        try:
            payload = EncryptedPayload.from_dict(container)
        except CryptoError as err:
            raise VaultCorruptedError(
                f"Vault file at '{target_path}' contains corrupted encrypted headers: {err}"
            ) from err

        key = self._crypto_engine.derive_key(
            password=password,
            salt=payload.salt,
            config=self._kdf_config,
        )

        try:
            decrypted_bytes = self._crypto_engine.decrypt_payload(
                payload=payload,
                key=key,
            )
        except DecryptionError as err:
            raise InvalidPasswordError(
                "Failed to decrypt vault: incorrect master password or tampered data."
            ) from err

        try:
            vault_dict = json.loads(decrypted_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise VaultCorruptedError(
                f"Decrypted payload from '{target_path}' is corrupted and could not be decoded as JSON: {err}"
            ) from err

        if not isinstance(vault_dict, dict) or "entries" not in vault_dict:
            raise VaultCorruptedError(
                f"Decrypted vault structure from '{target_path}' lacks valid 'entries' collection."
            )

        try:
            return Vault.from_dict(vault_dict)
        except Exception as err:
            raise VaultCorruptedError(
                f"Failed to instantiate Vault from payload at '{target_path}': {err}"
            ) from err

    def _resolve_path(self, file_path: str | Path | None) -> Path:
        """Resolves target path prioritizing explicit argument over default_path.

        Args:
            file_path: Optional path to resolve.

        Raises:
            ValueError: If neither explicit path nor default_path is available.

        Returns:
            Resolved Path instance.
        """
        if file_path is not None:
            return Path(file_path).resolve()
        if self._default_path is not None:
            return self._default_path
        raise ValueError("No vault file path provided and no default path configured.")

    @staticmethod
    def _validate_password(password: str | bytes) -> None:
        """Validates that the provided password is non-empty.

        Args:
            password: Password string or bytes.

        Raises:
            TypeError: If password is not str or bytes.
            ValueError: If password is empty.
        """
        if not isinstance(password, (str, bytes)):
            raise TypeError(f"Password must be str or bytes, got {type(password).__name__}.")
        if len(password) == 0:
            raise ValueError("Master password cannot be empty.")


__all__ = [
    "VaultRepository",
]
