"""Cryptographic size constants and defaults for KDF and AEAD encryption."""

from __future__ import annotations

AES_256_KEY_SIZE_BYTES: int = 32
AES_GCM_NONCE_SIZE_BYTES: int = 12
AES_GCM_TAG_SIZE_BYTES: int = 16
DEFAULT_SALT_SIZE_BYTES: int = 16

__all__ = [
    "AES_256_KEY_SIZE_BYTES",
    "AES_GCM_NONCE_SIZE_BYTES",
    "AES_GCM_TAG_SIZE_BYTES",
    "DEFAULT_SALT_SIZE_BYTES",
]
