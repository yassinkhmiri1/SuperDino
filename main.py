"""SuperDino application entry point."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType

from config import (
    LOG_BACKUP_COUNT,
    LOG_FOLDER_NAME,
    LOG_FILENAME,
    LOG_MAX_BYTES,
    SUCCESS_EXIT_CODE,
)
from core.data_directory import user_data_directory

logger = logging.getLogger(__name__)


def _configure_logging(data_directory: Path) -> None:
    """Configure console logging and, when available, rotating-file logging.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    log_directory = (data_directory / LOG_FOLDER_NAME).resolve()
    file_handler: RotatingFileHandler | None = None
    try:
        log_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=log_directory,
            prefix=".write-check-",
        ) as temporary_file:
            temporary_file.write("ok\n")
            temporary_file.flush()
        file_handler = RotatingFileHandler(
            log_directory / LOG_FILENAME,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError:
        if file_handler is not None:
            file_handler.close()
        root_logger.warning(
            "Could not configure file logging; continuing with console logging",
            exc_info=True,
        )


def _handle_uncaught_exception(
    exception_type: type[BaseException],
    exception_value: BaseException,
    traceback: TracebackType | None,
) -> None:
    """Log an uncaught exception and its traceback.

    Args:
        exception_type: The class of the uncaught exception.
        exception_value: The uncaught exception instance.
        traceback: The traceback associated with the exception.
    """
    try:
        raise exception_value.with_traceback(traceback)
    except exception_type:
        logger.exception("Uncaught exception; application is terminating")


def main() -> int:
    """Configure the application and run the game.

    Returns:
        The process exit code.

    Raises:
        pygame.error: If pygame cannot initialize or create the display.
    """
    data_directory = user_data_directory(os.environ, Path.home())
    _configure_logging(data_directory)
    sys.excepthook = _handle_uncaught_exception
    logger.info("Starting SuperDino")

    from game.application import Game

    game = Game()
    exit_code = game.run()

    if exit_code == SUCCESS_EXIT_CODE:
        logger.info("SuperDino exited successfully")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
