"""Encrypted JSON backup importer for vault credentials."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.argon2_config import Argon2Config
from core.crypto import CryptoEngine
from core.encrypted_payload import EncryptedPayload
from core.entry import Entry
from core.exceptions import (
    CryptoError,
    DecryptionError,
    InvalidPasswordError,
    VaultImportError,
    VaultNotFoundError,
)
from storage.interfaces.importer import BaseVaultImporter


class EncryptedJsonImporter(BaseVaultImporter):
    """Decrypts and imports credentials from an authenticated backup container file."""

    def __init__(
        self,
        crypto_engine: CryptoEngine | None = None,
        kdf_config: Argon2Config | None = None,
    ) -> None:
        """Initializes the encrypted importer with cryptographic dependencies.

        Args:
            crypto_engine: Cryptographic engine provider (defaults to default CryptoEngine).
            kdf_config: Argon2 KDF configuration presets (defaults to Argon2Config standard).
        """
        self._crypto_engine: CryptoEngine = crypto_engine if crypto_engine is not None else CryptoEngine()
        self._kdf_config: Argon2Config | None = kdf_config

    def import_entries(
        self,
        source_path: str | Path,
        password: str | bytes | None = None,
        **kwargs: Any,
    ) -> list[Entry]:
        """Decrypts and imports credentials from an authenticated backup container.

        Args:
            source_path: File system path of the encrypted backup file.
            password: Required export password used to decrypt the container.
            **kwargs: Additional optional parameters.

        Raises:
            ValueError: If password is empty or not provided.
            VaultNotFoundError: If the backup file does not exist.
            InvalidPasswordError: If decryption fails due to wrong password or tampered data.
            VaultImportError: If reading, parsing, or container structure is invalid.

        Returns:
            List of decrypted and validated Entry instances.
        """
        self._validate_password(password)
        src_path = Path(source_path).resolve()
        if not src_path.is_file():
            raise VaultNotFoundError(f"Encrypted backup file not found at: {src_path}")

        try:
            raw_bytes = src_path.read_bytes()
        except OSError as err:
            raise VaultImportError(f"Failed to read backup file from '{src_path}': {err}") from err

        try:
            container = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise VaultImportError(f"Backup file at '{src_path}' contains invalid JSON: {err}") from err

        if not isinstance(container, dict):
            raise VaultImportError(f"Backup file at '{src_path}' must be a JSON object.")

        try:
            payload = EncryptedPayload.from_dict(container)
        except CryptoError as err:
            raise VaultImportError(
                f"Backup file at '{src_path}' contains corrupted encrypted headers: {err}"
            ) from err

        assert password is not None
        key = self._crypto_engine.derive_key(
            password=password,
            salt=payload.salt,
            config=self._kdf_config,
        )

        try:
            decrypted_bytes = self._crypto_engine.decrypt_payload(payload=payload, key=key)
        except DecryptionError as err:
            raise InvalidPasswordError(
                "Failed to decrypt backup: incorrect export password or corrupted payload."
            ) from err

        try:
            content = json.loads(decrypted_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise VaultImportError(
                f"Decrypted backup from '{src_path}' contains invalid JSON: {err}"
            ) from err

        if not isinstance(content, dict) or "entries" not in content or not isinstance(content["entries"], list):
            raise VaultImportError(
                f"Decrypted backup from '{src_path}' does not contain a valid 'entries' list."
            )

        try:
            return [Entry.from_dict(item) for item in content["entries"]]
        except Exception as err:
            raise VaultImportError(
                f"Failed to deserialize entries from decrypted backup '{src_path}': {err}"
            ) from err

    @staticmethod
    def _validate_password(password: str | bytes | None) -> None:
        """Validates that a password is provided and non-empty.

        Args:
            password: Password string or bytes.

        Raises:
            ValueError: If password is None or empty.
            TypeError: If password is not str or bytes.
        """
        if password is None:
            raise ValueError("Password is required for encrypted import.")
        if not isinstance(password, (str, bytes)):
            raise TypeError(f"Password must be str or bytes, got {type(password).__name__}.")
        if len(password) == 0:
            raise ValueError("Password cannot be empty.")


__all__ = [
    "EncryptedJsonImporter",
]
