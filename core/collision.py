"""Pure Python hitbox construction and collision checks."""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    BIRD_COLLISION_SPRITE_SIZE,
    BIRD_HEIGHT_OFFSETS,
    BIRD_HITBOX_INSET_BOTTOM,
    BIRD_HITBOX_INSET_TOP,
    BIRD_HITBOX_INSET_X,
    CACTUS_HITBOX_INSET_BOTTOM,
    CACTUS_HITBOX_INSET_TOP,
    CACTUS_HITBOX_INSET_X,
    CACTUS_SPRITE_SIZES,
    DINO_DUCK_SPRITE_SIZE,
    DINO_HITBOX_INSET_BOTTOM,
    DINO_HITBOX_INSET_TOP,
    DINO_HITBOX_INSET_X,
    DINO_JUMP_SPRITE_SIZE,
    DINO_RUN_SPRITE_SIZE,
)
from core.obstacles import Obstacle, bird_vertical_offset
from core.player import PlayerState


@dataclass(frozen=True, slots=True)
class Hitbox:
    """Axis-aligned rectangle used for collision checks.

    Attributes:
        left: Left edge.
        top: Top edge.
        right: Right edge.
        bottom: Bottom edge.
    """

    left: float
    top: float
    right: float
    bottom: float


def player_hitbox(player: PlayerState, center_x: float, ground_y: float) -> Hitbox:
    """Build a tight hitbox for the dino's current pose.

    Args:
        player: Current dino movement and posture state.
        center_x: Horizontal bottom-center sprite anchor.
        ground_y: Vertical ground-line anchor, adjusted for jump height.

    Returns:
        The dino hitbox.
    """
    if not player.grounded:
        width, height = DINO_JUMP_SPRITE_SIZE
    elif player.ducking:
        width, height = DINO_DUCK_SPRITE_SIZE
    else:
        width, height = DINO_RUN_SPRITE_SIZE

    return _inset_hitbox(
        center_x,
        ground_y,
        width,
        height,
        DINO_HITBOX_INSET_X,
        DINO_HITBOX_INSET_TOP,
        DINO_HITBOX_INSET_BOTTOM,
    )


def obstacle_hitbox(obstacle: Obstacle, ground_y: float) -> Hitbox:
    """Build a tight hitbox for a cactus or bird.

    Args:
        obstacle: Obstacle with its bottom-center anchor position.
        ground_y: Ground line before applying the bird's flight height.

    Returns:
        The obstacle hitbox.

    Raises:
        ValueError: If the obstacle kind or variant is invalid.
    """
    if obstacle.kind == "cactus":
        if not 0 <= obstacle.variant < len(CACTUS_SPRITE_SIZES):
            raise ValueError(f"Invalid cactus variant: {obstacle.variant}")
        width, height = CACTUS_SPRITE_SIZES[obstacle.variant]
        inset_x = CACTUS_HITBOX_INSET_X
        inset_top = CACTUS_HITBOX_INSET_TOP
        inset_bottom = CACTUS_HITBOX_INSET_BOTTOM
        obstacle_ground_y = ground_y
    elif obstacle.kind == "bird":
        width, height = BIRD_COLLISION_SPRITE_SIZE
        inset_x = BIRD_HITBOX_INSET_X
        inset_top = BIRD_HITBOX_INSET_TOP
        inset_bottom = BIRD_HITBOX_INSET_BOTTOM
        if not 0 <= obstacle.variant < len(BIRD_HEIGHT_OFFSETS):
            raise ValueError(f"Invalid bird height variant: {obstacle.variant}")
        obstacle_ground_y = (
            ground_y
            - BIRD_HEIGHT_OFFSETS[obstacle.variant]
            - round(bird_vertical_offset(obstacle))
        )
    else:
        raise ValueError(f"Invalid obstacle kind: {obstacle.kind}")

    return _inset_hitbox(
        obstacle.x,
        obstacle_ground_y,
        width,
        height,
        inset_x,
        inset_top,
        inset_bottom,
    )


def hitboxes_overlap(first: Hitbox, second: Hitbox) -> bool:
    """Return whether two axis-aligned hitboxes overlap.

    Args:
        first: First hitbox.
        second: Second hitbox.

    Returns:
        True when the rectangles overlap with positive area.
    """
    return (
        first.left < second.right
        and first.right > second.left
        and first.top < second.bottom
        and first.bottom > second.top
    )


def _inset_hitbox(
    center_x: float,
    bottom_y: float,
    width: int,
    height: int,
    inset_x: int,
    inset_top: int,
    inset_bottom: int,
) -> Hitbox:
    """Create an axis-aligned hitbox inset from its sprite bounds.

    Args:
        center_x: Horizontal bottom-center anchor.
        bottom_y: Vertical bottom anchor.
        width: Sprite width.
        height: Sprite height.
        inset_x: Inset applied to both horizontal sides.
        inset_top: Inset from the sprite top.
        inset_bottom: Inset from the sprite bottom.

    Returns:
        The resulting smaller hitbox.
    """
    half_width = width / 2
    return Hitbox(
        left=center_x - half_width + inset_x,
        top=bottom_y - height + inset_top,
        right=center_x + half_width - inset_x,
        bottom=bottom_y - inset_bottom,
    )
