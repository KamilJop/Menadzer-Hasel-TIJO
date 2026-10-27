"""Character diversity validation rule verifying character classes."""

from __future__ import annotations

import string

from core.rules.base import ValidationRule
from core.validation_result import RuleResult


class CharacterDiversityRule(ValidationRule):
    """Ensures password contains a diverse selection of character categories."""

    SPECIAL_CHARACTERS: str = string.punctuation
    DEFAULT_PENALTY_PER_MISSING_CLASS: int = 10

    def __init__(self, penalty_per_missing_class: int = DEFAULT_PENALTY_PER_MISSING_CLASS) -> None:
        """Initializes character diversity rule.

        Args:
            penalty_per_missing_class: Penalty deducted per missing character category (default: 10).
        """
        self._penalty_per_missing_class = penalty_per_missing_class

    @property
    def name(self) -> str:
        """Unique identifier of the rule.

        Returns:
            String name identifying this validation rule.
        """
        return "character_diversity"

    def evaluate(self, password: str) -> RuleResult:
        """Checks for lowercase, uppercase, numeric digits, and special characters.

        Args:
            password: Plaintext password string to inspect for character diversity.

        Returns:
            RuleResult containing diversity evaluation status, penalty deductions,
            actionable guidance feedback, and character presence flags in metadata.
        """
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(
            c in self.SPECIAL_CHARACTERS or (not c.isalnum() and not c.isspace())
            for c in password
        )
        has_whitespace = any(c.isspace() for c in password)

        missing_categories: list[str] = []
        if not has_lower:
            missing_categories.append("lowercase letters")
        if not has_upper:
            missing_categories.append("uppercase letters")
        if not has_digit:
            missing_categories.append("numeric digits")
        if not has_symbol:
            missing_categories.append("special symbols")

        metadata = {
            "has_lowercase": has_lower,
            "has_uppercase": has_upper,
            "has_digits": has_digit,
            "has_symbols": has_symbol,
            "has_whitespace": has_whitespace,
            "missing_categories": missing_categories,
        }

        if missing_categories:
            feedback = f"Add {', '.join(missing_categories)} to increase strength."
            penalty = len(missing_categories) * self._penalty_per_missing_class
            return RuleResult(
                rule_name=self.name,
                is_passed=False,
                feedback=feedback,
                penalty=penalty,
                metadata=metadata,
            )

        return RuleResult(rule_name=self.name, is_passed=True, penalty=0, metadata=metadata)
