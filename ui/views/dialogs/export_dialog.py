"""Modal dialogs for exporting and importing vault credential entries."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.entry import Entry
from core.exceptions import (
    InvalidPasswordError,
    VaultImportError,
)
from storage.encrypted_json_exporter import EncryptedJsonExporter
from storage.encrypted_json_importer import EncryptedJsonImporter
from storage.interfaces import BaseVaultExporter, BaseVaultImporter
from storage.plaintext_json_exporter import PlaintextJsonExporter
from storage.plaintext_json_importer import PlaintextJsonImporter
from ui.widgets import CustomLineEdit, PasswordField


class ExportDialog(QDialog):
    """Modal dialog allowing users to export credentials to encrypted or plaintext JSON."""

    def __init__(
        self,
        entries: Sequence[Entry],
        parent: QWidget | None = None,
        encrypted_exporter: BaseVaultExporter | None = None,
        plaintext_exporter: BaseVaultExporter | None = None,
    ) -> None:
        """Initializes the export credentials dialog.

        Args:
            entries: Sequence of Entry models to export.
            parent: Optional parent QWidget.
            encrypted_exporter: Optional custom encrypted exporter implementation.
            plaintext_exporter: Optional custom plaintext exporter implementation.
        """
        super().__init__(parent)
        self._entries: Sequence[Entry] = entries
        self._encrypted_exporter: BaseVaultExporter = (
            encrypted_exporter if encrypted_exporter is not None else EncryptedJsonExporter()
        )
        self._plaintext_exporter: BaseVaultExporter = (
            plaintext_exporter if plaintext_exporter is not None else PlaintextJsonExporter()
        )
        self._saved_path: Path | None = None

        self.setWindowTitle("Export Passwords")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.resize(520, 480)

        self._setup_ui()

    @property
    def saved_path(self) -> Path | None:
        """Resolved file path of the successfully exported file.

        Returns:
            Path instance if export succeeded, None otherwise.
        """
        return self._saved_path

    def _setup_ui(self) -> None:
        """Constructs and arranges dialog layout, inputs, and action buttons."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(14)

        self._setup_header(main_layout)
        self._setup_format_section(main_layout)
        self._setup_password_section(main_layout)
        self._setup_warning_section(main_layout)
        self._setup_destination_section(main_layout)
        self._setup_error_label(main_layout)
        self._setup_action_buttons(main_layout)

    def _setup_header(self, layout: QVBoxLayout) -> None:
        """Configures the title and informational subtitle for the dialog.

        Args:
            layout: Target vertical layout to attach header widgets.
        """
        header_title = QLabel("Export Passwords", self)
        header_title.setProperty("variant", "dialog-title")

        header_subtitle = QLabel("Backup your passwords to a JSON file.", self)
        header_subtitle.setProperty("variant", "muted")

        layout.addWidget(header_title)
        layout.addWidget(header_subtitle)
        layout.addSpacing(6)

    def _setup_format_section(self, layout: QVBoxLayout) -> None:
        """Configures the radio button group for format selection.

        Args:
            layout: Target vertical layout to attach format widgets.
        """
        format_label = QLabel("Export Format *", self)
        layout.addWidget(format_label)

        self._radio_encrypted = QRadioButton("Encrypted Backup (.json) - Recommended", self)
        self._radio_encrypted.setChecked(True)
        self._radio_plaintext = QRadioButton("Plaintext JSON (.json) - Unencrypted", self)

        self._format_group = QButtonGroup(self)
        self._format_group.addButton(self._radio_encrypted)
        self._format_group.addButton(self._radio_plaintext)
        self._format_group.buttonClicked.connect(self._on_format_changed)

        layout.addWidget(self._radio_encrypted)
        layout.addWidget(self._radio_plaintext)
        layout.addSpacing(4)

    def _setup_password_section(self, layout: QVBoxLayout) -> None:
        """Configures password and password confirmation inputs for encrypted export.

        Args:
            layout: Target vertical layout to attach password container.
        """
        self._password_container = QWidget(self)
        pwd_layout = QVBoxLayout(self._password_container)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(10)

        pwd_label = QLabel("Export Password *", self._password_container)
        self._password_input = PasswordField(placeholder="Choose export password", parent=self._password_container)

        confirm_label = QLabel("Confirm Password *", self._password_container)
        self._confirm_input = PasswordField(placeholder="Repeat export password", parent=self._password_container)

        pwd_layout.addWidget(pwd_label)
        pwd_layout.addWidget(self._password_input)
        pwd_layout.addWidget(confirm_label)
        pwd_layout.addWidget(self._confirm_input)

        layout.addWidget(self._password_container)

    def _setup_warning_section(self, layout: QVBoxLayout) -> None:
        """Configures security notification box displayed during unencrypted export.

        Args:
            layout: Target vertical layout to attach warning frame.
        """
        self._warning_frame = QFrame(self)
        self._warning_frame.setProperty("variant", "warning-card")
        warning_layout = QVBoxLayout(self._warning_frame)
        warning_layout.setContentsMargins(12, 12, 12, 12)

        warning_label = QLabel(
            "Passwords will be saved unencrypted. Anyone with access to this file can read them.",
            self._warning_frame,
        )
        warning_label.setWordWrap(True)
        warning_label.setProperty("variant", "warning")

        warning_layout.addWidget(warning_label)
        self._warning_frame.setVisible(False)
        layout.addWidget(self._warning_frame)

    def _setup_destination_section(self, layout: QVBoxLayout) -> None:
        """Configures file destination input and file browser picker button.

        Args:
            layout: Target vertical layout to attach destination row.
        """
        dest_label = QLabel("Destination File *", self)
        layout.addWidget(dest_label)

        dest_row = QHBoxLayout()
        dest_row.setContentsMargins(0, 0, 0, 0)
        dest_row.setSpacing(8)

        self._dest_input = CustomLineEdit(placeholder="Select destination path...", parent=self)
        self._dest_input.setReadOnly(True)

        self._browse_button = QPushButton("Browse...", self)
        self._browse_button.setProperty("variant", "secondary")
        self._browse_button.clicked.connect(self._on_browse_clicked)

        dest_row.addWidget(self._dest_input, stretch=1)
        dest_row.addWidget(self._browse_button)
        layout.addLayout(dest_row)

    def _setup_error_label(self, layout: QVBoxLayout) -> None:
        """Configures the validation error message label.

        Args:
            layout: Target vertical layout to attach error label.
        """
        self._error_label = QLabel("", self)
        self._error_label.setProperty("variant", "error")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)
        layout.addSpacing(6)

    def _setup_action_buttons(self, layout: QVBoxLayout) -> None:
        """Configures dialog action buttons for cancel and export operations.

        Args:
            layout: Target vertical layout to attach action buttons.
        """
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setProperty("variant", "minimal")
        self._cancel_button.clicked.connect(self.reject)

        self._export_button = QPushButton("Export", self)
        self._export_button.clicked.connect(self._on_export_clicked)

        actions_layout.addStretch()
        actions_layout.addWidget(self._cancel_button)
        actions_layout.addWidget(self._export_button)
        layout.addLayout(actions_layout)

    def _on_format_changed(self) -> None:
        """Toggles visibility of password controls and security warnings based on format selection."""
        is_encrypted = self._radio_encrypted.isChecked()
        self._password_container.setVisible(is_encrypted)
        self._warning_frame.setVisible(not is_encrypted)
        self._clear_error()

    def _on_browse_clicked(self) -> None:
        """Prompts the user with a native file save dialog to choose destination."""
        default_filename = "passwords_backup.json" if self._radio_encrypted.isChecked() else "passwords_export.json"
        selected_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export File",
            default_filename,
            "JSON Files (*.json);;All Files (*)",
        )
        if selected_file:
            self._dest_input.setText(selected_file)
            self._clear_error()

    def _on_export_clicked(self) -> None:
        """Validates export parameters, prompts confirmation if plaintext, and saves data."""
        dest_path_str = self._dest_input.text().strip()
        if not dest_path_str:
            self._on_browse_clicked()
            dest_path_str = self._dest_input.text().strip()
            if not dest_path_str:
                self._show_error("Please select a destination file path.")
                return

        dest_path = Path(dest_path_str)
        is_encrypted = self._radio_encrypted.isChecked()

        if is_encrypted:
            self._execute_encrypted_export(dest_path)
        else:
            self._execute_plaintext_export(dest_path)

    def _execute_encrypted_export(self, dest_path: Path) -> None:
        """Validates credentials and writes an authenticated encrypted backup file.

        Args:
            dest_path: Target filesystem path for the encrypted backup.
        """
        password = self._password_input.text()
        confirm = self._confirm_input.text()

        if not password:
            self._show_error("Export password cannot be empty.")
            self._password_input.set_error(True)
            self._password_input.setFocus()
            return

        if password != confirm:
            self._show_error("Export passwords do not match.")
            self._confirm_input.set_error(True)
            self._confirm_input.setFocus()
            return

        try:
            self._saved_path = self._encrypted_exporter.export_entries(
                entries=self._entries,
                destination_path=dest_path,
                password=password,
            )
            self.accept()
        except Exception as err:
            self._show_error(f"Export failed: {err}")

    def _execute_plaintext_export(self, dest_path: Path) -> None:
        """Prompts security warning confirmation and writes unencrypted JSON file.

        Args:
            dest_path: Target filesystem path for the plaintext JSON export.
        """
        reply = QMessageBox.warning(
            self,
            "Export Without Encryption",
            "Passwords in this file will not be encrypted and can be read by anyone.\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._saved_path = self._plaintext_exporter.export_entries(
                entries=self._entries,
                destination_path=dest_path,
            )
            self.accept()
        except Exception as err:
            self._show_error(f"Export failed: {err}")

    def _show_error(self, message: str) -> None:
        """Displays error message banner.

        Args:
            message: Informational error message string.
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _clear_error(self) -> None:
        """Hides and resets the error message banner."""
        self._error_label.setText("")
        self._error_label.setVisible(False)


class ImportDialog(QDialog):
    """Modal dialog allowing users to restore credentials from encrypted or plaintext JSON."""

    def __init__(
        self,
        parent: QWidget | None = None,
        encrypted_importer: BaseVaultImporter | None = None,
        plaintext_importer: BaseVaultImporter | None = None,
    ) -> None:
        """Initializes the import credentials dialog.

        Args:
            parent: Optional parent QWidget.
            encrypted_importer: Optional custom encrypted importer implementation.
            plaintext_importer: Optional custom plaintext importer implementation.
        """
        super().__init__(parent)
        self._encrypted_importer: BaseVaultImporter = (
            encrypted_importer if encrypted_importer is not None else EncryptedJsonImporter()
        )
        self._plaintext_importer: BaseVaultImporter = (
            plaintext_importer if plaintext_importer is not None else PlaintextJsonImporter()
        )
        self._imported_entries: list[Entry] = []

        self.setWindowTitle("Import Passwords")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.resize(520, 420)

        self._setup_ui()

    def get_imported_entries(self) -> list[Entry]:
        """Returns the list of validated entries imported from the file.

        Returns:
            List of parsed Entry instances.
        """
        return list(self._imported_entries)

    def _setup_ui(self) -> None:
        """Constructs and arranges dialog layout, inputs, and action buttons."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(14)

        self._setup_header(main_layout)
        self._setup_source_section(main_layout)
        self._setup_format_section(main_layout)
        self._setup_password_section(main_layout)
        self._setup_error_label(main_layout)
        self._setup_action_buttons(main_layout)

    def _setup_header(self, layout: QVBoxLayout) -> None:
        """Configures the title and informational subtitle for the dialog.

        Args:
            layout: Target vertical layout to attach header widgets.
        """
        header_title = QLabel("Import Passwords", self)
        header_title.setProperty("variant", "dialog-title")

        header_subtitle = QLabel("Restore passwords from a JSON backup file.", self)
        header_subtitle.setProperty("variant", "muted")

        layout.addWidget(header_title)
        layout.addWidget(header_subtitle)
        layout.addSpacing(6)

    def _setup_source_section(self, layout: QVBoxLayout) -> None:
        """Configures file source input and file browser picker button.

        Args:
            layout: Target vertical layout to attach source row.
        """
        source_label = QLabel("Source File *", self)
        layout.addWidget(source_label)

        source_row = QHBoxLayout()
        source_row.setContentsMargins(0, 0, 0, 0)
        source_row.setSpacing(8)

        self._source_input = CustomLineEdit(placeholder="Select backup file to import...", parent=self)
        self._source_input.setReadOnly(True)

        self._browse_button = QPushButton("Browse...", self)
        self._browse_button.setProperty("variant", "secondary")
        self._browse_button.clicked.connect(self._on_browse_clicked)

        source_row.addWidget(self._source_input, stretch=1)
        source_row.addWidget(self._browse_button)
        layout.addLayout(source_row)

    def _setup_format_section(self, layout: QVBoxLayout) -> None:
        """Configures the radio button group for format selection.

        Args:
            layout: Target vertical layout to attach format widgets.
        """
        format_label = QLabel("File Format *", self)
        layout.addWidget(format_label)

        self._radio_encrypted = QRadioButton("Encrypted Backup (.json)", self)
        self._radio_encrypted.setChecked(True)
        self._radio_plaintext = QRadioButton("Plaintext JSON (.json)", self)

        self._format_group = QButtonGroup(self)
        self._format_group.addButton(self._radio_encrypted)
        self._format_group.addButton(self._radio_plaintext)
        self._format_group.buttonClicked.connect(self._on_format_changed)

        layout.addWidget(self._radio_encrypted)
        layout.addWidget(self._radio_plaintext)
        layout.addSpacing(4)

    def _setup_password_section(self, layout: QVBoxLayout) -> None:
        """Configures password input container for encrypted backup files.

        Args:
            layout: Target vertical layout to attach password container.
        """
        self._password_container = QWidget(self)
        pwd_layout = QVBoxLayout(self._password_container)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(6)

        pwd_label = QLabel("Decryption Password *", self._password_container)
        self._password_input = PasswordField(placeholder="Enter backup password", parent=self._password_container)

        pwd_layout.addWidget(pwd_label)
        pwd_layout.addWidget(self._password_input)
        layout.addWidget(self._password_container)

    def _setup_error_label(self, layout: QVBoxLayout) -> None:
        """Configures the validation error message label.

        Args:
            layout: Target vertical layout to attach error label.
        """
        self._error_label = QLabel("", self)
        self._error_label.setProperty("variant", "error")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)
        layout.addSpacing(6)

    def _setup_action_buttons(self, layout: QVBoxLayout) -> None:
        """Configures dialog action buttons for cancel and import operations.

        Args:
            layout: Target vertical layout to attach action buttons.
        """
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setProperty("variant", "minimal")
        self._cancel_button.clicked.connect(self.reject)

        self._import_button = QPushButton("Import", self)
        self._import_button.clicked.connect(self._on_import_clicked)

        actions_layout.addStretch()
        actions_layout.addWidget(self._cancel_button)
        actions_layout.addWidget(self._import_button)
        layout.addLayout(actions_layout)

    def _on_format_changed(self) -> None:
        """Toggles password input based on whether encrypted format is selected."""
        is_encrypted = self._radio_encrypted.isChecked()
        self._password_container.setVisible(is_encrypted)
        self._clear_error()

    def _on_browse_clicked(self) -> None:
        """Prompts the user with a native file open dialog to select a backup file."""
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File to Import",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if selected_file:
            self._source_input.setText(selected_file)
            self._clear_error()

    def _on_import_clicked(self) -> None:
        """Validates source file and password, then performs import via selected strategy."""
        source_path_str = self._source_input.text().strip()
        if not source_path_str:
            self._on_browse_clicked()
            source_path_str = self._source_input.text().strip()
            if not source_path_str:
                self._show_error("Please select a file to import.")
                return

        source_path = Path(source_path_str)
        if not source_path.is_file():
            self._show_error("Selected file does not exist.")
            return

        is_encrypted = self._radio_encrypted.isChecked()

        try:
            if is_encrypted:
                self._execute_encrypted_import(source_path)
            else:
                self._execute_plaintext_import(source_path)
            self.accept()
        except InvalidPasswordError:
            self._show_error("Incorrect decryption password or tampered backup file.")
            self._password_input.set_error(True)
            self._password_input.setFocus()
        except VaultImportError as err:
            self._show_error(f"Import failed: {err}")
        except Exception as err:
            self._show_error(f"Failed to read backup file: {err}")

    def _execute_encrypted_import(self, source_path: Path) -> None:
        """Decrypts and imports credentials using user-supplied password.

        Args:
            source_path: Target filesystem path to decrypt and parse.

        Raises:
            InvalidPasswordError: If the password is incorrect or file tampered.
            VaultImportError: If reading or schema validation fails.
        """
        password = self._password_input.text()
        if not password:
            self._show_error("Decryption password cannot be empty.")
            self._password_input.set_error(True)
            self._password_input.setFocus()
            return

        self._imported_entries = self._encrypted_importer.import_entries(
            source_path=source_path,
            password=password,
        )

    def _execute_plaintext_import(self, source_path: Path) -> None:
        """Parses and imports credentials from unencrypted JSON file.

        Args:
            source_path: Target filesystem path to read and parse.

        Raises:
            VaultImportError: If reading or schema validation fails.
        """
        self._imported_entries = self._plaintext_importer.import_entries(
            source_path=source_path,
        )

    def _show_error(self, message: str) -> None:
        """Displays error message banner.

        Args:
            message: Informational error message string.
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _clear_error(self) -> None:
        """Hides and resets the error message banner."""
        self._error_label.setText("")
        self._error_label.setVisible(False)


__all__ = [
    "ExportDialog",
    "ImportDialog",
]
