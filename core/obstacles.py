"""Pure Python obstacle spawning and movement rules."""

from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random
from typing import Literal

from config import (
    BIRD_HEIGHT_OFFSETS,
    BIRD_VERTICAL_SLOPE_PER_HORIZONTAL_PIXEL,
    CACTUS_FRAME_PATHS,
    OBSTACLE_BIRD_SPAWN_CHANCE,
    OBSTACLE_CULL_MARGIN,
    OBSTACLE_MAX_GAP_SECONDS,
    OBSTACLE_MIN_GAP_SECONDS,
    OBSTACLE_SPAWN_OFFSET,
    WINDOW_WIDTH,
)


ObstacleKind = Literal["cactus", "bird"]


@dataclass(frozen=True, slots=True)
class Obstacle:
    """One moving obstacle in the game world.

    Attributes:
        kind: Whether this obstacle is a cactus or bird.
        variant: Image index for a cactus or height index for a bird.
        x: Horizontal position of the obstacle's bottom-center anchor.
        bird_vertical_offset_pixels: Vertical displacement from its base height.
        bird_direction: Whether the bird moves upward or downward as it flies left.
    """

    kind: ObstacleKind
    variant: int
    x: float
    bird_vertical_offset_pixels: float = 0.0
    bird_direction: Literal[-1, 1] = 1


@dataclass(frozen=True, slots=True)
class ObstacleUpdate:
    """Obstacle positions and distance remaining until the next spawn.

    Attributes:
        obstacles: Current obstacles, ordered by spawn time.
        next_spawn_distance: Distance to travel before the next spawn.
    """

    obstacles: tuple[Obstacle, ...]
    next_spawn_distance: float


def choose_obstacle_gap(speed: float, randomizer: Random) -> float:
    """Choose the next spawn distance based on current world speed.

    Args:
        speed: World speed in pixels per second.
        randomizer: Random generator used for reproducible spawning.

    Returns:
        Distance in pixels before the next obstacle spawn.

    Raises:
        ValueError: If speed is not finite and positive.
    """
    if not math.isfinite(speed) or speed <= 0.0:
        raise ValueError("speed must be a finite, positive value")
    gap_seconds = randomizer.uniform(
        OBSTACLE_MIN_GAP_SECONDS,
        OBSTACLE_MAX_GAP_SECONDS,
    )
    return speed * gap_seconds


def update_obstacles(
    obstacles: tuple[Obstacle, ...],
    delta_seconds: float,
    speed: float,
    next_spawn_distance: float,
    randomizer: Random,
) -> ObstacleUpdate:
    """Move obstacles and spawn new ones after speed-scaled gaps.

    Args:
        obstacles: Obstacles from the previous frame.
        delta_seconds: Time elapsed since the previous update, in seconds.
        speed: Horizontal world speed in pixels per second.
        next_spawn_distance: Distance remaining until the next spawn.
        randomizer: Random generator used for obstacle selection.

    Returns:
        Updated obstacles and distance to the next spawn.

    Raises:
        ValueError: If timing, speed, or spawn distance is invalid.
    """
    if not math.isfinite(delta_seconds) or delta_seconds < 0.0:
        raise ValueError("delta_seconds must be a finite, non-negative value")
    if not math.isfinite(speed) or speed <= 0.0:
        raise ValueError("speed must be a finite, positive value")
    if not math.isfinite(next_spawn_distance) or next_spawn_distance < 0.0:
        raise ValueError("next_spawn_distance must be a finite, non-negative value")

    distance_travelled = speed * delta_seconds
    moved_obstacles = tuple(
        _move_obstacle(obstacle, distance_travelled)
        for obstacle in obstacles
        if obstacle.x - distance_travelled >= -OBSTACLE_CULL_MARGIN
    )
    distance_remaining = next_spawn_distance - distance_travelled
    spawned_obstacles = list(moved_obstacles)

    while distance_remaining <= 0.0:
        overshoot = -distance_remaining
        spawned_obstacles.append(
            _create_obstacle(
                WINDOW_WIDTH + OBSTACLE_SPAWN_OFFSET - overshoot,
                randomizer,
            )
        )
        distance_remaining += choose_obstacle_gap(speed, randomizer)

    return ObstacleUpdate(tuple(spawned_obstacles), distance_remaining)


def bird_vertical_offset(obstacle: Obstacle) -> float:
    """Return a bird's vertical displacement from its configured height.

    Args:
        obstacle: Bird obstacle with its current normalized animation phase.

    Returns:
        Signed vertical displacement in pixels; positive is upward.

    Raises:
        ValueError: If a bird's displacement or direction is invalid.
    """
    if obstacle.kind != "bird":
        return 0.0
    if not math.isfinite(obstacle.bird_vertical_offset_pixels):
        raise ValueError("bird vertical offset must be finite")
    if obstacle.bird_direction not in (-1, 1):
        raise ValueError("bird direction must be -1 or 1")
    return obstacle.bird_vertical_offset_pixels


def _move_obstacle(obstacle: Obstacle, distance_travelled: float) -> Obstacle:
    """Move an obstacle horizontally and continue a bird's straight flight path.

    Args:
        obstacle: Obstacle to move.
        distance_travelled: Horizontal distance moved toward the player.

    Returns:
        The updated obstacle.
    """
    vertical_offset = obstacle.bird_vertical_offset_pixels
    if obstacle.kind == "bird":
        vertical_offset += (
            obstacle.bird_direction
            * distance_travelled
            * BIRD_VERTICAL_SLOPE_PER_HORIZONTAL_PIXEL
        )
    return Obstacle(
        kind=obstacle.kind,
        variant=obstacle.variant,
        x=obstacle.x - distance_travelled,
        bird_vertical_offset_pixels=vertical_offset,
        bird_direction=obstacle.bird_direction,
    )


def _create_obstacle(x: float, randomizer: Random) -> Obstacle:
    """Select a cactus variant or bird flight height.

    Args:
        x: Horizontal spawn position.
        randomizer: Random generator used for selection.

    Returns:
        The selected obstacle.
    """
    if randomizer.random() < OBSTACLE_BIRD_SPAWN_CHANCE:
        return Obstacle(
            kind="bird",
            variant=randomizer.randrange(len(BIRD_HEIGHT_OFFSETS)),
            x=x,
            bird_direction=randomizer.choice((-1, 1)),
        )
    cactus_variant = randomizer.randrange(len(CACTUS_FRAME_PATHS))
    return Obstacle(kind="cactus", variant=cactus_variant, x=x)
