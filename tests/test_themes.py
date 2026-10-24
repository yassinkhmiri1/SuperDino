"""Tests for theme selection and pure color calculations."""

from __future__ import annotations

import unittest
from random import Random

from config import (
    BIRD_HEIGHT_OFFSETS,
    DAY,
    DINO_GRAVITY,
    DINO_JUMP_INITIAL_VELOCITY,
    GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
    MAX_SPEED,
    OBSTACLE_MAX_GAP_SECONDS,
    OBSTACLE_MIN_GAP_SECONDS,
    SCORE_PER_PIXEL,
    SPEED_GROWTH_FACTOR,
    SPEED_STEP_SCORE,
    SUNSET,
    THEME_CHANGE_SCORE,
    THEMES,
)
from core.collision import obstacle_hitbox, player_hitbox
from core.obstacles import Obstacle, choose_obstacle_gap
from core.player import PlayerState
from core.speed import speed_for_score
from core.themes import blend_themes, contrast_ratio, theme_for_score

OBSTACLE_DARK_COLOR = (83, 83, 83)


class ThemeSelectionTests(unittest.TestCase):
    """Tests for score-based selection of visual themes."""

    def test_score_boundaries_and_wraparound(self) -> None:
        """Theme selection advances at 500 points and cycles through all themes."""
        expected = {
            0: 0,
            499: 0,
            500: 1,
            999: 1,
            1000: 2,
            1500: 3,
            2000: 0,
            2500: 1,
        }
        for score, theme_index in expected.items():
            with self.subTest(score=score):
                self.assertEqual(theme_for_score(score), theme_index)
        self.assertEqual(THEME_CHANGE_SCORE, 500)

    def test_negative_scores_are_rejected(self) -> None:
        """Invalid negative scores cannot select a theme."""
        with self.assertRaises(ValueError):
            theme_for_score(-1)


class ThemeBlendingTests(unittest.TestCase):
    """Tests for blending theme colors without mutating source themes."""

    def test_blend_at_endpoints_and_midpoint(self) -> None:
        """Progress zero and one preserve their themes; midpoint blends colors."""
        self.assertIs(blend_themes(DAY, SUNSET, 0.0), DAY)
        self.assertIs(blend_themes(DAY, SUNSET, 1.0), SUNSET)

        midpoint = blend_themes(DAY, SUNSET, 0.5)
        self.assertEqual(
            midpoint.background_color,
            (251, 214, 178),
        )
        self.assertEqual(midpoint.gradient_color, (226, 208, 236))
        self.assertEqual(midpoint.ground_tint, (86, 72, 82))

    def test_invalid_progress_is_rejected(self) -> None:
        """Progress outside the inclusive unit interval is invalid."""
        for progress in (-0.1, 1.1, float("nan"), float("inf")):
            with self.subTest(progress=progress):
                with self.assertRaises(ValueError):
                    blend_themes(DAY, SUNSET, progress)


class ThemeContrastTests(unittest.TestCase):
    """Tests for WCAG contrast of theme text and obstacle silhouettes."""

    def test_theme_text_contrasts_with_every_background_stop(self) -> None:
        """Primary and secondary text meet 4.5:1 on both gradient endpoints."""
        for theme in THEMES:
            backgrounds = (theme.background_color, theme.gradient_color)
            for background in backgrounds:
                if background is None:
                    continue
                for label, text_color in (
                    ("primary", theme.text_color),
                    ("secondary", theme.secondary_text_color),
                ):
                    with self.subTest(theme=theme.name, label=label):
                        self.assertGreaterEqual(
                            contrast_ratio(text_color, background),
                            4.5,
                        )

    def test_obstacle_silhouettes_contrast_with_each_theme(self) -> None:
        """The dominant obstacle color remains at least 3:1 against the scene."""
        for theme in THEMES:
            obstacle_color = (
                tuple(255 - channel for channel in OBSTACLE_DARK_COLOR)
                if theme.sprite_treatment == "INVERT"
                else OBSTACLE_DARK_COLOR
            )
            backgrounds = (theme.background_color, theme.gradient_color)
            for background in backgrounds:
                if background is None:
                    continue
                with self.subTest(theme=theme.name, background=background):
                    self.assertGreaterEqual(
                        contrast_ratio(obstacle_color, background),
                        3.0,
                    )


class ThemeGameplayIsolationTests(unittest.TestCase):
    """Tests that selecting a visual theme cannot affect gameplay rules."""

    def test_gameplay_values_are_unchanged_for_every_theme(self) -> None:
        """Movement, spawn, speed, and hitbox values do not depend on themes."""
        score = 1_250
        baseline = (
            speed_for_score(score),
            choose_obstacle_gap(200.0, Random(17)),
            DINO_GRAVITY,
            DINO_JUMP_INITIAL_VELOCITY,
            GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
            MAX_SPEED,
            SCORE_PER_PIXEL,
            SPEED_GROWTH_FACTOR,
            SPEED_STEP_SCORE,
            OBSTACLE_MIN_GAP_SECONDS,
            OBSTACLE_MAX_GAP_SECONDS,
            BIRD_HEIGHT_OFFSETS,
            player_hitbox(PlayerState(), 80, 350),
            obstacle_hitbox(Obstacle("cactus", 0, 80), 350),
        )

        for theme_index in range(len(THEMES)):
            score_for_theme = theme_index * THEME_CHANGE_SCORE
            self.assertEqual(theme_for_score(score_for_theme), theme_index)
            gameplay_values = (
                speed_for_score(score),
                choose_obstacle_gap(200.0, Random(17)),
                DINO_GRAVITY,
                DINO_JUMP_INITIAL_VELOCITY,
                GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                MAX_SPEED,
                SCORE_PER_PIXEL,
                SPEED_GROWTH_FACTOR,
                SPEED_STEP_SCORE,
                OBSTACLE_MIN_GAP_SECONDS,
                OBSTACLE_MAX_GAP_SECONDS,
                BIRD_HEIGHT_OFFSETS,
                player_hitbox(PlayerState(), 80, 350),
                obstacle_hitbox(Obstacle("cactus", 0, 80), 350),
            )
            self.assertEqual(gameplay_values, baseline)


if __name__ == "__main__":
    unittest.main()
