"""Unit tests for the cryptographic engine (CryptoEngine), Argon2id KDF, and AES-256-GCM AEAD."""

from __future__ import annotations

import pytest

from core.argon2_config import (
    AES_256_KEY_SIZE_BYTES,
    AES_GCM_NONCE_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
    Argon2Config,
)
from core.crypto import CryptoEngine
from core.encrypted_payload import EncryptedPayload
from core.exceptions import (
    CryptoError,
    DecryptionError,
    InvalidKeyError,
    InvalidPasswordError,
)


class TestCryptoGenerators:
    """Tests for salt and nonce generation methods."""

    def test_generate_salt_default_length(self) -> None:
        """Verifies default salt length is 16 bytes and produces non-repeating values."""
        salt1 = CryptoEngine.generate_salt()
        salt2 = CryptoEngine.generate_salt()

        assert isinstance(salt1, bytes)
        assert len(salt1) == DEFAULT_SALT_SIZE_BYTES
        assert salt1 != salt2

    def test_generate_salt_custom_length(self) -> None:
        """Verifies custom salt length generation."""
        custom_salt = CryptoEngine.generate_salt(32)
        assert len(custom_salt) == 32

    def test_generate_salt_rejects_too_short_length(self) -> None:
        """Verifies that requesting salt < 16 bytes raises CryptoError."""
        with pytest.raises(CryptoError, match="must be at least 16 bytes"):
            CryptoEngine.generate_salt(15)

    def test_generate_nonce_default_length(self) -> None:
        """Verifies default nonce length is 12 bytes and unique."""
        nonce1 = CryptoEngine.generate_nonce()
        nonce2 = CryptoEngine.generate_nonce()

        assert isinstance(nonce1, bytes)
        assert len(nonce1) == AES_GCM_NONCE_SIZE_BYTES
        assert nonce1 != nonce2

    def test_generate_nonce_rejects_invalid_length(self) -> None:
        """Verifies that requesting nonce != 12 bytes raises CryptoError."""
        with pytest.raises(CryptoError, match="must be exactly 12 bytes"):
            CryptoEngine.generate_nonce(16)


class TestKeyDerivation:
    """Tests for Argon2id key derivation function."""

    @pytest.fixture
    def test_salt(self) -> bytes:
        """Provides consistent salt for deterministic tests."""
        return b"1234567890abcdef"

    def test_derive_key_deterministic(
        self, test_salt: bytes, fast_argon2_config: Argon2Config
    ) -> None:
        """Verifies that same password and salt produce the exact same 32-byte key."""
        key1 = CryptoEngine.derive_key("SecretMasterPassword!", test_salt, fast_argon2_config)
        key2 = CryptoEngine.derive_key("SecretMasterPassword!", test_salt, fast_argon2_config)

        assert isinstance(key1, bytes)
        assert len(key1) == AES_256_KEY_SIZE_BYTES
        assert key1 == key2

    def test_derive_key_differs_by_password(
        self, test_salt: bytes, fast_argon2_config: Argon2Config
    ) -> None:
        """Verifies that different passwords yield different keys."""
        key1 = CryptoEngine.derive_key("Password123", test_salt, fast_argon2_config)
        key2 = CryptoEngine.derive_key("Password124", test_salt, fast_argon2_config)

        assert key1 != key2

    def test_derive_key_differs_by_salt(self, fast_argon2_config: Argon2Config) -> None:
        """Verifies that different salts yield different keys for the same password."""
        salt1 = b"salt_one_1234567"
        salt2 = b"salt_two_1234567"
        key1 = CryptoEngine.derive_key("SamePassword", salt1, fast_argon2_config)
        key2 = CryptoEngine.derive_key("SamePassword", salt2, fast_argon2_config)

        assert key1 != key2

    def test_derive_key_accepts_bytes_password(
        self, test_salt: bytes, fast_argon2_config: Argon2Config
    ) -> None:
        """Verifies that password passed as raw bytes is derived identically."""
        key_str = CryptoEngine.derive_key("MyPassword", test_salt, fast_argon2_config)
        key_bytes = CryptoEngine.derive_key(b"MyPassword", test_salt, fast_argon2_config)

        assert key_str == key_bytes

    def test_derive_key_empty_password_raises(
        self, test_salt: bytes, fast_argon2_config: Argon2Config
    ) -> None:
        """Verifies that empty string or bytes raises InvalidPasswordError."""
        with pytest.raises(InvalidPasswordError, match="cannot be empty"):
            CryptoEngine.derive_key("", test_salt, fast_argon2_config)

        with pytest.raises(InvalidPasswordError, match="cannot be empty"):
            CryptoEngine.derive_key(b"", test_salt, fast_argon2_config)

    def test_derive_key_invalid_password_type(
        self, test_salt: bytes, fast_argon2_config: Argon2Config
    ) -> None:
        """Verifies that non-string/bytes password raises InvalidPasswordError."""
        with pytest.raises(InvalidPasswordError, match="must be a str or bytes"):
            CryptoEngine.derive_key(12345, test_salt, fast_argon2_config)  # type: ignore[arg-type]

    def test_derive_key_default_production_config(self, test_salt: bytes) -> None:
        """Verifies that default production Argon2Config derives a valid 32-byte key."""
        key = CryptoEngine.derive_key("ProductionMasterKey!987", test_salt)
        assert isinstance(key, bytes)
        assert len(key) == AES_256_KEY_SIZE_BYTES

    def test_derive_key_short_or_invalid_salt(self, fast_argon2_config: Argon2Config) -> None:
        """Verifies that salt shorter than 16 bytes or invalid type raises CryptoError."""
        with pytest.raises(CryptoError, match="must be at least 16 bytes"):
            CryptoEngine.derive_key("password", b"short", fast_argon2_config)

        with pytest.raises(CryptoError, match="must be at least 16 bytes"):
            CryptoEngine.derive_key("password", "invalid_str_salt", fast_argon2_config)  # type: ignore[arg-type]


class TestAESGCMEncryptionDecryption:
    """Tests for AES-256-GCM authenticated encryption and decryption."""

    @pytest.fixture
    def valid_key(self) -> bytes:
        """Returns a valid 32-byte AES-256 key."""
        return b"\x01" * 32

    def test_encrypt_decrypt_bytes_roundtrip(self, valid_key: bytes) -> None:
        """Verifies encryption and successful decryption of arbitrary byte payload."""
        plaintext = b"Sensitive Vault Database Content \x00\xff"
        payload = CryptoEngine.encrypt(plaintext, valid_key)

        assert isinstance(payload, EncryptedPayload)
        assert len(payload.nonce) == AES_GCM_NONCE_SIZE_BYTES
        assert payload.ciphertext != plaintext
        # AES-GCM ciphertext includes 16-byte authentication tag
        assert len(payload.ciphertext) == len(plaintext) + 16

        decrypted = CryptoEngine.decrypt(payload, valid_key)
        assert decrypted == plaintext
        assert len(payload.salt) == DEFAULT_SALT_SIZE_BYTES

    def test_encrypt_with_explicit_nonce_and_salt(self, valid_key: bytes) -> None:
        """Verifies encryption with custom nonce and salt retained in payload."""
        explicit_nonce = b"custom_nonce"
        explicit_salt = b"custom_salt_1234"
        plaintext = b"Hello, World!"

        payload = CryptoEngine.encrypt(
            data=plaintext,
            key=valid_key,
            nonce=explicit_nonce,
            salt=explicit_salt,
        )

        assert payload.nonce == explicit_nonce
        assert payload.salt == explicit_salt

        decrypted = CryptoEngine.decrypt(payload, valid_key)
        assert decrypted == plaintext

    def test_encrypt_decrypt_empty_payload(self, valid_key: bytes) -> None:
        """Verifies handling of empty byte payload (produces 16-byte AEAD tag)."""
        payload = CryptoEngine.encrypt(b"", valid_key)
        assert len(payload.ciphertext) == 16
        assert CryptoEngine.decrypt(payload, valid_key) == b""

    def test_encrypt_invalid_key_length(self) -> None:
        """Verifies that key not equal to 32 bytes raises InvalidKeyError."""
        with pytest.raises(InvalidKeyError, match="must be exactly 32 bytes"):
            CryptoEngine.encrypt(b"data", b"too_short_key_16b")

        with pytest.raises(InvalidKeyError, match="must be exactly 32 bytes"):
            CryptoEngine.encrypt(b"data", b"\x00" * 64)

    def test_encrypt_invalid_nonce_length(self, valid_key: bytes) -> None:
        """Verifies that nonce not equal to 12 bytes raises CryptoError."""
        with pytest.raises(CryptoError, match="must be exactly 12 bytes"):
            CryptoEngine.encrypt(b"data", valid_key, nonce=b"bad_len")

    def test_encrypt_invalid_salt_length(self, valid_key: bytes) -> None:
        """Verifies that salt shorter than 16 bytes raises CryptoError."""
        with pytest.raises(CryptoError, match="must be at least 16 bytes"):
            CryptoEngine.encrypt(b"data", valid_key, salt=b"too_short")

    def test_decrypt_invalid_payload_type(self, valid_key: bytes) -> None:
        """Verifies that non-EncryptedPayload raises CryptoError."""
        with pytest.raises(CryptoError, match="must be an instance of EncryptedPayload"):
            CryptoEngine.decrypt("invalid_payload", valid_key)  # type: ignore[arg-type]

    def test_decrypt_invalid_key_length(self, valid_key: bytes) -> None:
        """Verifies that decrypting with wrong key length raises InvalidKeyError."""
        payload = CryptoEngine.encrypt(b"data", valid_key)
        with pytest.raises(InvalidKeyError, match="must be exactly 32 bytes"):
            CryptoEngine.decrypt(payload, b"short_key")

    def test_decrypt_invalid_nonce_length_in_payload(self, valid_key: bytes) -> None:
        """Verifies that corrupted nonce length in payload raises CryptoError."""
        corrupted_payload = EncryptedPayload(
            ciphertext=b"some_ct",
            nonce=b"too_short",
            salt=b"valid_salt_16_bytes",
        )
        with pytest.raises(CryptoError, match="must be exactly 12 bytes"):
            CryptoEngine.decrypt(corrupted_payload, valid_key)


class TestTamperResistance:
    """Tests for tamper-detection, tag verification, and associated data authentication."""

    @pytest.fixture
    def valid_key(self) -> bytes:
        """Returns a valid 32-byte key."""
        return b"\x42" * 32

    def test_tampered_ciphertext_byte_raises_decryption_error(self, valid_key: bytes) -> None:
        """Verifies that altering a single byte in ciphertext triggers DecryptionError."""
        payload = CryptoEngine.encrypt(b"Top Secret Credentials", valid_key)

        tampered_bytes = bytearray(payload.ciphertext)
        tampered_bytes[0] ^= 0x01
        tampered_payload = EncryptedPayload(
            ciphertext=bytes(tampered_bytes),
            nonce=payload.nonce,
            salt=payload.salt,
        )

        with pytest.raises(DecryptionError, match="Authentication tag verification failed"):
            CryptoEngine.decrypt(tampered_payload, valid_key)

    def test_tampered_nonce_byte_raises_decryption_error(self, valid_key: bytes) -> None:
        """Verifies that altering nonce byte triggers DecryptionError."""
        payload = CryptoEngine.encrypt(b"Top Secret Credentials", valid_key)

        tampered_nonce = bytearray(payload.nonce)
        tampered_nonce[0] ^= 0xFF
        tampered_payload = EncryptedPayload(
            ciphertext=payload.ciphertext,
            nonce=bytes(tampered_nonce),
            salt=payload.salt,
        )

        with pytest.raises(DecryptionError, match="Authentication tag verification failed"):
            CryptoEngine.decrypt(tampered_payload, valid_key)

    def test_decrypt_with_wrong_key_raises_decryption_error(self, valid_key: bytes) -> None:
        """Verifies that attempting decryption with wrong key raises DecryptionError."""
        payload = CryptoEngine.encrypt(b"Sensitive Data", valid_key)
        wrong_key = b"\x99" * 32

        with pytest.raises(DecryptionError, match="Authentication tag verification failed"):
            CryptoEngine.decrypt(payload, wrong_key)

    def test_associated_data_protection(self, valid_key: bytes) -> None:
        """Verifies that Associated Authenticated Data (AAD) must match during decryption."""
        plaintext = b"Payload with associated header"
        aad_header = b"VAULT_FORMAT_V1"

        payload = CryptoEngine.encrypt(
            data=plaintext,
            key=valid_key,
            associated_data=aad_header,
        )

        # Successful decryption with matching AAD
        decrypted = CryptoEngine.decrypt(payload, valid_key, associated_data=aad_header)
        assert decrypted == plaintext

        # Mismatched AAD must fail
        with pytest.raises(DecryptionError, match="Authentication tag verification failed"):
            CryptoEngine.decrypt(payload, valid_key, associated_data=b"VAULT_FORMAT_V2")

        # Missing AAD must fail
        with pytest.raises(DecryptionError, match="Authentication tag verification failed"):
            CryptoEngine.decrypt(payload, valid_key, associated_data=None)


class TestTextConvenienceHelpers:
    """Tests for encrypt_text and decrypt_text convenience helpers."""

    @pytest.fixture
    def valid_key(self) -> bytes:
        return b"\xaa" * 32

    def test_encrypt_decrypt_text_roundtrip(self, valid_key: bytes) -> None:
        """Verifies UTF-8 string encryption and decryption including unicode & emojis."""
        sample_text = "Master Password 🔐 – Zażółć gęślą jaźń! #1234"
        salt = b"test_salt_123456"

        payload = CryptoEngine.encrypt_text(sample_text, valid_key, salt=salt)
        assert payload.salt == salt

        decrypted_text = CryptoEngine.decrypt_text(payload, valid_key)
        assert decrypted_text == sample_text

    def test_encrypt_text_type_check(self, valid_key: bytes) -> None:
        """Verifies that passing non-string to encrypt_text raises TypeError."""
        with pytest.raises(TypeError, match="Expected text to be a str"):
            CryptoEngine.encrypt_text(12345, valid_key)  # type: ignore[arg-type]

    def test_decrypt_text_corrupted_utf8_raises(self, valid_key: bytes) -> None:
        """Verifies that valid ciphertext containing non-UTF8 bytes raises DecryptionError on decode."""
        invalid_utf8_bytes = b"\xff\xfe\xfd"
        payload = CryptoEngine.encrypt(invalid_utf8_bytes, valid_key)

        with pytest.raises(DecryptionError, match="Failed to decode decrypted payload as UTF-8"):
            CryptoEngine.decrypt_text(payload, valid_key)


class TestEncryptedPayloadSerialization:
    """Tests for EncryptedPayload to_dict and from_dict serialization."""

    def test_payload_dict_serialization_roundtrip(self) -> None:
        """Verifies serialization and deserialization with required salt."""
        payload = EncryptedPayload(
            ciphertext=b"ciphertext_bytes_here",
            nonce=b"123456789012",
            salt=b"salt_16_bytes___",
        )
        serialized = payload.to_dict()
        assert isinstance(serialized, dict)
        assert "ciphertext" in serialized
        assert "nonce" in serialized
        assert "salt" in serialized

        restored = EncryptedPayload.from_dict(serialized)
        assert restored.ciphertext == payload.ciphertext
        assert restored.nonce == payload.nonce
        assert restored.salt == payload.salt

    def test_payload_from_dict_missing_salt_raises(self) -> None:
        """Verifies that dictionary missing required salt raises CryptoError."""
        payload_data = {
            "ciphertext": "AAAA",
            "nonce": "BBBB",
        }
        with pytest.raises(CryptoError, match="Failed to deserialize encrypted payload"):
            EncryptedPayload.from_dict(payload_data)

    def test_payload_from_dict_missing_fields_raises(self) -> None:
        """Verifies that incomplete dictionary raises CryptoError."""
        with pytest.raises(CryptoError, match="Failed to deserialize encrypted payload"):
            EncryptedPayload.from_dict({"ciphertext": "AAAA"})

    def test_payload_from_dict_corrupted_base64_raises(self) -> None:
        """Verifies that invalid base64 input raises CryptoError."""
        with pytest.raises(CryptoError, match="Failed to deserialize encrypted payload"):
            EncryptedPayload.from_dict({
                "ciphertext": "!!!not_base64!!!",
                "nonce": "AAAA",
                "salt": "BBBB",
            })
