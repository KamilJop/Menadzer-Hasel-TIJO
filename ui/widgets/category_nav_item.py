"""Interactive navigation item widget representing a credential category with animated horizontal expansion."""

from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    QRectF,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QEnterEvent,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from core.category import Category
from ui.resources.colors import NavColors
from ui.utils import interpolate_color

_MAX_EXTENSION_PX: float = 16.0
_CARD_OFFSET_X: float = 4.0
_CARD_OFFSET_Y: float = 2.0
_CARD_CORNER_RADIUS: float = 8.0
_CARD_BORDER_WIDTH: float = 1.2
_ANIMATION_DURATION_MS: int = 180
_MIN_ITEM_HEIGHT: int = 38
_MAX_ITEM_HEIGHT: int = 56
_BADGE_SIZE: int = 22
_BASE_RIGHT_MARGIN: int = 14
_BASE_LEFT_MARGIN: int = 16


class CategoryNavItem(QWidget):
    """Navigation tile with smooth horizontal length interpolation and background illumination.

    Attributes:
        item_clicked: Signal emitted when the item is clicked, supplying the Category or None.
    """

    item_clicked = pyqtSignal(object)
    """pyqtSignal(object): Emitted when this navigation item is clicked."""

    def __init__(
        self,
        title: str,
        category: Category | None = None,
        count: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the navigation item widget.

        Args:
            title: Display label for the navigation item.
            category: Associated Category enum member, or None for all items.
            count: Initial credential entries count.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._category: Category | None = category
        self._title: str = title
        self._count: int = count
        self._selected: bool = False
        self._hovered: bool = False
        self._progress: float = 0.0

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(_MIN_ITEM_HEIGHT)
        self.setMaximumHeight(_MAX_ITEM_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setProperty("navItem", "true")

        self._setup_ui()
        self._setup_animation()

    @pyqtProperty(float)
    def progress(self) -> float:
        """Interpolation progress factor for length expansion and illumination.

        Returns:
            Current progress float value between 0.0 and 1.0.
        """
        return self._progress

    @progress.setter
    def progress(self, value: float) -> None:
        """Sets the interpolation progress factor and triggers repaint.

        Args:
            value: Float progress factor between 0.0 and 1.0.
        """
        self._progress = max(0.0, min(1.0, value))
        self._update_layout_margins()
        self.update()

    @property
    def category(self) -> Category | None:
        """Associated credential category.

        Returns:
            Category enum instance or None for all items.
        """
        return self._category

    @property
    def selected(self) -> bool:
        """Current selection state flag.

        Returns:
            True if the item is currently active, False otherwise.
        """
        return self._selected

    def set_selected(self, selected: bool, animate: bool = True) -> None:
        """Updates the selection state and animates horizontal elongation.

        Args:
            selected: New selection state boolean.
            animate: Whether to animate the transition.
        """
        if self._selected == selected:
            return

        self._selected = selected
        self._update_label_styles()
        target_progress = 1.0 if selected else 0.0

        if animate:
            self._animation.stop()
            self._animation.setStartValue(self._progress)
            self._animation.setEndValue(target_progress)
            self._animation.start()
        else:
            self.progress = target_progress

    def set_count(self, count: int) -> None:
        """Updates the displayed credential count badge.

        Args:
            count: Number of credential entries to display.
        """
        self._count = max(0, count)
        if self._count > 0:
            self._badge_label.setText(str(self._count))
            self._badge_label.setVisible(True)
        else:
            self._badge_label.setText("")
            self._badge_label.setVisible(False)

    def enterEvent(self, event: QEnterEvent | None) -> None:
        """Handles mouse enter event to trigger subtle hover state.

        Args:
            event: Enter event instance.
        """
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent | None) -> None:
        """Handles mouse leave event to clear hover state.

        Args:
            event: Event instance.
        """
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Handles mouse press events to trigger item selection.

        Args:
            event: Mouse event instance.
        """
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            self.item_clicked.emit(self._category)
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Renders the rounded background capsule with dynamic length and interpolated lighting.

        Args:
            event: Paint event instance.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        extension = _MAX_EXTENSION_PX * self._progress
        card_x = _CARD_OFFSET_X
        card_y = _CARD_OFFSET_Y
        card_w = self.width() - (2 * _CARD_OFFSET_X) - _MAX_EXTENSION_PX + extension
        card_h = self.height() - (_CARD_OFFSET_Y * 2)
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        bg_color = interpolate_color(
            NavColors.HOVER_BG if self._hovered and not self._selected else NavColors.BASE_BG,
            NavColors.ACTIVE_BG,
            self._progress,
        )

        border_color = interpolate_color(
            NavColors.HOVER_BORDER if self._hovered and not self._selected else NavColors.BASE_BORDER,
            NavColors.ACTIVE_BORDER,
            self._progress,
        )

        pen = QPen(border_color, _CARD_BORDER_WIDTH)
        painter.setPen(pen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(card_rect, _CARD_CORNER_RADIUS, _CARD_CORNER_RADIUS)

    def _setup_ui(self) -> None:
        """Initializes and lays out child visual widgets."""
        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(8)

        self._title_label = QLabel(self._title, self)
        self._title_label.setProperty("variant", "nav-title")
        self._title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._badge_label = QLabel("", self)
        self._badge_label.setProperty("variant", "nav-badge")
        self._badge_label.setFixedSize(_BADGE_SIZE, _BADGE_SIZE)
        self._badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._badge_label.setVisible(False)

        self._layout.addWidget(self._title_label, stretch=1)
        self._layout.addWidget(self._badge_label)

        self.set_count(self._count)
        self._update_layout_margins()
        self._update_label_styles()

    def _setup_animation(self) -> None:
        """Initializes the horizontal expansion property animation."""
        self._animation = QPropertyAnimation(self, b"progress", self)
        self._animation.setDuration(_ANIMATION_DURATION_MS)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _update_layout_margins(self) -> None:
        """Synchronizes layout horizontal padding with current length expansion."""
        right_margin = int(_BASE_RIGHT_MARGIN + (_MAX_EXTENSION_PX * (1.0 - self._progress)))
        self._layout.setContentsMargins(_BASE_LEFT_MARGIN, 0, right_margin, 0)

    def _update_label_styles(self) -> None:
        """Applies dynamic style property states matching selection state."""
        selected_prop = "true" if self._selected else "false"
        self._title_label.setProperty("selected", selected_prop)
        self._badge_label.setProperty("selected", selected_prop)

        for label in (self._title_label, self._badge_label):
            style = label.style()
            if style is not None:
                style.unpolish(label)
                style.polish(label)


__all__ = [
    "CategoryNavItem",
]
