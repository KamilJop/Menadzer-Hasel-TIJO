"""Custom domain exceptions for the password manager application."""

from __future__ import annotations


class PasswordManagerError(Exception):
    """Base exception for all domain and application errors."""

# Model Exceptions

class ModelError(PasswordManagerError):
    """Base exception for model-level and entity validation errors."""


class DuplicateEntryError(ModelError):
    """Raised when an entry with the same identifier already exists in the vault."""

    def __init__(self, entry_id: str, message: str | None = None) -> None:
        """Initializes DuplicateEntryError with the conflicting ID.

        Args:
            entry_id: Identifier of the conflicting entry.
            message: Optional custom message.
        """
        self.entry_id = entry_id
        super().__init__(message or f"Entry with ID '{entry_id}' already exists.")


class EntryNotFoundError(ModelError):
    """Raised when an entry cannot be found by its identifier."""

    def __init__(self, entry_id: str, message: str | None = None) -> None:
        """Initializes EntryNotFoundError with the missing ID.

        Args:
            entry_id: Identifier of the missing entry.
            message: Optional custom message.
        """
        self.entry_id = entry_id
        super().__init__(message or f"Entry with ID '{entry_id}' not found.")


class InvalidEntryError(ModelError):
    """Raised when entry data payload is invalid or corrupted."""


# Cryptographic & Authentication Exceptions


class CryptoError(PasswordManagerError):
    """Base exception for cryptographic operations and authentication failures."""


class InvalidPasswordError(CryptoError):
    """Raised when the master password or export password verification fails."""


class DecryptionError(CryptoError):
    """Raised when AES-GCM decryption fails or payload integrity is compromised."""


class InvalidKeyError(CryptoError):
    """Raised when an encryption key has invalid length or parameters."""



# Storage Exceptions


class StorageError(PasswordManagerError):
    """Base exception for file I/O and persistence failures."""


class VaultCorruptedError(StorageError):
    """Raised when vault file structure or headers are invalid or unreadable."""


class VaultNotFoundError(StorageError):
    """Raised when the requested vault file does not exist."""


class ExportError(StorageError):
    """Raised when vault export operation fails."""


class VaultImportError(StorageError):
    """Raised when importing vault entries fails or schema is incompatible."""


# Generator Exceptions


class GeneratorError(PasswordManagerError):
    """Base exception for password generator operations and configuration issues."""


class InvalidGeneratorConfigError(GeneratorError):
    """Raised when generator configuration parameters are invalid or contradictory."""

