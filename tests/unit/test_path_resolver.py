"""Unit tests for VaultPathResolver and hidden directory resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from storage.interfaces import BaseVaultPathResolver
from storage.path_resolver import VaultPathResolver, get_default_vault_path


class TestVaultPathResolver:
    """Validates vault path resolution, hidden directory creation, and legacy migration."""

    def test_implements_interface(self) -> None:
        """Verifies that VaultPathResolver implements BaseVaultPathResolver."""
        resolver = VaultPathResolver()
        assert isinstance(resolver, BaseVaultPathResolver)

    def test_resolve_path_creates_directory(self, tmp_path: Path) -> None:
        """Verifies that resolve_path creates the directory structure within the base path."""
        resolver = VaultPathResolver(
            app_directory_name=".test_vault_dir",
            vault_filename="secure_vault.dat",
            custom_base_directory=tmp_path,
        )

        resolved_path = resolver.resolve_path()

        assert resolved_path.parent.is_dir()
        assert resolved_path.parent.name == ".test_vault_dir"
        assert resolved_path.name == "secure_vault.dat"

    def test_resolve_path_migrates_legacy_vault(self, tmp_path: Path) -> None:
        """Verifies that legacy vault is safely copied to the new hidden location if absent."""
        legacy_dir = tmp_path / "legacy"
        legacy_dir.mkdir()
        legacy_file = legacy_dir / "vault.dat"
        legacy_file.write_bytes(b"encrypted_vault_sample_data")

        resolver = VaultPathResolver(
            app_directory_name=".migrated_vault_dir",
            vault_filename="vault.dat",
            custom_base_directory=tmp_path,
        )

        with patch.object(Path, "resolve", return_value=legacy_file):
            resolved_path = resolver.resolve_path()

        assert resolved_path.is_file()
        assert resolved_path.read_bytes() == b"encrypted_vault_sample_data"

    def test_resolve_path_does_not_overwrite_existing(self, tmp_path: Path) -> None:
        """Ensures that existing vault in the hidden folder is preserved and not overwritten."""
        resolver = VaultPathResolver(
            app_directory_name=".existing_dir",
            vault_filename="vault.dat",
            custom_base_directory=tmp_path,
        )

        target_file = tmp_path / ".existing_dir" / "vault.dat"
        target_file.parent.mkdir(parents=True)
        target_file.write_bytes(b"original_existing_content")

        resolved_path = resolver.resolve_path()
        assert resolved_path.read_bytes() == b"original_existing_content"

    def test_get_default_vault_path_returns_valid_path(self) -> None:
        """Verifies the module-level convenience helper returns an absolute Path."""
        path = get_default_vault_path()
        assert isinstance(path, Path)
        assert path.is_absolute()
        assert path.name == "vault.dat"
        assert ".password_manager" in str(path)
