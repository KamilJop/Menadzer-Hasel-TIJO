"""Password field component with integrated visibility toggle action."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QLineEdit, QWidget

from ui.components.text_field import CustomLineEdit


class PasswordField(CustomLineEdit):
    """Custom styled password input field with embedded show/hide visibility toggle."""

    def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
        """Initializes the password field with masked echo mode and visibility toggle.

        Args:
            placeholder: Optional placeholder text displayed when field is empty.
            parent: Optional parent QWidget.
        """
        super().__init__(placeholder=placeholder, parent=parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)

        icons_dir = Path(__file__).resolve().parent.parent / "resources" / "icons"
        self._eye_open_icon: QIcon = QIcon(str(icons_dir / "eye_open.svg"))
        self._eye_closed_icon: QIcon = QIcon(str(icons_dir / "eye_closed.svg"))

        self._toggle_action: QAction = self.addAction(
            self._eye_closed_icon,
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self._toggle_action.setToolTip("Toggle password visibility")
        self._toggle_action.triggered.connect(self.toggle_password_visibility)

    def is_password_visible(self) -> bool:
        """Checks whether the password characters are currently unmasked.

        Returns:
            True if text is displayed as normal characters, False if masked.
        """
        return self.echoMode() == QLineEdit.EchoMode.Normal

    def toggle_password_visibility(self) -> None:
        """Toggles the password between masked and plaintext echo modes."""
        if self.echoMode() == QLineEdit.EchoMode.Password:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_action.setIcon(self._eye_open_icon)
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_action.setIcon(self._eye_closed_icon)


__all__ = [
    "PasswordField",
]
