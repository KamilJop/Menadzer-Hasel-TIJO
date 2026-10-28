"""Abstract interface for vault exporting services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from core.entry import Entry


class BaseVaultExporter(ABC):
    """Abstract interface defining the contract for exporting vault entries."""

    @abstractmethod
    def export_entries(
        self,
        entries: Sequence[Entry],
        destination_path: str | Path,
        **kwargs: Any,
    ) -> Path:
        """Exports credential entries to the specified destination path.

        Args:
            entries: Sequence of Entry instances to export.
            destination_path: File system path where exported data should be written.
            **kwargs: Additional strategy-specific parameters (e.g. password).

        Raises:
            ExportError: If exporting or disk writing fails.
            ValueError: If input parameters or entries are invalid.

        Returns:
            Resolved Path of the saved export file.
        """


__all__ = [
    "BaseVaultExporter",
]
