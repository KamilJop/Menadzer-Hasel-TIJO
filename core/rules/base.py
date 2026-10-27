"""Abstract base class establishing the contract for validation rule strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.validation_result import RuleResult


class ValidationRule(ABC):
    """Abstract base class representing an extensible password validation rule strategy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the rule.

        Returns:
            String name identifying this validation rule.
        """

    @abstractmethod
    def evaluate(self, password: str) -> RuleResult:
        """Evaluates the given password against this rule's criteria.

        Args:
            password: Plaintext password string to evaluate.

        Returns:
            RuleResult instance containing status, penalty, feedback, and diagnostics.
        """
