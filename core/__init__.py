"""Core domain package for business logic, models, cryptography, and validation."""

from core.argon2_config import (
    AES_256_KEY_SIZE_BYTES,
    AES_GCM_NONCE_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
    Argon2Config,
)
from core.category import Category
from core.crypto import CryptoEngine
from core.encrypted_payload import EncryptedPayload
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
    "AES_256_KEY_SIZE_BYTES",
    "AES_GCM_NONCE_SIZE_BYTES",
    "Argon2Config",
    "Category",
    "CryptoEngine",
    "CryptoError",
    "DEFAULT_SALT_SIZE_BYTES",
    "DecryptionError",
    "DuplicateEntryError",
    "EncryptedPayload",
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
