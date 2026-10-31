"""Vault storage path resolution and hidden directory management."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

from storage.interfaces.path_resolver import BaseVaultPathResolver

_WINDOWS_FILE_ATTRIBUTE_HIDDEN: int = 0x02


class VaultPathResolver(BaseVaultPathResolver):
    """Resolves and prepares the default platform-specific hidden vault storage directory."""

    def __init__(
        self,
        app_directory_name: str = ".password_manager",
        vault_filename: str = "vault.dat",
        custom_base_directory: Path | None = None,
    ) -> None:
        """Initializes the resolver with directory name, filename, and optional base path override.

        Args:
            app_directory_name: Folder name used in application data directory (defaults to '.password_manager').
            vault_filename: Vault binary filename (defaults to 'vault.dat').
            custom_base_directory: Optional base directory override for testing.
        """
        self._app_directory_name: str = app_directory_name
        self._vault_filename: str = vault_filename
        self._custom_base_directory: Path | None = custom_base_directory

    def resolve_path(self) -> Path:
        """Resolves, creates, and protects the persistent vault storage file path.

        Ensures parent directory exists, applies hidden file attributes on Windows,
        and migrates any legacy unhidden vault file to the secure location.

        Returns:
            Resolved absolute Path pointing to the vault storage file.
        """
        data_directory = self._resolve_data_directory()
        data_directory.mkdir(parents=True, exist_ok=True)
        self._apply_hidden_attribute(data_directory)

        target_file_path = (data_directory / self._vault_filename).resolve()
        self._migrate_legacy_vaults_if_needed(target_file_path)

        if target_file_path.exists():
            self._apply_hidden_attribute(target_file_path)

        return target_file_path

    def _resolve_data_directory(self) -> Path:
        """Determines the platform-specific base application data directory.

        Returns:
            Path pointing to the application data directory.
        """
        if self._custom_base_directory is not None:
            return self._custom_base_directory / self._app_directory_name

        if sys.platform == "win32":
            app_data_env = os.environ.get("APPDATA")
            base_dir = Path(app_data_env) if app_data_env else Path.home() / "AppData" / "Roaming"
            return base_dir / self._app_directory_name

        return Path.home() / ".local" / "share" / self._app_directory_name

    def _migrate_legacy_vaults_if_needed(self, target_path: Path) -> None:
        """Migrates legacy local vault files to the hidden persistent directory if target is absent.

        Args:
            target_path: Destination vault path where migrated data should be placed.
        """
        if target_path.exists():
            return

        candidate_paths: list[Path] = [
            Path("vault.dat").resolve(),
        ]
        if sys.platform == "win32":
            app_data_env = os.environ.get("APPDATA")
            if app_data_env:
                candidate_paths.append((Path(app_data_env) / "PasswordManager" / "vault.dat").resolve())

        for candidate in candidate_paths:
            if candidate.is_file() and candidate != target_path:
                try:
                    shutil.copy2(candidate, target_path)
                    break
                except OSError:
                    continue

    @staticmethod
    def _apply_hidden_attribute(path: Path) -> None:
        """Sets the Windows FILE_ATTRIBUTE_HIDDEN flag to hide the file or folder from Explorer.

        Args:
            path: Target filesystem path to hide.
        """
        if sys.platform == "win32" and path.exists():
            try:
                import ctypes

                current_attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if current_attributes != -1 and not (current_attributes & _WINDOWS_FILE_ATTRIBUTE_HIDDEN):
                    ctypes.windll.kernel32.SetFileAttributesW(
                        str(path), current_attributes | _WINDOWS_FILE_ATTRIBUTE_HIDDEN
                    )
            except (AttributeError, OSError):
                pass


def get_default_vault_path() -> Path:
    """Convenience helper resolving the default persistent hidden vault path.

    Returns:
        Resolved absolute Path to the vault file.
    """
    return VaultPathResolver().resolve_path()


__all__ = [
    "VaultPathResolver",
    "get_default_vault_path",
]
