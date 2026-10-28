"""Plaintext JSON exporter for vault credentials."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from core.entry import Entry
from core.exceptions import ExportError, StorageError
from core.utils import get_utc_now_iso
from storage.file_writer import FileWriter
from storage.interfaces.exporter import BaseVaultExporter
from storage.interfaces.file_writer import BaseFileWriter


class PlaintextJsonExporter(BaseVaultExporter):
    """Exports credentials to an unencrypted, human-readable JSON file."""

    DEFAULT_FORMAT_VERSION: int = 1
    EXPORT_TYPE: str = "plaintext"

    def __init__(self, file_writer: BaseFileWriter | None = None) -> None:
        """Initializes the exporter with an optional safe file writer.

        Args:
            file_writer: Safe file writer provider (defaults to FileWriter).
        """
        self._file_writer: BaseFileWriter = file_writer if file_writer is not None else FileWriter()

    def export_entries(
        self,
        entries: Sequence[Entry],
        destination_path: str | Path,
        **kwargs: Any,
    ) -> Path:
        """Exports entries to an unencrypted JSON file.

        Args:
            entries: Sequence of Entry objects to export.
            destination_path: File system destination path.
            **kwargs: Ignored additional keyword arguments.

        Raises:
            TypeError: If entries is not an iterable of Entry instances.
            ExportError: If file writing or serialization fails.

        Returns:
            Resolved Path of the created export file.
        """
        dest_path = Path(destination_path).resolve()

        for item in entries:
            if not isinstance(item, Entry):
                raise TypeError(f"Expected Entry instance in entries, got {type(item).__name__}.")

        payload: dict[str, Any] = {
            "format_version": self.DEFAULT_FORMAT_VERSION,
            "export_type": self.EXPORT_TYPE,
            "exported_at": get_utc_now_iso(),
            "entries_count": len(entries),
            "entries": [entry.to_dict() for entry in entries],
        }

        try:
            json_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            self._file_writer.write_bytes(dest_path, json_bytes)
            return dest_path
        except StorageError as err:
            raise ExportError(f"Failed to export plaintext JSON to '{dest_path}': {err}") from err


__all__ = [
    "PlaintextJsonExporter",
]
