"""Fixed-size pygame window for the game."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, replace

import pygame

from config import (
    ANIMATION_SPEED_SCALE,
    BIRD_FRAME_PATHS,
    BIRD_HEIGHT_OFFSETS,
    CACTUS_FRAME_PATHS,
    CLOUD_ANCHOR_POSITIONS,
    CLOUD_ASSET_PATH,
    CLOUD_SCROLL_SPEED_PIXELS_PER_SECOND,
    CLOUD_SOURCE_COLOR,
    CONTROLS_FONT_SIZE,
    CONTROLS_HITBOX_HEIGHT,
    CONTROLS_HITBOX_WIDTH,
    CONTROLS_INSTRUCTIONS,
    CONTROLS_INSTRUCTION_FONT_SIZE,
    CONTROLS_INSTRUCTION_TOP,
    CONTROLS_MESSAGE_FONT_SIZE,
    CONTROLS_MESSAGE_TOP,
    CONTROLS_ROW_TOPS,
    CONTROLS_TITLE_TOP,
    DEBUG_FORCE_THEME_INDEX,
    DEBUG_OVERLAY,
    DEBUG_OVERLAY_FONT_SIZE,
    DEBUG_OVERLAY_LEFT,
    DEBUG_OVERLAY_LINE_SPACING,
    DEBUG_OVERLAY_TOP,
    DINO_CENTER_X,
    DINO_DEAD_FRAME_PATH,
    DINO_DUCK_ANIMATION_INTERVAL_SECONDS,
    DINO_DUCK_FRAME_PATHS,
    DINO_JUMP_FRAME_PATH,
    DINO_RUN_ANIMATION_INTERVAL_SECONDS,
    DINO_RUN_FRAME_PATHS,
    DINO_START_FRAME_PATH,
    FRAME_RATE_LIMIT,
    GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
    GAME_OVER_CENTER_X,
    GAME_OVER_IMAGE_PATH,
    GAME_OVER_IMAGE_TOP_Y,
    GAME_OVER_RESTART_MESSAGE,
    GAME_OVER_RESTART_MESSAGE_TOP,
    GROUND_LINE_Y,
    GROUND_TRACK_LINE_OFFSET_Y,
    KEY_BINDINGS,
    MILLISECONDS_PER_SECOND,
    MENU_ITEM_FONT_SIZE,
    MENU_ITEM_HORIZONTAL_PADDING,
    MENU_ITEM_TOPS,
    MENU_ITEM_VERTICAL_PADDING,
    MENU_LABELS,
    MINIMUM_TEXT_CONTRAST_RATIO,
    OBSTACLE_ANIMATION_INTERVAL_SECONDS,
    PAUSE_ITEM_TOPS,
    PAUSE_MESSAGE_FONT_SIZE,
    PLAYTIME_HUD_LEFT_MARGIN,
    PLAYTIME_HUD_TOP,
    PLAYTIME_LABEL,
    SCORE_DISPLAY_DIGITS,
    SCORE_HUD_FONT_SIZE,
    SCORE_HUD_RIGHT_MARGIN,
    SCORE_HUD_TOP,
    RESET_CONFIRMATION_ITEM_TOPS,
    SOUND_HITBOX_HEIGHT,
    SOUND_HITBOX_WIDTH,
    SOUND_INSTRUCTIONS,
    SOUND_INSTRUCTION_TOP,
    SOUND_MESSAGE_TOP,
    SOUND_ROW_TOPS,
    SOUND_TITLE_TOP,
    SECONDS_PER_MINUTE,
    TITLE_FONT_SIZE,
    THEME_FADE_SECONDS,
    THEME_SPRITE_SWITCH_PROGRESS,
    TRACK_ASSET_PATH,
    THEMES,
    WINDOW_HEIGHT,
    WINDOW_SIZE,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from core.menu import (
    CONTROLS_ITEMS,
    MENU_ITEMS,
    PAUSE_ITEMS,
    RESET_CONFIRMATION_ITEMS,
    SOUND_ITEMS,
)
from core.obstacles import Obstacle, ObstacleKind, bird_vertical_offset
from core.player import PlayerState
from core.settings import KeyBindings, Settings
from core.state import GameState
from core.themes import Theme, blend_themes, contrast_ratio, theme_for_score
from ui.key_names import pygame_key_code, readable_key_name, stable_key_name
from ui.screens import draw_confirm, draw_menu, draw_pause

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InputFrame:
    """Input and window status for one game-loop iteration.

    Attributes:
        running: Whether the game should continue running.
        jump_pressed: Whether the jump binding was newly pressed.
        duck_held: Whether the duck binding is held.
        menu_direction: Keyboard navigation direction; negative means up.
        menu_selection: Menu item index selected by mouse input, if any.
        menu_activate: Whether a menu item was clicked.
        control_key_pressed: Whether a key was pressed on the controls screen.
        control_key_name: Stable settings name for the pressed key, if supported.
        control_slot_direction: Left/Right direction for binding-slot selection.
        delete_pressed: Whether Delete was newly pressed.
    """

    running: bool
    jump_pressed: bool
    duck_held: bool
    pause_pressed: bool = False
    restart_pressed: bool = False
    menu_direction: int = 0
    menu_selection: int | None = None
    menu_activate: bool = False
    control_key_pressed: bool = False
    control_key_name: str | None = None
    control_slot_direction: int = 0
    delete_pressed: bool = False


@dataclass(frozen=True, slots=True)
class _SpriteSet:
    """Cached sprite surfaces used when rendering one theme."""

    run_frames: tuple[pygame.Surface, ...]
    jump_frame: pygame.Surface
    duck_frames: tuple[pygame.Surface, ...]
    start_frame: pygame.Surface
    dead_frame: pygame.Surface
    cactus_frames: tuple[pygame.Surface, ...]
    bird_frames: tuple[pygame.Surface, ...]
    game_over_image: pygame.Surface


class GroundAssetError(RuntimeError):
    """Raised when the required ground track image cannot be loaded."""


class DinoAssetError(RuntimeError):
    """Raised when a required dino image cannot be loaded."""


class ObstacleAssetError(RuntimeError):
    """Raised when a required obstacle image cannot be loaded."""


class GameOverAssetError(RuntimeError):
    """Raised when a required game-over image cannot be loaded."""


class CloudAssetError(RuntimeError):
    """Raised when the cloud image cannot be loaded or has no visible pixels."""


class GameWindow:
    """Manage the game display and basic window events.

    Raises:
        DinoAssetError: If dino animation images cannot be loaded.
        GameOverAssetError: If a game-over image cannot be loaded.
        GroundAssetError: If the ground track cannot be loaded.
        ObstacleAssetError: If an obstacle image cannot be loaded.
        pygame.error: If pygame cannot initialize or create the display.
    """

    def __init__(self, key_bindings: KeyBindings = KeyBindings()) -> None:
        """Initialize a centered, fixed-size game window.

        Raises:
            DinoAssetError: If a dino animation image cannot be loaded.
            CloudAssetError: If the cloud image cannot be loaded or has no visible pixels.
            GameOverAssetError: If a game-over image cannot be loaded.
            GroundAssetError: If the ground track cannot be loaded.
            ObstacleAssetError: If an obstacle image cannot be loaded.
            pygame.error: If pygame cannot initialize or create the display.
        """
        if (
            DEBUG_FORCE_THEME_INDEX is not None
            and not 0 <= DEBUG_FORCE_THEME_INDEX < len(THEMES)
        ):
            raise ValueError(
                "DEBUG_FORCE_THEME_INDEX must be None or a valid theme index"
            )
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

        try:
            pygame.display.init()
            self._surface = pygame.display.set_mode(WINDOW_SIZE)
            pygame.display.set_caption(WINDOW_TITLE)
            try:
                self._track = pygame.image.load(TRACK_ASSET_PATH).convert_alpha()
            except (OSError, pygame.error) as error:
                logger.exception("Could not load ground track: %s", TRACK_ASSET_PATH)
                raise GroundAssetError(
                    f"Unable to load required ground track: {TRACK_ASSET_PATH}"
                ) from error
            self._track_alpha_mask = self._create_alpha_mask(self._track)
            self._theme_backgrounds = {
                theme.name: self._create_theme_background(theme)
                for theme in THEMES
            }
            self._track_cache: tuple[
                tuple[int, int, int],
                pygame.Surface,
            ] | None = None
            self._tracks_by_theme = {
                theme.name: self._create_theme_track(theme)
                for theme in THEMES
            }
            try:
                self._run_frames = tuple(
                    pygame.image.load(path).convert_alpha()
                    for path in DINO_RUN_FRAME_PATHS
                )
                self._jump_frame = pygame.image.load(
                    DINO_JUMP_FRAME_PATH
                ).convert_alpha()
                self._duck_frames = tuple(
                    pygame.image.load(path).convert_alpha()
                    for path in DINO_DUCK_FRAME_PATHS
                )
                self._start_frame = pygame.image.load(
                    DINO_START_FRAME_PATH
                ).convert_alpha()
            except (OSError, pygame.error) as error:
                logger.exception("Could not load required dino images")
                raise DinoAssetError(
                    f"Unable to load a required dino image: {error}"
                ) from error
            try:
                self._cactus_frames = tuple(
                    pygame.image.load(path).convert_alpha()
                    for path in CACTUS_FRAME_PATHS
                )
                self._bird_frames = tuple(
                    pygame.image.load(path).convert_alpha()
                    for path in BIRD_FRAME_PATHS
                )
            except (OSError, pygame.error) as error:
                logger.exception("Could not load required obstacle images")
                raise ObstacleAssetError(
                    f"Unable to load a required obstacle image: {error}"
                ) from error
            try:
                self._dead_frame = pygame.image.load(
                    DINO_DEAD_FRAME_PATH
                ).convert_alpha()
                self._game_over_image = pygame.image.load(
                    GAME_OVER_IMAGE_PATH
                ).convert_alpha()
            except (OSError, pygame.error) as error:
                logger.exception("Could not load required game-over images")
                raise GameOverAssetError(
                    f"Unable to load a required game-over image: {error}"
                ) from error
            self._sprite_sets_by_theme = {
                theme.name: self._create_sprite_set(theme)
                for theme in THEMES
            }
            self._sprite_sets_by_treatment = {
                theme.sprite_treatment: self._sprite_sets_by_theme[theme.name]
                for theme in THEMES
            }
            try:
                cloud = pygame.image.load(CLOUD_ASSET_PATH).convert_alpha()
            except (OSError, pygame.error) as error:
                logger.exception("Could not load cloud image: %s", CLOUD_ASSET_PATH)
                raise CloudAssetError(
                    f"Unable to load cloud image: {CLOUD_ASSET_PATH}"
                ) from error
            self._cloud = self._crop_visible_surface(cloud)
            self._clouds_by_theme = {
                theme.name: self._tint_cloud(theme)
                for theme in THEMES
            }
            self._cloud_cache: tuple[
                tuple[int, int, int],
                pygame.Surface,
            ] | None = None
            self._cloud_offset = 0.0
            self.reset_theme_transition()
        except pygame.error:
            logger.exception("Could not initialize the game window")
            pygame.display.quit()
            raise
        except (
            CloudAssetError,
            DinoAssetError,
            GameOverAssetError,
            GroundAssetError,
            ObstacleAssetError,
        ):
            pygame.display.quit()
            raise

        self._clock = pygame.time.Clock()
        pygame.font.init()
        self._score_font = pygame.font.Font(None, SCORE_HUD_FONT_SIZE)
        self._pause_font = pygame.font.Font(None, PAUSE_MESSAGE_FONT_SIZE)
        self._title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self._menu_font = pygame.font.Font(None, MENU_ITEM_FONT_SIZE)
        self._controls_font = pygame.font.Font(None, CONTROLS_FONT_SIZE)
        self._controls_instruction_font = pygame.font.Font(
            None,
            CONTROLS_INSTRUCTION_FONT_SIZE,
        )
        self._controls_message_font = pygame.font.Font(
            None,
            CONTROLS_MESSAGE_FONT_SIZE,
        )
        self._menu_item_rects = self._create_menu_item_rects()
        self._pause_item_rects = self._create_pause_item_rects()
        self._confirmation_item_rects = self._create_confirmation_item_rects()
        self._controls_item_rects = self._create_controls_item_rects()
        self._sound_item_rects = self._create_sound_item_rects()
        self._debug_font = pygame.font.Font(None, DEBUG_OVERLAY_FONT_SIZE)
        self._pause_key = pygame.key.key_code(KEY_BINDINGS["pause"])
        self._restart_key = pygame.key.key_code(KEY_BINDINGS["restart"])
        self._held_keys: set[int] = set()
        self.set_key_bindings(key_bindings)
        self._dino_animation_elapsed = 0.0
        self._dino_animation_index = 0
        self._obstacle_animation_elapsed = 0.0
        self._obstacle_animation_index = 0
        logger.info("Opened fixed-size window: %s", WINDOW_SIZE)

    def set_key_bindings(self, key_bindings: KeyBindings) -> None:
        """Update the gameplay keys used to collect jump and duck input."""
        jump_keys = frozenset(
            pygame_key_code(name) for name in key_bindings.jump
        )
        duck_keys = frozenset(
            pygame_key_code(name) for name in key_bindings.duck
        )
        self._jump_keys = jump_keys
        self._duck_keys = duck_keys
        self._action_keys = (
            self._jump_keys
            | self._duck_keys
            | frozenset((self._pause_key, self._restart_key))
        )
        self._held_keys.intersection_update(self._action_keys)

    @property
    def ground_width(self) -> int:
        """Return the ground image width.

        Returns:
            The width of one ground tile, in pixels.
        """
        return self._track.get_width()

    def tick(self) -> float:
        """Limit the loop and return elapsed time in seconds.

        Returns:
            The time since the preceding tick, in seconds.
        """
        elapsed_milliseconds = self._clock.tick(FRAME_RATE_LIMIT)
        return elapsed_milliseconds / MILLISECONDS_PER_SECOND

    def process_events(self, game_state: GameState) -> InputFrame:
        """Collect window, gameplay, and current-screen input for this frame.

        Args:
            game_state: Current game screen, used for mouse hit testing.

        Returns:
            The window and player input state for this frame.
        """
        running = True
        jump_pressed = False
        pause_pressed = False
        restart_pressed = False
        menu_direction = 0
        menu_selection: int | None = None
        menu_activate = False
        control_key_pressed = False
        control_key_name: str | None = None
        control_slot_direction = 0
        delete_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    menu_direction = -1
                elif event.key == pygame.K_DOWN:
                    menu_direction = 1
                elif event.key == pygame.K_LEFT:
                    control_slot_direction = -1
                elif event.key == pygame.K_RIGHT:
                    control_slot_direction = 1
                if game_state == "SETTINGS_CONTROLS" and not getattr(
                    event,
                    "repeat",
                    False,
                ):
                    control_key_pressed = True
                    control_key_name = stable_key_name(event.key)
                    delete_pressed = event.key == pygame.K_DELETE
                if event.key in self._action_keys and event.key not in self._held_keys:
                    jump_pressed = event.key in self._jump_keys
                    pause_pressed = event.key == self._pause_key
                    restart_pressed = event.key == self._restart_key
                if event.key in self._action_keys:
                    self._held_keys.add(event.key)
            elif event.type == pygame.MOUSEMOTION:
                hovered_item = self._menu_item_at(event.pos, game_state)
                if hovered_item is not None:
                    menu_selection = hovered_item
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_item = self._menu_item_at(event.pos, game_state)
                if clicked_item is not None:
                    menu_selection = clicked_item
                    menu_activate = True
            elif event.type == pygame.KEYUP and event.key in self._action_keys:
                self._held_keys.discard(event.key)
            elif event.type == pygame.WINDOWFOCUSLOST:
                self._held_keys.clear()
        return InputFrame(
            running=running,
            jump_pressed=jump_pressed,
            duck_held=bool(self._duck_keys & self._held_keys),
            pause_pressed=pause_pressed,
            restart_pressed=restart_pressed,
            menu_direction=menu_direction,
            menu_selection=menu_selection,
            menu_activate=menu_activate,
            control_key_pressed=control_key_pressed,
            control_key_name=control_key_name,
            control_slot_direction=control_slot_direction,
            delete_pressed=delete_pressed,
        )

    def render(
        self,
        ground_offset: float,
        player: PlayerState,
        obstacles: tuple[Obstacle, ...],
        delta_seconds: float,
        game_state: GameState,
        score: int,
        high_score: int,
        playtime_seconds: float,
        debug_world_speed: float,
        debug_ground_speed: float,
        debug_obstacle_speed: float,
        debug_spawn_gap_seconds: float,
        menu_selected_index: int,
        pause_selected_index: int,
        confirmation_selected_index: int,
        controls_selected_index: int,
        controls_binding_slot: int,
        controls_listening: bool,
        controls_message: str,
        key_bindings: KeyBindings,
        sound_selected_index: int,
        settings: Settings,
    ) -> None:
        """Draw the window background, scrolling ground, and dino.

        Args:
            ground_offset: Horizontal offset into the repeating ground tile.
            player: Current pure movement state of the dino.
            obstacles: Current obstacles to draw.
            delta_seconds: Time elapsed since the previous frame, in seconds.
            game_state: Current explicit game state.
            score: Current run score.
            high_score: Best score loaded or achieved during this run.
            playtime_seconds: Elapsed active gameplay time for this run.
            debug_world_speed: World speed actually used by the simulation.
            debug_ground_speed: Speed actually used to scroll the ground.
            debug_obstacle_speed: Speed actually used to move obstacles.
            debug_spawn_gap_seconds: Remaining spawn gap in current-speed seconds.
            menu_selected_index: Zero-based selected main-menu item.
            pause_selected_index: Zero-based selected pause-menu item.
            confirmation_selected_index: Selected Yes/No reset answer index.
            controls_selected_index: Selected row on the controls screen.
            controls_binding_slot: Selected Jump or Duck binding slot.
            controls_listening: Whether a controls row is waiting for a key.
            controls_message: Current controls-screen instruction or status.
            key_bindings: Active user-configured gameplay bindings.
            sound_selected_index: Selected sound-settings row.
            settings: Active persisted settings.
        """
        if game_state in (
            "MENU",
            "CONFIRM_RESET",
            "SETTINGS_CONTROLS",
            "SETTINGS_SOUND",
        ):
            self.reset_theme_transition()
            theme = THEMES[0]
        else:
            target_theme = self._theme_for_render(game_state, score)
            theme = self._advance_theme_transition(target_theme, delta_seconds)
        if self._transition_elapsed >= THEME_FADE_SECONDS:
            self._track_cache = None
            self._cloud_cache = None
        sprite_set = self._sprite_sets_by_treatment[theme.sprite_treatment]
        self._draw_theme_background(theme)
        if game_state == "RUNNING":
            self._cloud_offset = (
                self._cloud_offset
                + CLOUD_SCROLL_SPEED_PIXELS_PER_SECOND * delta_seconds
            ) % (WINDOW_WIDTH + self._cloud.get_width())
        if game_state in ("RUNNING", "PAUSED", "GAME_OVER"):
            self._draw_clouds(theme)
        animation_rate_multiplier = (
            debug_world_speed
            / GROUND_SCROLL_SPEED_PIXELS_PER_SECOND
            * ANIMATION_SPEED_SCALE
        )
        animation_delta_seconds = delta_seconds * animation_rate_multiplier
        tile_x = -int(ground_offset)
        track_y = GROUND_LINE_Y - GROUND_TRACK_LINE_OFFSET_Y
        if self._transition_elapsed >= THEME_FADE_SECONDS:
            track = self._tracks_by_theme[theme.name]
        else:
            if (
                self._track_cache is None
                or self._track_cache[0] != theme.ground_tint
            ):
                self._track_cache = (
                    theme.ground_tint,
                    self._create_theme_track(theme),
                )
            track = self._track_cache[1]
        while tile_x < self._surface.get_width():
            self._surface.blit(track, (tile_x, track_y))
            tile_x += self.ground_width
        if game_state in (
            "MENU",
            "CONFIRM_RESET",
            "SETTINGS_CONTROLS",
            "SETTINGS_SOUND",
        ):
            dino_frame = sprite_set.start_frame
        elif game_state == "GAME_OVER":
            dino_frame = sprite_set.dead_frame
        elif game_state == "PAUSED":
            dino_frame = self._current_dino_frame(player, sprite_set)
        else:
            dino_frame = self._select_dino_frame(
                player,
                animation_delta_seconds,
                sprite_set,
            )
        dino_rect = dino_frame.get_rect(
            midbottom=(
                DINO_CENTER_X,
                int(GROUND_LINE_Y - player.ground_offset),
            )
        )
        self._surface.blit(dino_frame, dino_rect)
        if game_state == "RUNNING":
            self._advance_obstacle_animation(animation_delta_seconds)
        for obstacle in obstacles:
            obstacle_frame = self._obstacle_frame(
                obstacle.kind,
                obstacle.variant,
                sprite_set,
            )
            obstacle_rect = obstacle_frame.get_rect(
                midbottom=(
                    round(obstacle.x),
                    GROUND_LINE_Y - self._obstacle_height(obstacle),
                )
            )
            self._surface.blit(obstacle_frame, obstacle_rect)
        if game_state == "MENU":
            draw_menu(
                self._surface,
                self._title_font,
                self._menu_font,
                self._menu_item_rects,
                theme,
                high_score,
                menu_selected_index,
                self._theme_text_color,
            )
        elif game_state == "CONFIRM_RESET":
            draw_confirm(
                self._surface,
                self._title_font,
                self._menu_font,
                self._confirmation_item_rects,
                theme,
                confirmation_selected_index,
                self._theme_text_color,
            )
        elif game_state == "SETTINGS_CONTROLS":
            title_surface = self._title_font.render(
                MENU_LABELS["controls"],
                True,
                self._theme_text_color(
                    theme,
                    CONTROLS_TITLE_TOP,
                    theme.text_color,
                ),
            )
            title_rect = title_surface.get_rect(
                midtop=(
                    self._surface.get_width() // 2,
                    CONTROLS_TITLE_TOP,
                )
            )
            self._surface.blit(title_surface, title_rect)
            instructions = self._controls_instruction_font.render(
                CONTROLS_INSTRUCTIONS,
                True,
                self._theme_text_color(
                    theme,
                    CONTROLS_INSTRUCTION_TOP,
                    theme.text_color,
                ),
            )
            self._surface.blit(
                instructions,
                instructions.get_rect(
                    midtop=(
                        self._surface.get_width() // 2,
                        CONTROLS_INSTRUCTION_TOP,
                    )
                ),
            )
            for item_index, item in enumerate(CONTROLS_ITEMS):
                if item in ("jump", "duck"):
                    action_bindings = getattr(key_bindings, item)
                    selected_slot = controls_binding_slot
                    key_labels = [
                        readable_key_name(key_name)
                        for key_name in action_bindings
                    ]
                    if selected_slot >= len(action_bindings):
                        selected_key_label = "Empty"
                    else:
                        selected_key_label = key_labels[selected_slot]
                    other_key_labels = [
                        label
                        for slot_index, label in enumerate(key_labels)
                        if slot_index != selected_slot
                    ]
                    binding_text = (
                        f"{MENU_LABELS[item]} - slot {selected_slot + 1}: "
                        f"{selected_key_label}"
                    )
                    if other_key_labels:
                        binding_text += f"   Other: {', '.join(other_key_labels)}"
                else:
                    binding_text = MENU_LABELS[item]
                item_surface = self._controls_font.render(
                    binding_text,
                    True,
                    self._theme_text_color(
                        theme,
                        self._controls_item_rects[item_index].centery,
                        theme.secondary_text_color
                        if item_index == controls_selected_index
                        else theme.text_color,
                    ),
                )
                self._surface.blit(
                    item_surface,
                    item_surface.get_rect(
                        center=self._controls_item_rects[item_index].center
                    ),
                )
            message = (
                "Press a key to bind (Esc cancels)"
                if controls_listening
                else controls_message
            )
            message_surface = self._controls_message_font.render(
                message,
                True,
                self._theme_text_color(
                    theme,
                    CONTROLS_MESSAGE_TOP,
                    theme.text_color,
                ),
            )
            self._surface.blit(
                message_surface,
                message_surface.get_rect(
                    midtop=(
                        self._surface.get_width() // 2,
                        CONTROLS_MESSAGE_TOP,
                    )
                ),
            )
        elif game_state == "SETTINGS_SOUND":
            title_surface = self._title_font.render(
                MENU_LABELS["sound"],
                True,
                self._theme_text_color(
                    theme,
                    SOUND_TITLE_TOP,
                    theme.text_color,
                ),
            )
            self._surface.blit(
                title_surface,
                title_surface.get_rect(
                    midtop=(
                        self._surface.get_width() // 2,
                        SOUND_TITLE_TOP,
                    )
                ),
            )
            instructions = self._controls_instruction_font.render(
                SOUND_INSTRUCTIONS,
                True,
                self._theme_text_color(
                    theme,
                    SOUND_INSTRUCTION_TOP,
                    theme.text_color,
                ),
            )
            self._surface.blit(
                instructions,
                instructions.get_rect(
                    midtop=(
                        self._surface.get_width() // 2,
                        SOUND_INSTRUCTION_TOP,
                    )
                ),
            )
            sound_values = {
                "music_volume": f"{settings.music_volume}%",
                "effects_volume": f"{settings.effects_volume}%",
                "muted": MENU_LABELS["on"] if settings.muted else MENU_LABELS["off"],
                "back_to_menu": "",
            }
            for item_index, item in enumerate(SOUND_ITEMS):
                label = MENU_LABELS[item]
                value = sound_values[item]
                text = f"{label}: {value}" if value else label
                item_surface = self._controls_font.render(
                    text,
                    True,
                    self._theme_text_color(
                        theme,
                        self._sound_item_rects[item_index].centery,
                        theme.secondary_text_color
                        if item_index == sound_selected_index
                        else theme.text_color,
                    ),
                )
                self._surface.blit(
                    item_surface,
                    item_surface.get_rect(
                        center=self._sound_item_rects[item_index].center
                    ),
                )
            if controls_message:
                message_surface = self._controls_message_font.render(
                    controls_message,
                    True,
                    self._theme_text_color(
                        theme,
                        SOUND_MESSAGE_TOP,
                        theme.text_color,
                    ),
                )
                self._surface.blit(
                    message_surface,
                    message_surface.get_rect(
                        midtop=(
                            self._surface.get_width() // 2,
                            SOUND_MESSAGE_TOP,
                        )
                    ),
                )
        elif game_state == "GAME_OVER":
            game_over_rect = sprite_set.game_over_image.get_rect(
                midtop=(GAME_OVER_CENTER_X, GAME_OVER_IMAGE_TOP_Y)
            )
            self._surface.blit(sprite_set.game_over_image, game_over_rect)
        elif game_state == "PAUSED":
            draw_pause(
                self._surface,
                self._pause_font,
                self._controls_instruction_font,
                self._menu_font,
                self._pause_item_rects,
                theme,
                pause_selected_index,
                self._theme_text_color,
            )
        if game_state == "GAME_OVER":
            restart_surface = self._pause_font.render(
                GAME_OVER_RESTART_MESSAGE,
                True,
                self._theme_text_color(
                    theme,
                    GAME_OVER_RESTART_MESSAGE_TOP,
                    theme.text_color,
                ),
            )
            restart_rect = restart_surface.get_rect(
                midtop=(
                    self._surface.get_width() // 2,
                    GAME_OVER_RESTART_MESSAGE_TOP,
                )
            )
            self._surface.blit(restart_surface, restart_rect)
        if game_state not in (
            "MENU",
            "CONFIRM_RESET",
            "SETTINGS_CONTROLS",
            "SETTINGS_SOUND",
        ):
            score_surface = self._score_font.render(
                f"HI {high_score:0{SCORE_DISPLAY_DIGITS}d} "
                f"{score:0{SCORE_DISPLAY_DIGITS}d}",
                True,
                self._theme_text_color(theme, SCORE_HUD_TOP, theme.text_color),
            )
            score_rect = score_surface.get_rect(
                top=SCORE_HUD_TOP,
                right=self._surface.get_width() - SCORE_HUD_RIGHT_MARGIN,
            )
            self._surface.blit(score_surface, score_rect)
            playtime_minutes, playtime_remainder = divmod(
                int(playtime_seconds),
                SECONDS_PER_MINUTE,
            )
            playtime_surface = self._score_font.render(
                f"{PLAYTIME_LABEL} {playtime_minutes:02d}:{playtime_remainder:02d}",
                True,
                self._theme_text_color(theme, PLAYTIME_HUD_TOP, theme.text_color),
            )
            playtime_rect = playtime_surface.get_rect(
                top=PLAYTIME_HUD_TOP,
                left=PLAYTIME_HUD_LEFT_MARGIN,
            )
            self._surface.blit(playtime_surface, playtime_rect)
        # DEBUG: Temporary overlay to verify live speed and spawn values.
        if DEBUG_OVERLAY:
            debug_lines = (
                f"DEBUG score: {score}",
                f"world speed: {debug_world_speed:.2f} px/s",
                f"ground speed used: {debug_ground_speed:.2f} px/s",
                f"obstacle speed used: {debug_obstacle_speed:.2f} px/s",
                f"spawn gap remaining: {debug_spawn_gap_seconds:.2f} s",
                f"animation rate multiplier: {animation_rate_multiplier:.2f}x",
            )
            for line_index, line in enumerate(debug_lines):
                debug_surface = self._debug_font.render(
                    line,
                    True,
                    self._theme_text_color(
                        theme,
                        DEBUG_OVERLAY_TOP
                        + line_index * DEBUG_OVERLAY_LINE_SPACING,
                        theme.text_color,
                    ),
                )
                self._surface.blit(
                    debug_surface,
                    (
                        DEBUG_OVERLAY_LEFT,
                        DEBUG_OVERLAY_TOP
                        + line_index * DEBUG_OVERLAY_LINE_SPACING,
                    ),
                )
        pygame.display.flip()

    @staticmethod
    def _create_theme_background(theme: Theme) -> pygame.Surface:
        """Build a cached solid or vertical-gradient background surface."""
        background = pygame.Surface(WINDOW_SIZE)
        bottom_color = theme.gradient_color or theme.background_color
        if bottom_color == theme.background_color:
            background.fill(theme.background_color)
            return background

        last_y = WINDOW_HEIGHT - 1
        for y in range(WINDOW_HEIGHT):
            progress = y / last_y
            color = tuple(
                round(top + (bottom - top) * progress)
                for top, bottom in zip(
                    theme.background_color,
                    bottom_color,
                    strict=True,
                )
            )
            pygame.draw.line(background, color, (0, y), (WINDOW_WIDTH - 1, y))
        return background

    def _draw_theme_background(self, theme: Theme) -> None:
        """Draw a cached endpoint background or the current blended gradient."""
        if self._transition_elapsed >= THEME_FADE_SECONDS:
            background = self._theme_backgrounds.get(theme.name)
            if background is not None and background.get_at((0, 0))[:3] == (
                theme.background_color
            ):
                self._surface.blit(background, (0, 0))
                return

        bottom_color = theme.gradient_color or theme.background_color
        if bottom_color == theme.background_color:
            self._surface.fill(theme.background_color)
            return

        last_y = WINDOW_HEIGHT - 1
        for y in range(WINDOW_HEIGHT):
            progress = y / last_y
            color = (
                round(
                    theme.background_color[0]
                    + (bottom_color[0] - theme.background_color[0]) * progress
                ),
                round(
                    theme.background_color[1]
                    + (bottom_color[1] - theme.background_color[1]) * progress
                ),
                round(
                    theme.background_color[2]
                    + (bottom_color[2] - theme.background_color[2]) * progress
                ),
            )
            pygame.draw.line(
                self._surface,
                color,
                (0, y),
                (WINDOW_WIDTH - 1, y),
            )

    @staticmethod
    def _create_alpha_mask(source: pygame.Surface) -> pygame.Surface:
        """Create an opaque-white RGB mask preserving the source alpha channel."""
        mask = pygame.Surface(source.get_size(), pygame.SRCALPHA, 32)
        for y in range(source.get_height()):
            for x in range(source.get_width()):
                alpha = source.get_at((x, y)).a
                mask.set_at((x, y), (255, 255, 255, alpha))
        return mask

    def _create_theme_track(self, theme: Theme) -> pygame.Surface:
        """Create a ground track tinted for one theme."""
        track = pygame.Surface(self._track.get_size(), pygame.SRCALPHA, 32)
        track.fill((*theme.ground_tint, 255))
        track.blit(
            self._track_alpha_mask,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        return track

    def _create_sprite_set(self, theme: Theme) -> _SpriteSet:
        """Build one cached sprite set, inverting visible pixels when required."""
        if theme.sprite_treatment == "INVERT":
            recolor = self._invert_surface
            return _SpriteSet(
                run_frames=tuple(map(recolor, self._run_frames)),
                jump_frame=recolor(self._jump_frame),
                duck_frames=tuple(map(recolor, self._duck_frames)),
                start_frame=recolor(self._start_frame),
                dead_frame=recolor(self._dead_frame),
                cactus_frames=tuple(map(recolor, self._cactus_frames)),
                bird_frames=tuple(map(recolor, self._bird_frames)),
                game_over_image=recolor(self._game_over_image),
            )
        return _SpriteSet(
            run_frames=self._run_frames,
            jump_frame=self._jump_frame,
            duck_frames=self._duck_frames,
            start_frame=self._start_frame,
            dead_frame=self._dead_frame,
            cactus_frames=self._cactus_frames,
            bird_frames=self._bird_frames,
            game_over_image=self._game_over_image,
        )

    @staticmethod
    def _invert_surface(source: pygame.Surface) -> pygame.Surface:
        """Invert visible RGB pixels while preserving source alpha."""
        inverted = source.copy()
        for y in range(source.get_height()):
            for x in range(source.get_width()):
                red, green, blue, alpha = source.get_at((x, y))
                if alpha:
                    inverted.set_at(
                        (x, y),
                        (255 - red, 255 - green, 255 - blue, alpha),
                    )
        return inverted

    @staticmethod
    def _crop_visible_surface(source: pygame.Surface) -> pygame.Surface:
        """Crop transparent padding without changing the source image."""
        visible_bounds = source.get_bounding_rect(min_alpha=1)
        if visible_bounds.width == 0 or visible_bounds.height == 0:
            raise CloudAssetError("Cloud image has no visible pixels")
        return source.subsurface(visible_bounds).copy()

    def _tint_cloud(self, theme: Theme) -> pygame.Surface:
        """Create a theme-tinted version of the cropped cloud image."""
        cloud = self._cloud.copy()
        for y in range(cloud.get_height()):
            for x in range(cloud.get_width()):
                red, green, blue, alpha = self._cloud.get_at((x, y))
                if alpha == 0:
                    continue
                cloud.set_at(
                    (x, y),
                    (
                        min(
                            255,
                            round(red * theme.cloud_tint[0] / CLOUD_SOURCE_COLOR[0]),
                        ),
                        min(
                            255,
                            round(green * theme.cloud_tint[1] / CLOUD_SOURCE_COLOR[1]),
                        ),
                        min(
                            255,
                            round(blue * theme.cloud_tint[2] / CLOUD_SOURCE_COLOR[2]),
                        ),
                        alpha,
                    ),
                )
        return cloud

    def _draw_clouds(self, theme: Theme) -> None:
        """Draw slow clouds below the HUD, behind the ground and obstacles."""
        if self._transition_elapsed >= THEME_FADE_SECONDS:
            cloud = self._clouds_by_theme[theme.name]
        else:
            if (
                self._cloud_cache is None
                or self._cloud_cache[0] != theme.cloud_tint
            ):
                self._cloud_cache = (
                    theme.cloud_tint,
                    self._tint_cloud(theme),
                )
            cloud = self._cloud_cache[1]
        cloud_width = cloud.get_width()
        wrap_width = WINDOW_WIDTH + cloud_width
        for anchor_x, y in CLOUD_ANCHOR_POSITIONS:
            x = round((anchor_x - self._cloud_offset) % wrap_width) - cloud_width
            self._surface.blit(cloud, (x, y))

    def reset_theme_transition(self) -> None:
        """Reset the active theme and fade to DAY for a new game."""
        self._transition_from_theme = THEMES[0]
        self._transition_to_theme = THEMES[0]
        self._transition_elapsed = THEME_FADE_SECONDS

    def _advance_theme_transition(
        self,
        target_theme: Theme,
        delta_seconds: float,
    ) -> Theme:
        """Advance the transition timer and blend the current theme colors."""
        if target_theme.name != self._transition_to_theme.name:
            self._transition_from_theme = self._theme_at_transition_progress()
            self._transition_to_theme = target_theme
            self._transition_elapsed = 0.0
        else:
            self._transition_elapsed = min(
                THEME_FADE_SECONDS,
                self._transition_elapsed + delta_seconds,
            )

        if self._transition_elapsed >= THEME_FADE_SECONDS:
            return self._transition_to_theme

        progress = self._transition_elapsed / THEME_FADE_SECONDS
        blended = blend_themes(
            self._transition_from_theme,
            self._transition_to_theme,
            progress,
        )
        sprite_treatment = (
            self._transition_to_theme.sprite_treatment
            if progress >= THEME_SPRITE_SWITCH_PROGRESS
            else self._transition_from_theme.sprite_treatment
        )
        return replace(blended, sprite_treatment=sprite_treatment)

    def _theme_at_transition_progress(self) -> Theme:
        """Return the current blended theme without advancing elapsed time."""
        if self._transition_elapsed >= THEME_FADE_SECONDS:
            return self._transition_to_theme
        progress = self._transition_elapsed / THEME_FADE_SECONDS
        blended = blend_themes(
            self._transition_from_theme,
            self._transition_to_theme,
            progress,
        )
        sprite_treatment = (
            self._transition_to_theme.sprite_treatment
            if progress >= THEME_SPRITE_SWITCH_PROGRESS
            else self._transition_from_theme.sprite_treatment
        )
        return replace(blended, sprite_treatment=sprite_treatment)

    def _theme_text_color(
        self,
        theme: Theme,
        y: int,
        preferred_color: tuple[int, int, int],
    ) -> tuple[int, int, int]:
        """Keep transition text readable against the gradient at its screen row."""
        if self._transition_elapsed >= THEME_FADE_SECONDS:
            return preferred_color

        top_color = theme.background_color
        bottom_color = theme.gradient_color or top_color
        progress = min(1.0, max(0.0, y / max(1, WINDOW_HEIGHT - 1)))
        background = (
            round(top_color[0] + (bottom_color[0] - top_color[0]) * progress),
            round(top_color[1] + (bottom_color[1] - top_color[1]) * progress),
            round(top_color[2] + (bottom_color[2] - top_color[2]) * progress),
        )
        if (
            contrast_ratio(preferred_color, background)
            >= MINIMUM_TEXT_CONTRAST_RATIO
        ):
            return preferred_color

        black = (0, 0, 0)
        white = (255, 255, 255)
        return (
            black
            if contrast_ratio(black, background) >= contrast_ratio(white, background)
            else white
        )

    @staticmethod
    def _theme_for_render(game_state: GameState, score: int) -> Theme:
        """Use DAY on menu screens and the selected score theme in gameplay."""
        if game_state in (
            "MENU",
            "CONFIRM_RESET",
            "SETTINGS_CONTROLS",
            "SETTINGS_SOUND",
        ):
            return THEMES[0]
        if DEBUG_FORCE_THEME_INDEX is not None:
            return THEMES[DEBUG_FORCE_THEME_INDEX]
        return THEMES[theme_for_score(score)]

    def _create_menu_item_rects(self) -> tuple[pygame.Rect, ...]:
        """Create menu button rectangles shared by drawing and mouse input."""
        rectangles = []
        for item, top in zip(MENU_ITEMS, MENU_ITEM_TOPS, strict=True):
            label = self._menu_font.render(
                MENU_LABELS[item],
                True,
                THEMES[0].text_color,
            )
            rectangles.append(
                label.get_rect(
                    midtop=(self._surface.get_width() // 2, top)
                ).inflate(
                    MENU_ITEM_HORIZONTAL_PADDING,
                    MENU_ITEM_VERTICAL_PADDING,
                )
            )
        return tuple(rectangles)

    def _create_pause_item_rects(self) -> tuple[pygame.Rect, ...]:
        """Create pause-menu button rectangles for drawing and mouse input."""
        rectangles = []
        for item, top in zip(PAUSE_ITEMS, PAUSE_ITEM_TOPS, strict=True):
            label = self._menu_font.render(
                MENU_LABELS[item],
                True,
                THEMES[0].text_color,
            )
            rectangles.append(
                label.get_rect(
                    midtop=(self._surface.get_width() // 2, top)
                ).inflate(
                    MENU_ITEM_HORIZONTAL_PADDING,
                    MENU_ITEM_VERTICAL_PADDING,
                )
            )
        return tuple(rectangles)

    def _create_confirmation_item_rects(self) -> tuple[pygame.Rect, ...]:
        """Create Yes/No rectangles shared by confirmation drawing and input."""
        rectangles = []
        for item, top in zip(
            RESET_CONFIRMATION_ITEMS,
            RESET_CONFIRMATION_ITEM_TOPS,
            strict=True,
        ):
            label = self._menu_font.render(
                MENU_LABELS[item],
                True,
                THEMES[0].text_color,
            )
            rectangles.append(
                label.get_rect(
                    midtop=(self._surface.get_width() // 2, top)
                ).inflate(
                    MENU_ITEM_HORIZONTAL_PADDING,
                    MENU_ITEM_VERTICAL_PADDING,
                )
            )
        return tuple(rectangles)

    def _create_controls_item_rects(self) -> tuple[pygame.Rect, ...]:
        """Create controls-screen button rectangles for drawing and mouse input."""
        rectangles = []
        for top in CONTROLS_ROW_TOPS:
            rectangles.append(
                pygame.Rect(
                    0,
                    top,
                    CONTROLS_HITBOX_WIDTH,
                    CONTROLS_HITBOX_HEIGHT,
                )
            )
            rectangles[-1].centerx = self._surface.get_width() // 2
        return tuple(rectangles)

    def _create_sound_item_rects(self) -> tuple[pygame.Rect, ...]:
        """Create sound-screen hit boxes shared by drawing and mouse input."""
        rectangles = []
        for top in SOUND_ROW_TOPS:
            rectangle = pygame.Rect(
                0,
                top,
                SOUND_HITBOX_WIDTH,
                SOUND_HITBOX_HEIGHT,
            )
            rectangle.centerx = self._surface.get_width() // 2
            rectangles.append(rectangle)
        return tuple(rectangles)

    def _menu_item_at(
        self,
        position: tuple[int, int],
        game_state: GameState,
    ) -> int | None:
        """Return the menu or confirmation item under the mouse."""
        if game_state == "CONFIRM_RESET":
            rectangles = self._confirmation_item_rects
        elif game_state == "MENU":
            rectangles = self._menu_item_rects
        elif game_state == "PAUSED":
            rectangles = self._pause_item_rects
        elif game_state == "SETTINGS_CONTROLS":
            rectangles = self._controls_item_rects
        elif game_state == "SETTINGS_SOUND":
            rectangles = self._sound_item_rects
        else:
            return None
        for item_index, rectangle in enumerate(rectangles):
            if rectangle.collidepoint(position):
                return item_index
        return None

    def _advance_obstacle_animation(self, delta_seconds: float) -> None:
        """Advance the bird wing-flap animation timer.

        Args:
            delta_seconds: Time elapsed since the previous frame, in seconds.
        """
        self._obstacle_animation_elapsed += delta_seconds
        while (
            self._obstacle_animation_elapsed
            >= OBSTACLE_ANIMATION_INTERVAL_SECONDS
        ):
            self._obstacle_animation_elapsed -= OBSTACLE_ANIMATION_INTERVAL_SECONDS
            self._obstacle_animation_index = (
                self._obstacle_animation_index + 1
            ) % len(self._bird_frames)

    def _obstacle_frame(
        self,
        kind: ObstacleKind,
        variant: int,
        sprite_set: _SpriteSet,
    ) -> pygame.Surface:
        """Return the preloaded image for an obstacle.

        Args:
            kind: Obstacle kind.
            variant: Image index for cacti or height index for birds.

        Returns:
            The image surface to draw.

        Raises:
            ValueError: If the kind or variant is invalid.
        """
        if kind == "cactus":
            if not 0 <= variant < len(sprite_set.cactus_frames):
                raise ValueError(f"Invalid cactus variant: {variant}")
            return sprite_set.cactus_frames[variant]
        if kind == "bird":
            if not 0 <= variant < len(BIRD_HEIGHT_OFFSETS):
                raise ValueError(f"Invalid bird height variant: {variant}")
            return sprite_set.bird_frames[self._obstacle_animation_index]
        raise ValueError(f"Invalid obstacle kind: {kind}")

    @staticmethod
    def _obstacle_height(obstacle: Obstacle) -> int:
        """Return the obstacle's bottom-center anchor offset above the ground.

        Args:
            obstacle: Obstacle to position.

        Returns:
            Vertical distance of the anchor above the ground line.

        Raises:
            ValueError: If a bird's flight-height index is invalid.
        """
        if obstacle.kind == "bird":
            if not 0 <= obstacle.variant < len(BIRD_HEIGHT_OFFSETS):
                raise ValueError(f"Invalid bird height variant: {obstacle.variant}")
            return (
                BIRD_HEIGHT_OFFSETS[obstacle.variant]
                + round(bird_vertical_offset(obstacle))
            )
        return 0

    def _select_dino_frame(
        self,
        player: PlayerState,
        delta_seconds: float,
        sprite_set: _SpriteSet,
    ) -> pygame.Surface:
        """Select a dino frame and advance its animation timer.

        Args:
            player: Current movement and posture state.
            delta_seconds: Time elapsed since the previous frame, in seconds.

        Returns:
            The image surface to draw for the current dino pose.
        """
        if not player.grounded:
            self._dino_animation_elapsed = 0.0
            self._dino_animation_index = 0
            return sprite_set.jump_frame

        self._dino_animation_elapsed += delta_seconds
        animation_interval = (
            DINO_DUCK_ANIMATION_INTERVAL_SECONDS
            if player.ducking
            else DINO_RUN_ANIMATION_INTERVAL_SECONDS
        )
        while (
            self._dino_animation_elapsed
            >= animation_interval
        ):
            self._dino_animation_elapsed -= animation_interval
            self._dino_animation_index = (
                self._dino_animation_index + 1
            ) % len(sprite_set.run_frames)

        frames = sprite_set.duck_frames if player.ducking else sprite_set.run_frames
        return frames[self._dino_animation_index]

    def _current_dino_frame(
        self,
        player: PlayerState,
        sprite_set: _SpriteSet,
    ) -> pygame.Surface:
        """Return the current dino pose without advancing its animation.

        Args:
            player: Current movement and posture state.

        Returns:
            The frame corresponding to the current pose.
        """
        if not player.grounded:
            return sprite_set.jump_frame
        frames = sprite_set.duck_frames if player.ducking else sprite_set.run_frames
        return frames[self._dino_animation_index]

    def reset_animations(self) -> None:
        """Reset dino and bird animation timers for a new run."""
        self._dino_animation_elapsed = 0.0
        self._dino_animation_index = 0
        self._obstacle_animation_elapsed = 0.0
        self._obstacle_animation_index = 0

    def close(self) -> None:
        """Shut down the pygame display cleanly."""
        pygame.display.quit()
        logger.info("Closed game window")
