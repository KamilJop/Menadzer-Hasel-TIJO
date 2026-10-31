"""Abstract interface for vault storage path resolution services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseVaultPathResolver(ABC):
    """Contract for determining and preparing the persistent vault file location."""

    @abstractmethod
    def resolve_path(self) -> Path:
        """Resolves and prepares the absolute path to the default vault storage file.

        Returns:
            Resolved absolute Path pointing to the vault storage file.
        """


__all__ = [
    "BaseVaultPathResolver",
]
