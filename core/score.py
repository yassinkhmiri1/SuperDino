"""Pure Python score progression rules."""

from __future__ import annotations

import math
from dataclasses import dataclass

from config import SCORE_PER_PIXEL


@dataclass(frozen=True, slots=True)
class ScoreState:
    """Integer score and accumulated fractional score.

    Attributes:
        points: Whole points earned so far.
        score_remainder: Fractional points accumulated toward the next point.
    """

    points: int = 0
    score_remainder: float = 0.0


def advance_score(
    state: ScoreState,
    delta_seconds: float,
    speed: float,
) -> ScoreState:
    """Award score proportional to distance travelled at the current speed.

    Args:
        state: Current score and partial-distance state.
        delta_seconds: Time elapsed since the previous update, in seconds.
        speed: World speed in pixels per second.

    Returns:
        Updated score state.

    Raises:
        ValueError: If elapsed time, speed, or score state is invalid.
    """
    if not math.isfinite(delta_seconds) or delta_seconds < 0.0:
        raise ValueError("delta_seconds must be a finite, non-negative value")
    if not math.isfinite(speed) or speed <= 0.0:
        raise ValueError("speed must be a finite, positive value")
    if state.points < 0:
        raise ValueError("points must be non-negative")
    if (
        not math.isfinite(state.score_remainder)
        or not 0.0 <= state.score_remainder < 1.0
    ):
        raise ValueError(
            "score_remainder must be finite and below one point"
        )

    accumulated_score = (
        state.score_remainder
        + speed * delta_seconds * SCORE_PER_PIXEL
    )
    points_earned = int(accumulated_score)
    return ScoreState(
        points=state.points + points_earned,
        score_remainder=accumulated_score - points_earned,
    )
