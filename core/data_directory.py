"""Resolve the per-user directory used for persistent game data."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Mapping
from pathlib import Path

logger = logging.getLogger(__name__)


def user_data_directory(
    environment: Mapping[str, str],
    home_directory: Path,
) -> Path:
    """Return the user data directory for the supplied environment.

    Args:
        environment: Environment variables used to select the platform path.
        home_directory: User home directory used when LOCALAPPDATA is unset.

    Returns:
        The per-user SuperDino data directory.
    """
    local_app_data = environment.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "SuperDino" / "data"
    return home_directory / ".superdino" / "data"


def prepare_user_data_directory(directory: Path) -> bool:
    """Create and verify a user data directory is writable.

    Args:
        directory: Directory to create and check.

    Returns:
        Whether the directory is available for persistence.
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=directory,
            prefix=".write-check-",
        ) as temporary_file:
            temporary_file.write(b"ok")
            temporary_file.flush()
    except OSError:
        logger.warning(
            "User data directory is unavailable; using defaults without saving: %s",
            directory,
            exc_info=True,
        )
        return False
    return True
