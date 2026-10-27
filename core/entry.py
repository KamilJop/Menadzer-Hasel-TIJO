"""Credential entry model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

from core.category import Category
from core.exceptions import InvalidEntryError
from core.utils import get_utc_now_iso


@dataclass
class Entry:
    """Represents a single credential entry stored inside the vault.

    Includes audit timestamps (created_at, updated_at) used for tracking
    credential age, expiration checks, and synchronization history.

    Attributes:
        title: User-friendly label or name of the service/website.
        username: Username or email associated with the account.
        password: Plaintext password string for this credential.
        category: Category enum used for grouping credentials.
        url: Optional website URL or network address.
        notes: Optional user notes or additional security details.
        id: Unique identifier for the entry (UUID4).
        created_at: ISO 8601 UTC timestamp of when the entry was created.
        updated_at: ISO 8601 UTC timestamp of the last entry modification.
    """

    title: str
    username: str
    password: str = field(repr=False)
    category: Category = Category.OTHER
    url: str | None = None
    notes: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=get_utc_now_iso)
    updated_at: str = field(default_factory=get_utc_now_iso)

    def mark_updated(self) -> None:
        """Refreshes the updated_at timestamp to the current UTC time."""
        self.updated_at = get_utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        """Serializes the entry instance into a dictionary.

        Returns:
            Dictionary containing entry attributes.
        """
        return {
            "id": self.id,
            "title": self.title,
            "username": self.username,
            "password": self.password,
            "category": self.category.value,
            "url": self.url,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Entry:
        """Instantiates an Entry from a dictionary payload.

        Args:
            data: Dictionary containing key-value pairs matching Entry attributes.

        Raises:
            InvalidEntryError: If required fields (title, username, password) are missing.

        Returns:
            New Entry instance populated with data.
        """
        raw_category = data.get("category", Category.OTHER.value)
        try:
            category = Category(raw_category)
        except ValueError:
            category = Category.OTHER

        now_iso = get_utc_now_iso()
        try:
            return cls(
                id=data.get("id", str(uuid.uuid4())),
                title=data["title"],
                username=data["username"],
                password=data["password"],
                category=category,
                url=data.get("url"),
                notes=data.get("notes"),
                created_at=data.get("created_at", now_iso),
                updated_at=data.get("updated_at", now_iso),
            )
        except KeyError as err:
            raise InvalidEntryError(f"Missing required entry field: {err}") from err
