"""Color manipulation and interpolation utilities."""

from __future__ import annotations

from PyQt6.QtGui import QColor


def interpolate_color(c1: QColor, c2: QColor, factor: float) -> QColor:
    """Linearly interpolates between two QColor instances.

    Args:
        c1: Starting source color.
        c2: Ending target color.
        factor: Interpolation factor from 0.0 to 1.0.

    Returns:
        Blended QColor result.
    """
    clamped_factor = max(0.0, min(1.0, factor))
    r = int(c1.red() + (c2.red() - c1.red()) * clamped_factor)
    g = int(c1.green() + (c2.green() - c1.green()) * clamped_factor)
    b = int(c1.blue() + (c2.blue() - c1.blue()) * clamped_factor)
    a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * clamped_factor)
    return QColor(r, g, b, a)


__all__ = [
    "interpolate_color",
]
