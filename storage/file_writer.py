"""Safe file persistence handler with temporary swap mechanics."""

from __future__ import annotations

import os
from pathlib import Path

from core.exceptions import StorageError
from storage.interfaces import BaseFileWriter


class FileWriter(BaseFileWriter):
    """Safe file writer ensuring data integrity via temporary file swap and flush."""

    def write_bytes(self, target_path: Path, data: bytes) -> None:
        """Safely writes binary data to disk with temporary file replacement.

        Args:
            target_path: Destination path of the target file.
            data: Binary payload to write.

        Raises:
            StorageError: If directory creation, file write, or swap fails.
        """
        resolved_path = target_path.resolve()
        temp_path = resolved_path.with_name(f"{resolved_path.name}.tmp")

        try:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "wb") as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, resolved_path)
        except OSError as err:
            if temp_path.exists():
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise StorageError(f"Failed to safely persist file to '{resolved_path}': {err}") from err


__all__ = [
    "FileWriter",
]
