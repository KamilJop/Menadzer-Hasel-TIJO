"""Utility module for loading application QSS stylesheets."""

from __future__ import annotations

from pathlib import Path


def load_app_stylesheets() -> str:
    """Loads and combines all QSS stylesheet files from the resources directory.

    Returns:
        Consolidated QSS stylesheet string for the application.
    """
    resources_dir = Path(__file__).resolve().parent
    stylesheet_parts: list[str] = []

    for file_name in ("styles.qss", "inputs.qss"):
        qss_file = resources_dir / file_name
        if qss_file.is_file():
            try:
                stylesheet_parts.append(qss_file.read_text(encoding="utf-8"))
            except OSError:
                pass

    return "\n\n".join(stylesheet_parts)


__all__ = [
    "load_app_stylesheets",
]
