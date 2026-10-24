"""Validated settings and atomic JSON persistence."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, Literal

from config import (
    DEFAULT_DUCK_KEYS,
    DEFAULT_EFFECTS_VOLUME,
    DEFAULT_JUMP_KEYS,
    DEFAULT_MUSIC_VOLUME,
    DEFAULT_SOUND_MUTED,
    MAX_KEYS_PER_ACTION,
    MUSIC_BASE_GAIN,
    MUSIC_MAX_VOLUME,
    SETTINGS_VOLUME_ROUNDING_PRECISION,
    RESERVED_SETTING_KEYS,
    SETTING_ACTION_NAMES,
    SUPPORTED_SETTING_KEY_NAMES,
    VOLUME_MAX,
    VOLUME_MIN,
    VOLUME_STEP,
)

logger = logging.getLogger(__name__)

_ROOT_FIELDS: Final[frozenset[str]] = frozenset(
    ("key_bindings", "music_volume", "effects_volume", "muted")
)
_ACTION_FIELDS: Final[frozenset[str]] = frozenset(SETTING_ACTION_NAMES)
SettingAction = Literal["jump", "duck"]
VolumeSetting = Literal["music_volume", "effects_volume"]


@dataclass(frozen=True, slots=True)
class KeyBindings:
    """Stable key names assigned to gameplay actions."""

    jump: tuple[str, ...] = DEFAULT_JUMP_KEYS
    duck: tuple[str, ...] = DEFAULT_DUCK_KEYS


@dataclass(frozen=True, slots=True)
class Settings:
    """User-adjustable controls and sound settings."""

    key_bindings: KeyBindings = KeyBindings()
    music_volume: int = DEFAULT_MUSIC_VOLUME
    effects_volume: int = DEFAULT_EFFECTS_VOLUME
    muted: bool = DEFAULT_SOUND_MUTED


DEFAULT_SETTINGS: Final[Settings] = Settings()


def default_settings() -> Settings:
    """Return the default settings value."""
    return DEFAULT_SETTINGS


def validate_settings(settings: Settings) -> Settings:
    """Validate all settings and return them unchanged.

    Raises:
        ValueError: If any setting is invalid.
    """
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a Settings instance")
    if not isinstance(settings.key_bindings, KeyBindings):
        raise ValueError("key_bindings must be a KeyBindings instance")
    _validate_action_bindings(
        {
            "jump": settings.key_bindings.jump,
            "duck": settings.key_bindings.duck,
        }
    )
    _validate_volume("music_volume", settings.music_volume)
    _validate_volume("effects_volume", settings.effects_volume)
    if not isinstance(settings.muted, bool):
        raise ValueError("muted must be a boolean")
    return settings


def bind_key(
    settings: Settings,
    action: SettingAction,
    slot: int,
    key: str,
) -> Settings:
    """Bind a key to an action slot and validate the resulting settings.

    Args:
        settings: Current validated user settings.
        action: Gameplay action receiving the key.
        slot: Zero-based key slot; slot one can append a second key.
        key: Stable, pygame-independent key name.

    Returns:
        Updated validated settings.

    Raises:
        ValueError: If the action, slot, key, or resulting bindings are invalid.
    """
    validate_settings(settings)
    if action not in _ACTION_FIELDS:
        raise ValueError(f"Unknown key-binding action: {action}")
    if (
        not isinstance(slot, int)
        or isinstance(slot, bool)
        or not 0 <= slot < MAX_KEYS_PER_ACTION
    ):
        raise ValueError(f"Invalid key-binding slot: {slot!r}")

    current = getattr(settings.key_bindings, action)
    if len(current) == len(DEFAULT_JUMP_KEYS):
        updated = (
            (key, current[1])
            if slot == 0
            else (current[0], key)
        )
    elif slot < len(current):
        updated = (*current[:slot], key, *current[slot + 1 :])
    elif slot == len(current) and len(current) < MAX_KEYS_PER_ACTION:
        updated = (*current, key)
    else:
        raise ValueError(f"{action} has no available key slot {slot + 1}")

    return validate_settings(
        replace(
            settings,
            key_bindings=replace(settings.key_bindings, **{action: updated}),
        )
    )


def clear_key_binding(
    settings: Settings,
    action: SettingAction,
    slot: int,
) -> Settings:
    """Remove a key from an action while preserving at least one binding."""
    validate_settings(settings)
    if action not in _ACTION_FIELDS:
        raise ValueError(f"Unknown key-binding action: {action}")
    if (
        not isinstance(slot, int)
        or isinstance(slot, bool)
        or not 0 <= slot < MAX_KEYS_PER_ACTION
    ):
        raise ValueError(f"Invalid key-binding slot: {slot!r}")

    current = getattr(settings.key_bindings, action)
    if slot >= len(current):
        raise ValueError(f"{action} key slot {slot + 1} is empty")
    if len(current) <= 1:
        raise ValueError(f"{action} must retain at least one key")
    updated = (*current[:slot], *current[slot + 1 :])
    return validate_settings(
        replace(
            settings,
            key_bindings=replace(settings.key_bindings, **{action: updated}),
        )
    )


def reset_key_bindings(settings: Settings) -> Settings:
    """Restore default gameplay keys without changing sound settings."""
    validate_settings(settings)
    return replace(settings, key_bindings=KeyBindings())


def adjust_volume(
    settings: Settings,
    volume_setting: VolumeSetting,
    direction: int,
) -> Settings:
    """Adjust a volume by one configured step, clamped to its valid range."""
    validate_settings(settings)
    if volume_setting not in ("music_volume", "effects_volume"):
        raise ValueError(f"Unknown volume setting: {volume_setting}")
    if direction == 0:
        return settings
    current = getattr(settings, volume_setting)
    adjusted = min(
        VOLUME_MAX,
        max(VOLUME_MIN, current + (VOLUME_STEP if direction > 0 else -VOLUME_STEP)),
    )
    return validate_settings(replace(settings, **{volume_setting: adjusted}))


def toggle_mute(settings: Settings) -> Settings:
    """Return settings with mute toggled."""
    validate_settings(settings)
    return replace(settings, muted=not settings.muted)


def music_volume_for_percentage(volume_percent: int) -> float:
    """Map a menu percentage to the capped mixer music volume.

    Args:
        volume_percent: Integer slider value from zero to one hundred.

    Returns:
        Mixer volume between zero and ``MUSIC_MAX_VOLUME``.

    Raises:
        ValueError: If the percentage is not an integer in the supported range.
    """
    if (
        isinstance(volume_percent, bool)
        or not isinstance(volume_percent, int)
        or not VOLUME_MIN <= volume_percent <= VOLUME_MAX
    ):
        raise ValueError(
            f"music volume percentage must be an integer from "
            f"{VOLUME_MIN} to {VOLUME_MAX}"
        )
    return round(
        min(
            MUSIC_MAX_VOLUME,
            volume_percent
            / VOLUME_MAX
            * MUSIC_MAX_VOLUME
            * MUSIC_BASE_GAIN,
        ),
        SETTINGS_VOLUME_ROUNDING_PRECISION,
    )


def settings_from_dict(data: object) -> Settings:
    """Parse and validate settings from decoded JSON data.

    Raises:
        ValueError: If the document has unknown, missing, or invalid values.
    """
    if not isinstance(data, dict):
        raise ValueError("settings document must be a JSON object")
    _require_exact_fields(data, _ROOT_FIELDS, "settings")

    bindings_data = data["key_bindings"]
    if not isinstance(bindings_data, dict):
        raise ValueError("key_bindings must be a JSON object")
    _require_exact_fields(bindings_data, _ACTION_FIELDS, "key_bindings")
    settings = Settings(
        key_bindings=KeyBindings(
            jump=_parse_key_list(bindings_data["jump"], "jump"),
            duck=_parse_key_list(bindings_data["duck"], "duck"),
        ),
        music_volume=data["music_volume"],
        effects_volume=data["effects_volume"],
        muted=data["muted"],
    )
    return validate_settings(settings)


def load_settings(path: Path) -> Settings:
    """Load settings, using defaults when the file is missing or invalid.

    Args:
        path: JSON settings file location.

    Returns:
        Valid settings from disk or defaults.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return settings_from_dict(data)
    except FileNotFoundError:
        logger.warning("Settings file is missing; using defaults: %s", path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        logger.warning(
            "Settings file is invalid; using defaults: %s",
            path,
            exc_info=True,
        )
    return default_settings()


def save_settings(settings: Settings, path: Path) -> None:
    """Atomically save validated settings as JSON.

    Args:
        settings: Settings to persist.
        path: Destination JSON file location.

    Raises:
        ValueError: If any setting is invalid.
        OSError: If the file cannot be saved or replaced.
    """
    validate_settings(settings)
    document = {
        "key_bindings": {
            "jump": list(settings.key_bindings.jump),
            "duck": list(settings.key_bindings.duck),
        },
        "music_volume": settings.music_volume,
        "effects_volume": settings.effects_volume,
        "muted": settings.muted,
    }
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(document, temporary_file, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except OSError:
        logger.exception("Could not save settings file: %s", path)
        raise
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                logger.warning(
                    "Could not remove temporary settings file: %s",
                    temporary_path,
                    exc_info=True,
                )

    logger.info("Saved settings: %s", path)


def _validate_volume(name: str, value: object) -> None:
    """Validate a volume percentage against the configured step."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not VOLUME_MIN <= value <= VOLUME_MAX
        or value % VOLUME_STEP != 0
    ):
        raise ValueError(
            f"{name} must be an integer from {VOLUME_MIN} to {VOLUME_MAX} "
            f"in steps of {VOLUME_STEP}"
        )


def _parse_key_list(value: object, action: str) -> tuple[str, ...]:
    """Parse a JSON key list and validate its basic shape."""
    if not isinstance(value, list):
        raise ValueError(f"{action} keys must be a JSON list")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{action} keys must be strings")
    keys = tuple(value)
    if not 1 <= len(keys) <= MAX_KEYS_PER_ACTION and not (
        action == "jump" and keys == DEFAULT_JUMP_KEYS
    ):
        raise ValueError(
            f"{action} must have between one and {MAX_KEYS_PER_ACTION} keys, "
            "except for the required three-key Jump defaults"
        )
    return keys


def _validate_action_bindings(bindings: dict[str, tuple[str, ...]]) -> None:
    """Validate known actions, key names, limits, and binding conflicts."""
    if frozenset(bindings) != _ACTION_FIELDS:
        raise ValueError("key bindings contain unknown or missing actions")

    owners: dict[str, str] = {}
    for action, keys in bindings.items():
        if not isinstance(keys, tuple):
            raise ValueError(f"{action} keys must be a tuple")
        if not 1 <= len(keys) <= MAX_KEYS_PER_ACTION and not (
            action == "jump" and keys == DEFAULT_JUMP_KEYS
        ):
            raise ValueError(
                f"{action} must have between one and {MAX_KEYS_PER_ACTION} keys, "
                "except for the required three-key Jump defaults"
            )
        for key in keys:
            if not isinstance(key, str):
                raise ValueError(f"Unknown key name for {action}: {key!r}")
            if key in RESERVED_SETTING_KEYS:
                raise ValueError(f"Reserved key cannot be bound: {key}")
            if key not in SUPPORTED_SETTING_KEY_NAMES:
                raise ValueError(f"Unknown key name for {action}: {key!r}")
            if key in owners:
                raise ValueError(
                    f"Key {key!r} is already assigned to {owners[key]}"
                )
            owners[key] = action


def _require_exact_fields(
    document: dict[object, object],
    expected: frozenset[str],
    name: str,
) -> None:
    """Reject missing or unknown object fields."""
    if frozenset(document) != expected:
        unknown = frozenset(document) - expected
        missing = expected - frozenset(document)
        raise ValueError(
            f"{name} fields mismatch (unknown={sorted(unknown, key=str)}, "
            f"missing={sorted(missing)})"
        )
