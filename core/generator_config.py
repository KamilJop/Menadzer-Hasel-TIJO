"""Configuration specification for password generation."""

from __future__ import annotations

from dataclasses import dataclass

from core.exceptions import InvalidGeneratorConfigError
from core.generator_constants import (
    AMBIGUOUS_CHARS,
    DEFAULT_PASSWORD_LENGTH,
    DEFAULT_SYMBOL_CHARS,
    DIGIT_CHARS,
    LOWERCASE_CHARS,
    UPPERCASE_CHARS,
)


@dataclass(frozen=True)
class PasswordGeneratorConfig:
    """Configuration settings for generating secure passwords.

    Attributes:
        length: Desired length of the generated password (default matches validator recommended length).
        include_lowercase: Whether to include lowercase letters (a-z).
        include_uppercase: Whether to include uppercase letters (A-Z).
        include_digits: Whether to include decimal digits (0-9).
        include_symbols: Whether to include special symbols (string.punctuation).
        exclude_ambiguous: Whether to exclude visually ambiguous glyphs (il1Lo0O|I).
        custom_symbols: Optional custom string of symbol characters.
        ensure_each_selected_type: Whether to guarantee at least one char per chosen category.
        validate_with_rules: Whether to verify candidate passwords against domain validation rules.
    """

    length: int = DEFAULT_PASSWORD_LENGTH
    include_lowercase: bool = True
    include_uppercase: bool = True
    include_digits: bool = True
    include_symbols: bool = True
    exclude_ambiguous: bool = False
    custom_symbols: str | None = None
    ensure_each_selected_type: bool = True
    validate_with_rules: bool = True

    def __post_init__(self) -> None:
        """Validates configuration parameters immediately upon instantiation.

        Raises:
            InvalidGeneratorConfigError: If configuration values are out of bounds or conflicting.
        """
        self.validate()

    def validate(self) -> None:
        """Validates generator configuration parameters for correctness.

        Raises:
            InvalidGeneratorConfigError: If configuration constraints are violated.
        """
        if self.length < 1:
            raise InvalidGeneratorConfigError("Password length must be at least 1.")

        if not any(
            (
                self.include_lowercase,
                self.include_uppercase,
                self.include_digits,
                self.include_symbols,
            )
        ):
            raise InvalidGeneratorConfigError("At least one character set must be enabled.")

        if self.include_symbols and self.custom_symbols is not None and len(self.custom_symbols) == 0:
            raise InvalidGeneratorConfigError("Custom symbols cannot be empty when symbols are included.")

        active_pools = self.get_active_pools()
        if any(len(pool) == 0 for pool in active_pools):
            raise InvalidGeneratorConfigError("One or more selected character sets are empty after exclusions.")

        if self.ensure_each_selected_type and self.length < len(active_pools):
            raise InvalidGeneratorConfigError(
                f"Password length ({self.length}) cannot be less than the number of "
                f"guaranteed character categories ({len(active_pools)})."
            )

    def get_active_pools(self) -> list[str]:
        """Resolves the individual non-empty character pools based on active flags and filters.

        Returns:
            List of non-empty character pool strings corresponding to enabled options.
        """
        pools: list[str] = []

        if self.include_lowercase:
            pools.append(self._filter(LOWERCASE_CHARS))
        if self.include_uppercase:
            pools.append(self._filter(UPPERCASE_CHARS))
        if self.include_digits:
            pools.append(self._filter(DIGIT_CHARS))
        if self.include_symbols:
            symbols = self.custom_symbols if self.custom_symbols is not None else DEFAULT_SYMBOL_CHARS
            pools.append(self._filter(symbols))

        return pools

    def _filter(self, source: str) -> str:
        """Filters out ambiguous characters if requested.

        Args:
            source: Input character string to filter.

        Returns:
            String with ambiguous characters removed if exclude_ambiguous is True.
        """
        if not self.exclude_ambiguous:
            return source
        ambiguous_set = set(AMBIGUOUS_CHARS)
        return "".join(char for char in source if char not in ambiguous_set)
