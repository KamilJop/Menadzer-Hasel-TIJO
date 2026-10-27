"""Length validation rule checking minimum and recommended password lengths."""

from __future__ import annotations

from core.rules.base import ValidationRule
from core.validation_result import RuleResult


class LengthRule(ValidationRule):
    """Validates that password length satisfies minimum and recommended bounds."""

    DEFAULT_MIN_LENGTH: int = 12
    DEFAULT_RECOMMENDED_LENGTH: int = 16
    DEFAULT_PENALTY_PER_CHAR: int = 6
    DEFAULT_MAX_PENALTY: int = 40

    def __init__(
        self,
        min_length: int = DEFAULT_MIN_LENGTH,
        recommended_length: int = DEFAULT_RECOMMENDED_LENGTH,
        penalty_per_char_under_min: int = DEFAULT_PENALTY_PER_CHAR,
        max_penalty: int = DEFAULT_MAX_PENALTY,
    ) -> None:
        """Initializes the length rule with configurable thresholds.

        Args:
            min_length: Minimum acceptable password length (default: 12).
            recommended_length: Recommended length for strong security (default: 16).
            penalty_per_char_under_min: Score penalty per character below minimum length (default: 6).
            max_penalty: Maximum cumulative penalty for insufficient length (default: 40).
        """
        self._min_length = min_length
        self._recommended_length = recommended_length
        self._penalty_per_char = penalty_per_char_under_min
        self._max_penalty = max_penalty

    @property
    def name(self) -> str:
        """Unique identifier of the rule.

        Returns:
            String name identifying this validation rule.
        """
        return "length"

    def evaluate(self, password: str) -> RuleResult:
        """Evaluates password length against minimum and recommended thresholds.

        Args:
            password: Plaintext password string to measure.

        Returns:
            RuleResult containing length evaluation status, penalty deductions,
            actionable guidance feedback, and length metadata.
        """
        length = len(password)
        metadata = {"length": length, "min_length": self._min_length}

        if length == 0:
            return RuleResult(
                rule_name=self.name,
                is_passed=False,
                feedback="Password cannot be empty.",
                penalty=self._max_penalty,
                metadata=metadata,
            )

        if length < self._min_length:
            chars_missing = self._min_length - length
            penalty = min(self._max_penalty, chars_missing * self._penalty_per_char)
            feedback = (
                f"Password is too short ({length} characters). "
                f"Use at least {self._min_length} characters."
            )
            return RuleResult(
                rule_name=self.name,
                is_passed=False,
                feedback=feedback,
                penalty=penalty,
                metadata=metadata,
            )

        if length < self._recommended_length:
            return RuleResult(
                rule_name=self.name,
                is_passed=True,
                feedback=f"Consider using {self._recommended_length}+ characters for maximum security.",
                penalty=0,
                metadata=metadata,
            )

        return RuleResult(rule_name=self.name, is_passed=True, penalty=0, metadata=metadata)
