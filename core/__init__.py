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
from core.rules import (
    CharacterDiversityRule,
    CommonPasswordRule,
    EntropyRule,
    LengthRule,
    SequenceAndRepetitionRule,
    ValidationRule,
)
from core.strength_level import StrengthLevel
from core.validation_result import RuleResult, ValidationResult
from core.validator import PasswordValidator, get_default_validation_rules
from core.vault import Vault

__all__ = [
    "AES_256_KEY_SIZE_BYTES",
    "AES_GCM_NONCE_SIZE_BYTES",
    "Argon2Config",
    "Category",
    "CharacterDiversityRule",
    "CommonPasswordRule",
    "CryptoEngine",
    "CryptoError",
    "DEFAULT_SALT_SIZE_BYTES",
    "DecryptionError",
    "DuplicateEntryError",
    "EncryptedPayload",
    "Entry",
    "EntryNotFoundError",
    "EntropyRule",
    "ExportError",
    "InvalidEntryError",
    "InvalidKeyError",
    "InvalidPasswordError",
    "LengthRule",
    "ModelError",
    "PasswordManagerError",
    "PasswordValidator",
    "RuleResult",
    "SequenceAndRepetitionRule",
    "StorageError",
    "StrengthLevel",
    "ValidationResult",
    "ValidationRule",
    "Vault",
    "VaultCorruptedError",
    "VaultImportError",
    "VaultNotFoundError",
    "get_default_validation_rules",
]
