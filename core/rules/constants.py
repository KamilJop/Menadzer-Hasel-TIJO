"""Default constants, dictionary lists, and keyboard sequences for password validation."""

from __future__ import annotations

import functools
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

RESOURCES_DIRECTORY: Path = Path(__file__).resolve().parent.parent.parent / "resources"
COMMON_PASSWORDS_FILE_PATH: Path = RESOURCES_DIRECTORY / "common_passwords.txt"
COMMON_SEQUENCES_FILE_PATH: Path = RESOURCES_DIRECTORY / "common_sequences.txt"


def load_common_passwords(file_path: Path | str | None = None) -> frozenset[str]:
    """Loads forbidden common passwords from an external text file.

    Args:
        file_path: Path to the text file containing one password per line. Defaults
            to resources/common_passwords.txt.

    Returns:
        Frozenset of lowercased forbidden password strings.
    """
    target_path = Path(file_path) if file_path is not None else COMMON_PASSWORDS_FILE_PATH
    if not target_path.is_file():
        logger.warning(
            "Common passwords dictionary file not found at '%s'. Common password checking may be impaired.",
            target_path,
        )
        return frozenset()

    with target_path.open("r", encoding="utf-8") as file:
        return frozenset(
            line.strip().lower()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        )


def load_common_sequences(file_path: Path | str | None = None) -> tuple[str, ...]:
    """Loads sequential patterns and keyboard layouts from an external text file.

    Args:
        file_path: Path to the text file containing one sequence per line. Defaults
            to resources/common_sequences.txt.

    Returns:
        Tuple of lowercased sequence strings.
    """
    target_path = Path(file_path) if file_path is not None else COMMON_SEQUENCES_FILE_PATH
    if not target_path.is_file():
        logger.warning(
            "Common sequences file not found at '%s'. Sequential pattern checking may be impaired.",
            target_path,
        )
        return ()

    with target_path.open("r", encoding="utf-8") as file:
        return tuple(
            line.strip().lower()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        )


@functools.lru_cache(maxsize=1)
def get_default_common_passwords() -> frozenset[str]:
    """Returns cached set of common passwords loaded from the default resource file.

    Returns:
        Cached frozenset of lowercased forbidden password strings.
    """
    return load_common_passwords(COMMON_PASSWORDS_FILE_PATH)


@functools.lru_cache(maxsize=1)
def get_default_sequences() -> tuple[str, ...]:
    """Returns cached tuple of common sequences loaded from the default resource file.

    Returns:
        Cached tuple of lowercased sequence strings.
    """
    return load_common_sequences(COMMON_SEQUENCES_FILE_PATH)


def __getattr__(name: str) -> Any:
    """Provides lazy access to default sets for backwards compatibility."""
    if name == "DEFAULT_COMMON_PASSWORDS":
        return get_default_common_passwords()
    if name == "DEFAULT_SEQUENCES":
        return get_default_sequences()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "COMMON_PASSWORDS_FILE_PATH",
    "COMMON_SEQUENCES_FILE_PATH",
    "DEFAULT_COMMON_PASSWORDS",
    "DEFAULT_SEQUENCES",
    "RESOURCES_DIRECTORY",
    "get_default_common_passwords",
    "get_default_sequences",
    "load_common_passwords",
    "load_common_sequences",
]
