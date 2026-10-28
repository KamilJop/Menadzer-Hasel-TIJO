"""Plaintext JSON importer for vault credentials."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.entry import Entry
from core.exceptions import (
    InvalidEntryError,
    VaultImportError,
    VaultNotFoundError,
)
from storage.interfaces.importer import BaseVaultImporter


class PlaintextJsonImporter(BaseVaultImporter):
    """Imports credentials from an unencrypted JSON file with browser field normalization."""

    def import_entries(
        self,
        source_path: str | Path,
        **kwargs: Any,
    ) -> list[Entry]:
        """Imports entries from an unencrypted JSON file with browser field normalization.

        Args:
            source_path: File system path of the JSON file to import.
            **kwargs: Ignored additional keyword arguments.

        Raises:
            VaultNotFoundError: If the source file does not exist.
            VaultImportError: If reading, parsing, or entry validation fails.

        Returns:
            List of parsed and validated Entry instances.
        """
        src_path = Path(source_path).resolve()
        if not src_path.is_file():
            raise VaultNotFoundError(f"Export file not found at: {src_path}")

        try:
            raw_bytes = src_path.read_bytes()
        except OSError as err:
            raise VaultImportError(f"Failed to read file from '{src_path}': {err}") from err

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise VaultImportError(f"Invalid JSON format in '{src_path}': {err}") from err

        raw_entries: list[Any]
        if isinstance(data, dict) and "entries" in data:
            if not isinstance(data["entries"], list):
                raise VaultImportError(f"Field 'entries' in '{src_path}' must be a list.")
            raw_entries = data["entries"]
        elif isinstance(data, list):
            raw_entries = data
        else:
            raise VaultImportError(f"File '{src_path}' does not contain a recognizable entries collection.")

        imported_entries: list[Entry] = []
        for index, item in enumerate(raw_entries):
            if not isinstance(item, dict):
                raise VaultImportError(f"Entry at index {index} is not a valid dictionary object.")

            title = item.get("title") or item.get("name")
            username = item.get("username") or item.get("login") or item.get("user")
            password = item.get("password")

            if not title or not password:
                raise VaultImportError(
                    f"Entry at index {index} is missing required title or password fields."
                )

            normalized_dict: dict[str, Any] = {
                **item,
                "title": title,
                "username": username if username is not None else "",
                "password": password,
            }

            try:
                entry = Entry.from_dict(normalized_dict)
                imported_entries.append(entry)
            except (InvalidEntryError, ValueError, TypeError) as err:
                raise VaultImportError(f"Failed to parse entry at index {index}: {err}") from err

        return imported_entries


__all__ = [
    "PlaintextJsonImporter",
]
