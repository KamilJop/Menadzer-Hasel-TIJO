"""Responsive layout scaling utilities."""

from __future__ import annotations


def calculate_scale_factor(
    current: float,
    min_bound: float = 740.0,
    max_bound: float = 1920.0,
) -> float:
    """Calculates normalized progress factor clamped between 0.0 and 1.0.

    Args:
        current: Current viewport dimension (e.g. width or height).
        min_bound: Lower viewport breakpoint limit.
        max_bound: Upper viewport breakpoint limit.

    Returns:
        Progress factor float clamped between 0.0 and 1.0.
    """
    if max_bound <= min_bound:
        return 0.0
    return max(0.0, min(1.0, (current - min_bound) / (max_bound - min_bound)))


def lerp(start: float, end: float, factor: float) -> float:
    """Linearly interpolates between start and end values by a normalized factor.

    Args:
        start: Starting minimum boundary value.
        end: Ending maximum boundary value.
        factor: Normalized progress factor between 0.0 and 1.0.

    Returns:
        Interpolated float result.
    """
    clamped_factor = max(0.0, min(1.0, factor))
    return start + (end - start) * clamped_factor


def responsive_scale(
    current: float,
    min_bound: float,
    max_bound: float,
    target_min: float,
    target_max: float,
) -> int:
    """Calculates responsive target dimension based on viewport boundaries (similar to CSS clamp).

    Args:
        current: Current viewport dimension (e.g. width or height).
        min_bound: Lower viewport breakpoint limit.
        max_bound: Upper viewport breakpoint limit.
        target_min: Target dimension at or below lower viewport bound.
        target_max: Target dimension at or above upper viewport bound.

    Returns:
        Scaled integer value rounded to the nearest pixel.
    """
    factor = calculate_scale_factor(current, min_bound, max_bound)
    return int(round(lerp(target_min, target_max, factor)))


__all__ = [
    "calculate_scale_factor",
    "lerp",
    "responsive_scale",
]
