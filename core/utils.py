"""Utility functions for time formatting and core operations."""

from datetime import datetime, timezone


def get_utc_now_iso() -> str:
    """Returns the current UTC timestamp formatted as an ISO 8601 string.

    Returns:
        ISO 8601 formatted UTC timestamp string.
    """
    return datetime.now(timezone.utc).isoformat()
