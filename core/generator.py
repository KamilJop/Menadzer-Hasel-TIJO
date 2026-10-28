"""Cryptographically secure password generation engine coordinated with validation rules."""

from __future__ import annotations

import secrets

from core.exceptions import GeneratorError, InvalidGeneratorConfigError
from core.generator_config import PasswordGeneratorConfig
from core.generator_constants import (
    DEFAULT_PASSWORD_LENGTH,
    MAX_GENERATION_ATTEMPTS,
    MIN_STRONG_PASSWORD_LENGTH,
)
from core.generator_interfaces import BasePasswordGenerator
from core.strength_level import StrengthLevel
from core.validator import PasswordValidator


class PasswordGenerator(BasePasswordGenerator):
    """Cryptographically secure password generator coordinated with domain validation rules."""

    def __init__(
        self,
        rng: secrets.SystemRandom | None = None,
        validator: PasswordValidator | None = None,
    ) -> None:
        """Initializes the password generator with optional CSPRNG and validator dependencies.

        Args:
            rng: Optional SystemRandom instance (defaults to secrets.SystemRandom()).
            validator: Optional PasswordValidator instance (defaults to PasswordValidator.create_default()).
        """
        self._rng: secrets.SystemRandom = rng if rng is not None else secrets.SystemRandom()
        self._validator: PasswordValidator = (
            validator if validator is not None else PasswordValidator.create_default()
        )

    def generate(self, config: PasswordGeneratorConfig | None = None) -> str:
        """Generates a cryptographically strong random password adhering to rules.

        Args:
            config: Optional PasswordGeneratorConfig specifying length, charset, and rules.

        Raises:
            InvalidGeneratorConfigError: If configuration is invalid.
            GeneratorError: If compliant password generation fails within attempt limit.

        Returns:
            Randomly generated password string compliant with validation rules.
        """
        active_config = config if config is not None else PasswordGeneratorConfig()
        active_config.validate()

        if not active_config.validate_with_rules:
            return self._build_candidate(active_config)

        for _ in range(MAX_GENERATION_ATTEMPTS):
            candidate = self._build_candidate(active_config)
            validation = self._validator.validate(candidate)

            if validation.is_common_or_pattern:
                continue

            if (
                active_config.length >= MIN_STRONG_PASSWORD_LENGTH
                and active_config.include_lowercase
                and active_config.include_uppercase
                and active_config.include_digits
                and active_config.include_symbols
                and not validation.is_acceptable(StrengthLevel.STRONG)
            ):
                continue

            return candidate

        raise GeneratorError(
            f"Failed to generate a password satisfying strength validation rules within {MAX_GENERATION_ATTEMPTS} attempts."
        )

    def _build_candidate(self, config: PasswordGeneratorConfig) -> str:
        """Constructs an individual random candidate password from active character pools.

        Args:
            config: Validated PasswordGeneratorConfig instance.

        Returns:
            Shuffled random password candidate string.
        """
        pools = config.get_active_pools()
        result_chars: list[str] = []

        if config.ensure_each_selected_type:
            for pool in pools:
                result_chars.append(self._rng.choice(pool))

        combined_pool = "".join(pools)
        remaining_count = config.length - len(result_chars)

        for _ in range(remaining_count):
            result_chars.append(self._rng.choice(combined_pool))

        self._rng.shuffle(result_chars)
        return "".join(result_chars)

    def generate_with_options(
        self,
        length: int = DEFAULT_PASSWORD_LENGTH,
        include_lowercase: bool = True,
        include_uppercase: bool = True,
        include_digits: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = False,
        custom_symbols: str | None = None,
        ensure_each_selected_type: bool = True,
        validate_with_rules: bool = True,
    ) -> str:
        """Convenience helper to generate a password directly with individual parameters.

        Args:
            length: Length of the password.
            include_lowercase: Include lowercase letters.
            include_uppercase: Include uppercase letters.
            include_digits: Include numbers.
            include_symbols: Include special characters.
            exclude_ambiguous: Exclude visually confusing characters.
            custom_symbols: Custom symbols string.
            ensure_each_selected_type: Guarantee each active character type is included.
            validate_with_rules: Check candidate passwords against validation rules.

        Raises:
            InvalidGeneratorConfigError: If configuration options are invalid.
            GeneratorError: If compliant password generation fails within attempt limit.

        Returns:
            Generated secure password string.
        """
        config = PasswordGeneratorConfig(
            length=length,
            include_lowercase=include_lowercase,
            include_uppercase=include_uppercase,
            include_digits=include_digits,
            include_symbols=include_symbols,
            exclude_ambiguous=exclude_ambiguous,
            custom_symbols=custom_symbols,
            ensure_each_selected_type=ensure_each_selected_type,
            validate_with_rules=validate_with_rules,
        )
        return self.generate(config)


__all__ = [
    "PasswordGenerator",
]
