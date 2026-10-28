"""Abstract interface for vault importing services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from core.entry import Entry


class BaseVaultImporter(ABC):
    """Abstract interface defining the contract for importing vault entries."""

    @abstractmethod
    def import_entries(
        self,
        source_path: str | Path,
        **kwargs: Any,
    ) -> list[Entry]:
        """Imports credential entries from the specified source file.

        Args:
            source_path: File system path to the file to import.
            **kwargs: Additional strategy-specific parameters (e.g. password).

        Raises:
            VaultImportError: If the file format or schema is corrupted or incompatible.
            InvalidPasswordError: If decryption fails due to invalid password.
            VaultNotFoundError: If the source file does not exist.

        Returns:
            List of parsed and validated Entry instances.
        """


__all__ = [
    "BaseVaultImporter",
]
