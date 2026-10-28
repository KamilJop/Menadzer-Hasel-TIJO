"""Main application dashboard window."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
)


class MainWindow(QMainWindow):
    """Primary application window for password management."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the main application window.

        Args:
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self.setWindowTitle("Password Manager")
        self.resize(900, 600)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Sets up the initial user interface layout."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)


__all__ = [
    "MainWindow",
]
