"""Floating Action Button (FAB) component with smooth hover elevation and centered icon."""

from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QColor,
    QEnterEvent,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QPushButton,
    QWidget,
)

_BUTTON_SIZE: int = 56
_CORNER_RADIUS: float = 14.0
_BORDER_WIDTH: float = 1.2
_PLUS_ARM_LENGTH: float = 9.0
_PLUS_STROKE_WIDTH: float = 2.6
_MAX_ELEVATION_PX: float = 4.0
_ANIMATION_DURATION_MS: int = 150

_SHADOW_BASE_BLUR_RADIUS: int = 12
_SHADOW_BASE_OFFSET_Y: int = 3
_SHADOW_COLOR: QColor = QColor(0, 0, 0, 140)

_BG_DEFAULT: QColor = QColor(79, 70, 229)
_BG_HOVER: QColor = QColor(99, 102, 241)
_BG_PRESSED: QColor = QColor(67, 56, 202)

_BORDER_DEFAULT: QColor = QColor(99, 102, 241)
_BORDER_HOVER: QColor = QColor(129, 140, 248)

_PLUS_COLOR: QColor = QColor(255, 255, 255)


class FloatingActionButton(QPushButton):
    """Floating square action button with rounded corners, centered cross, and hover elevation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the floating action button with geometry, shadow, and animations.

        Args:
            parent: Optional parent widget hosting the floating button.
        """
        super().__init__(parent)
        self.setText("+")
        self.setFixedSize(_BUTTON_SIZE, _BUTTON_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Add New Password")

        self._base_x: int = 0
        self._base_y: int = 0
        self._elevation: float = 0.0
        self._hovered: bool = False
        self._pressed: bool = False
        self._shadow: QGraphicsDropShadowEffect | None = None
        self._anim: QPropertyAnimation | None = None

        self._setup_shadow()
        self._setup_animation()

    @pyqtProperty(float)
    def elevation(self) -> float:
        """Current upward translation distance in pixels.

        Returns:
            Float vertical shift between 0.0 and _MAX_ELEVATION_PX.
        """
        return self._elevation

    @elevation.setter
    def elevation(self, value: float) -> None:
        """Sets vertical translation shift and updates physical widget position.

        Args:
            value: Float elevation distance in pixels.
        """
        self._elevation = max(0.0, min(_MAX_ELEVATION_PX, value))
        self.move(self._base_x, int(self._base_y - self._elevation))
        if self._shadow is not None:
            self._shadow.setBlurRadius(_SHADOW_BASE_BLUR_RADIUS + int(self._elevation * 2))
            self._shadow.setOffset(0, _SHADOW_BASE_OFFSET_Y + int(self._elevation))
        self.update()

    def set_base_pos(self, x: int, y: int) -> None:
        """Updates the resting anchor position coordinates of the floating button.

        Args:
            x: Target horizontal pixel coordinate.
            y: Target vertical pixel coordinate.
        """
        self._base_x = x
        self._base_y = y
        self.move(self._base_x, int(self._base_y - self._elevation))

    def _setup_shadow(self) -> None:
        """Configures and attaches drop shadow graphic effect."""
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(_SHADOW_BASE_BLUR_RADIUS)
        self._shadow.setColor(_SHADOW_COLOR)
        self._shadow.setOffset(0, _SHADOW_BASE_OFFSET_Y)
        self.setGraphicsEffect(self._shadow)

    def _setup_animation(self) -> None:
        """Initializes easing elevation property animation."""
        self._anim = QPropertyAnimation(self, b"elevation")
        self._anim.setDuration(_ANIMATION_DURATION_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _animate_elevation(self, target_elevation: float) -> None:
        """Transitions elevation toward the specified target value.

        Args:
            target_elevation: Target elevation offset in pixels.
        """
        if self._anim is None:
            return
        self._anim.stop()
        self._anim.setStartValue(self._elevation)
        self._anim.setEndValue(target_elevation)
        self._anim.start()

    def enterEvent(self, event: QEnterEvent | None) -> None:
        """Smoothly translates button upward when hovered.

        Args:
            event: Enter event instance.
        """
        self._hovered = True
        self._animate_elevation(_MAX_ELEVATION_PX)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent | None) -> None:
        """Restores button downward to baseline anchor position.

        Args:
            event: Event instance.
        """
        self._hovered = False
        self._animate_elevation(0.0)
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Handles mouse press state for the left mouse button.

        Args:
            event: Mouse event instance.
        """
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        """Handles mouse release state.

        Args:
            event: Mouse event instance.
        """
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def _resolve_palette(self) -> tuple[QColor, QColor]:
        """Resolves background and border colors based on current interaction state.

        Returns:
            Tuple containing the background QColor and border QColor.
        """
        if self._pressed:
            return _BG_PRESSED, _BORDER_DEFAULT
        if self._hovered:
            return _BG_HOVER, _BORDER_HOVER
        return _BG_DEFAULT, _BORDER_DEFAULT

    def _draw_background(self, painter: QPainter) -> None:
        """Renders rounded rectangular button body and outline.

        Args:
            painter: Active anti-aliased QPainter instance.
        """
        bg_color, border_color = self._resolve_palette()
        card_rect = QRectF(1.0, 1.0, float(self.width() - 2), float(self.height() - 2))
        painter.setPen(QPen(border_color, _BORDER_WIDTH))
        painter.setBrush(bg_color)
        painter.drawRoundedRect(card_rect, _CORNER_RADIUS, _CORNER_RADIUS)

    def _draw_plus_icon(self, painter: QPainter) -> None:
        """Renders mathematically centered plus icon with round caps.

        Args:
            painter: Active anti-aliased QPainter instance.
        """
        center_x = float(self.width()) / 2.0
        center_y = float(self.height()) / 2.0

        plus_pen = QPen(
            _PLUS_COLOR,
            _PLUS_STROKE_WIDTH,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(plus_pen)

        painter.drawLine(
            QPointF(center_x - _PLUS_ARM_LENGTH, center_y),
            QPointF(center_x + _PLUS_ARM_LENGTH, center_y),
        )
        painter.drawLine(
            QPointF(center_x, center_y - _PLUS_ARM_LENGTH),
            QPointF(center_x, center_y + _PLUS_ARM_LENGTH),
        )

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Renders rounded background and centered icon.

        Args:
            event: Paint event instance.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_background(painter)
        self._draw_plus_icon(painter)


__all__ = [
    "FloatingActionButton",
]
