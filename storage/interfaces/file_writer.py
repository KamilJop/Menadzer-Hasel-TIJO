"""Abstract interface for safe file persistence services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseFileWriter(ABC):
    """Abstract interface defining the contract for safe file persistence."""

    @abstractmethod
    def write_bytes(self, target_path: Path, data: bytes) -> None:
        """Safely writes binary data to the target file path.

        Args:
            target_path: Destination path where data should be stored.
            data: Binary payload to write.

        Raises:
            StorageError: If the write or swap operation fails due to I/O error.
        """


__all__ = [
    "BaseFileWriter",
]
