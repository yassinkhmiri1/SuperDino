"""Atomic local high-score storage."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class HighScoreStorageError(RuntimeError):
    """Raised when the high score cannot be read or saved."""


def load_high_score(path: Path) -> int:
    """Load a high score from a plain-text file.

    Args:
        path: Location of the high-score file.

    Returns:
        Stored high score, or zero if the file is missing or corrupted.

    Raises:
        HighScoreStorageError: If the file cannot be read for another reason.
    """
    try:
        contents = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.warning("High-score file is missing; starting from zero: %s", path)
        return 0
    except UnicodeDecodeError:
        logger.warning("High-score file is corrupted; starting from zero: %s", path)
        return 0
    except OSError as error:
        logger.exception("Could not read high-score file: %s", path)
        raise HighScoreStorageError(
            f"Unable to read high-score file: {path}"
        ) from error

    try:
        score = int(contents)
    except ValueError:
        logger.warning("High-score file is corrupted; starting from zero: %s", path)
        return 0
    if score < 0 or contents != str(score):
        logger.warning("High-score file is corrupted; starting from zero: %s", path)
        return 0
    return score


def save_high_score(path: Path, score: int) -> None:
    """Atomically save a non-negative high score.

    Args:
        path: Destination high-score file.
        score: Non-negative whole-number score to persist.

    Raises:
        ValueError: If score is negative or not an integer.
        HighScoreStorageError: If the score cannot be saved.
    """
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("score must be a non-negative integer")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(f"{score}\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except OSError as error:
        logger.exception("Could not save high-score file: %s", path)
        raise HighScoreStorageError(
            f"Unable to save high-score file: {path}"
        ) from error
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                logger.warning(
                    "Could not remove temporary high-score file: %s",
                    temporary_path,
                    exc_info=True,
                )

    logger.info("Saved high score: %d", score)
