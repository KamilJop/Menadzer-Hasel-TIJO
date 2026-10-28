"""Main application dashboard window."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.vault import Vault
from storage.interfaces import BaseVaultRepository


class MainWindow(QMainWindow):
    """Primary application window for password management dashboard.

    Attributes:
        vault_locked: Signal emitted when the user requests locking the vault session.
    """

    vault_locked = pyqtSignal()
    """pyqtSignal: Emitted when the user requests locking the active vault session."""

    def __init__(
        self,
        vault: Vault | None = None,
        password: str = "",
        vault_path: Path | None = None,
        repository: BaseVaultRepository | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the main application window with vault session data.

        Args:
            vault: Active Vault instance containing user credentials.
            password: User password for re-encrypting changes.
            vault_path: Resolved path to the vault storage file.
            repository: Vault persistence repository.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._vault: Vault | None = vault
        self._password: str = password
        self._vault_path: Path | None = vault_path
        self._repository: BaseVaultRepository | None = repository

        self.setWindowTitle("Password Manager")
        self.resize(900, 600)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Sets up the initial dashboard layout."""
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        top_bar = QHBoxLayout()
        title_label = QLabel("Password Manager", central_widget)
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)

        entries_count = len(self._vault) if self._vault is not None else 0
        self._status_label = QLabel(f"{entries_count} entries stored", central_widget)
        self._status_label.setProperty("variant", "muted")

        self._lock_button = QPushButton("Lock", central_widget)
        self._lock_button.setProperty("variant", "minimal")
        self._lock_button.clicked.connect(self._on_lock_clicked)

        top_bar.addWidget(title_label)
        top_bar.addWidget(self._status_label)
        top_bar.addStretch()
        top_bar.addWidget(self._lock_button)

        main_layout.addLayout(top_bar)
        main_layout.addStretch()

        self.setCentralWidget(central_widget)

    def _on_lock_clicked(self) -> None:
        """Slot handling vault locking request by emitting vault_locked signal."""
        self.vault_locked.emit()


__all__ = [
    "MainWindow",
]
