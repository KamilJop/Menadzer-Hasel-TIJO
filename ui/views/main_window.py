"""Main application dashboard window."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.category import Category
from core.vault import Vault
from storage.interfaces import BaseVaultRepository
from ui.components import CategorySidebar
from ui.utils import responsive_scale

_MIN_WINDOW_WIDTH: int = 740
_MAX_WINDOW_WIDTH: int = 1920

_CONTENT_H_MARGIN_MIN: int = 24
_CONTENT_H_MARGIN_MAX: int = 52
_CONTENT_V_MARGIN_MIN: int = 20
_CONTENT_V_MARGIN_MAX: int = 36

_TITLE_FONT_SIZE_MIN: int = 16
_TITLE_FONT_SIZE_MAX: int = 22


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
        vault_path: Path | None = None,
        repository: BaseVaultRepository | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the main application window with vault session data.

        Args:
            vault: Active Vault instance containing user credentials.
            vault_path: Resolved path to the vault storage file.
            repository: Vault persistence repository.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._vault: Vault | None = vault
        self._vault_path: Path | None = vault_path
        self._repository: BaseVaultRepository | None = repository

        self.setWindowTitle("Password Manager")
        self.resize(940, 590)
        self.setMinimumSize(780, 520)
        self._setup_ui()
        self._update_sidebar_counts()

    def _setup_ui(self) -> None:
        """Sets up the initial dashboard layout including responsive splitter and content view."""
        central_widget = QWidget(self)
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal, central_widget)
        self._splitter.setChildrenCollapsible(False)

        self._sidebar = CategorySidebar(self._splitter)
        self._sidebar.category_selected.connect(self._on_category_selected)
        self._splitter.addWidget(self._sidebar)

        content_widget = QWidget(self._splitter)
        content_widget.setMinimumWidth(480)
        self._content_layout = QVBoxLayout(content_widget)
        self._content_layout.setContentsMargins(28, 20, 28, 20)
        self._content_layout.setSpacing(16)

        top_bar = QHBoxLayout()
        self._category_title_label = QLabel("All Items", content_widget)
        title_font = self._category_title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self._category_title_label.setFont(title_font)

        self._lock_button = QPushButton("Lock", content_widget)
        self._lock_button.setProperty("variant", "minimal")
        self._lock_button.clicked.connect(self._on_lock_clicked)

        top_bar.addWidget(self._category_title_label)
        top_bar.addStretch()
        top_bar.addWidget(self._lock_button)

        self._content_layout.addLayout(top_bar)

        self._entries_card = QFrame(content_widget)
        self._entries_card.setProperty("variant", "card")
        entries_card_layout = QVBoxLayout(self._entries_card)
        entries_card_layout.setContentsMargins(24, 24, 24, 24)
        entries_card_layout.setSpacing(12)

        self._empty_state_label = QLabel(
            "No entries found in this category.\nAdd your first password to get started.",
            self._entries_card,
        )
        self._empty_state_label.setProperty("variant", "muted")
        self._empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        entries_card_layout.addStretch()
        entries_card_layout.addWidget(self._empty_state_label)
        entries_card_layout.addStretch()

        self._content_layout.addWidget(self._entries_card, stretch=1)

        self._splitter.addWidget(content_widget)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([230, 610])

        root_layout.addWidget(self._splitter)
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        """Handles window geometry resizing to update responsive layout.

        Args:
            event: Resize event instance containing old and new sizes.
        """
        super().resizeEvent(event)
        if event is not None:
            width = event.size().width()
            height = event.size().height()
            self._on_window_resized(width, height)

    def _on_window_resized(self, width: int, height: int) -> None:
        """Recalculates fluid layout proportions, margins, and typography on window resize.

        Args:
            width: Current window width in pixels.
            height: Current window height in pixels.
        """
        h_margin = responsive_scale(
            width,
            _MIN_WINDOW_WIDTH,
            _MAX_WINDOW_WIDTH,
            _CONTENT_H_MARGIN_MIN,
            _CONTENT_H_MARGIN_MAX,
        )
        v_margin = responsive_scale(
            width,
            _MIN_WINDOW_WIDTH,
            _MAX_WINDOW_WIDTH,
            _CONTENT_V_MARGIN_MIN,
            _CONTENT_V_MARGIN_MAX,
        )
        self._content_layout.setContentsMargins(h_margin, v_margin, h_margin, v_margin)

        font_size = responsive_scale(
            width,
            _MIN_WINDOW_WIDTH,
            _MAX_WINDOW_WIDTH,
            _TITLE_FONT_SIZE_MIN,
            _TITLE_FONT_SIZE_MAX,
        )
        title_font = self._category_title_label.font()
        title_font.setPointSize(font_size)
        self._category_title_label.setFont(title_font)

    def _update_sidebar_counts(self) -> None:
        """Calculates credential counts per category and updates the sidebar badges."""
        counts: dict[Category | None, int] = {}
        if self._vault is not None:
            counts[None] = len(self._vault)
            for category in Category:
                counts[category] = len(self._vault.get_entries_by_category(category))
        else:
            counts[None] = 0
            for category in Category:
                counts[category] = 0
        self._sidebar.update_counts(counts)

    def _on_category_selected(self, category: Category | None) -> None:
        """Handles category selection changes from the sidebar.

        Args:
            category: Selected Category enum member or None for all items.
        """
        title = "All Items" if category is None else category.value
        self._category_title_label.setText(title)

    def _on_lock_clicked(self) -> None:
        """Slot handling vault locking request by emitting vault_locked signal."""
        self.vault_locked.emit()


__all__ = [
    "MainWindow",
]
