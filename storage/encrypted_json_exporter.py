"""Encrypted JSON backup exporter for vault credentials."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from core.argon2_config import Argon2Config
from core.crypto import CryptoEngine
from core.entry import Entry
from core.exceptions import CryptoError, ExportError, StorageError
from core.utils import get_utc_now_iso
from storage.file_writer import FileWriter
from storage.interfaces.exporter import BaseVaultExporter
from storage.interfaces.file_writer import BaseFileWriter


class EncryptedJsonExporter(BaseVaultExporter):
    """Exports credentials to an authenticated AES-256-GCM + Argon2id encrypted container file."""

    DEFAULT_FORMAT_VERSION: int = 1
    EXPORT_TYPE: str = "encrypted_backup"

    def __init__(
        self,
        crypto_engine: CryptoEngine | None = None,
        kdf_config: Argon2Config | None = None,
        file_writer: BaseFileWriter | None = None,
    ) -> None:
        """Initializes the encrypted exporter with dependencies.

        Args:
            crypto_engine: Cryptographic engine provider (defaults to default CryptoEngine).
            kdf_config: Argon2 KDF configuration presets (defaults to Argon2Config standard).
            file_writer: Safe file writer provider (defaults to FileWriter).
        """
        self._crypto_engine: CryptoEngine = crypto_engine if crypto_engine is not None else CryptoEngine()
        self._kdf_config: Argon2Config | None = kdf_config
        self._file_writer: BaseFileWriter = file_writer if file_writer is not None else FileWriter()

    def export_entries(
        self,
        entries: Sequence[Entry],
        destination_path: str | Path,
        password: str | bytes | None = None,
        **kwargs: Any,
    ) -> Path:
        """Exports entries to an encrypted container file using Argon2id and AES-256-GCM.

        Args:
            entries: Sequence of Entry objects to encrypt and export.
            destination_path: Destination file path.
            password: Required export password for key derivation.
            **kwargs: Additional optional parameters.

        Raises:
            ValueError: If export password is empty or not provided.
            TypeError: If entries contain invalid items or password has invalid type.
            ExportError: If encryption or file writing fails.

        Returns:
            Resolved Path of the saved encrypted container file.
        """
        self._validate_password(password)
        dest_path = Path(destination_path).resolve()

        for item in entries:
            if not isinstance(item, Entry):
                raise TypeError(f"Expected Entry instance in entries, got {type(item).__name__}.")

        content: dict[str, Any] = {
            "format_version": self.DEFAULT_FORMAT_VERSION,
            "export_type": self.EXPORT_TYPE,
            "exported_at": get_utc_now_iso(),
            "entries_count": len(entries),
            "entries": [entry.to_dict() for entry in entries],
        }

        salt = self._crypto_engine.generate_salt()
        assert password is not None
        key = self._crypto_engine.derive_key(
            password=password,
            salt=salt,
            config=self._kdf_config,
        )

        try:
            plaintext_bytes = json.dumps(content, ensure_ascii=False).encode("utf-8")
            payload = self._crypto_engine.encrypt_payload(
                data=plaintext_bytes,
                key=key,
                salt=salt,
            )

            container: dict[str, Any] = {
                "format_version": self.DEFAULT_FORMAT_VERSION,
                "export_type": self.EXPORT_TYPE,
                "exported_at": content["exported_at"],
                "kdf": "Argon2id",
                "cipher": "AES-256-GCM",
                **payload.to_dict(),
            }

            json_bytes = json.dumps(container, indent=2).encode("utf-8")
            self._file_writer.write_bytes(dest_path, json_bytes)
            return dest_path
        except (CryptoError, StorageError) as err:
            raise ExportError(f"Failed to export encrypted backup to '{dest_path}': {err}") from err

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
            raise ValueError("Password is required for encrypted export.")
        if not isinstance(password, (str, bytes)):
            raise TypeError(f"Password must be str or bytes, got {type(password).__name__}.")
        if len(password) == 0:
            raise ValueError("Password cannot be empty.")


__all__ = [
    "EncryptedJsonExporter",
]
