"""Pattern validation rule detecting repeated characters and keyboard sequences."""

from __future__ import annotations

import re

from core.rules.base import ValidationRule
from core.rules.constants import get_default_sequences
from core.validation_result import RuleResult


class SequenceAndRepetitionRule(ValidationRule):
    """Detects sequential keyboard/alphabetical runs and repetitive characters."""

    REPEATED_CHARS_REGEX = re.compile(r"(.)\1{2,}")
    DEFAULT_REPETITION_PENALTY: int = 15
    DEFAULT_BASE_SEQUENCE_PENALTY: int = 10
    DEFAULT_PER_CHUNK_PENALTY: int = 5
    DEFAULT_MAX_SEQUENCE_PENALTY: int = 25

    def __init__(
        self,
        sequences: tuple[str, ...] | None = None,
        repetition_penalty: int = DEFAULT_REPETITION_PENALTY,
        base_sequence_penalty: int = DEFAULT_BASE_SEQUENCE_PENALTY,
        per_chunk_penalty: int = DEFAULT_PER_CHUNK_PENALTY,
        max_sequence_penalty: int = DEFAULT_MAX_SEQUENCE_PENALTY,
    ) -> None:
        """Initializes sequence and repetition analysis rule with configurable penalties.

        Args:
            sequences: Tuple of sequence strings to scan for (e.g. keyboard runs). Defaults
                to standard keyboard and alphabetical sequences.
            repetition_penalty: Score deduction for 3+ identical consecutive characters (default: 15).
            base_sequence_penalty: Base score deduction when at least one sequence is found (default: 10).
            per_chunk_penalty: Additional penalty for each matched sequence pattern chunk (default: 5).
            max_sequence_penalty: Maximum total penalty for sequential pattern matches (default: 25).
        """
        self._sequences = sequences if sequences is not None else get_default_sequences()
        self._repetition_penalty = repetition_penalty
        self._base_sequence_penalty = base_sequence_penalty
        self._per_chunk_penalty = per_chunk_penalty
        self._max_sequence_penalty = max_sequence_penalty

    @property
    def name(self) -> str:
        """Unique identifier of the rule.

        Returns:
            String name identifying this validation rule.
        """
        return "patterns"

    def evaluate(self, password: str) -> RuleResult:
        """Scans password for character repeats and sequential patterns.

        Args:
            password: Plaintext password string to analyze for patterns.

        Returns:
            RuleResult containing pattern detection status, penalty deductions,
            actionable guidance feedback, and detected pattern metadata.
        """
        feedback_messages: list[str] = []
        detected_patterns: list[str] = []
        penalty = 0

        if self.REPEATED_CHARS_REGEX.search(password):
            feedback_messages.append(
                "Avoid repeating the same character 3 or more times consecutively."
            )
            detected_patterns.append("consecutive_repetitions")
            penalty += self._repetition_penalty

        lower_pass = password.lower()
        found_chunks: list[str] = []
        for sequence in self._sequences:
            for i in range(len(sequence) - 2):
                chunk = sequence[i : i + 3]
                if chunk in lower_pass and chunk not in found_chunks:
                    found_chunks.append(chunk)

        if found_chunks:
            feedback_messages.append(
                f"Avoid sequential patterns like '{', '.join(found_chunks[:3])}'."
            )
            detected_patterns.append("sequential_pattern")
            calculated_sequence_penalty = (
                self._base_sequence_penalty + len(found_chunks) * self._per_chunk_penalty
            )
            penalty += min(self._max_sequence_penalty, calculated_sequence_penalty)

        is_passed = len(detected_patterns) == 0
        feedback = " ".join(feedback_messages) if feedback_messages else None
        metadata = {
            "detected_patterns": detected_patterns,
            "sequential_chunks": found_chunks,
            "is_common_or_pattern": not is_passed,
        }

        return RuleResult(
            rule_name=self.name,
            is_passed=is_passed,
            feedback=feedback,
            penalty=penalty,
            metadata=metadata,
        )
