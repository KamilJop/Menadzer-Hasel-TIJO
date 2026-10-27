"""Structured validation models and results for password evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.strength_level import StrengthLevel


@dataclass(frozen=True)
class RuleResult:
    """Outcome produced by an individual validation rule evaluation.

    Attributes:
        rule_name: Distinct identifier of the evaluated rule.
        is_passed: Boolean indicating whether password satisfies the rule criteria.
        feedback: Human-readable guidance message if the rule failed or needs advisory.
        penalty: Numeric score deduction applied when the rule fails.
        metadata: Additional contextual diagnostics and metrics collected by the rule.
    """

    rule_name: str
    is_passed: bool
    feedback: str | None = None
    penalty: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    """Aggregate evaluation report produced by the password validation engine.

    Attributes:
        score: Normalized overall security score from 0 (critically weak) to 100 (maximum).
        level: Categorical StrengthLevel classification.
        entropy_bits: Theoretical Shannon entropy in bits.
        feedback: Tuple of unique actionable recommendations for improving password strength.
        rule_results: Tuple of individual RuleResult instances from all executed rules.
    """

    score: int
    level: StrengthLevel
    entropy_bits: float
    feedback: tuple[str, ...]
    rule_results: tuple[RuleResult, ...] = ()

    @property
    def has_uppercase(self) -> bool:
        """Indicates whether password contains uppercase characters."""
        return self._lookup_metadata_flag("has_uppercase")

    @property
    def has_lowercase(self) -> bool:
        """Indicates whether password contains lowercase characters."""
        return self._lookup_metadata_flag("has_lowercase")

    @property
    def has_digits(self) -> bool:
        """Indicates whether password contains numeric digits."""
        return self._lookup_metadata_flag("has_digits")

    @property
    def has_symbols(self) -> bool:
        """Indicates whether password contains special punctuation or symbols."""
        return self._lookup_metadata_flag("has_symbols")

    @property
    def is_common_or_pattern(self) -> bool:
        """Indicates whether password was flagged for common dictionary words or sequences."""
        for result in self.rule_results:
            if not result.is_passed and result.metadata.get("is_common_or_pattern", False):
                return True
        return False

    def is_acceptable(self, minimum_level: StrengthLevel = StrengthLevel.FAIR) -> bool:
        """Evaluates whether the password meets the requested acceptance threshold.

        Args:
            minimum_level: Minimum acceptable StrengthLevel (defaults to FAIR).

        Returns:
            True if password level is at least minimum_level and no common patterns were flagged.
        """
        return self.level >= minimum_level and not self.is_common_or_pattern

    def _lookup_metadata_flag(self, key: str) -> bool:
        """Searches rule metadata across all executed rules for a boolean flag.

        Args:
            key: Metadata dictionary key to look up.

        Returns:
            Boolean value if found in rule metadata, False otherwise.
        """
        for result in self.rule_results:
            if key in result.metadata and isinstance(result.metadata[key], bool):
                return result.metadata[key]
        return False
