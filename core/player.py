"""Pure Python player movement rules."""

from __future__ import annotations

import math
from dataclasses import dataclass

from config import (
    DINO_GRAVITY,
    DINO_JUMP_INITIAL_VELOCITY,
    PHYSICS_ACCELERATION_COEFFICIENT,
)


@dataclass(frozen=True, slots=True)
class PlayerState:
    """Immutable vertical movement and posture state for the dino.

    Attributes:
        ground_offset: Distance above the ground, in pixels.
        vertical_velocity: Vertical speed, in pixels per second.
        grounded: Whether the dino is standing on the ground.
        ducking: Whether the dino is ducking on the ground.
    """

    ground_offset: float = 0.0
    vertical_velocity: float = 0.0
    grounded: bool = True
    ducking: bool = False


def update_player(
    state: PlayerState,
    delta_seconds: float,
    jump_pressed: bool,
    duck_held: bool,
) -> PlayerState:
    """Advance the dino movement state by elapsed real time.

    Args:
        state: Current movement state.
        delta_seconds: Time elapsed since the previous update, in seconds.
        jump_pressed: Whether the jump binding was pressed this frame.
        duck_held: Whether the duck binding is currently held.

    Returns:
        The updated movement state.

    Raises:
        ValueError: If delta_seconds is negative or not finite.
    """
    if not math.isfinite(delta_seconds) or delta_seconds < 0.0:
        raise ValueError("delta_seconds must be a finite, non-negative value")

    if jump_pressed and state.grounded:
        state = PlayerState(
            ground_offset=state.ground_offset,
            vertical_velocity=DINO_JUMP_INITIAL_VELOCITY,
            grounded=False,
        )

    if not state.grounded:
        if delta_seconds == 0.0:
            return state
        velocity = state.vertical_velocity + DINO_GRAVITY * delta_seconds
        ground_offset = state.ground_offset - (
            state.vertical_velocity * delta_seconds
            + PHYSICS_ACCELERATION_COEFFICIENT
            * DINO_GRAVITY
            * delta_seconds**2
        )
        if ground_offset <= 0.0:
            return PlayerState(ducking=duck_held)
        return PlayerState(
            ground_offset=ground_offset,
            vertical_velocity=velocity,
            grounded=False,
        )

    return PlayerState(ducking=duck_held)
