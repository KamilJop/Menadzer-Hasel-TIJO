"""Password strength level enumeration supporting comparative evaluation."""

from __future__ import annotations

from enum import IntEnum


class StrengthLevel(IntEnum):
    """Categorical classification of password security strength with ordinal values."""

    VERY_WEAK = 1
    WEAK = 2
    FAIR = 3
    STRONG = 4
    VERY_STRONG = 5

    @property
    def rank(self) -> int:
        """Numerical ordering rank for comparative evaluations (1 to 5).

        Returns:
            Integer rank value corresponding to the enumeration value.
        """
        return self.value

    def is_at_least(self, minimum_level: StrengthLevel) -> bool:
        """Checks if this level meets or exceeds the specified minimum level.

        Args:
            minimum_level: Target StrengthLevel to compare against.

        Returns:
            True if this level rank is greater than or equal to minimum_level.
        """
        return self.value >= minimum_level.value
