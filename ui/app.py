"""Application bootstrap and entry point for the desktop password manager."""

from __future__ import annotations

from pathlib import Path
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QWidget

from core.vault import Vault
from storage.interfaces import BaseVaultRepository
from storage.repository import VaultRepository
from ui.resources.style_loader import load_app_stylesheets
from ui.views.login_window import LoginWindow
from ui.views.main_window import MainWindow
from ui.views.welcome_window import WelcomeWindow


class AppController:
    """Manages application lifecycle and navigation between primary window states."""

    def __init__(
        self,
        app: QApplication,
        vault_path: Path | None = None,
        repository: BaseVaultRepository | None = None,
    ) -> None:
        """Initializes the controller with application instance and vault file target.

        Args:
            app: Active QApplication instance.
            vault_path: Optional explicit path for the vault storage file.
            repository: Optional persistence repository implementing BaseVaultRepository.
        """
        self._app: QApplication = app
        self._vault_path: Path = (
            Path(vault_path).resolve() if vault_path is not None else Path("vault.dat").resolve()
        )
        self._repository: BaseVaultRepository = (
            repository if repository is not None else VaultRepository(default_path=self._vault_path)
        )
        self._active_window: QWidget | None = None

    def start(self) -> None:
        """Determines initial application view based on existing vault presence."""
        if self._repository.exists(self._vault_path):
            self._show_login()
        else:
            self._show_welcome()

    def _show_welcome(self) -> None:
        """Instantiates and presents the onboarding welcome window."""
        self._close_active_window()
        window = WelcomeWindow(
            vault_path=self._vault_path,
            repository=self._repository,
        )
        window.vault_created.connect(self._on_vault_unlocked)
        window.show()
        self._active_window = window

    def _show_login(self) -> None:
        """Instantiates and presents the login unlock window."""
        self._close_active_window()
        window = LoginWindow(
            vault_path=self._vault_path,
            repository=self._repository,
        )
        window.vault_unlocked.connect(self._on_vault_unlocked)
        window.show()
        self._active_window = window

    def _on_vault_unlocked(self, vault: Vault, password: str, path: Path) -> None:
        """Switches to the main dashboard after successful vault creation or unlock.

        Args:
            vault: Unlocked or newly created Vault instance.
            password: User password for encrypting changes.
            path: Path to the vault storage file.
        """
        self._close_active_window()
        window = MainWindow(
            vault=vault,
            vault_path=path,
            repository=self._repository,
            master_password=password,
        )
        window.vault_locked.connect(self._on_vault_locked)
        window.show()
        self._active_window = window

    def _on_vault_locked(self) -> None:
        """Transitions back to the login window upon vault lock."""
        self._close_active_window()
        self._show_login()

    def _close_active_window(self) -> None:
        """Safely closes and unregisters the active view window."""
        if self._active_window is not None:
            self._active_window.close()
            self._active_window = None


def create_application() -> QApplication:
    """Creates and configures the global QApplication instance.

    Returns:
        Configured QApplication instance.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Password Manager")
    app.setApplicationDisplayName("Password Manager")
    app.setOrganizationName("Yuris")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(load_app_stylesheets())
    return app


def main() -> int:
    """Entry point initializing and starting the desktop application event loop.

    Returns:
        Exit code returned by Qt event loop execution.
    """
    app = create_application()
    controller = AppController(app)
    controller.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

__all__ = [
    "AppController",
    "create_application",
    "main",
]
