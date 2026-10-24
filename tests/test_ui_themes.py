"""Tests for pygame sprite theme treatment."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import pygame

from config import (
    CLOUD_SCROLL_SPEED_PIXELS_PER_SECOND,
    DAY,
    GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
    NIGHT,
    SNOW,
    SUNSET,
    THEMES,
    THEME_FADE_SECONDS,
    THEME_SPRITE_SWITCH_PROGRESS,
    WINDOW_HEIGHT,
)
from core.player import PlayerState
from core.themes import blend_themes, contrast_ratio
from ui.window import GameWindow


class SpriteThemeTests(unittest.TestCase):
    """Tests for cached theme sprite surfaces and alpha preservation."""

    def test_invert_surface_changes_visible_rgb_and_preserves_alpha(self) -> None:
        """Only visible RGB channels invert; source and alpha remain unchanged."""
        source = pygame.Surface((2, 1), pygame.SRCALPHA, 32)
        source.set_at((0, 0), (83, 83, 83, 255))
        source.set_at((1, 0), (12, 34, 56, 0))

        inverted = GameWindow._invert_surface(source)

        self.assertEqual(inverted.get_at((0, 0),), (172, 172, 172, 255))
        self.assertEqual(inverted.get_at((1, 0),).a, 0)
        self.assertEqual(source.get_at((0, 0),), (83, 83, 83, 255))
        self.assertEqual(source.get_at((1, 0),).a, 0)

    def test_dark_theme_sprite_set_is_recolored_but_day_reuses_originals(
        self,
    ) -> None:
        """INVERT themes receive distinct recolors while DAY shares source sprites."""
        source = pygame.Surface((1, 1), pygame.SRCALPHA, 32)
        source.set_at((0, 0), (83, 83, 83, 255))
        window = GameWindow.__new__(GameWindow)
        window._run_frames = (source,)
        window._jump_frame = source
        window._duck_frames = (source,)
        window._start_frame = source
        window._dead_frame = source
        window._cactus_frames = (source,)
        window._bird_frames = (source,)
        window._game_over_image = source

        day_sprites = window._create_sprite_set(DAY)
        night_sprites = window._create_sprite_set(NIGHT)

        self.assertIs(day_sprites.run_frames[0], source)
        self.assertIs(day_sprites.game_over_image, source)
        self.assertIsNot(night_sprites.run_frames[0], source)
        self.assertIsNot(night_sprites.game_over_image, source)
        self.assertEqual(
            night_sprites.cactus_frames[0].get_at((0, 0)),
            (172, 172, 172, 255),
        )
        self.assertEqual(
            night_sprites.bird_frames[0].get_at((0, 0)),
            (172, 172, 172, 255),
        )
        self.assertEqual(
            night_sprites.game_over_image.get_at((0, 0)),
            (172, 172, 172, 255),
        )


class ThemeTransitionTests(unittest.TestCase):
    """Tests for the theme transition clock and visible cloud crop."""

    def _window(self) -> GameWindow:
        """Create a renderer without initializing a pygame display."""
        window = GameWindow.__new__(GameWindow)
        window.reset_theme_transition()
        return window

    def test_theme_transition_blends_colors_and_switches_sprites_early(self) -> None:
        """A score change begins a fade and changes sprites at 26% progress."""
        window = self._window()
        at_change = window._advance_theme_transition(SUNSET, 0.0)
        self.assertEqual(at_change.background_color, DAY.background_color)
        self.assertEqual(at_change.sprite_treatment, DAY.sprite_treatment)

        progress = THEME_SPRITE_SWITCH_PROGRESS
        during_fade = window._advance_theme_transition(
            SUNSET,
            THEME_FADE_SECONDS * progress,
        )
        self.assertEqual(
            during_fade.background_color,
            blend_themes(DAY, SUNSET, progress).background_color,
        )
        self.assertEqual(during_fade.sprite_treatment, SUNSET.sprite_treatment)

        complete = window._advance_theme_transition(
            SUNSET,
            THEME_FADE_SECONDS * (1.0 - progress),
        )
        self.assertIs(complete, SUNSET)

    def test_reset_returns_transition_state_to_day(self) -> None:
        """A new-run reset clears the old theme and any active fade."""
        window = self._window()
        window._advance_theme_transition(NIGHT, 0.0)
        window.reset_theme_transition()

        self.assertIs(window._transition_from_theme, DAY)
        self.assertIs(window._transition_to_theme, DAY)
        self.assertEqual(window._transition_elapsed, THEME_FADE_SECONDS)

    def test_fade_text_uses_contrast_safe_colors_at_each_gradient_row(self) -> None:
        """Text stays at least 4.5:1 against the local transition background."""
        window = self._window()
        for first, second in (
            (DAY, SUNSET),
            (SUNSET, NIGHT),
            (NIGHT, SNOW),
            (SNOW, DAY),
        ):
            for progress in (0.0, 0.25, 0.5, 0.75, 0.99):
                theme = blend_themes(first, second, progress)
                window._transition_elapsed = THEME_FADE_SECONDS * progress
                for y in (0, 100, 200, 300, 399):
                    bottom = theme.gradient_color or theme.background_color
                    vertical_progress = y / 399
                    background = tuple(
                        round(top + (end - top) * vertical_progress)
                        for top, end in zip(
                            theme.background_color,
                            bottom,
                            strict=True,
                        )
                    )
                    text_color = window._theme_text_color(
                        theme,
                        y,
                        theme.text_color,
                    )
                    with self.subTest(
                        transition=(first.name, second.name),
                        progress=progress,
                        y=y,
                    ):
                        self.assertGreaterEqual(
                            contrast_ratio(text_color, background),
                            4.5,
                        )

    def test_cloud_crop_discards_transparent_padding_only(self) -> None:
        """Cloud cropping uses visible pixels and leaves the loaded source intact."""
        source = pygame.Surface((10, 9), pygame.SRCALPHA, 32)
        source.fill((218, 218, 218, 0))
        source.fill((218, 218, 218, 255), pygame.Rect(2, 3, 6, 3))

        cropped = GameWindow._crop_visible_surface(source)

        self.assertEqual(cropped.get_size(), (6, 3))
        self.assertEqual(cropped.get_at((0, 0)).a, 255)
        self.assertEqual(source.get_at((0, 0)).a, 0)

    def test_transition_surfaces_are_replaced_and_theme_surfaces_reused(self) -> None:
        """Interpolated surfaces stay transient and completed fades use fixed caches."""
        window = self._window()
        window._track = pygame.Surface((800, 1), pygame.SRCALPHA, 32)
        window._track_alpha_mask = pygame.Surface((800, 1), pygame.SRCALPHA, 32)
        window._tracks_by_theme = {
            theme.name: window._create_theme_track(theme)
            for theme in THEMES
        }
        window._cloud = pygame.Surface((2, 2), pygame.SRCALPHA, 32)
        window._cloud.fill((218, 218, 218, 255))
        window._clouds_by_theme = {
            theme.name: window._tint_cloud(theme)
            for theme in THEMES
        }
        window._track_cache = None
        window._cloud_cache = None
        window._cloud_offset = 0.0
        window._surface = Mock()
        window._surface.get_width.return_value = 800
        window._sprite_sets_by_treatment = {
            theme.sprite_treatment: None
            for theme in THEMES
        }
        dino = pygame.Surface((1, 1), pygame.SRCALPHA, 32)
        window._select_dino_frame = Mock(return_value=dino)
        window._advance_obstacle_animation = Mock()
        window._draw_theme_background = Mock()
        window._score_font = Mock()
        window._score_font.render.return_value = dino

        render_args = {
            "ground_offset": 0.0,
            "player": PlayerState(),
            "obstacles": (),
            "delta_seconds": 0.1,
            "game_state": "RUNNING",
            "score": 0,
            "high_score": 0,
            "playtime_seconds": 0.0,
            "debug_world_speed": GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
            "debug_ground_speed": GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
            "debug_obstacle_speed": GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
            "debug_spawn_gap_seconds": 1.0,
            "menu_selected_index": 0,
            "pause_selected_index": 0,
            "confirmation_selected_index": 0,
            "controls_selected_index": 0,
            "controls_binding_slot": 0,
            "controls_listening": False,
            "controls_message": "",
            "key_bindings": None,
            "sound_selected_index": 0,
            "settings": None,
        }
        transitions = (
            (SUNSET, 500),
            (NIGHT, 1000),
            (SNOW, 1500),
            (DAY, 0),
        )
        track_tints = set()
        cloud_tints = set()

        with patch("pygame.display.flip"):
            for target, score in transitions:
                for _ in range(10):
                    old_track = window._track_cache
                    old_cloud = window._cloud_cache
                    window._surface.blit.reset_mock()
                    render_args["score"] = score
                    window.render(**render_args)

                    self.assertFalse(hasattr(window, "_tracks_by_tint"))
                    self.assertFalse(hasattr(window, "_clouds_by_tint"))
                    if window._transition_elapsed < THEME_FADE_SECONDS:
                        self.assertIsNotNone(window._track_cache)
                        self.assertIsNotNone(window._cloud_cache)
                        self.assertEqual(
                            len(window._track_cache),
                            2,
                        )
                        self.assertEqual(
                            len(window._cloud_cache),
                            2,
                        )
                        if old_track is not None:
                            if window._track_cache[0] == old_track[0]:
                                self.assertIs(window._track_cache[1], old_track[1])
                            else:
                                self.assertIsNot(
                                    window._track_cache[1],
                                    old_track[1],
                                )
                        if old_cloud is not None:
                            if window._cloud_cache[0] == old_cloud[0]:
                                self.assertIs(window._cloud_cache[1], old_cloud[1])
                            else:
                                self.assertIsNot(
                                    window._cloud_cache[1],
                                    old_cloud[1],
                                )
                        track_tints.add(window._track_cache[0])
                        cloud_tints.add(window._cloud_cache[0])
                        calls = window._surface.blit.call_args_list
                        self.assertTrue(
                            any(
                                call.args[0] is window._track_cache[1]
                                for call in calls
                            )
                        )
                        self.assertTrue(
                            any(
                                call.args[0] is window._cloud_cache[1]
                                for call in calls
                            )
                        )
                    else:
                        self.assertIsNone(window._track_cache)
                        self.assertIsNone(window._cloud_cache)
                        calls = window._surface.blit.call_args_list
                        self.assertTrue(
                            any(
                                call.args[0] is window._tracks_by_theme[target.name]
                                for call in calls
                            )
                        )
                        self.assertTrue(
                            any(
                                call.args[0] is window._clouds_by_theme[target.name]
                                for call in calls
                            )
                        )

        self.assertGreater(len(track_tints), 4)
        self.assertGreater(len(cloud_tints), 4)

    def test_cloud_speed_is_slower_than_ground(self) -> None:
        """Cloud motion remains slower than the fastest configured ground rate."""
        self.assertLess(
            CLOUD_SCROLL_SPEED_PIXELS_PER_SECOND,
            GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
        )

    def test_sprite_switch_progress_maximizes_sampled_obstacle_contrast(self) -> None:
        """The configured switch maximizes minimum contrast at five fade samples."""
        dark_sprite = (83, 83, 83)
        inverted_sprite = tuple(255 - channel for channel in dark_sprite)
        progress_samples = (0.0, 0.25, 0.5, 0.75, 1.0)

        def worst_contrast(switch_progress: float) -> float:
            """Find the minimum sampled obstacle contrast for a switch point."""
            minimum = float("inf")
            for first, second in zip(THEMES, THEMES[1:] + THEMES[:1]):
                for progress in progress_samples:
                    theme = blend_themes(first, second, progress)
                    treatment = (
                        second.sprite_treatment
                        if progress >= switch_progress
                        else first.sprite_treatment
                    )
                    sprite = (
                        inverted_sprite
                        if treatment == "INVERT"
                        else dark_sprite
                    )
                    bottom = theme.gradient_color or theme.background_color
                    for y in range(WINDOW_HEIGHT):
                        vertical_progress = y / (WINDOW_HEIGHT - 1)
                        background = tuple(
                            round(top + (end - top) * vertical_progress)
                            for top, end in zip(
                                theme.background_color,
                                bottom,
                                strict=True,
                            )
                        )
                        minimum = min(
                            minimum,
                            contrast_ratio(sprite, background),
                        )
            return minimum

        measured = worst_contrast(THEME_SPRITE_SWITCH_PROGRESS)
        best_sampled = max(
            worst_contrast(candidate / 100)
            for candidate in range(101)
        )

        self.assertAlmostEqual(measured, best_sampled)
        self.assertAlmostEqual(measured, 1.9, places=1)


if __name__ == "__main__":
    unittest.main()
