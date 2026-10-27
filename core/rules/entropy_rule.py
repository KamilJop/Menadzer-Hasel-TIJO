"""Entropy validation rule computing theoretical keyspace password entropy."""

from __future__ import annotations

import math
import string

from core.rules.base import ValidationRule
from core.validation_result import RuleResult


class EntropyRule(ValidationRule):
    """Calculates keyspace/NIST entropy in bits based on the active character pool size."""

    SPECIAL_CHARACTERS: str = string.punctuation
    MINIMUM_ENTROPY_BITS: float = 36.0
    RECOMMENDED_ENTROPY_BITS: float = 60.0
    DEFAULT_EMPTY_PENALTY: int = 40
    DEFAULT_MAX_ENTROPY_PENALTY: int = 35

    def __init__(
        self,
        min_entropy_bits: float = MINIMUM_ENTROPY_BITS,
        recommended_entropy_bits: float = RECOMMENDED_ENTROPY_BITS,
        empty_penalty: int = DEFAULT_EMPTY_PENALTY,
        max_entropy_penalty: int = DEFAULT_MAX_ENTROPY_PENALTY,
    ) -> None:
        """Initializes entropy rule with configurable thresholds and penalties.

        Args:
            min_entropy_bits: Minimum acceptable Shannon entropy bits (default: 36.0).
            recommended_entropy_bits: Target entropy bits for optimal protection (default: 60.0).
            empty_penalty: Deduction applied when evaluating empty passwords (default: 40).
            max_entropy_penalty: Maximum deduction applied for insufficient entropy (default: 35).
        """
        self._min_entropy = min_entropy_bits
        self._recommended_entropy = recommended_entropy_bits
        self._empty_penalty = empty_penalty
        self._max_entropy_penalty = max_entropy_penalty

    @property
    def name(self) -> str:
        """Unique identifier of the rule.

        Returns:
            String name identifying this validation rule.
        """
        return "entropy"

    def evaluate(self, password: str) -> RuleResult:
        """Calculates theoretical keyspace entropy in bits based on character pool diversity.

        Args:
            password: Plaintext password string to calculate entropy for.

        Returns:
            RuleResult containing entropy evaluation status, penalty deductions,
            actionable guidance feedback, and entropy metrics in metadata.
        """
        if not password:
            return RuleResult(
                rule_name=self.name,
                is_passed=False,
                feedback="Entropy is 0 bits for empty password.",
                penalty=self._empty_penalty,
                metadata={"entropy_bits": 0.0},
            )

        pool_size = 0
        if any(c.islower() for c in password):
            pool_size += 26
        if any(c.isupper() for c in password):
            pool_size += 26
        if any(c.isdigit() for c in password):
            pool_size += 10
        if any(c in self.SPECIAL_CHARACTERS for c in password):
            pool_size += 32
        if any(c.isspace() for c in password):
            pool_size += 1

        extra_chars = sum(
            1
            for c in set(password)
            if not (c.islower() or c.isupper() or c.isdigit() or c in self.SPECIAL_CHARACTERS or c.isspace())
        )
        pool_size += extra_chars

        if pool_size <= 1:
            entropy = 0.0
        else:
            entropy = round(len(password) * math.log2(pool_size), 2)

        metadata = {"entropy_bits": entropy, "pool_size": pool_size}

        if entropy < self._min_entropy:
            shortfall = self._min_entropy - entropy
            penalty = min(
                self._max_entropy_penalty,
                int((shortfall / self._min_entropy) * self._max_entropy_penalty),
            )
            return RuleResult(
                rule_name=self.name,
                is_passed=False,
                feedback=f"Password entropy ({entropy:.1f} bits) is low. Add more variety and length.",
                penalty=penalty,
                metadata=metadata,
            )

        return RuleResult(rule_name=self.name, is_passed=True, penalty=0, metadata=metadata)
