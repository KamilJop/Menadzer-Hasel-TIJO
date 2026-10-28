"""Abstract interfaces for repository storage and file persistence services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.vault import Vault


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


class BaseVaultRepository(ABC):
    """Abstract interface defining the contract for encrypted vault persistence."""

    @abstractmethod
    def save(
        self,
        vault: Vault,
        password: str | bytes,
        file_path: str | Path | None = None,
    ) -> Path:
        """Encrypts and persists vault data to disk.

        Args:
            vault: Vault instance to encrypt and store.
            password: Master password used to derive the encryption key.
            file_path: Optional destination path (defaults to configured default path).

        Raises:
            StorageError: If disk writing or directory creation fails.
            CryptoError: If encryption key derivation or payload encryption fails.
            ValueError: If password is empty or no valid file path is provided.

        Returns:
            Resolved Path where the vault file was saved.
        """

    @abstractmethod
    def load(
        self,
        password: str | bytes,
        file_path: str | Path | None = None,
    ) -> Vault:
        """Loads and decrypts a vault file from disk.

        Args:
            password: Master password used to decrypt the vault file.
            file_path: Optional path to the vault file (defaults to configured default path).

        Raises:
            VaultNotFoundError: If the vault file does not exist at the target path.
            VaultCorruptedError: If file content or payload format is invalid or unreadable.
            InvalidPasswordError: If decryption fails due to incorrect password or tampered data.

        Returns:
            Decrypted and reconstructed Vault instance.
        """

    @abstractmethod
    def exists(self, file_path: str | Path | None = None) -> bool:
        """Checks whether a vault file exists at the specified or default path.

        Args:
            file_path: Optional file path to verify (defaults to configured default path).

        Returns:
            True if the vault file exists and is a regular file, False otherwise.
        """
