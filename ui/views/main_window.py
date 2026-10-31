"""Main application dashboard window."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QResizeEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.category import Category
from core.entry import Entry
from core.vault import Vault
from storage.interfaces import BaseVaultRepository
from ui.services.clipboard_service import ClipboardService
from ui.services.favicon_service import FaviconService
from ui.utils import responsive_scale
from ui.views.dialogs import EntryDialog
from ui.widgets.category_sidebar import CategorySidebar
from ui.widgets.entry_card import EntryCard
from ui.widgets.floating_action_button import FloatingActionButton
from ui.widgets.toast import ToastNotification

_logger = logging.getLogger(__name__)

_CLIPBOARD_AUTO_CLEAR_DELAY_MS: int = 30_000

_MIN_WINDOW_WIDTH: int = 740
_MAX_WINDOW_WIDTH: int = 1920

_CONTENT_H_MARGIN_MIN: int = 24
_CONTENT_H_MARGIN_MAX: int = 52
_CONTENT_V_MARGIN_MIN: int = 20
_CONTENT_V_MARGIN_MAX: int = 36

_TITLE_FONT_SIZE_MIN: int = 16
_TITLE_FONT_SIZE_MAX: int = 22

_FAB_SIZE: int = 56
_FAB_MARGIN_RIGHT: int = 44
_FAB_MARGIN_BOTTOM: int = 40


class MainWindow(QMainWindow):
    """Primary application window for password management dashboard.

    Adheres to the Single Responsibility Principle (SRP) and Dependency Inversion
    Principle (DIP) by delegating persistence to repositories, navigation to the sidebar,
    entry card rendering to EntryCard, clipboard auto-clearing to ClipboardService,
    and favicon fetching to FaviconService.

    Attributes:
        vault_locked: Signal emitted when the user requests locking the vault session.
    """

    vault_locked = pyqtSignal()

    def __init__(
        self,
        vault: Vault | None = None,
        vault_path: Path | None = None,
        repository: BaseVaultRepository | None = None,
        master_password: str | None = None,
        favicon_service: FaviconService | None = None,
        clipboard_service: ClipboardService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the main application window with vault session data.

        Args:
            vault: Active Vault instance containing user credentials.
            vault_path: Resolved path to the vault storage file.
            repository: Vault persistence repository implementing BaseVaultRepository.
            master_password: Master password string for encrypting vault changes.
            favicon_service: Optional pre-configured FaviconService instance.
            clipboard_service: Optional pre-configured ClipboardService instance.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._vault: Vault | None = vault
        self._vault_path: Path | None = vault_path
        self._repository: BaseVaultRepository | None = repository
        self._master_password: str | None = master_password
        self._selected_category: Category | None = None

        icons_dir = Path(__file__).resolve().parent.parent / "resources" / "icons"
        self._check_icon: QIcon = QIcon(str(icons_dir / "check.svg"))

        self._favicon_service: FaviconService = (
            favicon_service if favicon_service is not None else FaviconService(self)
        )
        self._clipboard_service: ClipboardService = (
            clipboard_service
            if clipboard_service is not None
            else ClipboardService(
                parent=self,
                auto_clear_delay_ms=_CLIPBOARD_AUTO_CLEAR_DELAY_MS,
            )
        )

        self._splitter: QSplitter
        self._sidebar: CategorySidebar
        self._content_layout: QVBoxLayout
        self._category_title_label: QLabel
        self._lock_button: QPushButton
        self._entries_card: QFrame
        self._entries_card_layout: QVBoxLayout
        self._empty_state_label: QLabel
        self._scroll_area: QScrollArea
        self._entries_container: QWidget
        self._entries_list_layout: QVBoxLayout
        self._fab_button: FloatingActionButton
        self._toast: ToastNotification = ToastNotification(self)

        self.setWindowTitle("Password Manager")
        self.resize(940, 590)
        self.setMinimumSize(780, 520)
        self._setup_ui()
        self._update_sidebar_counts()
        self._refresh_entries_view()

    def _setup_ui(self) -> None:
        """Sets up the initial dashboard layout including responsive splitter and content view."""
        central_widget = QWidget(self)
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._splitter = self._create_main_splitter(central_widget)
        root_layout.addWidget(self._splitter)
        self.setCentralWidget(central_widget)

        self._setup_floating_action_button(central_widget)
        self._on_window_resized(self.width(), self.height())

    def _create_main_splitter(self, parent: QWidget) -> QSplitter:
        """Constructs the horizontal splitter separating sidebar and entries content.

        Args:
            parent: Parent container widget.

        Returns:
            Configured QSplitter widget.
        """
        splitter = QSplitter(Qt.Orientation.Horizontal, parent)
        splitter.setChildrenCollapsible(False)

        self._sidebar = CategorySidebar(splitter)
        self._sidebar.category_selected.connect(self._on_category_selected)
        splitter.addWidget(self._sidebar)

        content_widget = self._create_content_area(splitter)
        splitter.addWidget(content_widget)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([230, 610])
        return splitter

    def _create_content_area(self, parent: QWidget) -> QWidget:
        """Constructs the right-hand dashboard content container.

        Args:
            parent: Parent container widget.

        Returns:
            Configured content QWidget.
        """
        content_widget = QWidget(parent)
        content_widget.setMinimumWidth(480)
        self._content_layout = QVBoxLayout(content_widget)
        self._content_layout.setContentsMargins(28, 20, 28, 20)
        self._content_layout.setSpacing(16)

        top_bar = self._create_top_bar(content_widget)
        self._content_layout.addLayout(top_bar)

        self._entries_card = self._create_entries_card(content_widget)
        self._content_layout.addWidget(self._entries_card, stretch=1)
        return content_widget

    def _create_top_bar(self, parent: QWidget) -> QHBoxLayout:
        """Constructs the top action bar containing category title and lock button.

        Args:
            parent: Parent container widget.

        Returns:
            Configured QHBoxLayout instance.
        """
        top_bar = QHBoxLayout()
        self._category_title_label = QLabel("All Items", parent)
        title_font = self._category_title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self._category_title_label.setFont(title_font)

        self._lock_button = QPushButton("Lock", parent)
        self._lock_button.setProperty("variant", "minimal")
        self._lock_button.clicked.connect(self._on_lock_clicked)

        top_bar.addWidget(self._category_title_label)
        top_bar.addStretch()
        top_bar.addWidget(self._lock_button)
        return top_bar

    def _create_entries_card(self, parent: QWidget) -> QFrame:
        """Constructs the card frame containing the scroll area and empty state label.

        Args:
            parent: Parent container widget.

        Returns:
            Configured QFrame card widget.
        """
        card = QFrame(parent)
        card.setProperty("variant", "card")
        self._entries_card_layout = QVBoxLayout(card)
        self._entries_card_layout.setContentsMargins(20, 20, 20, 20)
        self._entries_card_layout.setSpacing(12)

        self._empty_state_label = QLabel(
            "No entries found in this category.\nClick '+' below to get started.",
            card,
        )
        self._empty_state_label.setProperty("variant", "muted")
        self._empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._entries_card_layout.addWidget(self._empty_state_label)

        self._scroll_area = QScrollArea(card)
        self._scroll_area.setObjectName("entriesScrollArea")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self._entries_container = QWidget()
        self._entries_container.setObjectName("entriesContainer")
        self._entries_list_layout = QVBoxLayout(self._entries_container)
        self._entries_list_layout.setContentsMargins(0, 0, 0, 0)
        self._entries_list_layout.setSpacing(10)
        self._entries_list_layout.addStretch()

        self._scroll_area.setWidget(self._entries_container)
        self._scroll_area.setVisible(False)
        self._entries_card_layout.addWidget(self._scroll_area)
        return card

    def _setup_floating_action_button(self, parent: QWidget) -> None:
        """Configures the floating action button for adding new credentials.

        Args:
            parent: Parent container widget.
        """
        self._fab_button = FloatingActionButton(parent)
        self._fab_button.clicked.connect(self._open_add_entry_dialog)
        self._fab_button.raise_()

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
        if width <= 0 or height <= 0:
            return

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

        font_size = max(
            1,
            responsive_scale(
                width,
                _MIN_WINDOW_WIDTH,
                _MAX_WINDOW_WIDTH,
                _TITLE_FONT_SIZE_MIN,
                _TITLE_FONT_SIZE_MAX,
            ),
        )
        title_font = self._category_title_label.font()
        title_font.setPointSize(font_size)
        self._category_title_label.setFont(title_font)

        fab_x = width - _FAB_SIZE - _FAB_MARGIN_RIGHT
        fab_y = height - _FAB_SIZE - _FAB_MARGIN_BOTTOM
        self._fab_button.set_base_pos(fab_x, fab_y)
        self._fab_button.raise_()
        self._toast.reposition()

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
        self._selected_category = category
        title = "All Items" if category is None else category.value
        self._category_title_label.setText(title)
        self._refresh_entries_view()

    def _open_add_entry_dialog(self) -> None:
        """Opens the modal entry dialog to create a new password in the current category."""
        dialog = EntryDialog(
            parent=self,
            initial_category=self._selected_category,
        )
        if dialog.exec() == EntryDialog.DialogCode.Accepted:
            new_entry = dialog.get_entry()
            if new_entry is not None and self._vault is not None:
                self._vault.add_entry(new_entry)
                self._save_vault()
                self._update_sidebar_counts()
                self._refresh_entries_view()
                self._toast.show_message(
                    f"Password '{new_entry.title}' added successfully.",
                    icon=self._check_icon,
                )

    def _save_vault(self) -> None:
        """Saves current vault contents to storage using master password if available."""
        if (
            self._vault is not None
            and self._repository is not None
            and self._vault_path is not None
            and self._master_password is not None
        ):
            try:
                self._repository.save(
                    vault=self._vault,
                    password=self._master_password,
                    file_path=self._vault_path,
                )
            except Exception as err:
                _logger.exception("Failed to persist vault changes to storage: %s", err)
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save vault changes to storage:\n{err}",
                )

    def _clear_entries_list(self) -> None:
        """Removes all currently displayed entry rows from the scroll container."""
        while self._entries_list_layout.count() > 1:
            item = self._entries_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _get_active_entries(self) -> list[Entry]:
        """Retrieves entries matching the active category filter.

        Returns:
            List of matching Entry instances.
        """
        if self._vault is None:
            return []
        if self._selected_category is None:
            return list(self._vault.entries)
        return self._vault.get_entries_by_category(self._selected_category)

    def _refresh_entries_view(self) -> None:
        """Refreshes the entries card display based on active category selection."""
        self._clear_entries_list()
        entries = self._get_active_entries()

        if not entries:
            self._empty_state_label.setVisible(True)
            self._scroll_area.setVisible(False)
            return

        self._empty_state_label.setVisible(False)
        self._scroll_area.setVisible(True)

        for entry in entries:
            card_widget = self._create_entry_row(entry)
            self._entries_list_layout.insertWidget(
                self._entries_list_layout.count() - 1, card_widget
            )

    def _create_entry_row(self, entry: Entry) -> EntryCard:
        """Constructs an EntryCard widget displaying credential data and action handlers.

        Args:
            entry: Credential entry instance to display.

        Returns:
            Configured EntryCard component.
        """
        card = EntryCard(
            entry=entry,
            favicon_service=self._favicon_service,
            parent=self._entries_container,
        )
        card.copy_requested.connect(self._on_copy_requested)
        card.delete_requested.connect(self._delete_entry)
        return card

    def _on_copy_requested(self, text: str, field_name: str) -> None:
        """Handles copy request by copying text via ClipboardService and showing toast.

        Args:
            text: Plaintext credential to copy into clipboard.
            field_name: Descriptive name of the copied credential field.
        """
        if self._clipboard_service.copy_text(text):
            self._toast.show_message(
                "Copied to clipboard. Auto-clearing in 30 seconds.",
                icon=self._check_icon,
            )

    def _delete_entry(self, entry: Entry, confirm: bool = True) -> None:
        """Prompts confirmation and removes the specified credential entry from vault.

        Args:
            entry: Entry instance to remove.
            confirm: Whether to show confirmation prompt dialog before removal.
        """
        if self._vault is None:
            return

        if confirm:
            reply = QMessageBox.question(
                self,
                "Delete Password",
                f"Are you sure you want to delete '{entry.title}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        entry_title = entry.title
        self._vault.remove_entry(entry.id)
        self._save_vault()
        self._update_sidebar_counts()
        self._refresh_entries_view()
        self._toast.show_message(
            f"Password '{entry_title}' deleted.",
            icon=self._check_icon,
        )

    def _on_lock_clicked(self) -> None:
        """Slot handling vault locking request by emitting vault_locked signal."""
        self.vault_locked.emit()


__all__ = [
    "MainWindow",
]
