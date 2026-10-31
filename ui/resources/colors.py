"""Theme color definitions and semantic palette for user interface components."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from core.strength_level import StrengthLevel


class NavColors:
    """Color constants for category navigation items and sidebars."""

    BASE_BG: QColor = QColor(24, 25, 34)
    HOVER_BG: QColor = QColor(30, 32, 44)
    ACTIVE_BG: QColor = QColor(40, 44, 70)

    BASE_BORDER: QColor = QColor(38, 40, 54)
    HOVER_BORDER: QColor = QColor(55, 58, 78)
    ACTIVE_BORDER: QColor = QColor(99, 102, 241)

    TEXT_MUTED: QColor = QColor(161, 161, 170)
    TEXT_ACTIVE: QColor = QColor(255, 255, 255)

    BADGE_BASE_BG: QColor = QColor(36, 38, 52)
    BADGE_ACTIVE_BG: QColor = QColor(67, 56, 202)
    BADGE_BASE_FG: QColor = QColor(130, 134, 150)
    BADGE_ACTIVE_FG: QColor = QColor(230, 235, 255)


class StrengthColors:
    """Color palette definitions for password security strength tiers."""

    VERY_WEAK: QColor = QColor(239, 68, 68)
    WEAK: QColor = QColor(249, 115, 22)
    FAIR: QColor = QColor(234, 179, 8)
    STRONG: QColor = QColor(34, 197, 94)
    VERY_STRONG: QColor = QColor(16, 185, 129)
    EMPTY: QColor = QColor(39, 39, 42)
    TEXT_MUTED: QColor = QColor(113, 113, 122)

    @classmethod
    def get_color(cls, level: StrengthLevel | None) -> QColor:
        """Resolves theme QColor for the specified strength level.

        Args:
            level: StrengthLevel enum member or None for empty state.

        Returns:
            Resolved QColor instance.
        """
        match level:
            case StrengthLevel.VERY_WEAK:
                return cls.VERY_WEAK
            case StrengthLevel.WEAK:
                return cls.WEAK
            case StrengthLevel.FAIR:
                return cls.FAIR
            case StrengthLevel.STRONG:
                return cls.STRONG
            case StrengthLevel.VERY_STRONG:
                return cls.VERY_STRONG
            case _:
                return cls.EMPTY


__all__ = [
    "NavColors",
    "StrengthColors",
]
