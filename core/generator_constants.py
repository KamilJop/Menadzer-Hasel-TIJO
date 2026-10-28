"""Constants and character sets used for secure password generation."""

from __future__ import annotations

import string

DEFAULT_PASSWORD_LENGTH: int = 16
MIN_STRONG_PASSWORD_LENGTH: int = 12
MAX_GENERATION_ATTEMPTS: int = 50

LOWERCASE_CHARS: str = string.ascii_lowercase
UPPERCASE_CHARS: str = string.ascii_uppercase
DIGIT_CHARS: str = string.digits
DEFAULT_SYMBOL_CHARS: str = string.punctuation
AMBIGUOUS_CHARS: str = "il1Lo0O|I"
