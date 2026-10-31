"""Welcome and onboarding window for initial vault creation."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.vault import Vault
from storage.interfaces import BaseVaultRepository
from storage.repository import VaultRepository
from ui.widgets import PasswordField


class WelcomeWindow(QWidget):
    """Initial onboarding window for setting up password and creating the vault.

    Attributes:
        vault_created: Signal emitted upon initial creation and persistence of the vault,
            supplying (vault, password, vault_path).
    """

    vault_created = pyqtSignal(Vault, str, Path)
    """pyqtSignal(Vault, str, Path): Emitted upon initial creation and persistence of the vault."""

    def __init__(
        self,
        vault_path: Path,
        repository: BaseVaultRepository | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the welcome onboarding window.

        Args:
            vault_path: Target path where the new vault will be persisted.
            repository: Optional repository provider (defaults to VaultRepository).
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._vault_path: Path = vault_path
        self._repository: BaseVaultRepository = (
            repository if repository is not None else VaultRepository()
        )

        self.setObjectName("welcomeWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle("Password Manager - Welcome")
        self.setFixedSize(480, 500)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Sets up the visual layout and form components."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 40, 40, 40)

        header_label = QLabel("Welcome to Password Manager", self)
        header_font = header_label.font()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(
            "Secure local vault for your credentials.\nLet's get started by setting up your password.",
            self,
        )
        subtitle_label.setProperty("variant", "muted")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._password_input = PasswordField(placeholder="Enter password", parent=self)
        self._confirm_input = PasswordField(placeholder="Confirm password", parent=self)

        self._password_input.returnPressed.connect(self._confirm_input.setFocus)
        self._confirm_input.returnPressed.connect(self._create_vault)

        self._error_label = QLabel("", self)
        self._error_label.setProperty("variant", "error")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setVisible(False)

        self._create_button = QPushButton("Create Vault", self)
        self._create_button.clicked.connect(self._create_vault)

        layout.addWidget(header_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(10)
        layout.addWidget(self._password_input)
        layout.addWidget(self._confirm_input)
        layout.addWidget(self._error_label)
        layout.addSpacing(10)
        layout.addWidget(self._create_button)

    def _create_vault(self) -> None:
        """Validates passwords and initializes a new encrypted vault."""
        password = self._password_input.text()
        confirm = self._confirm_input.text()

        if not password:
            self._show_error("Password cannot be empty.")
            self._password_input.set_error(True)
            self._password_input.setFocus()
            return

        if password != confirm:
            self._show_error("Passwords do not match.")
            self._confirm_input.set_error(True)
            self._confirm_input.setFocus()
            return

        self._clear_error()
        new_vault = Vault()

        try:
            saved_path = self._repository.save(
                vault=new_vault,
                password=password,
                file_path=self._vault_path,
            )
            self._password_input.clear()
            self._confirm_input.clear()
            self.vault_created.emit(new_vault, password, saved_path)
        except Exception as err:
            self._show_error(f"Failed to create vault: {err}")

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
    "WelcomeWindow",
]
