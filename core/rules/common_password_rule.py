"""Dictionary validation rule checking against common and compromised passwords."""

from __future__ import annotations

from core.rules.base import ValidationRule
from core.rules.constants import get_default_common_passwords
from core.validation_result import RuleResult


class CommonPasswordRule(ValidationRule):
    """Flags passwords matching known dictionary lists or breached credentials."""

    DEFAULT_COMMON_PASSWORD_PENALTY: int = 80

    def __init__(
        self,
        common_passwords: frozenset[str] | None = None,
        penalty: int = DEFAULT_COMMON_PASSWORD_PENALTY,
    ) -> None:
        """Initializes dictionary check rule with configurable penalty.

        Args:
            common_passwords: Set of lowercased forbidden common passwords. Defaults
                to default common passwords resource.
            penalty: Score deduction applied when password matches common list (default: 80).
        """
        self._common_passwords = (
            common_passwords if common_passwords is not None else get_default_common_passwords()
        )
        self._penalty = penalty

    @property
    def name(self) -> str:
        """Unique identifier of the rule.

        Returns:
            String name identifying this validation rule.
        """
        return "common_passwords"

    def evaluate(self, password: str) -> RuleResult:
        """Checks if password exists in the forbidden common passwords dictionary.

        Args:
            password: Plaintext password string to cross-reference with dictionary.

        Returns:
            RuleResult containing dictionary match status, penalty deductions,
            actionable guidance feedback, and match metadata.
        """
        is_common = password.lower() in self._common_passwords
        if is_common:
            return RuleResult(
                rule_name=self.name,
                is_passed=False,
                feedback="This is a commonly used password that can be easily cracked.",
                penalty=self._penalty,
                metadata={"matched_common_word": True, "is_common_or_pattern": True},
            )

        return RuleResult(
            rule_name=self.name,
            is_passed=True,
            penalty=0,
            metadata={"matched_common_word": False, "is_common_or_pattern": False},
        )
