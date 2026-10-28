"""Theme color definitions and semantic palette for user interface components."""

from __future__ import annotations

from PyQt6.QtGui import QColor


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


__all__ = [
    "NavColors",
]
