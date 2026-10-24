"""Shared game state type."""

from __future__ import annotations

from typing import Literal

GameState = Literal[
    "MENU",
    "SETTINGS_CONTROLS",
    "SETTINGS_SOUND",
    "CONFIRM_RESET",
    "RUNNING",
    "PAUSED",
    "GAME_OVER",
]
