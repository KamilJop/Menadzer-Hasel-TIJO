"""Service managing system clipboard interactions and timed auto-clearing for secrets."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

_DEFAULT_CLIPBOARD_AUTO_CLEAR_DELAY_MS: int = 30_000


class ClipboardService(QObject):
    """Coordinates system clipboard copies and scheduled clearing of sensitive credentials.

    Adheres to the Single Responsibility Principle (SRP) by managing clipboard state
    and security timeouts decoupled from UI views.

    Attributes:
        text_copied: Signal emitted when text is copied to clipboard, providing the copied string.
        clipboard_cleared: Signal emitted when the sensitive text is wiped from clipboard.
    """

    text_copied = pyqtSignal(str)
    clipboard_cleared = pyqtSignal()

    def __init__(
        self,
        parent: QObject | None = None,
        auto_clear_delay_ms: int = _DEFAULT_CLIPBOARD_AUTO_CLEAR_DELAY_MS,
        clipboard_provider: Callable[[], object | None] | None = None,
    ) -> None:
        """Initializes clipboard manager service with timer and optional dependencies.

        Args:
            parent: Optional parent QObject for Qt lifecycle management.
            auto_clear_delay_ms: Duration in milliseconds before clearing sensitive contents.
            clipboard_provider: Optional factory returning a QClipboard-compatible object.
        """
        super().__init__(parent)
        self._auto_clear_delay_ms: int = auto_clear_delay_ms
        self._clipboard_provider: Callable[[], object | None] = (
            clipboard_provider if clipboard_provider is not None else QApplication.clipboard
        )
        self._pending_secret: str | None = None
        self._wipe_timer: QTimer = QTimer(self)
        self._wipe_timer.setSingleShot(True)
        self._wipe_timer.timeout.connect(self._on_wipe_timeout)

    @property
    def pending_secret(self) -> str | None:
        """Current secret string pending automatic wipe from clipboard.

        Returns:
            Sensitive string pending wipe, or None if no wipe is scheduled.
        """
        return self._pending_secret

    @pending_secret.setter
    def pending_secret(self, value: str | None) -> None:
        """Sets the pending secret string for clipboard wiping.

        Args:
            value: Secret string to track or None to clear.
        """
        self._pending_secret = value

    @property
    def auto_clear_delay_ms(self) -> int:
        """Configured timeout duration in milliseconds before clearing clipboard.

        Returns:
            Integer millisecond delay.
        """
        return self._auto_clear_delay_ms

    def copy_text(self, text: str, auto_clear: bool = True) -> bool:
        """Copies secret text to system clipboard and schedules automatic wipe.

        Args:
            text: Plaintext string to copy into system clipboard.
            auto_clear: Whether to schedule automatic wipe after the timeout.

        Returns:
            True if clipboard was available and text was copied, False otherwise.
        """
        clipboard = self._clipboard_provider()
        if clipboard is None:
            return False

        clipboard.setText(text)
        self.text_copied.emit(text)

        if auto_clear:
            self._pending_secret = text
            self._wipe_timer.stop()
            self._wipe_timer.start(self._auto_clear_delay_ms)
        return True

    def clear_if_matches(self) -> bool:
        """Immediately clears clipboard if it still contains the pending secret.

        Returns:
            True if clipboard was cleared, False otherwise.
        """
        return self._on_wipe_timeout()

    def _on_wipe_timeout(self) -> bool:
        """Slot triggered on wipe timer expiry to clear clipboard if text matches.

        Returns:
            True if clipboard text matched and was cleared, False otherwise.
        """
        clipboard = self._clipboard_provider()
        cleared = False
        if clipboard is not None and self._pending_secret is not None:
            if clipboard.text() == self._pending_secret:
                clipboard.clear()
                cleared = True
                self.clipboard_cleared.emit()
        self._pending_secret = None
        return cleared


__all__ = [
    "ClipboardService",
]
