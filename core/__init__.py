"""Core domain package for business logic, models, cryptography, and validation."""

from core.argon2_config import Argon2Config
from core.category import Category
from core.crypto import CryptoEngine
from core.crypto_constants import (
    AES_256_KEY_SIZE_BYTES,
    AES_GCM_NONCE_SIZE_BYTES,
    AES_GCM_TAG_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
)
from core.crypto_interfaces import BaseDataEncryptor, BaseKeyDerivator
from core.data_encryptor import DataEncryptor
from core.encrypted_payload import EncryptedPayload
from core.entry import Entry
from core.exceptions import (
    CryptoError,
    DecryptionError,
    DuplicateEntryError,
    EntryNotFoundError,
    ExportError,
    GeneratorError,
    InvalidEntryError,
    InvalidGeneratorConfigError,
    InvalidKeyError,
    InvalidPasswordError,
    ModelError,
    PasswordManagerError,
    StorageError,
    VaultCorruptedError,
    VaultImportError,
    VaultNotFoundError,
)
from core.generator import PasswordGenerator
from core.generator_config import PasswordGeneratorConfig
from core.generator_constants import (
    AMBIGUOUS_CHARS,
    DEFAULT_PASSWORD_LENGTH,
    DEFAULT_SYMBOL_CHARS,
    DIGIT_CHARS,
    LOWERCASE_CHARS,
    MAX_GENERATION_ATTEMPTS,
    MIN_STRONG_PASSWORD_LENGTH,
    UPPERCASE_CHARS,
)
from core.generator_interfaces import BasePasswordGenerator
from core.key_derivator import KeyDerivator
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
    "AES_GCM_TAG_SIZE_BYTES",
    "AMBIGUOUS_CHARS",
    "Argon2Config",
    "BaseDataEncryptor",
    "BaseKeyDerivator",
    "BasePasswordGenerator",
    "Category",
    "CharacterDiversityRule",
    "CommonPasswordRule",
    "CryptoEngine",
    "CryptoError",
    "DEFAULT_PASSWORD_LENGTH",
    "DEFAULT_SALT_SIZE_BYTES",
    "DEFAULT_SYMBOL_CHARS",
    "DIGIT_CHARS",
    "DataEncryptor",
    "DecryptionError",
    "DuplicateEntryError",
    "EncryptedPayload",
    "Entry",
    "EntryNotFoundError",
    "EntropyRule",
    "ExportError",
    "GeneratorError",
    "InvalidEntryError",
    "InvalidGeneratorConfigError",
    "InvalidKeyError",
    "InvalidPasswordError",
    "KeyDerivator",
    "LOWERCASE_CHARS",
    "LengthRule",
    "MAX_GENERATION_ATTEMPTS",
    "MIN_STRONG_PASSWORD_LENGTH",
    "ModelError",
    "PasswordGenerator",
    "PasswordGeneratorConfig",
    "PasswordManagerError",
    "PasswordValidator",
    "RuleResult",
    "SequenceAndRepetitionRule",
    "StorageError",
    "StrengthLevel",
    "UPPERCASE_CHARS",
    "ValidationResult",
    "ValidationRule",
    "Vault",
    "VaultCorruptedError",
    "VaultImportError",
    "VaultNotFoundError",
    "get_default_validation_rules",
]
