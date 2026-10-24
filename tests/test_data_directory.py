"""Tests for resolving the per-user game data directory."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.data_directory import (
    prepare_user_data_directory,
    user_data_directory,
)


class UserDataDirectoryTests(unittest.TestCase):
    """Tests for platform-specific user data locations."""

    def test_local_app_data_uses_superdino_data_subdirectory(self) -> None:
        """Windows data is placed below LOCALAPPDATA."""
        with tempfile.TemporaryDirectory() as directory:
            local_app_data = Path(directory) / "Local"

            result = user_data_directory(
                {"LOCALAPPDATA": str(local_app_data)},
                Path(directory) / "home",
            )

            self.assertEqual(result, local_app_data / "SuperDino" / "data")

    def test_missing_local_app_data_uses_hidden_home_directory(self) -> None:
        """Unset LOCALAPPDATA uses the shared hidden data-folder structure."""
        with tempfile.TemporaryDirectory() as directory:
            home_directory = Path(directory) / "home"

            result = user_data_directory({}, home_directory)

            self.assertEqual(result, home_directory / ".superdino" / "data")

    def test_empty_local_app_data_uses_hidden_home_directory(self) -> None:
        """Empty LOCALAPPDATA uses the shared hidden data-folder structure."""
        with tempfile.TemporaryDirectory() as directory:
            home_directory = Path(directory) / "home"

            result = user_data_directory(
                {"LOCALAPPDATA": ""},
                home_directory,
            )

            self.assertEqual(result, home_directory / ".superdino" / "data")

    def test_unwritable_directory_returns_false_with_warning(self) -> None:
        """A failed write check warns and disables persistent data."""
        with tempfile.TemporaryDirectory() as directory:
            data_directory = Path(directory) / "data"
            with (
                patch(
                    "core.data_directory.tempfile.NamedTemporaryFile",
                    side_effect=PermissionError("read-only"),
                ),
                self.assertLogs("core.data_directory", level="WARNING"),
            ):
                self.assertFalse(prepare_user_data_directory(data_directory))


if __name__ == "__main__":
    unittest.main()
