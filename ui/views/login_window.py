"""Login and unlock window for existing vault instances."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import InvalidPasswordError
from core.vault import Vault
from storage.interfaces import BaseVaultRepository
from storage.repository import VaultRepository
from ui.widgets import PasswordField


class LoginWindow(QWidget):
    """Authentication window for unlocking existing password vaults.

    Attributes:
        vault_unlocked: Signal emitted upon successful authentication and decryption of the vault,
            supplying (vault, password, vault_path).
    """

    vault_unlocked = pyqtSignal(Vault, str, Path)
    """pyqtSignal(Vault, str, Path): Emitted upon successful authentication and decryption of the vault."""

    def __init__(
        self,
        vault_path: Path,
        repository: BaseVaultRepository | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the login unlock window.

        Args:
            vault_path: Path of the encrypted vault file.
            repository: Optional repository provider (defaults to VaultRepository).
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._vault_path: Path = vault_path
        self._repository: BaseVaultRepository = (
            repository if repository is not None else VaultRepository()
        )

        self.setObjectName("loginWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle("Password Manager - Unlock")
        self.setFixedSize(460, 420)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Sets up the visual layout and login components."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 40, 40, 40)

        header_label = QLabel("Welcome Back", self)
        header_font = header_label.font()
        header_font.setPointSize(20)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(
            "Enter your password to unlock your vault.",
            self,
        )
        subtitle_label.setProperty("variant", "muted")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._password_input = PasswordField(placeholder="Password", parent=self)
        self._password_input.returnPressed.connect(self._unlock_vault)

        self._error_label = QLabel("", self)
        self._error_label.setProperty("variant", "error")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setVisible(False)

        self._unlock_button = QPushButton("Unlock Vault", self)
        self._unlock_button.clicked.connect(self._unlock_vault)

        layout.addWidget(header_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(10)
        layout.addWidget(self._password_input)
        layout.addWidget(self._error_label)
        layout.addSpacing(10)
        layout.addWidget(self._unlock_button)

    def _unlock_vault(self) -> None:
        """Attempts to decrypt and load the vault using the entered password."""
        password = self._password_input.text()

        if not password:
            self._show_error("Password cannot be empty.")
            self._password_input.set_error(True)
            self._password_input.setFocus()
            return

        try:
            vault = self._repository.load(
                password=password,
                file_path=self._vault_path,
            )
            self._clear_error()
            self._password_input.clear()
            self.vault_unlocked.emit(vault, password, self._vault_path)
        except InvalidPasswordError:
            self._show_error("Incorrect password.")
            self._password_input.set_error(True)
            self._password_input.setFocus()
        except Exception as err:
            self._show_error(f"Failed to load vault: {err}")

    def _show_error(self, message: str) -> None:
        """Displays error message banner.

        Args:
            message: Error text message to display.
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _clear_error(self) -> None:
        """Clears and hides error message banner."""
        self._error_label.setText("")
        self._error_label.setVisible(False)


__all__ = [
    "LoginWindow",
]
