"""Tests for application-level game-state transitions."""

from __future__ import annotations

import os
from math import ceil
from random import Random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.menu import MenuState, PauseMenuState, SoundMenuState
from core.obstacles import Obstacle
from core.player import PlayerState
from core.score import ScoreState
from core.settings import default_settings
from config import (
    HIGH_SCORE_FILENAME,
    MAX_FRAME_SECONDS,
    MAX_PHYSICS_STEP_SECONDS,
    SETTINGS_FILENAME,
)
from game.application import Game
from ui.window import InputFrame

class PauseStateTests(unittest.TestCase):
    """Tests for pause actions without interrupting background music."""

    def _game(self, state: str, selected_index: int = 0) -> Game:
        """Create a lightweight application instance without a pygame window."""
        game = Game.__new__(Game)
        game._state = state
        game._pause_state = PauseMenuState(selected_index)
        game._menu_state = MenuState(3)
        game._audio = Mock()
        game._score = ScoreState(125)
        game._playtime_seconds = 12.0
        game._ground_offset = 10.0
        game._player = PlayerState()
        game._obstacles = ()
        game._randomizer = Random(0)
        game._window = Mock()
        game._persistence_enabled = True
        game._high_score_path = Path("high_score.txt")
        game._settings_path = Path("settings.json")
        return game

    def test_escape_pauses_running_game_without_pausing_music(self) -> None:
        """Escape enters pause state while music continues."""
        game = self._game("RUNNING")

        game._handle_state_input(InputFrame(True, False, False, pause_pressed=True))

        self.assertEqual(game._state, "PAUSED")
        self.assertEqual(game._pause_state, PauseMenuState())
        game._audio.pause_music.assert_not_called()
        game._audio.fade_out_music.assert_not_called()

    def test_escape_resumes_paused_game_without_restarting_music(self) -> None:
        """Escape resumes the game while existing music continues."""
        game = self._game("PAUSED", 1)

        game._handle_state_input(InputFrame(True, False, False, pause_pressed=True))

        self.assertEqual(game._state, "RUNNING")
        game._audio.fade_in_music.assert_not_called()

    def test_back_to_menu_resets_run_without_restarting_music(self) -> None:
        """Back to menu resets the run while leaving background music alone."""
        game = self._game("PAUSED", 1)

        game._handle_state_input(InputFrame(True, False, False, restart_pressed=True))

        self.assertEqual(game._state, "MENU")
        self.assertEqual(game._menu_state, MenuState())
        self.assertEqual(game._score, ScoreState())
        self.assertEqual(game._playtime_seconds, 0.0)
        game._audio.fade_in_music.assert_not_called()

    def test_game_over_restart_fades_music_back_in(self) -> None:
        """Restarting after game over resets the run and fades music in."""
        game = self._game("GAME_OVER")

        game._handle_state_input(
            InputFrame(True, False, False, restart_pressed=True)
        )

        self.assertEqual(game._state, "RUNNING")
        self.assertEqual(game._score, ScoreState())
        game._audio.fade_in_music.assert_called_once_with()
        game._window.reset_theme_transition.assert_called_once_with()

    @patch("game.application.hitboxes_overlap", return_value=True)
    def test_collision_fades_music_out(
        self,
        hitboxes_overlap_mock: Mock,
    ) -> None:
        """A collision enters game over and starts a music fade-out."""
        game = self._game("RUNNING")
        game._obstacles = (Obstacle("cactus", 0, 100.0),)

        game._check_collisions()

        self.assertEqual(game._state, "GAME_OVER")
        game._audio.play_death.assert_called_once_with()
        game._audio.fade_out_music.assert_called_once_with()
        hitboxes_overlap_mock.assert_called_once()

    def test_long_frame_caps_running_simulation_and_playtime(self) -> None:
        """A long frame advances only the configured maximum simulation time."""
        game = self._game("RUNNING")
        game._window.ground_width = 800
        game._playtime_seconds = 0.0
        game._high_score = game._score.points
        game._next_spawn_distance = 100_000.0
        max_steps = ceil(MAX_FRAME_SECONDS / MAX_PHYSICS_STEP_SECONDS)

        with patch.object(
            game,
            "_advance_ground",
            wraps=game._advance_ground,
        ) as advance_ground:
            game._update_running(5.0, False, False)

        self.assertLessEqual(advance_ground.call_count, max_steps)
        self.assertAlmostEqual(game._playtime_seconds, MAX_FRAME_SECONDS)


class SoundSettingsApplicationTests(unittest.TestCase):
    """Tests for applying persisted Sound-screen changes immediately."""

    def test_music_slider_and_mute_persist_and_update_audio(self) -> None:
        """Volume and mute changes save before applying live mixer values."""
        game = Game.__new__(Game)
        game._settings = default_settings()
        game._settings_message = ""
        game._sound_state = SoundMenuState()
        game._window = Mock()
        game._audio = Mock()
        game._persistence_enabled = True
        game._settings_path = Path("settings.json")

        with patch("game.application.save_settings") as save_settings_mock:
            game._handle_sound_input(
                InputFrame(
                    True,
                    False,
                    False,
                    menu_selection=0,
                    control_slot_direction=1,
                )
            )
            save_settings_mock.assert_called_once_with(
                game._settings,
                game._settings_path,
            )
            game._audio.set_volumes.assert_called_once_with(0.28, 0.8, False)
            self.assertEqual(game._settings.music_volume, 80)

            game._handle_sound_input(
                InputFrame(
                    True,
                    False,
                    False,
                    menu_selection=2,
                    menu_activate=True,
                )
            )

        self.assertTrue(game._settings.muted)
        self.assertEqual(save_settings_mock.call_count, 2)
        self.assertEqual(
            game._audio.set_volumes.call_args_list[1].args,
            (0.28, 0.8, True),
        )


class ApplicationDataPathTests(unittest.TestCase):
    """Tests that application persistence paths use the per-user directory."""

    def test_default_persistence_paths_are_in_user_data_directory(self) -> None:
        """High-score and settings files are outside the source tree."""
        with tempfile.TemporaryDirectory() as directory:
            local_app_data = Path(directory) / "local"
            expected_data_directory = local_app_data / "SuperDino" / "data"
            with (
                patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}),
                patch("game.application.load_settings", return_value=default_settings()),
                patch("game.application.load_high_score", return_value=0),
                patch("game.application.GameWindow"),
                patch("game.application.AudioController"),
            ):
                game = Game()

            source_directory = Path(__file__).resolve().parents[1]
            self.assertEqual(
                game._settings_path,
                expected_data_directory / SETTINGS_FILENAME,
            )
            self.assertEqual(
                game._high_score_path,
                expected_data_directory / HIGH_SCORE_FILENAME,
            )
            for path in (game._settings_path, game._high_score_path):
                self.assertTrue(path.is_absolute())
                self.assertNotIn(source_directory, path.parents)

    def test_unavailable_data_directory_uses_defaults_without_saving(self) -> None:
        """Failed data-directory preparation keeps the game on defaults."""
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.dict(
                    os.environ,
                    {"LOCALAPPDATA": str(Path(directory) / "local")},
                ),
                patch("game.application.prepare_user_data_directory", return_value=False),
                patch("game.application.load_settings") as load_settings_mock,
                patch("game.application.load_high_score") as load_high_score_mock,
                patch("game.application.GameWindow"),
                patch("game.application.AudioController"),
            ):
                game = Game()

            self.assertEqual(game._settings, default_settings())
            self.assertEqual(game._high_score, 0)
            self.assertFalse(game._persistence_enabled)
            load_settings_mock.assert_not_called()
            load_high_score_mock.assert_not_called()
            with patch("game.application.save_settings") as save_settings_mock:
                self.assertFalse(game._save_settings_update(default_settings()))
            save_settings_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
