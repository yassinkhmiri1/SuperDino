"""Tests for settings validation and persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from config import DEFAULT_DUCK_KEYS, DEFAULT_JUMP_KEYS
from core.settings import (
    KeyBindings,
    Settings,
    adjust_volume,
    bind_key,
    clear_key_binding,
    default_settings,
    load_settings,
    music_volume_for_percentage,
    save_settings,
    reset_key_bindings,
    settings_from_dict,
    toggle_mute,
    validate_settings,
)

class SettingsPersistenceTests(unittest.TestCase):
    """Tests for JSON settings round trips and fallback behavior."""

    def test_settings_round_trip_is_atomic(self) -> None:
        """Saved settings reload exactly and leave no temporary file."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = Settings(
                key_bindings=KeyBindings(
                    jump=("space", "up"),
                    duck=("down", "s"),
                ),
                music_volume=40,
                effects_volume=90,
                muted=True,
            )

            save_settings(settings, path)

            self.assertEqual(load_settings(path), settings)
            self.assertEqual(
                sorted(item.name for item in path.parent.iterdir()),
                ["settings.json"],
            )

    def test_three_key_jump_defaults_round_trip(self) -> None:
        """The required three-key Jump defaults remain valid in stored JSON."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"

            save_settings(default_settings(), path)

            self.assertEqual(load_settings(path), default_settings())

    def test_missing_or_corrupt_settings_fall_back_to_defaults(self) -> None:
        """Missing and malformed settings return defaults with warnings."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            with self.assertLogs("core.settings", level="WARNING"):
                self.assertEqual(load_settings(path), default_settings())

            path.write_text("{not json", encoding="utf-8")
            with self.assertLogs("core.settings", level="WARNING"):
                self.assertEqual(load_settings(path), default_settings())

    def test_invalid_documents_fall_back_to_defaults(self) -> None:
        """Invalid settings content is warned about and ignored on load."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            invalid_documents = (
                {"extra": True},
                {
                    "key_bindings": {"jump": ["space"], "duck": ["s"]},
                    "music_volume": 35,
                    "effects_volume": 80,
                    "muted": False,
                },
                {
                    "key_bindings": {"jump": ["space"], "unknown": ["s"]},
                    "music_volume": 30,
                    "effects_volume": 80,
                    "muted": False,
                },
            )
            for document in invalid_documents:
                with self.subTest(document=document):
                    path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertLogs("core.settings", level="WARNING"):
                        self.assertEqual(load_settings(path), default_settings())


class SettingsValidationTests(unittest.TestCase):
    """Tests for rejecting invalid settings and bindings."""

    def test_invalid_volume_values_are_rejected(self) -> None:
        """Volumes must be integer percentages in configured increments."""
        for value in (-10, 110, 35, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_settings(replace(default_settings(), music_volume=value))

    def test_music_volume_percentage_maps_to_capped_mixer_level(self) -> None:
        """The music slider maps linearly to the configured safe mixer cap."""
        self.assertEqual(music_volume_for_percentage(0), 0.0)
        self.assertEqual(music_volume_for_percentage(50), 0.175)
        self.assertEqual(music_volume_for_percentage(100), 0.35)
        self.assertAlmostEqual(music_volume_for_percentage(70), 0.245)
        for value in (-1, 101, True, 50.0):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    music_volume_for_percentage(value)

    def test_duplicate_and_reserved_keys_are_rejected(self) -> None:
        """A key cannot serve two actions or reserved navigation controls."""
        with self.assertRaisesRegex(ValueError, "already assigned"):
            validate_settings(
                Settings(key_bindings=KeyBindings(jump=("space",), duck=("space",)))
            )
        for reserved_key in ("escape", "enter", "return"):
            with self.subTest(reserved_key=reserved_key):
                with self.assertRaisesRegex(ValueError, "Reserved"):
                    validate_settings(
                        Settings(
                            key_bindings=KeyBindings(
                                jump=(reserved_key,),
                                duck=DEFAULT_DUCK_KEYS,
                            )
                        )
                    )

    def test_unknown_key_name_and_action_are_rejected(self) -> None:
        """Unknown stable key names and action names are invalid."""
        with self.assertRaisesRegex(ValueError, "Unknown key name"):
            validate_settings(
                Settings(
                    key_bindings=KeyBindings(
                        jump=("not-a-key",),
                        duck=DEFAULT_DUCK_KEYS,
                    )
                )
            )
        data = {
            "key_bindings": {
                "jump": list(DEFAULT_JUMP_KEYS),
                "duck": list(DEFAULT_DUCK_KEYS),
                "fly": ["f"],
            },
            "music_volume": default_settings().music_volume,
            "effects_volume": default_settings().effects_volume,
            "muted": False,
        }
        with self.assertRaisesRegex(ValueError, "fields mismatch"):
            settings_from_dict(data)

    def test_default_bindings_match_requested_defaults(self) -> None:
        """Required three-key Jump defaults are accepted as the sole exception."""
        settings = default_settings()

        self.assertEqual(settings.key_bindings.jump, ("space", "up", "z"))
        self.assertEqual(settings.key_bindings.duck, ("down", "s"))
        self.assertEqual(settings.key_bindings.jump, DEFAULT_JUMP_KEYS)
        self.assertEqual(settings.key_bindings.duck, DEFAULT_DUCK_KEYS)
        self.assertEqual(validate_settings(settings), settings)
        with self.assertRaisesRegex(ValueError, "three-key Jump defaults"):
            validate_settings(
                Settings(
                    key_bindings=KeyBindings(
                        jump=("space", "up", "z", "x"),
                        duck=DEFAULT_DUCK_KEYS,
                    )
                )
            )

    def test_reset_to_defaults_returns_immutable_defaults(self) -> None:
        """Callers can reset a modified settings value to the defaults."""
        modified = Settings(music_volume=50, muted=True)

        reset = default_settings()

        self.assertNotEqual(modified, reset)
        self.assertEqual(reset, Settings())

    def test_binding_slots_replace_append_and_respect_custom_limit(self) -> None:
        """Primary slots replace and the empty second slot appends a key."""
        defaults = default_settings()

        jump = bind_key(defaults, "jump", 0, "x")
        self.assertEqual(jump.key_bindings.jump, ("x", "up"))
        duck = bind_key(default_settings(), "duck", 1, "w")
        self.assertEqual(duck.key_bindings.duck, ("down", "w"))
        replaced = bind_key(duck, "duck", 1, "q")
        self.assertEqual(replaced.key_bindings.duck, ("down", "q"))

    def test_binding_rejects_reserved_duplicate_and_unknown_keys(self) -> None:
        """Invalid key assignments leave validation failures explicit."""
        for key, message in (
            ("escape", "Reserved"),
            ("space", "already assigned"),
            ("not-a-key", "Unknown key name"),
        ):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, message):
                    bind_key(default_settings(), "duck", 0, key)

    def test_clear_binding_preserves_one_key_and_reset_only_changes_controls(
        self,
    ) -> None:
        """Bindings can be cleared without clearing the last key or sound."""
        modified = replace(
            default_settings(),
            key_bindings=KeyBindings(jump=("x", "y"), duck=("down",)),
            music_volume=50,
            muted=True,
        )

        cleared = clear_key_binding(modified, "jump", 1)
        self.assertEqual(cleared.key_bindings.jump, ("x",))
        with self.assertRaisesRegex(ValueError, "at least one"):
            clear_key_binding(cleared, "jump", 0)

        reset = reset_key_bindings(modified)
        self.assertEqual(reset.key_bindings, default_settings().key_bindings)
        self.assertEqual(reset.music_volume, 50)
        self.assertTrue(reset.muted)

    def test_volume_adjustment_steps_and_clamps(self) -> None:
        """Sound volumes change in configured increments and stay in range."""
        defaults = default_settings()

        self.assertEqual(adjust_volume(defaults, "music_volume", 1).music_volume, 80)
        self.assertEqual(adjust_volume(defaults, "effects_volume", -1).effects_volume, 70)
        self.assertEqual(
            adjust_volume(replace(defaults, music_volume=100), "music_volume", 1)
            .music_volume,
            100,
        )
        self.assertEqual(
            adjust_volume(replace(defaults, effects_volume=0), "effects_volume", -1)
            .effects_volume,
            0,
        )

    def test_mute_toggle_preserves_volume_values(self) -> None:
        """Mute toggles independently of the saved music and effects levels."""
        defaults = default_settings()

        muted = toggle_mute(defaults)

        self.assertTrue(muted.muted)
        self.assertEqual(muted.music_volume, defaults.music_volume)
        self.assertEqual(muted.effects_volume, defaults.effects_volume)
        self.assertFalse(toggle_mute(muted).muted)


if __name__ == "__main__":
    unittest.main()
