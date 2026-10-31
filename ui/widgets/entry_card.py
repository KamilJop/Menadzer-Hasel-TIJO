"""Card widget component representing an individual credential entry."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.entry import Entry
from ui.services.favicon_service import FaviconService


class EntryCard(QFrame):
    """Component rendering an individual credential entry card with action controls.

    Adheres to the Single Responsibility Principle (SRP) by encapsulating entry presentation,
    credential masking toggles, and UI-level feedback.

    Attributes:
        copy_requested: Signal emitted when user copies credential text (text, field_name).
        delete_requested: Signal emitted when user requests deleting this credential entry.
    """

    copy_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(Entry)

    def __init__(
        self,
        entry: Entry,
        favicon_service: FaviconService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the entry card widget.

        Args:
            entry: Entry data model to display.
            favicon_service: Optional FaviconService for fetching website logos.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._entry: Entry = entry
        self._favicon_service: FaviconService | None = favicon_service

        icons_dir = Path(__file__).resolve().parent.parent / "resources" / "icons"
        self._copy_icon: QIcon = QIcon(str(icons_dir / "copy.svg"))
        self._check_icon: QIcon = QIcon(str(icons_dir / "check.svg"))
        self._delete_icon: QIcon = QIcon(str(icons_dir / "delete.svg"))
        self._eye_open_icon: QIcon = QIcon(str(icons_dir / "eye_open.svg"))
        self._eye_closed_icon: QIcon = QIcon(str(icons_dir / "eye_closed.svg"))

        self.setObjectName("entryCard")
        self.setProperty("variant", "entry-card")
        self._setup_ui()

    @property
    def entry(self) -> Entry:
        """Credential entry data model displayed by this card.

        Returns:
            The associated Entry instance.
        """
        return self._entry

    def _setup_ui(self) -> None:
        """Constructs layout including header, credentials row, notes, and actions."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(8)

        title_row = self._create_title_row()
        info_col.addLayout(title_row)

        credentials_row = self._create_credentials_row()
        info_col.addLayout(credentials_row)

        if self._entry.notes and self._entry.notes.strip():
            desc_row = self._create_description_row(self._entry.notes.strip())
            info_col.addLayout(desc_row)

        layout.addLayout(info_col, stretch=1)

        actions_col = self._create_actions_column()
        layout.addLayout(actions_col)

    def _create_title_row(self) -> QHBoxLayout:
        """Constructs the header row containing logo, title, and optional URL link.

        Returns:
            Configured QHBoxLayout instance.
        """
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        title_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        logo_label = QLabel(self)
        logo_label.setFixedSize(22, 22)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        initial_char = self._entry.title[:1].upper() if self._entry.title else "?"
        logo_label.setText(initial_char)
        logo_label.setProperty("variant", "entry-logo")

        if self._entry.url and self._favicon_service is not None:
            cached_pixmap = self._favicon_service.get_cached(self._entry.url)
            if cached_pixmap is not None:
                self._apply_favicon_to_label(logo_label, cached_pixmap)
            else:
                self._favicon_service.fetch_favicon(
                    self._entry.url,
                    lambda domain, px, lbl=logo_label: self._apply_favicon_to_label(lbl, px),
                )

        title_label = QLabel(self._entry.title, self)
        title_label.setProperty("variant", "entry-title")

        title_row.addWidget(logo_label)
        title_row.addWidget(title_label)

        if self._entry.url and self._entry.url.strip():
            raw_url = self._entry.url.strip()
            href = raw_url if raw_url.startswith(("http://", "https://")) else f"https://{raw_url}"
            separator_label = QLabel("/", self)
            separator_label.setProperty("variant", "entry-separator")

            url_label = QLabel(
                f'<a href="{href}" style="color: #818cf8; text-decoration: none;">{raw_url}</a>',
                self,
            )
            url_label.setOpenExternalLinks(True)
            url_label.setTextFormat(Qt.TextFormat.RichText)
            url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            url_label.setCursor(Qt.CursorShape.PointingHandCursor)
            url_label.setProperty("variant", "entry-url")

            title_row.addWidget(separator_label)
            title_row.addWidget(url_label)

        title_row.addStretch()
        return title_row

    def _create_credentials_row(self) -> QHBoxLayout:
        """Constructs the row displaying login and password inputs with action buttons.

        Returns:
            Configured QHBoxLayout instance.
        """
        credentials_row = QHBoxLayout()
        credentials_row.setContentsMargins(0, 0, 0, 0)
        credentials_row.setSpacing(14)
        credentials_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        login_group = self._create_credential_field_group(
            tag="Login:",
            value=self._entry.username,
            field_name="Login",
            on_reveal=lambda widget, btn, u=self._entry.username: self._toggle_login_visibility(widget, btn, u),
            on_copy=lambda btn, u=self._entry.username: self._on_copy_clicked(btn, u, "Login"),
        )
        credentials_row.addLayout(login_group, stretch=1)

        password_group = self._create_credential_field_group(
            tag="Password:",
            value=self._entry.password,
            field_name="Password",
            on_reveal=lambda widget, btn, p=self._entry.password: self._toggle_password_visibility(widget, btn, p),
            on_copy=lambda btn, p=self._entry.password: self._on_copy_clicked(btn, p, "Password"),
        )
        credentials_row.addLayout(password_group, stretch=1)

        return credentials_row

    def _create_description_row(self, notes_text: str) -> QHBoxLayout:
        """Constructs the description row containing category tag and notes text.

        Args:
            notes_text: Sanitized notes text to display.

        Returns:
            Configured QHBoxLayout instance.
        """
        desc_row = QHBoxLayout()
        desc_row.setContentsMargins(0, 0, 0, 0)
        desc_row.setSpacing(6)
        desc_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        desc_tag = QLabel("Description:", self)
        desc_tag.setProperty("variant", "cred-tag")

        desc_label = QLabel(notes_text, self)
        desc_label.setWordWrap(True)
        desc_label.setProperty("variant", "entry-notes")

        desc_row.addWidget(desc_tag)
        desc_row.addWidget(desc_label, stretch=1)
        return desc_row

    def _create_credential_field_group(
        self,
        tag: str,
        value: str,
        field_name: str,
        on_reveal: Callable[[QLineEdit, QPushButton], None],
        on_copy: Callable[[QPushButton], None],
    ) -> QHBoxLayout:
        """Constructs an individual credential input group with reveal and copy buttons.

        Args:
            tag: Text label identifying the field (e.g. 'Login:' or 'Password:').
            value: Credential value to populate.
            field_name: Descriptive name for tooltips.
            on_reveal: Callback slot triggered on visibility toggle.
            on_copy: Callback slot triggered on clipboard copy.

        Returns:
            Configured QHBoxLayout instance.
        """
        group = QHBoxLayout()
        group.setContentsMargins(0, 0, 0, 0)
        group.setSpacing(6)
        group.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        tag_label = QLabel(tag, self)
        tag_label.setProperty("variant", "cred-tag")

        input_field = QLineEdit(value, self)
        input_field.setReadOnly(True)
        input_field.setEchoMode(QLineEdit.EchoMode.Password)
        input_field.setFixedHeight(28)
        input_field.setProperty("variant", "credential-input")

        reveal_button = QPushButton(self)
        reveal_button.setProperty("variant", "icon-btn")
        reveal_button.setFixedSize(28, 28)
        reveal_button.setIcon(self._eye_closed_icon)
        reveal_button.setIconSize(QSize(13, 13))
        reveal_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reveal_button.setToolTip(f"Show {field_name}")
        reveal_button.clicked.connect(lambda: on_reveal(input_field, reveal_button))

        copy_button = QPushButton(self)
        copy_button.setProperty("variant", "icon-btn")
        copy_button.setFixedSize(28, 28)
        copy_button.setIcon(self._copy_icon)
        copy_button.setIconSize(QSize(13, 13))
        copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_button.setToolTip(f"Copy {field_name}")
        copy_button.clicked.connect(lambda: on_copy(copy_button))

        group.addWidget(tag_label)
        group.addWidget(input_field, stretch=1)
        group.addWidget(reveal_button)
        group.addWidget(copy_button)
        return group

    def _create_actions_column(self) -> QVBoxLayout:
        """Constructs the actions column containing the delete button.

        Returns:
            Configured QVBoxLayout instance.
        """
        actions_col = QVBoxLayout()
        actions_col.setContentsMargins(0, 0, 0, 0)
        actions_col.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        delete_button = QPushButton(self)
        delete_button.setProperty("variant", "icon-btn-danger")
        delete_button.setFixedSize(26, 26)
        delete_button.setIcon(self._delete_icon)
        delete_button.setIconSize(QSize(13, 13))
        delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_button.setToolTip("Delete Password")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self._entry))

        actions_col.addWidget(delete_button)
        return actions_col

    @classmethod
    def get_eye_icons(cls) -> tuple[QIcon, QIcon]:
        """Resolves eye open and eye closed icons for visibility toggling.

        Returns:
            Tuple of (eye_open_icon, eye_closed_icon).
        """
        icons_dir = Path(__file__).resolve().parent.parent / "resources" / "icons"
        return QIcon(str(icons_dir / "eye_open.svg")), QIcon(str(icons_dir / "eye_closed.svg"))

    @classmethod
    def toggle_masked_widget_visibility(
        cls,
        widget: QLabel | QLineEdit,
        button: QPushButton,
        plaintext: str,
        field_name: str,
    ) -> None:
        """Toggles masking between hidden and plaintext representation for a label or line edit.

        Args:
            widget: Target QLabel or QLineEdit displaying the credential text.
            button: QPushButton triggering the reveal action.
            plaintext: Plaintext credential value.
            field_name: Descriptive name of the field (e.g. 'Login' or 'Password').
        """
        eye_open, eye_closed = cls.get_eye_icons()
        if isinstance(widget, QLineEdit):
            is_masked = widget.echoMode() == QLineEdit.EchoMode.Password
            new_mode = QLineEdit.EchoMode.Normal if is_masked else QLineEdit.EchoMode.Password
            widget.setEchoMode(new_mode)
            button.setIcon(eye_open if is_masked else eye_closed)
            button.setToolTip(f"Hide {field_name}" if is_masked else f"Show {field_name}")
        else:
            is_masked = widget.text() == "••••••••"
            widget.setText(plaintext if is_masked else "••••••••")
            button.setIcon(eye_open if is_masked else eye_closed)
            button.setToolTip(f"Hide {field_name}" if is_masked else f"Show {field_name}")

    def _toggle_login_visibility(
        self,
        widget: QLabel | QLineEdit,
        button: QPushButton,
        username: str,
    ) -> None:
        """Toggles masking between hidden and plaintext username.

        Args:
            widget: Target QLabel or QLineEdit displaying the username text.
            button: QPushButton triggering the reveal action.
            username: Actual plaintext username string.
        """
        self.toggle_masked_widget_visibility(widget, button, username, "Login")

    def _toggle_password_visibility(
        self,
        widget: QLabel | QLineEdit,
        button: QPushButton,
        password: str,
    ) -> None:
        """Toggles masking between hidden and plaintext password.

        Args:
            widget: Target QLabel or QLineEdit displaying the password text.
            button: QPushButton triggering the reveal action.
            password: Actual plaintext password string.
        """
        self.toggle_masked_widget_visibility(widget, button, password, "Password")

    def _on_copy_clicked(self, button: QPushButton, text: str, field_name: str) -> None:
        """Updates copy button with temporary feedback and signals copy request.

        Args:
            button: QPushButton triggering the copy to visually update.
            text: Credential string value to copy.
            field_name: Descriptive name of credential field.
        """
        button.setIcon(self._check_icon)
        button.setToolTip("Copied!")
        QTimer.singleShot(1600, lambda: self._reset_copy_button(button, f"Copy {field_name}"))
        self.copy_requested.emit(text, field_name)

    def _reset_copy_button(self, button: QPushButton, tooltip: str = "Copy") -> None:
        """Restores default copy icon and tooltip on the copy button.

        Args:
            button: QPushButton to reset.
            tooltip: Tooltip to restore on the button.
        """
        button.setIcon(self._copy_icon)
        button.setToolTip(tooltip)

    def _apply_favicon_to_label(self, label: QLabel, pixmap: QPixmap) -> None:
        """Sets scaled favicon icon on target logo label with transparent background styling.

        Args:
            label: Target QLabel component.
            pixmap: Downloaded or cached favicon QPixmap.
        """
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                20,
                20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            label.setProperty("variant", "entry-logo-pixmap")
            label.style().unpolish(label)
            label.style().polish(label)
            label.setText("")
            label.setPixmap(scaled)


__all__ = [
    "EntryCard",
]
