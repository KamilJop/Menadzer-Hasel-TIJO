"""Core domain package for business logic, models, cryptography, and validation."""

from core.category import Category
from core.entry import Entry
from core.exceptions import (
    CryptoError,
    DecryptionError,
    DuplicateEntryError,
    EntryNotFoundError,
    ExportError,
    InvalidEntryError,
    InvalidKeyError,
    InvalidPasswordError,
    ModelError,
    PasswordManagerError,
    StorageError,
    VaultCorruptedError,
    VaultImportError,
    VaultNotFoundError,
)
from core.vault import Vault

__all__ = [
    "Category",
    "CryptoError",
    "DecryptionError",
    "DuplicateEntryError",
    "Entry",
    "EntryNotFoundError",
    "ExportError",
    "InvalidEntryError",
    "InvalidKeyError",
    "InvalidPasswordError",
    "ModelError",
    "PasswordManagerError",
    "StorageError",
    "Vault",
    "VaultCorruptedError",
    "VaultImportError",
    "VaultNotFoundError",
]
