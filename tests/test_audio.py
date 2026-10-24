"""Tests for audio controller setup and safe music startup."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

from audio.controller import AudioController
from config import (
    DEFAULT_EFFECTS_VOLUME,
    DEFAULT_MUSIC_VOLUME,
    MUSIC_FADE_IN_MILLISECONDS,
    MUSIC_FADE_OUT_MILLISECONDS,
    MUSIC_FILE_PATH,
    MUSIC_MAX_VOLUME,
    VOLUME_MAX,
)
from core.settings import music_volume_for_percentage

class AudioControllerTests(unittest.TestCase):
    """Tests for exact theme loading and continuous playback setup."""

    def test_theme_loads_and_loops_at_default_settings_volume(self) -> None:
        """The named theme uses the configured default level and loops forever."""
        mixer = Mock()
        fake_pygame = ModuleType("pygame")
        fake_pygame.mixer = mixer
        music_volume = music_volume_for_percentage(DEFAULT_MUSIC_VOLUME)

        with patch.dict(sys.modules, {"pygame": fake_pygame}):
            audio = AudioController(
                music_volume,
                DEFAULT_EFFECTS_VOLUME / VOLUME_MAX,
            )
            try:
                mixer.music.load.assert_called_once_with(str(MUSIC_FILE_PATH))
                mixer.music.set_volume.assert_called_once_with(music_volume)
                mixer.music.play.assert_called_once_with(loops=-1)
                self.assertTrue(audio._music_started)
            finally:
                audio.close()

    def test_game_over_fades_out_and_restart_fades_in(self) -> None:
        """Game-state fade methods call the mixer with configured durations."""
        mixer = Mock()
        fake_pygame = ModuleType("pygame")
        fake_pygame.mixer = mixer

        with patch.dict(sys.modules, {"pygame": fake_pygame}):
            audio = AudioController()
            try:
                audio.fade_out_music()
                mixer.music.fadeout.assert_called_once_with(
                    MUSIC_FADE_OUT_MILLISECONDS
                )

                audio.fade_in_music()
                self.assertEqual(
                    mixer.music.play.call_args_list[-1].kwargs,
                    {
                        "loops": -1,
                        "fade_ms": MUSIC_FADE_IN_MILLISECONDS,
                    },
                )
            finally:
                audio.close()

    def test_music_and_effect_volumes_mute_and_restore(self) -> None:
        """Mute silences both channels and unmute restores the configured levels."""
        mixer = Mock()
        effects = [Mock(), Mock(), Mock()]
        mixer.Sound.side_effect = effects
        fake_pygame = ModuleType("pygame")
        fake_pygame.mixer = mixer

        with patch.dict(sys.modules, {"pygame": fake_pygame}):
            audio = AudioController(0.2, 0.8)
            try:
                audio.set_volumes(0.2, 0.8, True)
                mixer.music.set_volume.assert_called_with(0.0)
                for effect in effects:
                    effect.set_volume.assert_called_with(0.0)

                audio.set_volumes(0.2, 0.8, False)
                mixer.music.set_volume.assert_called_with(0.2)
                for effect in effects:
                    effect.set_volume.assert_called_with(0.8)
            finally:
                audio.close()

    def test_music_volume_is_capped_at_safe_maximum(self) -> None:
        """Controller never applies music above the configured cap."""
        mixer = Mock()
        fake_pygame = ModuleType("pygame")
        fake_pygame.mixer = mixer

        with patch.dict(sys.modules, {"pygame": fake_pygame}):
            audio = AudioController(1.0, 0.8)
            try:
                mixer.music.set_volume.assert_called_once_with(MUSIC_MAX_VOLUME)
                audio.set_volumes(1.0, 0.8, False)
                mixer.music.set_volume.assert_called_with(MUSIC_MAX_VOLUME)
            finally:
                audio.close()

    def test_missing_music_file_warns_and_keeps_effects_available(self) -> None:
        """Missing theme music warns but effects still load normally."""
        mixer = Mock()
        fake_pygame = ModuleType("pygame")
        fake_pygame.mixer = mixer
        with tempfile.TemporaryDirectory() as directory:
            missing_music = Path(directory) / "missing.ogg"
            with (
                patch.dict(sys.modules, {"pygame": fake_pygame}),
                patch("audio.controller.MUSIC_FILE_PATH", missing_music),
                self.assertLogs("audio.controller", level="WARNING") as logs,
            ):
                audio = AudioController()
                try:
                    self.assertFalse(audio._music_started)
                    mixer.music.load.assert_not_called()
                    self.assertEqual(mixer.Sound.call_count, 3)
                    self.assertTrue(any("Theme music is missing" in line for line in logs.output))
                finally:
                    audio.close()

    def test_unavailable_mixer_warns_and_does_not_raise(self) -> None:
        """Mixer initialization failure leaves the game able to continue."""
        mixer = Mock()
        mixer.init.side_effect = RuntimeError("mixer unavailable")
        fake_pygame = ModuleType("pygame")
        fake_pygame.mixer = mixer

        with (
            patch.dict(sys.modules, {"pygame": fake_pygame}),
            self.assertLogs("audio.controller", level="WARNING") as logs,
        ):
            audio = AudioController()
            audio.close()

        self.assertTrue(
            any("Audio mixer unavailable" in line for line in logs.output)
        )


if __name__ == "__main__":
    unittest.main()
