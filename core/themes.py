"""Pure theme data and color calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, TypeAlias

Color: TypeAlias = tuple[int, int, int]
SpriteTreatment: TypeAlias = Literal["NONE", "INVERT"]


@dataclass(frozen=True, slots=True)
class Theme:
    """Immutable visual settings for one game theme."""

    name: str
    background_color: Color
    ground_tint: Color
    text_color: Color
    secondary_text_color: Color
    sprite_treatment: SpriteTreatment
    cloud_tint: Color
    gradient_color: Color | None = None


def theme_for_score(score: int) -> int:
    """Return the theme index for a non-negative score."""
    if not isinstance(score, int) or isinstance(score, bool) or score < 0:
        raise ValueError("score must be a non-negative integer")

    from config import THEME_CHANGE_SCORE, THEMES

    return (score // THEME_CHANGE_SCORE) % len(THEMES)


def _blend_color(first: Color, second: Color, progress: float) -> Color:
    """Blend two RGB colors using rounded 8-bit channel values."""
    return (
        round(first[0] + (second[0] - first[0]) * progress),
        round(first[1] + (second[1] - first[1]) * progress),
        round(first[2] + (second[2] - first[2]) * progress),
    )


def blend_themes(first: Theme, second: Theme, progress: float) -> Theme:
    """Blend theme colors by progress, which must be between zero and one."""
    if not math.isfinite(progress) or not 0.0 <= progress <= 1.0:
        raise ValueError("progress must be finite and between 0 and 1")
    if progress == 0.0:
        return first
    if progress == 1.0:
        return second

    first_gradient = first.gradient_color or first.background_color
    second_gradient = second.gradient_color or second.background_color
    return Theme(
        name=second.name,
        background_color=_blend_color(
            first.background_color,
            second.background_color,
            progress,
        ),
        gradient_color=(
            _blend_color(first_gradient, second_gradient, progress)
            if first.gradient_color is not None
            or second.gradient_color is not None
            else None
        ),
        ground_tint=_blend_color(first.ground_tint, second.ground_tint, progress),
        text_color=_blend_color(first.text_color, second.text_color, progress),
        secondary_text_color=_blend_color(
            first.secondary_text_color,
            second.secondary_text_color,
            progress,
        ),
        sprite_treatment=(
            first.sprite_treatment if progress < 0.5 else second.sprite_treatment
        ),
        cloud_tint=_blend_color(first.cloud_tint, second.cloud_tint, progress),
    )


def relative_luminance(color: Color) -> float:
    """Calculate WCAG relative luminance for an 8-bit sRGB color."""
    if len(color) != 3:
        raise ValueError("an RGB color must contain exactly three channels")
    channels = []
    for channel in color:
        if not isinstance(channel, int) or not 0 <= channel <= 255:
            raise ValueError("RGB channels must be integers between 0 and 255")
        normalized = channel / 255.0
        channels.append(
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )
    return (
        0.2126 * channels[0]
        + 0.7152 * channels[1]
        + 0.0722 * channels[2]
    )


def contrast_ratio(first: Color, second: Color) -> float:
    """Return the WCAG contrast ratio between two opaque sRGB colors."""
    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)
