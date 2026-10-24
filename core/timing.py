"""Frame-rate-independent simulation timing helpers."""

from __future__ import annotations

import math
from collections.abc import Iterator

from config import MAX_PHYSICS_STEP_SECONDS


def physics_time_steps(delta_seconds: float) -> Iterator[float]:
    """Split elapsed time into small, evenly sized physics steps.

    Args:
        delta_seconds: Elapsed real time, in seconds.

    Yields:
        Steps whose durations sum to delta_seconds and are no larger than the
        configured maximum. A zero-duration step is yielded for zero elapsed
        time so input can still be applied.

    Raises:
        ValueError: If delta_seconds is negative or not finite.
    """
    if not math.isfinite(delta_seconds) or delta_seconds < 0.0:
        raise ValueError("delta_seconds must be a finite, non-negative value")
    if delta_seconds == 0.0:
        yield 0.0
        return

    step_count = math.ceil(delta_seconds / MAX_PHYSICS_STEP_SECONDS)
    step_duration = delta_seconds / step_count
    for _ in range(step_count):
        yield step_duration
