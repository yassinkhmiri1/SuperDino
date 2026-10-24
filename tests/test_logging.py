"""Tests for data-directory-based application logging."""

from __future__ import annotations

import io
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from config import LOG_FILENAME, LOG_FOLDER_NAME
from core.data_directory import user_data_directory


class LoggingConfigurationTests(unittest.TestCase):
    """Tests for file logging and its console-only fallback."""

    def setUp(self) -> None:
        """Isolate root logger handlers for this test."""
        self.root_logger = logging.getLogger()
        self.original_handlers = self.root_logger.handlers[:]
        self.original_level = self.root_logger.level
        for handler in self.original_handlers:
            self.root_logger.removeHandler(handler)

    def tearDown(self) -> None:
        """Close test-created handlers and restore the previous logger."""
        self._close_test_handlers()
        for handler in self.original_handlers:
            self.root_logger.addHandler(handler)
        self.root_logger.setLevel(self.original_level)

    def _close_test_handlers(self) -> None:
        """Remove and close root handlers created during this test."""
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
            handler.close()

    def test_default_log_directory_is_absolute_and_inside_user_data(self) -> None:
        """The default log directory is rooted under the selected data folder."""
        with tempfile.TemporaryDirectory() as directory:
            local_app_data = Path(directory) / "local"
            data_directory = user_data_directory(
                {"LOCALAPPDATA": str(local_app_data)},
                Path(directory) / "home",
            )
            expected_log_directory = data_directory / LOG_FOLDER_NAME

            try:
                main._configure_logging(data_directory)

                file_handlers = [
                    handler
                    for handler in self.root_logger.handlers
                    if isinstance(handler, logging.FileHandler)
                ]
                self.assertEqual(len(file_handlers), 1)
                log_path = Path(file_handlers[0].baseFilename)
                self.assertTrue(log_path.is_absolute())
                self.assertEqual(log_path, expected_log_directory / LOG_FILENAME)
                self.assertTrue(log_path.parent.is_dir())
            finally:
                self._close_test_handlers()

    def test_directory_creation_failure_uses_console_only_and_crash_hook(self) -> None:
        """File-log setup failure warns once and leaves the crash hook usable."""
        with tempfile.TemporaryDirectory() as directory:
            data_directory = Path(directory) / "data"
            original_mkdir = Path.mkdir

            def fail_log_directory(
                path: Path,
                *args: object,
                **kwargs: object,
            ) -> None:
                if path.name == LOG_FOLDER_NAME:
                    raise OSError("simulated log directory failure")
                original_mkdir(path, *args, **kwargs)

            console = io.StringIO()
            with (
                patch.object(Path, "mkdir", fail_log_directory),
                patch("sys.stderr", console),
            ):
                main._configure_logging(data_directory)
                main._handle_uncaught_exception(
                    ValueError,
                    ValueError("simulated crash"),
                    None,
                )

            self.assertEqual(len(self.root_logger.handlers), 1)
            self.assertIsInstance(self.root_logger.handlers[0], logging.StreamHandler)
            self.assertNotIsInstance(
                self.root_logger.handlers[0],
                logging.FileHandler,
            )
            output = console.getvalue()
            self.assertEqual(
                output.count("Could not configure file logging"),
                1,
            )
            self.assertIn("Uncaught exception; application is terminating", output)


if __name__ == "__main__":
    unittest.main()
