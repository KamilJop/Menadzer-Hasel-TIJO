"""Custom styled text line edit component with auto-clearing error state."""

from __future__ import annotations

from PyQt6.QtWidgets import QLineEdit, QWidget


class CustomLineEdit(QLineEdit):
    """Custom styled text input with dynamic error handling and auto-clear on edit."""

    def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
        """Initializes the text line edit with optional placeholder text.

        Args:
            placeholder: Optional placeholder text displayed when empty.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._has_error: bool = False
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.textChanged.connect(self._on_text_changed)

    @property
    def has_error(self) -> bool:
        """Current error state flag.

        Returns:
            True if the input field is currently marked with error state.
        """
        return self._has_error

    def set_error(self, has_error: bool) -> None:
        """Sets or clears the visual error state of the input field.

        Args:
            has_error: Boolean flag indicating error state.
        """
        if self._has_error == has_error:
            return
        self._has_error = has_error
        self.setProperty("hasError", has_error)
        self.style().unpolish(self)
        self.style().polish(self)

    def _on_text_changed(self) -> None:
        """Internal slot automatically clearing error state when the user edits text."""
        if self._has_error:
            self.set_error(False)


__all__ = [
    "CustomLineEdit",
]
