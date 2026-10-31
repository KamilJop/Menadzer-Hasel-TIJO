"""Sidebar navigation widget organizing credentials by category with keyboard navigation."""

from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.category import Category
from ui.widgets.category_nav_item import CategoryNavItem


class CategorySidebar(QWidget):
    """Sidebar navigation panel presenting credential categories with arrow and tab navigation.

    Attributes:
        category_selected: Signal emitted when the user selects a category, supplying
            the selected Category enum member or None for all items.
    """

    category_selected = pyqtSignal(object)
    """pyqtSignal(object): Emitted when a category is selected by the user."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        categories: Iterable[Category] | None = None,
    ) -> None:
        """Initializes the category navigation sidebar.

        Args:
            parent: Optional parent QWidget.
            categories: Optional iterable of categories to display. Defaults to all Category enum items.
        """
        super().__init__(parent)
        self._selected_category: Category | None = None
        self._nav_items: list[CategoryNavItem] = []

        self.setMinimumWidth(210)
        self.setMaximumWidth(320)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setProperty("sidebar", "true")

        self._setup_ui()
        self.set_categories(list(Category) if categories is None else categories)
        self.select_category(None, animate=False)

    @property
    def selected_category(self) -> Category | None:
        """Currently selected category.

        Returns:
            Active Category enum member or None if All Items is selected.
        """
        return self._selected_category

    @property
    def item_count(self) -> int:
        """Total number of category navigation items in the sidebar.

        Returns:
            Integer count of navigation items.
        """
        return len(self._nav_items)

    def set_categories(self, categories: Iterable[Category]) -> None:
        """Populates the navigation items with the provided categories.

        Args:
            categories: Iterable sequence of Category enum members.
        """
        for item in self._nav_items:
            self._items_layout.removeWidget(item)
            item.deleteLater()
        self._nav_items.clear()

        all_item = CategoryNavItem(
            title="All Items",
            category=None,
            count=0,
            parent=self._scroll_content,
        )
        all_item.item_clicked.connect(self._on_item_clicked)
        all_item.installEventFilter(self)
        self._nav_items.append(all_item)
        self._items_layout.addWidget(all_item)

        for category in categories:
            item = CategoryNavItem(
                title=category.value,
                category=category,
                count=0,
                parent=self._scroll_content,
            )
            item.item_clicked.connect(self._on_item_clicked)
            item.installEventFilter(self)
            self._nav_items.append(item)
            self._items_layout.addWidget(item)

    def select_category(self, category: Category | None, animate: bool = True) -> None:
        """Sets the active category and updates visual selection states.

        Args:
            category: Target Category enum member or None for all items.
            animate: Whether to animate indicator transition.
        """
        self._selected_category = category
        for item in self._nav_items:
            is_active = item.category == category
            item.set_selected(is_active, animate=animate)

    def update_counts(self, counts: dict[Category | None, int]) -> None:
        """Updates entry count badges across all category navigation items.

        Args:
            counts: Mapping from Category (or None) to entry count integer.
        """
        for item in self._nav_items:
            count = counts.get(item.category, 0)
            item.set_count(count)

    def eventFilter(self, watched: object | None, event: QEvent | None) -> bool:
        """Filters key navigation events from child navigation items.

        Args:
            watched: Watched QObject source.
            event: Event being processed.

        Returns:
            True if event was intercepted and handled, False otherwise.
        """
        if event is not None and event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            if self._handle_key_press(event):
                return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        """Handles keyboard navigation for categories list.

        Args:
            event: Key event instance.
        """
        if event is not None and self._handle_key_press(event):
            return
        super().keyPressEvent(event)

    def _setup_ui(self) -> None:
        """Initializes child layout, header, and scroll area container."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 16, 0, 16)
        main_layout.setSpacing(6)

        header_label = QLabel("CATEGORIES", self)
        header_label.setProperty("variant", "sidebar-header")
        header_label.setContentsMargins(16, 0, 16, 4)
        main_layout.addWidget(header_label)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setProperty("variant", "sidebar-scroll")
        self._scroll_area.installEventFilter(self)

        self._scroll_content = QWidget(self._scroll_area)
        self._scroll_content.installEventFilter(self)
        self._items_layout = QVBoxLayout(self._scroll_content)
        self._items_layout.setContentsMargins(8, 0, 8, 0)
        self._items_layout.setSpacing(3)

        self._scroll_area.setWidget(self._scroll_content)
        main_layout.addWidget(self._scroll_area)

    def _handle_key_press(self, event: QKeyEvent) -> bool:
        """Processes Up/Down/W/S/Home/End/Enter navigation keys to switch categories.

        Args:
            event: Key event instance.

        Returns:
            True if key was recognized and handled, False otherwise.
        """
        key = event.key()

        if key in (Qt.Key.Key_Down, Qt.Key.Key_S):
            self._navigate_relative(1, wrap=False)
            return True
        if key in (Qt.Key.Key_Up, Qt.Key.Key_W):
            self._navigate_relative(-1, wrap=False)
            return True
        if key == Qt.Key.Key_Home:
            self._navigate_to_index(0)
            return True
        if key == Qt.Key.Key_End:
            self._navigate_to_index(len(self._nav_items) - 1)
            return True
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.category_selected.emit(self._selected_category)
            return True

        return False

    def _navigate_relative(self, step: int, wrap: bool) -> None:
        """Navigates relative to the currently active category index.

        Args:
            step: Step offset (+1 for forward/down, -1 for backward/up).
            wrap: Whether to wrap around list bounds.
        """
        if not self._nav_items:
            return

        current_idx = 0
        for idx, item in enumerate(self._nav_items):
            if item.category == self._selected_category:
                current_idx = idx
                break

        if wrap:
            new_idx = (current_idx + step) % len(self._nav_items)
        else:
            new_idx = max(0, min(len(self._nav_items) - 1, current_idx + step))

        self._navigate_to_index(new_idx)

    def _navigate_to_index(self, index: int) -> None:
        """Selects and scrolls to navigation item at given index.

        Args:
            index: Target item index.
        """
        if 0 <= index < len(self._nav_items):
            target_item = self._nav_items[index]
            self.select_category(target_item.category, animate=True)
            self.category_selected.emit(target_item.category)
            self._scroll_area.ensureWidgetVisible(target_item)
            target_item.setFocus()

    def _on_item_clicked(self, category: Category | None) -> None:
        """Handles item selection click, updates state and emits signal.

        Args:
            category: Selected Category enum instance or None.
        """
        if self._selected_category == category:
            return

        self.select_category(category, animate=True)
        self.category_selected.emit(category)


__all__ = [
    "CategorySidebar",
]
