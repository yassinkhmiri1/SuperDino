"""Optional music and sound-effect playback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from config import (
    DEATH_SOUND_PATH,
    JUMP_SOUND_PATH,
    MUSIC_FADE_IN_MILLISECONDS,
    MUSIC_FADE_OUT_MILLISECONDS,
    MUSIC_FILE_PATH,
    MUSIC_MAX_VOLUME,
    POINT_SOUND_PATH,
    EFFECTS_VOLUME,
    MUSIC_VOLUME,
)

logger = logging.getLogger(__name__)


class _Sound(Protocol):
    """Small interface for a mixer sound effect."""

    def set_volume(self, volume: float) -> None:
        """Set the sound effect volume."""

    def play(self) -> object | None:
        """Play the sound effect."""


class _Music(Protocol):
    """Small interface for mixer music playback."""

    def load(self, filename: str) -> None:
        """Load a music file."""

    def play(self, loops: int = 0, fade_ms: int = 0) -> None:
        """Start music playback."""

    def set_volume(self, volume: float) -> None:
        """Set the music volume."""

    def fadeout(self, time: int) -> None:
        """Fade out and stop the music."""

    def stop(self) -> None:
        """Stop music playback."""


class _Mixer(Protocol):
    """Small interface for mixer lifecycle operations."""

    music: _Music

    def init(self) -> None:
        """Initialize the audio mixer."""

    def Sound(self, file: str | Path) -> _Sound:
        """Load a sound effect."""

    def quit(self) -> None:
        """Shut down the audio mixer."""


class AudioController:
    """Load and play optional game music and effects.

    Mixer initialization is deliberately isolated here so audio failures never
    prevent the game from running silently.
    """

    def __init__(
        self,
        music_volume: float = MUSIC_VOLUME,
        effects_volume: float = EFFECTS_VOLUME,
        muted: bool = False,
    ) -> None:
        """Initialize the mixer and load available audio assets."""
        self._music_volume = self._validate_music_volume(music_volume)
        self._effects_volume = self._validate_volume(effects_volume)
        if not isinstance(muted, bool):
            raise ValueError("muted must be a boolean")
        self._muted = muted
        self._mixer: _Mixer | None = None
        self._sounds: dict[str, _Sound] = {}
        self._closed = False
        self._music_started = False

        try:
            from pygame import mixer

            self._mixer = mixer
            mixer.init()
        except Exception:
            logger.warning("Audio mixer unavailable; continuing silently", exc_info=True)
            self._mixer = None
            self._warn_if_music_missing()
            return

        self._load_effect("jump", JUMP_SOUND_PATH)
        self._load_effect("point", POINT_SOUND_PATH)
        self._load_effect("death", DEATH_SOUND_PATH)
        self._start_music_if_available()

    def set_volumes(
        self,
        music_volume: float,
        effects_volume: float,
        muted: bool,
    ) -> None:
        """Set music/effects volumes and mute state immediately."""
        self._music_volume = self._validate_music_volume(music_volume)
        self._effects_volume = self._validate_volume(effects_volume)
        if not isinstance(muted, bool):
            raise ValueError("muted must be a boolean")
        self._muted = muted
        if self._mixer is None or self._closed:
            return
        try:
            self._mixer.music.set_volume(
                0.0 if self._muted else self._music_volume
            )
        except Exception:
            logger.warning("Could not update background music volume", exc_info=True)
        for sound in self._sounds.values():
            try:
                sound.set_volume(
                    0.0 if self._muted else self._effects_volume
                )
            except Exception:
                logger.warning("Could not update sound effect volume", exc_info=True)

    def play_jump(self) -> None:
        """Play the jump effect if it is available."""
        self._play_effect("jump")

    def play_point(self) -> None:
        """Play the point effect if it is available."""
        self._play_effect("point")

    def play_death(self) -> None:
        """Play the death effect if it is available."""
        self._play_effect("death")

    def fade_out_music(self) -> None:
        """Fade out and stop background music at game over."""
        if self._mixer is None or not self._music_started or self._closed:
            return
        try:
            self._mixer.music.fadeout(MUSIC_FADE_OUT_MILLISECONDS)
        except Exception:
            logger.warning("Could not fade out background music", exc_info=True)

    def fade_in_music(self) -> None:
        """Restart looping background music with a short fade-in."""
        if self._mixer is None or not self._music_started or self._closed:
            return
        try:
            self._mixer.music.play(
                loops=-1,
                fade_ms=MUSIC_FADE_IN_MILLISECONDS,
            )
        except Exception:
            logger.warning("Could not fade in background music", exc_info=True)

    def close(self) -> None:
        """Stop music and release the mixer without interrupting game shutdown."""
        if self._closed:
            return
        self._closed = True
        if self._mixer is None:
            return
        try:
            self._mixer.music.stop()
        except Exception:
            logger.warning("Could not stop music cleanly", exc_info=True)
        try:
            self._mixer.quit()
        except Exception:
            logger.warning("Could not shut down the audio mixer cleanly", exc_info=True)

    def _load_effect(self, name: str, path: Path) -> None:
        """Load and configure one available sound effect.

        Args:
            name: Internal effect name.
            path: Audio file path.
        """
        if self._mixer is None:
            return
        try:
            sound = self._mixer.Sound(path)
            sound.set_volume(self._effective_effects_volume)
        except Exception:
            logger.warning(
                "Sound effect unavailable; continuing silently: %s",
                path,
                exc_info=True,
            )
            return
        self._sounds[name] = sound

    def _start_music_if_available(self) -> None:
        """Load the named theme and start looping at the configured volume."""
        if self._mixer is None:
            return
        if not MUSIC_FILE_PATH.is_file():
            logger.warning(
                "Theme music is missing; continuing silently: %s",
                MUSIC_FILE_PATH,
            )
            return
        try:
            self._mixer.music.load(str(MUSIC_FILE_PATH))
            self._mixer.music.set_volume(self._effective_music_volume)
            self._mixer.music.play(loops=-1)
            self._music_started = True
        except Exception:
            logger.warning(
                "Theme music unavailable; continuing without background music: %s",
                MUSIC_FILE_PATH,
                exc_info=True,
            )

    def _warn_if_music_missing(self) -> None:
        """Log that theme music is absent when audio initialization failed."""
        if not MUSIC_FILE_PATH.is_file():
            logger.warning(
                "Theme music is missing; continuing silently: %s",
                MUSIC_FILE_PATH,
            )

    def _play_effect(self, name: str) -> None:
        """Play an effect without allowing mixer errors to reach the game loop.

        Args:
            name: Internal effect name.
        """
        sound = self._sounds.get(name)
        if sound is None or self._closed:
            return
        try:
            sound.play()
        except Exception:
            logger.warning("Could not play %s sound effect", name, exc_info=True)

    @property
    def _effective_music_volume(self) -> float:
        """Return effective music volume after applying mute."""
        return 0.0 if self._muted else self._music_volume

    @property
    def _effective_effects_volume(self) -> float:
        """Return effective effects volume after applying mute."""
        return 0.0 if self._muted else self._effects_volume

    @staticmethod
    def _validate_volume(volume: float) -> float:
        """Validate a normalized floating-point volume."""
        if isinstance(volume, bool) or not isinstance(volume, (int, float)):
            raise ValueError("volume must be a number between zero and one")
        if not 0.0 <= volume <= 1.0:
            raise ValueError("volume must be between zero and one")
        return float(volume)

    @staticmethod
    def _validate_music_volume(volume: float) -> float:
        """Validate and cap normalized music volume below the effects level."""
        return min(
            MUSIC_MAX_VOLUME,
            AudioController._validate_volume(volume),
        )
