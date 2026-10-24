"""Characterization tests for rendered screens."""

from __future__ import annotations

import hashlib
import os
import unittest
from unittest.mock import patch

import pygame

from config import (
    GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
)
from core.menu import MENU_ITEMS, PAUSE_ITEMS, RESET_CONFIRMATION_ITEMS
from core.player import PlayerState
from core.settings import KeyBindings, default_settings
from ui.window import GameWindow


class MenuScreenTests(unittest.TestCase):
    def test_menu_selection_pixels_match(self) -> None:
        """Pin the current menu screen output for each selection."""
        expected_hashes = (
            "fca4e108d80c5983f730bace7902d06406428f30c4ec61ff139d425e0b7ac35d",
            "38cf8d1cc421204f09e28630b39949763f05e9d66becfc3a17aa9349b691b942",
            "afa9b7af7803457ce9a46fdecfe8963d1011b7be31b90b4dcd4f6f6a9c04e87d",
            "d11c1d0baa64aa99afcb9547f83141c9c64b07c6cd47bea6725842e6c24a387d",
            "3949d4e868d1dc2ba63f52b1aef978f9f9d1726af3717469fe1913a92b5dad8f",
        )
        # Font rendering affects these hashes, so they pin this machine's output.
        hashes = []
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy"}):
            window = GameWindow()
            self.addCleanup(window.close)
            for selected_index in range(len(MENU_ITEMS)):
                window.render(
                    ground_offset=0.0,
                    player=PlayerState(),
                    obstacles=(),
                    delta_seconds=0.0,
                    game_state="MENU",
                    score=0,
                    high_score=1234,
                    playtime_seconds=0.0,
                    debug_world_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_ground_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_obstacle_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_spawn_gap_seconds=1.0,
                    menu_selected_index=selected_index,
                    pause_selected_index=0,
                    confirmation_selected_index=0,
                    controls_selected_index=0,
                    controls_binding_slot=0,
                    controls_listening=False,
                    controls_message="",
                    key_bindings=KeyBindings(),
                    sound_selected_index=0,
                    settings=default_settings(),
                )
                pixels = pygame.image.tobytes(window._surface, "RGB")
                hashes.append(hashlib.sha256(pixels).hexdigest())

        self.assertEqual(tuple(hashes), expected_hashes)
        self.assertEqual(len(hashes), len(MENU_ITEMS))
        self.assertEqual(len(set(hashes)), len(hashes))


class ConfirmationScreenTests(unittest.TestCase):
    def test_confirmation_selection_pixels_match(self) -> None:
        """Pin the current confirmation screen output for each selection."""
        expected_hashes = (
            "a5bdb8fa1a4756e4cb3491328f6f6c143a0595524fd3889ddb34bae3c9281fcb",
            "0e65ea6c119652f143e2d0dfba58f8701a7c34a793f272b5475a7939cf618b59",
        )
        # Font rendering affects these hashes, so they pin this machine's output.
        hashes = []
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy"}):
            window = GameWindow()
            self.addCleanup(window.close)
            for selected_index in range(len(RESET_CONFIRMATION_ITEMS)):
                window.render(
                    ground_offset=0.0,
                    player=PlayerState(),
                    obstacles=(),
                    delta_seconds=0.0,
                    game_state="CONFIRM_RESET",
                    score=0,
                    high_score=0,
                    playtime_seconds=0.0,
                    debug_world_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_ground_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_obstacle_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_spawn_gap_seconds=1.0,
                    menu_selected_index=0,
                    pause_selected_index=0,
                    confirmation_selected_index=selected_index,
                    controls_selected_index=0,
                    controls_binding_slot=0,
                    controls_listening=False,
                    controls_message="",
                    key_bindings=KeyBindings(),
                    sound_selected_index=0,
                    settings=default_settings(),
                )
                pixels = pygame.image.tobytes(window._surface, "RGB")
                hashes.append(hashlib.sha256(pixels).hexdigest())

        self.assertEqual(tuple(hashes), expected_hashes)
        self.assertEqual(len(hashes), len(RESET_CONFIRMATION_ITEMS))
        self.assertEqual(len(set(hashes)), len(hashes))


class PauseScreenTests(unittest.TestCase):
    def test_pause_selection_pixels_match(self) -> None:
        """Pin the current paused screen output for each selection."""
        expected_hashes = (
            "9bbd083db00ee3dfdc9fdff4df47ed01b9f4a7300c839ad51a1c82b9ebbb20e4",
            "82997e5b9a7d83fc8b06d1685b5e9c616cc4d2d4fd7c0cc8e1d20835526ef84d",
        )
        # Font rendering affects these hashes, so they pin this machine's output.
        hashes = []
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy"}):
            window = GameWindow()
            self.addCleanup(window.close)
            for selected_index in range(len(PAUSE_ITEMS)):
                window.render(
                    ground_offset=0.0,
                    player=PlayerState(),
                    obstacles=(),
                    delta_seconds=0.0,
                    game_state="PAUSED",
                    score=0,
                    high_score=0,
                    playtime_seconds=0.0,
                    debug_world_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_ground_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_obstacle_speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                    debug_spawn_gap_seconds=1.0,
                    menu_selected_index=0,
                    pause_selected_index=selected_index,
                    confirmation_selected_index=0,
                    controls_selected_index=0,
                    controls_binding_slot=0,
                    controls_listening=False,
                    controls_message="",
                    key_bindings=KeyBindings(),
                    sound_selected_index=0,
                    settings=default_settings(),
                )
                pixels = pygame.image.tobytes(window._surface, "RGB")
                hashes.append(hashlib.sha256(pixels).hexdigest())

        self.assertEqual(tuple(hashes), expected_hashes)
        self.assertEqual(len(hashes), len(PAUSE_ITEMS))
        self.assertEqual(len(set(hashes)), len(hashes))
