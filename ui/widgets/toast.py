"""Floating toast notification component displaying transient status messages."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)

_DEFAULT_DISPLAY_DURATION_MS: int = 3500
_ANIMATION_DURATION_MS: int = 220
_SHADOW_BLUR_RADIUS: int = 16
_SHADOW_OFFSET_Y: int = 4
_BOTTOM_OFFSET_PX: int = 32


class ToastNotification(QFrame):
    """Floating pill-style toast notification widget for temporary feedback alerts.

    Adheres to the Single Responsibility Principle (SRP) by managing presentation
    and animation of transient notifications decoupled from application state.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the toast notification frame with layout, effects, and timers.

        Args:
            parent: Optional host QWidget inside which the toast will be centered.
        """
        super().__init__(parent)
        self.setObjectName("toastNotification")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setVisible(False)

        self._icon_label: QLabel
        self._message_label: QLabel
        self._opacity_effect: QGraphicsOpacityEffect
        self._anim: QPropertyAnimation | None = None
        self._hide_timer: QTimer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Constructs layout, label widgets, and styling effects."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 18, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel(self)
        self._icon_label.setFixedSize(16, 16)
        self._icon_label.setScaledContents(True)

        self._message_label = QLabel(self)
        self._message_label.setProperty("variant", "toast-message")

        layout.addWidget(self._icon_label)
        layout.addWidget(self._message_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(_SHADOW_BLUR_RADIUS)
        shadow.setOffset(0, _SHADOW_OFFSET_Y)
        shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(shadow)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)

    def show_message(
        self,
        message: str,
        icon: QIcon | None = None,
        duration_ms: int = _DEFAULT_DISPLAY_DURATION_MS,
    ) -> None:
        """Displays toast message with smooth fade-in and auto-hide timeout.

        Args:
            message: Informational text string to display.
            icon: Optional QIcon to display beside message text.
            duration_ms: Duration in milliseconds before fading out.
        """
        self._message_label.setText(message)

        if icon is not None and not icon.isNull():
            self._icon_label.setPixmap(icon.pixmap(16, 16))
            self._icon_label.setVisible(True)
        else:
            self._icon_label.setVisible(False)

        self.adjustSize()
        self.reposition()

        self._hide_timer.stop()
        self._fade_in()
        self._hide_timer.start(duration_ms)

    def reposition(self) -> None:
        """Recalculates horizontal center and bottom anchor coordinates within parent widget."""
        parent = self.parentWidget()
        if parent is None:
            return

        parent_width = parent.width()
        parent_height = parent.height()
        toast_width = self.width()
        toast_height = self.height()

        target_x = max(10, (parent_width - toast_width) // 2)
        target_y = max(10, parent_height - toast_height - _BOTTOM_OFFSET_PX)
        self.move(target_x, target_y)
        self.raise_()

    def _fade_in(self) -> None:
        """Animates opacity from transparent to fully visible."""
        self.setVisible(True)
        self.setGraphicsEffect(self._opacity_effect)
        if self._anim is not None:
            self._anim.stop()

        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._anim.setDuration(_ANIMATION_DURATION_MS)
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _fade_out(self) -> None:
        """Animates opacity to zero and hides the widget upon completion."""
        if self._anim is not None:
            self._anim.stop()

        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._anim.setDuration(_ANIMATION_DURATION_MS)
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(self._on_fade_out_finished)
        self._anim.start()

    def _on_fade_out_finished(self) -> None:
        """Hides widget after fade-out animation completes."""
        self.setVisible(False)


__all__ = [
    "ToastNotification",
]
