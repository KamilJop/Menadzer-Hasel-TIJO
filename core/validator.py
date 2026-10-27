"""Password validation orchestrator coordinating modular validation rule strategies."""

from __future__ import annotations

from collections.abc import Sequence

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


def get_default_validation_rules() -> tuple[ValidationRule, ...]:
    """Factory creating the default suite of password security rules.

    Returns:
        Tuple containing initialized default validation rules.
    """
    return (
        LengthRule(),
        CharacterDiversityRule(),
        EntropyRule(),
        CommonPasswordRule(),
        SequenceAndRepetitionRule(),
    )


class PasswordValidator:
    """Orchestrates modular password validation rules to produce comprehensive strength evaluations."""

    def __init__(self, rules: Sequence[ValidationRule] | None = None) -> None:
        """Initializes the password validator with specified or default rules.

        Args:
            rules: Sequence of ValidationRule instances to evaluate (defaults to standard rule suite).
        """
        self._rules: tuple[ValidationRule, ...] = (
            tuple(rules) if rules is not None else get_default_validation_rules()
        )

    @property
    def rules(self) -> tuple[ValidationRule, ...]:
        """Registered validation rules.

        Returns:
            Tuple of active ValidationRule instances configured for this validator.
        """
        return self._rules

    @classmethod
    def create_default(cls) -> PasswordValidator:
        """Creates a validator configured with the standard default rule set.

        Returns:
            PasswordValidator instance with default rules.
        """
        return cls(rules=get_default_validation_rules())

    def validate(self, password: str) -> ValidationResult:
        """Evaluates a password against all configured rules and calculates aggregate metrics.

        Args:
            password: Plaintext password string to analyze.

        Returns:
            ValidationResult containing score, strength level, entropy, and guidance messages.
        """
        if not isinstance(password, str):
            password = ""

        rule_results: list[RuleResult] = []
        feedback_list: list[str] = []
        total_penalties = 0
        entropy_bits = 0.0

        for rule in self._rules:
            result = rule.evaluate(password)
            rule_results.append(result)
            total_penalties += result.penalty

            if result.feedback:
                feedback_list.append(result.feedback)

            if "entropy_bits" in result.metadata:
                entropy_value = result.metadata["entropy_bits"]
                if isinstance(entropy_value, (int, float)):
                    entropy_bits = float(entropy_value)

        score = max(0, min(100, 100 - total_penalties))
        if not password:
            score = 0

        level = self._determine_level(score)

        return ValidationResult(
            score=score,
            level=level,
            entropy_bits=entropy_bits,
            feedback=tuple(feedback_list),
            rule_results=tuple(rule_results),
        )

    @staticmethod
    def _determine_level(score: int) -> StrengthLevel:
        """Maps an integer score (0–100) to its corresponding StrengthLevel tier.

        Args:
            score: Computed normalized password score between 0 and 100.

        Returns:
            Categorical StrengthLevel tier.
        """
        if score <= 20:
            return StrengthLevel.VERY_WEAK
        if score <= 40:
            return StrengthLevel.WEAK
        if score <= 60:
            return StrengthLevel.FAIR
        if score <= 80:
            return StrengthLevel.STRONG
        return StrengthLevel.VERY_STRONG
