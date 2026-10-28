"""Application bootstrap and entry point for the desktop password manager."""

from __future__ import annotations

import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from ui.resources.style_loader import load_app_stylesheets
from ui.views.main_window import MainWindow


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
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
