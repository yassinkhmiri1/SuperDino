"""Pure Python game speed progression."""

from __future__ import annotations

from config import (
    GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
    MAX_SPEED,
    SPEED_GROWTH_FACTOR,
    SPEED_STEP_SCORE,
)


def speed_for_score(score: int) -> float:
    """Return world speed for the current score.

    Args:
        score: Current non-negative whole-number score.

    Returns:
        Speed in pixels per second.

    Raises:
        ValueError: If score is negative or not an integer.
    """
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("score must be a non-negative integer")
    speed_steps = score // SPEED_STEP_SCORE
    return min(
        GROUND_SCROLL_SPEED_PIXELS_PER_SECOND
        * SPEED_GROWTH_FACTOR**speed_steps,
        MAX_SPEED,
    )
