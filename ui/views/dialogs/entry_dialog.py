"""Modal dialog for creating and editing credential entries."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.category import Category
from core.entry import Entry
from core.generator import PasswordGenerator
from core.validator import PasswordValidator
from ui.widgets import CustomLineEdit, PasswordField, StrengthBar


class EntryDialog(QDialog):
    """Modal dialog allowing users to create or edit credential entries.

    Configured as an application-modal dialog parented to MainWindow or another QWidget.
    Supports real-time password strength evaluation, integrated generator shortcut,
    and credential validation.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        initial_category: Category | None = None,
        entry: Entry | None = None,
        validator: PasswordValidator | None = None,
        generator: PasswordGenerator | None = None,
    ) -> None:
        """Initializes the credential entry dialog.

        Args:
            parent: Parent QWidget (typically MainWindow).
            initial_category: Optional initial Category to select in the dropdown.
            entry: Optional existing Entry to populate fields for editing mode.
            validator: Optional PasswordValidator instance for strength evaluation.
            generator: Optional PasswordGenerator instance for password generation.
        """
        super().__init__(parent)
        self._existing_entry: Entry | None = entry
        self._entry_result: Entry | None = entry
        self._initial_category: Category | None = initial_category
        self._generator: PasswordGenerator = generator or PasswordGenerator()
        self._validator: PasswordValidator = (
            validator if validator is not None else PasswordValidator.create_default()
        )

        self.setWindowTitle("Edit Password" if entry else "Add New Password")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.resize(520, 620)

        self._setup_ui()
        self._populate_initial_data()

    def _setup_ui(self) -> None:
        """Constructs and arranges dialog layout, inputs, and action buttons."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(14)

        self._setup_header(main_layout)
        self._setup_input_fields(main_layout)
        self._setup_password_section(main_layout)
        self._setup_category_section(main_layout)
        self._setup_optional_fields(main_layout)
        self._setup_error_label(main_layout)
        self._setup_action_buttons(main_layout)

    def _setup_header(self, layout: QVBoxLayout) -> None:
        """Configures the title and informational subtitle for the dialog.

        Args:
            layout: Target vertical layout to attach header widgets.
        """
        header_title = QLabel(
            "Edit Credential" if self._existing_entry else "Add New Password",
            self,
        )
        header_title.setProperty("variant", "dialog-title")

        header_subtitle = QLabel(
            "Store your credentials securely with authenticated local encryption.",
            self,
        )
        header_subtitle.setProperty("variant", "muted")

        layout.addWidget(header_title)
        layout.addWidget(header_subtitle)
        layout.addSpacing(6)

    def _setup_input_fields(self, layout: QVBoxLayout) -> None:
        """Configures title and username input controls.

        Args:
            layout: Target vertical layout to attach input widgets.
        """
        title_label = QLabel("Title *", self)
        self._title_input = CustomLineEdit(
            placeholder="e.g. GitHub, Google, Bank Account",
            parent=self,
        )
        layout.addWidget(title_label)
        layout.addWidget(self._title_input)

        username_label = QLabel("Username or Email *", self)
        self._username_input = CustomLineEdit(
            placeholder="e.g. user@example.com",
            parent=self,
        )
        layout.addWidget(username_label)
        layout.addWidget(self._username_input)

    def _setup_password_section(self, layout: QVBoxLayout) -> None:
        """Configures password input, generator button, and real-time strength meter.

        Args:
            layout: Target vertical layout to attach password components.
        """
        password_label = QLabel("Password *", self)
        password_row = QHBoxLayout()
        password_row.setContentsMargins(0, 0, 0, 0)
        password_row.setSpacing(8)

        self._password_input = PasswordField(
            placeholder="Enter secure password",
            parent=self,
        )
        self._generate_button = QPushButton("Generate", self)
        self._generate_button.setProperty("variant", "secondary")
        self._generate_button.setToolTip("Generate strong random password")
        self._generate_button.clicked.connect(self._on_generate_clicked)

        password_row.addWidget(self._password_input, stretch=1)
        password_row.addWidget(self._generate_button)

        layout.addWidget(password_label)
        layout.addLayout(password_row)

        self._strength_bar = StrengthBar(parent=self)
        self._password_input.textChanged.connect(self._on_password_changed)
        layout.addWidget(self._strength_bar)

    def _setup_category_section(self, layout: QVBoxLayout) -> None:
        """Configures category dropdown selection control.

        Args:
            layout: Target vertical layout to attach category widgets.
        """
        category_label = QLabel("Category", self)
        self._category_combobox = QComboBox(self)
        for cat in Category:
            self._category_combobox.addItem(cat.value, userData=cat)
        layout.addWidget(category_label)
        layout.addWidget(self._category_combobox)

    def _setup_optional_fields(self, layout: QVBoxLayout) -> None:
        """Configures optional website URL and description note inputs.

        Args:
            layout: Target vertical layout to attach optional inputs.
        """
        url_label = QLabel("Website URL (Optional)", self)
        self._url_input = CustomLineEdit(
            placeholder="https://example.com",
            parent=self,
        )
        layout.addWidget(url_label)
        layout.addWidget(self._url_input)

        notes_label = QLabel("Description / Notes (Optional)", self)
        self._notes_input = QPlainTextEdit(self)
        self._notes_input.setPlaceholderText("Additional description, recovery codes, or notes...")
        self._notes_input.setFixedHeight(72)
        layout.addWidget(notes_label)
        layout.addWidget(self._notes_input)

    def _setup_error_label(self, layout: QVBoxLayout) -> None:
        """Configures dynamic error message label banner.

        Args:
            layout: Target vertical layout to attach the error label.
        """
        self._error_label = QLabel("", self)
        self._error_label.setProperty("variant", "error")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)
        layout.addSpacing(6)

    def _setup_action_buttons(self, layout: QVBoxLayout) -> None:
        """Configures dialog action buttons for cancel and save operations.

        Args:
            layout: Target vertical layout to attach action button layout.
        """
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setProperty("variant", "minimal")
        self._cancel_button.clicked.connect(self.reject)

        self._save_button = QPushButton("Save Password", self)
        self._save_button.clicked.connect(self._on_save_clicked)

        actions_layout.addStretch()
        actions_layout.addWidget(self._cancel_button)
        actions_layout.addWidget(self._save_button)

        layout.addLayout(actions_layout)

    def _populate_initial_data(self) -> None:
        """Populates form controls with existing entry data or default selections."""
        if self._existing_entry is not None:
            self._populate_from_entry(self._existing_entry)
        else:
            self._select_default_category(self._initial_category)

    def _populate_from_entry(self, entry: Entry) -> None:
        """Populates input controls with values from an existing entry.

        Args:
            entry: Existing Entry instance whose attributes are displayed in the form.
        """
        self._title_input.setText(entry.title)
        self._username_input.setText(entry.username)
        self._password_input.setText(entry.password)
        self._strength_bar.set_result(self._validator.validate(entry.password))

        self._select_default_category(entry.category)

        if entry.url:
            self._url_input.setText(entry.url)
        if entry.notes:
            self._notes_input.setPlainText(entry.notes)

    def _select_default_category(self, target_category: Category | None) -> None:
        """Selects the specified category in the dropdown or defaults to Category.OTHER.

        Args:
            target_category: Category enum to select if present, or None.
        """
        category_to_select = target_category if target_category is not None else Category.OTHER
        index = self._category_combobox.findData(category_to_select)
        if index >= 0:
            self._category_combobox.setCurrentIndex(index)

    def _on_password_changed(self, text: str) -> None:
        """Internal slot evaluating password strength on text modification.

        Args:
            text: Current password text entered in the password field.
        """
        if not text:
            self._strength_bar.clear()
            return
        result = self._validator.validate(text)
        self._strength_bar.set_result(result)

    def _on_generate_clicked(self) -> None:
        """Slot generating and inserting a cryptographically secure random password."""
        try:
            generated = self._generator.generate()
            self._password_input.setText(generated)
            if not self._password_input.is_password_visible():
                self._password_input.toggle_password_visibility()
            self._clear_error()
        except Exception as err:
            self._show_error(f"Failed to generate password: {err}")

    def _validate_inputs(self) -> bool:
        """Validates mandatory input fields and sets visual error state on invalid fields.

        Returns:
            True if all required fields are populated, False otherwise.
        """
        title = self._title_input.text().strip()
        username = self._username_input.text().strip()
        password = self._password_input.text()

        if not title:
            self._show_error("Title is required.")
            self._title_input.set_error(True)
            self._title_input.setFocus()
            return False

        if not username:
            self._show_error("Username or email is required.")
            self._username_input.set_error(True)
            self._username_input.setFocus()
            return False

        if not password:
            self._show_error("Password is required.")
            self._password_input.set_error(True)
            self._password_input.setFocus()
            return False

        return True

    def _build_or_update_entry(self) -> Entry:
        """Constructs a new Entry or updates the existing entry from form inputs.

        Returns:
            Constructed or updated Entry instance.
        """
        title = self._title_input.text().strip()
        username = self._username_input.text().strip()
        password = self._password_input.text()

        selected_category_data = self._category_combobox.currentData()
        category = (
            selected_category_data
            if isinstance(selected_category_data, Category)
            else Category.OTHER
        )

        url_raw = self._url_input.text().strip()
        url = url_raw if url_raw else None

        notes_raw = self._notes_input.toPlainText().strip()
        notes = notes_raw if notes_raw else None

        if self._existing_entry is not None:
            self._existing_entry.title = title
            self._existing_entry.username = username
            self._existing_entry.password = password
            self._existing_entry.category = category
            self._existing_entry.url = url
            self._existing_entry.notes = notes
            self._existing_entry.mark_updated()
            return self._existing_entry

        return Entry(
            title=title,
            username=username,
            password=password,
            category=category,
            url=url,
            notes=notes,
        )

    def _on_save_clicked(self) -> None:
        """Validates all form fields and commits the entry creation or modification."""
        if not self._validate_inputs():
            return

        self._entry_result = self._build_or_update_entry()
        self.accept()

    def get_entry(self) -> Entry | None:
        """Returns the resulting Entry instance created or modified by this dialog.

        Returns:
            Constructed or updated Entry if saved, None if cancelled.
        """
        return self._entry_result

    def _show_error(self, message: str) -> None:
        """Displays error feedback message.

        Args:
            message: Error text message to display.
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _clear_error(self) -> None:
        """Clears and hides error feedback message."""
        self._error_label.setText("")
        self._error_label.setVisible(False)


__all__ = [
    "EntryDialog",
]
