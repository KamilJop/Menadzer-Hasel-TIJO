"""Configuration parameters for Argon2id Key Derivation Function."""

from __future__ import annotations

from dataclasses import dataclass

from core.crypto_constants import (
    AES_256_KEY_SIZE_BYTES,
    DEFAULT_SALT_SIZE_BYTES,
)


@dataclass(frozen=True)
class Argon2Config:
    """Configuration parameters for Argon2id Key Derivation Function.

    Attributes:
        time_cost: Number of iterations (t). Default 4 iterations.
        memory_cost: Memory usage in KiB (m). Default 128 MB (131,072 KiB).
        parallelism: Number of parallel threads (p). Default 4 threads.
        hash_len: Desired key length in bytes (32 bytes = 256 bits).
        salt_len: Length of the generated cryptographic salt in bytes (16 bytes).
    """

    time_cost: int = 4
    memory_cost: int = 131_072  # 128 MB
    parallelism: int = 4
    hash_len: int = AES_256_KEY_SIZE_BYTES
    salt_len: int = DEFAULT_SALT_SIZE_BYTES
