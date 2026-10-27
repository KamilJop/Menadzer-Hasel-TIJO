"""Vault container managing credential entries."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from core.category import Category
from core.entry import Entry


@dataclass
class Vault:
    """Container managing the collection of credential entries.

    Attributes:
        entries: List of credential entries in the vault.
    """

    entries: list[Entry] = field(default_factory=list)

    def add_entry(self, entry: Entry) -> None:
        """Adds a new entry to the vault.

        Args:
            entry: Entry instance to add.

        Raises:
            TypeError: If entry is not an instance of Entry.
            ValueError: If an entry with the same identifier already exists.
        """
        if not isinstance(entry, Entry):
            raise TypeError(f"Expected Entry instance, got {type(entry).__name__}.")
        if self.get_entry(entry.id) is not None:
            raise ValueError(f"Entry with ID '{entry.id}' already exists.")
        self.entries.append(entry)

    def get_entry(self, entry_id: str) -> Entry | None:
        """Finds an entry by its unique identifier.

        Args:
            entry_id: UUID string of the target entry.

        Raises:
            TypeError: If entry_id is not a string.

        Returns:
            Matching Entry instance or None if not found.
        """
        if not isinstance(entry_id, str):
            raise TypeError(f"Expected entry_id to be a str, got {type(entry_id).__name__}.")
        for item in self.entries:
            if item.id == entry_id:
                return item
        return None

    def update_entry(self, entry: Entry) -> bool:
        """Updates an existing entry in the vault and refreshes its timestamp.

        Args:
            entry: Entry instance containing updated information.

        Raises:
            TypeError: If entry is not an instance of Entry.

        Returns:
            True if the entry was found and updated, False otherwise.
        """
        if not isinstance(entry, Entry):
            raise TypeError(f"Expected Entry instance, got {type(entry).__name__}.")
        for index, item in enumerate(self.entries):
            if item.id == entry.id:
                entry.mark_updated()
                self.entries[index] = entry
                return True
        return False

    def remove_entry(self, entry_id: str) -> bool:
        """Removes an entry by its unique identifier.

        Args:
            entry_id: UUID string of the entry to remove.

        Raises:
            TypeError: If entry_id is not a string.

        Returns:
            True if an entry was removed, False if not found.
        """
        if not isinstance(entry_id, str):
            raise TypeError(f"Expected entry_id to be a str, got {type(entry_id).__name__}.")
        for index, item in enumerate(self.entries):
            if item.id == entry_id:
                del self.entries[index]
                return True
        return False

    def clear(self) -> None:
        """Removes all entries from the vault."""
        self.entries.clear()

    def find_entries(self, predicate: Callable[[Entry], bool]) -> list[Entry]:
        """Finds entries matching a filter predicate.

        Args:
            predicate: Callable that takes an Entry and returns True if it matches.

        Returns:
            List of entries satisfying the predicate.
        """
        return [item for item in self.entries if predicate(item)]

    def get_entries_by_category(self, category: Category) -> list[Entry]:
        """Filters entries by their assigned category.

        Args:
            category: Category enum to filter by.

        Returns:
            List of matching Entry instances.
        """
        return self.find_entries(lambda item: item.category == category)

    def to_dict(self) -> dict[str, Any]:
        """Converts vault data into a serializable dictionary.

        Returns:
            Dictionary containing serialized entries.
        """
        return {
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Vault:
        """Instantiates a Vault from a dictionary payload.

        Args:
            data: Dictionary representation of the vault containing an 'entries' list.

        Raises:
            KeyError: If an entry payload lacks required keys (title, username, password).

        Returns:
            Populated Vault instance.
        """
        raw_entries = data.get("entries", [])
        parsed_entries = [Entry.from_dict(item) for item in raw_entries]
        return cls(entries=parsed_entries)

    def __len__(self) -> int:
        """Returns the total number of entries in the vault."""
        return len(self.entries)

    def __iter__(self) -> Iterator[Entry]:
        """Allows iteration over entries in the vault."""
        return iter(self.entries)

    def __contains__(self, item: Entry | str) -> bool:
        """Checks if an entry or entry ID exists in the vault.

        Args:
            item: Entry instance or UUID string of the entry.

        Returns:
            True if matching entry exists, False otherwise.
        """
        target_id = item.id if isinstance(item, Entry) else item
        return any(entry.id == target_id for entry in self.entries)

    def __getitem__(self, index: int) -> Entry:
        """Accesses an entry by index."""
        return self.entries[index]
