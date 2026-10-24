"""Named configuration values for SuperDino."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

from core.themes import Theme

WINDOW_TITLE: Final[str] = "SuperDino"
WINDOW_WIDTH: Final[int] = 800
WINDOW_HEIGHT: Final[int] = 400
WINDOW_SIZE: Final[tuple[int, int]] = (WINDOW_WIDTH, WINDOW_HEIGHT)
THEME_CHANGE_SCORE: Final[int] = 500
MINIMUM_TEXT_CONTRAST_RATIO: Final[float] = 4.5
# Shortened after transition sampling found low obstacle contrast near mid-fade.
THEME_FADE_SECONDS: Final[float] = 0.75
# The 26% switch maximizes worst-case contrast at the requested five samples.
THEME_SPRITE_SWITCH_PROGRESS: Final[float] = 0.26
# Set to a theme index while checking gameplay rendering; None uses score selection.
DEBUG_FORCE_THEME_INDEX: Final[int | None] = None
FRAME_RATE_LIMIT: Final[int] = 60
MAX_PHYSICS_STEP_SECONDS: Final[float] = 1.0 / 120.0
# Cap simulation catch-up after a stalled frame so gameplay remains responsive.
MAX_FRAME_SECONDS: Final[float] = 0.1
MILLISECONDS_PER_SECOND: Final[float] = 1_000.0
WINDOW_BOTTOM_GROUND_OFFSET: Final[int] = 50
GROUND_LINE_Y: Final[int] = WINDOW_HEIGHT - WINDOW_BOTTOM_GROUND_OFFSET
GROUND_TRACK_LINE_OFFSET_Y: Final[int] = 10
GROUND_SCROLL_SPEED_PIXELS_PER_SECOND: Final[float] = 330.0
SCORE_PER_PIXEL: Final[float] = 0.03
SPEED_STEP_SCORE: Final[int] = 100
SPEED_GROWTH_FACTOR: Final[float] = 1.06
MAX_SPEED: Final[float] = GROUND_SCROLL_SPEED_PIXELS_PER_SECOND * 3.0
# DEBUG: Temporarily enable this to show the live speed diagnostics.
DEBUG_OVERLAY: Final[bool] = False
DEBUG_OVERLAY_LEFT: Final[int] = 8
DEBUG_OVERLAY_TOP: Final[int] = 44
DEBUG_OVERLAY_LINE_SPACING: Final[int] = 18
DEBUG_OVERLAY_FONT_SIZE: Final[int] = 16
SCORE_HUD_FONT_SIZE: Final[int] = 22
SCORE_HUD_RIGHT_MARGIN: Final[int] = 24
SCORE_HUD_TOP: Final[int] = 18
SCORE_DISPLAY_DIGITS: Final[int] = 5
PLAYTIME_LABEL: Final[str] = "PLAYTIME"
PLAYTIME_HUD_LEFT_MARGIN: Final[int] = 24
PLAYTIME_HUD_TOP: Final[int] = SCORE_HUD_TOP
SECONDS_PER_MINUTE: Final[int] = 60
PAUSE_MESSAGE: Final[str] = "PAUSED"
PAUSE_MESSAGE_FONT_SIZE: Final[int] = 36
PAUSE_MESSAGE_TOP: Final[int] = WINDOW_HEIGHT // 2 - 90
PAUSE_INSTRUCTIONS: Final[str] = "Up/Down select  Enter choose  Esc resume"
PAUSE_INSTRUCTIONS_TOP: Final[int] = PAUSE_MESSAGE_TOP + 50
PAUSE_ITEM_TOPS: Final[tuple[int, int]] = (205, 265)
GAME_OVER_RESTART_MESSAGE: Final[str] = "PRESS ENTER TO RESTART"
TITLE_MESSAGE: Final[str] = "SUPER DINO"
TITLE_FONT_SIZE: Final[int] = 48
TITLE_MESSAGE_TOP: Final[int] = 65
MENU_HIGH_SCORE_TOP: Final[int] = 125
MENU_ITEM_TOPS: Final[tuple[int, int, int, int, int]] = (
    165,
    205,
    245,
    285,
    325,
)
MENU_ITEM_FONT_SIZE: Final[int] = 26
MENU_ITEM_HORIZONTAL_PADDING: Final[int] = 24
MENU_ITEM_VERTICAL_PADDING: Final[int] = 4
CONTROLS_TITLE_TOP: Final[int] = 24
CONTROLS_ROW_TOPS: Final[tuple[int, int, int, int]] = (130, 190, 265, 320)
CONTROLS_INSTRUCTION_TOP: Final[int] = 80
CONTROLS_MESSAGE_TOP: Final[int] = 365
CONTROLS_FONT_SIZE: Final[int] = 23
CONTROLS_INSTRUCTION_FONT_SIZE: Final[int] = 19
CONTROLS_MESSAGE_FONT_SIZE: Final[int] = 18
CONTROLS_HITBOX_WIDTH: Final[int] = WINDOW_WIDTH - 80
CONTROLS_HITBOX_HEIGHT: Final[int] = 44
CONTROLS_INSTRUCTIONS: Final[str] = (
    "Up/Down select  Left/Right slot  Enter bind  Delete clear  Esc back"
)
CONTROLS_DEFAULT_LIMIT_MESSAGE: Final[str] = (
    "Jump's three default keys become two when customized."
)
SOUND_TITLE_TOP: Final[int] = CONTROLS_TITLE_TOP
SOUND_INSTRUCTION_TOP: Final[int] = CONTROLS_INSTRUCTION_TOP
SOUND_ROW_TOPS: Final[tuple[int, int, int, int]] = (140, 200, 260, 320)
SOUND_MESSAGE_TOP: Final[int] = CONTROLS_MESSAGE_TOP
SOUND_HITBOX_WIDTH: Final[int] = CONTROLS_HITBOX_WIDTH
SOUND_HITBOX_HEIGHT: Final[int] = CONTROLS_HITBOX_HEIGHT
SOUND_INSTRUCTIONS: Final[str] = (
    "Left/Right adjust volume  Enter or click to change  Esc back"
)
RESET_CONFIRMATION_MESSAGE_TOP: Final[int] = 155
RESET_CONFIRMATION_ITEM_TOPS: Final[tuple[int, int]] = (225, 275)
POINT_SOUND_INTERVAL_POINTS: Final[int] = 100
EFFECTS_VOLUME: Final[float] = 0.8
MUSIC_VOLUME: Final[float] = 0.25
MUSIC_MAX_VOLUME: Final[float] = 0.35
MUSIC_BASE_GAIN: Final[float] = 1.0
MUSIC_FADE_OUT_MILLISECONDS: Final[int] = 500
MUSIC_FADE_IN_MILLISECONDS: Final[int] = 500
DINO_CENTER_X: Final[int] = 80
DINO_JUMP_INITIAL_VELOCITY: Final[float] = -900.0
DINO_GRAVITY: Final[float] = 2_000.0
PHYSICS_ACCELERATION_COEFFICIENT: Final[float] = 0.5
DINO_RUN_ANIMATION_INTERVAL_SECONDS: Final[float] = 0.08
DINO_DUCK_ANIMATION_INTERVAL_SECONDS: Final[float] = 0.08
OBSTACLE_ANIMATION_INTERVAL_SECONDS: Final[float] = 0.18
ANIMATION_SPEED_SCALE: Final[float] = 1.0
BIRD_VERTICAL_SLOPE_PER_HORIZONTAL_PIXEL: Final[float] = 0.04
OBSTACLE_MIN_GAP_SECONDS: Final[float] = 1.2
OBSTACLE_MAX_GAP_SECONDS: Final[float] = 2.0
OBSTACLE_BIRD_SPAWN_CHANCE: Final[float] = 0.2
OBSTACLE_CULL_MARGIN: Final[int] = 120
BIRD_HEIGHT_OFFSETS: Final[tuple[int, ...]] = (45, 85, 125)
OBSTACLE_SPAWN_OFFSET: Final[int] = 60
GAME_OVER_CENTER_X: Final[int] = WINDOW_WIDTH // 2
KEY_BINDINGS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "pause": "escape",
        "restart": "return",
    }
)
TRACK_ASSET_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / "Other" / "Track.png"
)
CLOUD_ASSET_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / "Other" / "Cloud.png"
)
CLOUD_SOURCE_COLOR: Final[tuple[int, int, int]] = (218, 218, 218)
CLOUD_SCROLL_SPEED_PIXELS_PER_SECOND: Final[float] = 38.0
CLOUD_ANCHOR_POSITIONS: Final[tuple[tuple[int, int], ...]] = (
    (350, 110),
    (590, 165),
    (710, 220),
)
DINO_RUN_FRAME_PATHS: Final[tuple[Path, Path]] = (
    Path(__file__).resolve().parent / "assets" / "Dino" / "DinoRun1.png",
    Path(__file__).resolve().parent / "assets" / "Dino" / "DinoRun2.png",
)
DINO_JUMP_FRAME_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / "Dino" / "DinoJump.png"
)
DINO_DUCK_FRAME_PATHS: Final[tuple[Path, Path]] = (
    Path(__file__).resolve().parent / "assets" / "Dino" / "DinoDuck1.png",
    Path(__file__).resolve().parent / "assets" / "Dino" / "DinoDuck2.png",
)
CACTUS_FRAME_PATHS: Final[tuple[Path, ...]] = (
    Path(__file__).resolve().parent / "assets" / "Cactus" / "SmallCactus1.png",
    Path(__file__).resolve().parent / "assets" / "Cactus" / "SmallCactus2.png",
    Path(__file__).resolve().parent / "assets" / "Cactus" / "SmallCactus3.png",
    Path(__file__).resolve().parent / "assets" / "Cactus" / "LargeCactus1.png",
    Path(__file__).resolve().parent / "assets" / "Cactus" / "LargeCactus2.png",
    Path(__file__).resolve().parent / "assets" / "Cactus" / "LargeCactus3.png",
)
BIRD_FRAME_PATHS: Final[tuple[Path, Path]] = (
    Path(__file__).resolve().parent / "assets" / "Bird" / "Bird1.png",
    Path(__file__).resolve().parent / "assets" / "Bird" / "Bird2.png",
)
DINO_DEAD_FRAME_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / "Dino" / "DinoDead.png"
)
DINO_START_FRAME_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / "Dino" / "DinoStart.png"
)
GAME_OVER_IMAGE_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / "Other" / "GameOver.png"
)
HIGH_SCORE_FILENAME: Final[str] = "high_score.txt"
SETTINGS_FILENAME: Final[str] = "settings.json"
DEFAULT_JUMP_KEYS: Final[tuple[str, ...]] = ("space", "up", "z")
DEFAULT_DUCK_KEYS: Final[tuple[str, ...]] = ("down", "s")
SETTING_ACTION_NAMES: Final[tuple[str, ...]] = ("jump", "duck")
RESERVED_SETTING_KEYS: Final[tuple[str, ...]] = ("escape", "enter", "return")
VOLUME_MIN: Final[int] = 0
VOLUME_MAX: Final[int] = 100
VOLUME_STEP: Final[int] = 10
SETTINGS_VOLUME_ROUNDING_PRECISION: Final[int] = 6
DEFAULT_MUSIC_VOLUME: Final[int] = 70
DEFAULT_EFFECTS_VOLUME: Final[int] = 80
DEFAULT_SOUND_MUTED: Final[bool] = False
MAX_KEYS_PER_ACTION: Final[int] = 2
SUPPORTED_SETTING_KEY_NAMES: Final[frozenset[str]] = frozenset(
    (*"abcdefghijklmnopqrstuvwxyz", *"0123456789")
) | frozenset(
    (
        "space",
        "up",
        "down",
        "left",
        "right",
        "tab",
        "backspace",
        "delete",
        "insert",
        "home",
        "end",
        "pageup",
        "pagedown",
        "capslock",
        "minus",
        "equals",
        "leftbracket",
        "rightbracket",
        "backslash",
        "semicolon",
        "apostrophe",
        "comma",
        "period",
        "slash",
        "grave",
        *(f"f{number}" for number in range(1, 13)),
    )
)
MENU_LABELS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "start": "Start",
        "jump": "Jump",
        "duck": "Duck",
        "controls": "Controls",
        "sound": "Sound",
        "music_volume": "Music volume",
        "effects_volume": "Effects volume",
        "muted": "Muted",
        "on": "On",
        "off": "Off",
        "reset_high_score": "Reset High Score",
        "quit": "Quit",
        "resume": "Resume",
        "back_to_menu": "Back to menu",
        "confirm_reset": "Reset high score?",
        "yes": "Yes",
        "no": "No",
        "reset_to_defaults": "Reset to defaults",
        "high_score": "HIGH SCORE",
    }
)
AUDIO_ASSET_DIRECTORY: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / "audio"
)
MUSIC_FILE_NAME: Final[str] = "SuperDinoTheme.ogg"
MUSIC_FILE_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "assets" / MUSIC_FILE_NAME
)
JUMP_SOUND_PATH: Final[Path] = AUDIO_ASSET_DIRECTORY / "jump.wav"
POINT_SOUND_PATH: Final[Path] = AUDIO_ASSET_DIRECTORY / "point.wav"
DEATH_SOUND_PATH: Final[Path] = AUDIO_ASSET_DIRECTORY / "die.wav"
GAME_OVER_IMAGE_TOP_Y: Final[int] = WINDOW_HEIGHT // 2 - 100
GAME_OVER_RESTART_MESSAGE_TOP: Final[int] = WINDOW_HEIGHT // 2 + 25
DINO_RUN_SPRITE_SIZE: Final[tuple[int, int]] = (87, 94)
DINO_JUMP_SPRITE_SIZE: Final[tuple[int, int]] = (88, 94)
DINO_DUCK_SPRITE_SIZE: Final[tuple[int, int]] = (116, 60)
CACTUS_SPRITE_SIZES: Final[tuple[tuple[int, int], ...]] = (
    (40, 71),
    (68, 71),
    (105, 71),
    (48, 95),
    (99, 95),
    (102, 95),
)
BIRD_COLLISION_SPRITE_SIZE: Final[tuple[int, int]] = (97, 68)
DINO_HITBOX_INSET_X: Final[int] = 8
DINO_HITBOX_INSET_TOP: Final[int] = 8
DINO_HITBOX_INSET_BOTTOM: Final[int] = 4
CACTUS_HITBOX_INSET_X: Final[int] = 4
CACTUS_HITBOX_INSET_TOP: Final[int] = 5
CACTUS_HITBOX_INSET_BOTTOM: Final[int] = 2
BIRD_HITBOX_INSET_X: Final[int] = 7
BIRD_HITBOX_INSET_TOP: Final[int] = 8
BIRD_HITBOX_INSET_BOTTOM: Final[int] = 4
LOG_FOLDER_NAME: Final[str] = "logs"
LOG_FILENAME: Final[str] = "superdino.log"
LOG_MAX_BYTES: Final[int] = 1_000_000
LOG_BACKUP_COUNT: Final[int] = 5
SUCCESS_EXIT_CODE: Final[int] = 0

DAY: Final[Theme] = Theme(
    name="DAY",
    background_color=(247, 247, 247),
    ground_tint=(83, 83, 83),
    text_color=(55, 55, 55),
    secondary_text_color=(95, 95, 95),
    sprite_treatment="NONE",
    cloud_tint=(218, 218, 218),
)
SUNSET: Final[Theme] = Theme(
    name="SUNSET",
    background_color=(255, 180, 110),
    gradient_color=(205, 170, 225),
    ground_tint=(90, 61, 82),
    text_color=(45, 30, 52),
    secondary_text_color=(75, 52, 82),
    sprite_treatment="NONE",
    cloud_tint=(238, 183, 180),
)
NIGHT: Final[Theme] = Theme(
    name="NIGHT",
    background_color=(18, 22, 35),
    ground_tint=(172, 172, 172),
    text_color=(245, 245, 245),
    secondary_text_color=(195, 205, 220),
    sprite_treatment="INVERT",
    cloud_tint=(105, 116, 145),
)
SNOW: Final[Theme] = Theme(
    name="SNOW",
    background_color=(220, 232, 240),
    ground_tint=(83, 93, 105),
    text_color=(42, 58, 72),
    secondary_text_color=(75, 90, 105),
    sprite_treatment="NONE",
    cloud_tint=(250, 252, 255),
)
THEMES: Final[tuple[Theme, ...]] = (DAY, SUNSET, NIGHT, SNOW)
