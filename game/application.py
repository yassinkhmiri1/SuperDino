"""Application loop for the game."""

from __future__ import annotations

import logging
import os
from random import Random
from pathlib import Path

from audio.controller import AudioController
from config import (
    CONTROLS_DEFAULT_LIMIT_MESSAGE,
    DEFAULT_JUMP_KEYS,
    DINO_CENTER_X,
    GROUND_LINE_Y,
    HIGH_SCORE_FILENAME,
    MAX_FRAME_SECONDS,
    MENU_LABELS,
    POINT_SOUND_INTERVAL_POINTS,
    SETTINGS_FILENAME,
    SUCCESS_EXIT_CODE,
    VOLUME_MAX,
)
from core.collision import hitboxes_overlap, obstacle_hitbox, player_hitbox
from core.data_directory import (
    prepare_user_data_directory,
    user_data_directory,
)
from core.high_score import (
    HighScoreStorageError,
    load_high_score,
    save_high_score,
)
from core.menu import (
    ControlsMenuState,
    MenuState,
    PauseMenuState,
    ResetConfirmationState,
    SoundMenuState,
    activate_sound_selection,
    activate_pause_selection,
    activate_controls_selection,
    activate_confirmation_selection,
    activate_selection,
    move_controls_binding_slot,
    move_controls_selection,
    move_confirmation_selection,
    move_sound_selection,
    move_pause_selection,
    move_selection,
    select_confirmation_item,
    select_controls_item,
    select_item,
    select_sound_item,
    select_pause_item,
)
from core.obstacles import (
    Obstacle,
    choose_obstacle_gap,
    update_obstacles,
)
from core.player import PlayerState, update_player
from core.score import ScoreState, advance_score
from core.settings import (
    Settings,
    adjust_volume,
    bind_key,
    clear_key_binding,
    default_settings,
    load_settings,
    reset_key_bindings,
    save_settings,
    toggle_mute,
    music_volume_for_percentage,
)
from core.speed import speed_for_score
from core.state import GameState
from core.timing import physics_time_steps
from ui.window import GameWindow, InputFrame
from ui.key_names import readable_key_name

logger = logging.getLogger(__name__)


class Game:
    """Own the game loop and its window.

    Returns:
        A game application instance.
    """

    def __init__(self) -> None:
        """Create the game window."""
        data_directory = user_data_directory(os.environ, Path.home())
        self._settings_path = data_directory / SETTINGS_FILENAME
        self._high_score_path = data_directory / HIGH_SCORE_FILENAME
        self._persistence_enabled = prepare_user_data_directory(data_directory)
        if self._persistence_enabled:
            try:
                self._settings = load_settings(self._settings_path)
                self._high_score = load_high_score(self._high_score_path)
            except HighScoreStorageError:
                logger.warning(
                    "Could not load persistent game data; using defaults "
                    "without saving",
                    exc_info=True,
                )
                self._persistence_enabled = False
                self._settings = default_settings()
                self._high_score = 0
        else:
            self._settings = default_settings()
            self._high_score = 0
        self._settings_message = ""
        self._controls_listening = False
        self._loaded_high_score = self._high_score
        self._score = ScoreState()
        self._playtime_seconds = 0.0
        self._window = GameWindow(self._settings.key_bindings)
        self._audio = AudioController(
            music_volume_for_percentage(self._settings.music_volume),
            self._settings.effects_volume / VOLUME_MAX,
            self._settings.muted,
        )
        self._ground_offset = 0.0
        self._player = PlayerState()
        self._randomizer = Random()
        self._obstacles: tuple[Obstacle, ...] = ()
        self._next_spawn_distance = choose_obstacle_gap(
            speed_for_score(self._score.points),
            self._randomizer,
        )
        self._debug_world_speed = speed_for_score(self._score.points)
        self._debug_ground_speed = self._debug_world_speed
        self._debug_obstacle_speed = self._debug_world_speed
        self._debug_spawn_gap_seconds = (
            self._next_spawn_distance / self._debug_world_speed
        )
        self._state: GameState = "MENU"
        self._menu_state = MenuState()
        self._pause_state = PauseMenuState()
        self._confirmation_state = ResetConfirmationState()
        self._controls_state = ControlsMenuState()
        self._sound_state = SoundMenuState()

    def run(self) -> int:
        """Run until the window receives a quit event.

        Returns:
            The process exit code.
        """
        logger.info("Game loop started")
        running = True

        try:
            while running:
                delta_seconds = self._window.tick()
                input_frame = self._window.process_events(self._state)
                running = input_frame.running
                if running:
                    running = self._handle_state_input(input_frame)
                    if self._state == "RUNNING":
                        self._update_running(
                            delta_seconds,
                            input_frame.jump_pressed,
                            input_frame.duck_held,
                        )
                if running:
                    self._window.render(
                        self._ground_offset,
                        self._player,
                        self._obstacles,
                        delta_seconds,
                        self._state,
                        self._score.points,
                        self._high_score,
                        self._playtime_seconds,
                        self._debug_world_speed,
                        self._debug_ground_speed,
                        self._debug_obstacle_speed,
                        self._debug_spawn_gap_seconds,
                        self._menu_state.selected_index,
                        self._pause_state.selected_index,
                        self._confirmation_state.selected_index,
                        self._controls_state.selected_index,
                        self._controls_state.binding_slot,
                        self._controls_listening,
                        self._settings_message,
                        self._settings.key_bindings,
                        self._sound_state.selected_index,
                        self._settings,
                    )
            logger.info("Game loop stopped cleanly")
            return SUCCESS_EXIT_CODE
        finally:
            try:
                self._save_high_score_if_new()
            finally:
                try:
                    self._audio.close()
                finally:
                    self._window.close()

    def _advance_ground(self, delta_seconds: float, speed: float) -> None:
        """Advance the scrolling ground by elapsed real time.

        Args:
            delta_seconds: Time elapsed since the previous frame, in seconds.
            speed: Current world speed in pixels per second.
        """
        self._debug_ground_speed = speed
        self._ground_offset = (
            self._ground_offset
            + speed * delta_seconds
        ) % self._window.ground_width

    def _handle_state_input(
        self,
        input_frame: InputFrame,
    ) -> bool:
        """Handle menu, start, pause, resume, and restart controls.

        Args:
            input_frame: Collected keyboard and mouse input for this frame.

        Returns:
            Whether the game loop should continue.
        """
        if self._state == "MENU":
            if input_frame.menu_selection is not None:
                self._menu_state = select_item(input_frame.menu_selection)
            if input_frame.menu_direction:
                self._menu_state = move_selection(
                    self._menu_state,
                    input_frame.menu_direction,
                )
            if input_frame.restart_pressed or input_frame.menu_activate:
                action = activate_selection(self._menu_state)
                if action == "start":
                    self._reset_run()
                    logger.info("Game started from main menu")
                elif action == "controls":
                    self._controls_state = ControlsMenuState()
                    self._settings_message = ""
                    self._state = "SETTINGS_CONTROLS"
                elif action == "sound":
                    self._sound_state = SoundMenuState()
                    self._settings_message = ""
                    self._state = "SETTINGS_SOUND"
                elif action == "reset_high_score":
                    self._confirmation_state = ResetConfirmationState()
                    self._state = "CONFIRM_RESET"
                    logger.info("Opened high-score reset confirmation")
                else:
                    logger.info("Quit selected from main menu")
                    return False
            return True
        if self._state == "SETTINGS_CONTROLS":
            return self._handle_controls_input(input_frame)
        if self._state == "SETTINGS_SOUND":
            return self._handle_sound_input(input_frame)
        if self._state == "CONFIRM_RESET":
            if input_frame.menu_selection is not None:
                self._confirmation_state = select_confirmation_item(
                    input_frame.menu_selection
                )
            if input_frame.menu_direction:
                self._confirmation_state = move_confirmation_selection(
                    self._confirmation_state,
                    input_frame.menu_direction,
                )
            if input_frame.pause_pressed:
                self._state = "MENU"
                return True
            if input_frame.restart_pressed or input_frame.menu_activate:
                answer = activate_confirmation_selection(
                    self._confirmation_state
                )
                if answer == "yes":
                    if self._persistence_enabled:
                        try:
                            save_high_score(self._high_score_path, 0)
                        except HighScoreStorageError:
                            self._persistence_enabled = False
                            logger.warning(
                                "Could not save high score; disabling persistence",
                                exc_info=True,
                            )
                    self._high_score = 0
                    self._loaded_high_score = 0
                    logger.info("High score reset to zero")
                self._state = "MENU"
            return True
        if self._state == "GAME_OVER" and input_frame.restart_pressed:
            self._reset_run()
            self._audio.fade_in_music()
            return True
        if self._state == "PAUSED":
            if input_frame.menu_selection is not None:
                self._pause_state = select_pause_item(input_frame.menu_selection)
            if input_frame.menu_direction:
                self._pause_state = move_pause_selection(
                    self._pause_state,
                    input_frame.menu_direction,
                )
            if input_frame.pause_pressed:
                self._state = "RUNNING"
                logger.info("Game resumed")
            elif input_frame.restart_pressed or input_frame.menu_activate:
                action = activate_pause_selection(self._pause_state)
                if action == "resume":
                    self._state = "RUNNING"
                    logger.info("Game resumed")
                else:
                    self._reset_run("MENU")
                    self._menu_state = MenuState()
                    logger.info("Returned to main menu from pause")
            return True
        if not input_frame.pause_pressed:
            return True
        if self._state == "RUNNING":
            self._state = "PAUSED"
            self._pause_state = PauseMenuState()
            logger.info("Game paused")
        return True

    def _handle_controls_input(self, input_frame: InputFrame) -> bool:
        """Handle controls-screen navigation, rebinding, and reset actions."""
        if input_frame.pause_pressed:
            self._controls_listening = False
            self._settings_message = ""
            self._state = "MENU"
            return True

        if self._controls_listening:
            if not input_frame.control_key_pressed:
                return True
            if input_frame.control_key_name is None:
                self._settings_message = "That key is not supported for binding."
                return True
            selected_action = activate_controls_selection(self._controls_state)
            if selected_action not in ("jump", "duck"):
                raise RuntimeError("A non-binding controls item entered key capture")
            previous_bindings = getattr(
                self._settings.key_bindings,
                selected_action,
            )
            try:
                updated_settings = bind_key(
                    self._settings,
                    selected_action,
                    self._controls_state.binding_slot,
                    input_frame.control_key_name,
                )
            except ValueError as error:
                self._settings_message = str(error)
                return True
            if self._save_settings_update(updated_settings):
                self._controls_listening = False
                self._settings_message = (
                    f"{MENU_LABELS[selected_action]} bound to "
                    f"{readable_key_name(input_frame.control_key_name)}."
                )
                if len(previous_bindings) == len(DEFAULT_JUMP_KEYS):
                    self._settings_message += f" {CONTROLS_DEFAULT_LIMIT_MESSAGE}"
            return True

        if input_frame.menu_selection is not None:
            self._controls_state = select_controls_item(
                input_frame.menu_selection
            )
        if input_frame.menu_direction:
            self._controls_state = move_controls_selection(
                self._controls_state,
                input_frame.menu_direction,
            )
        selected_item = activate_controls_selection(self._controls_state)
        if (
            input_frame.control_slot_direction
            and selected_item in ("jump", "duck")
        ):
            self._controls_state = move_controls_binding_slot(
                self._controls_state,
                input_frame.control_slot_direction,
            )
        selected_item = activate_controls_selection(self._controls_state)
        if input_frame.delete_pressed and selected_item in ("jump", "duck"):
            try:
                updated_settings = clear_key_binding(
                    self._settings,
                    selected_item,
                    self._controls_state.binding_slot,
                )
            except ValueError as error:
                self._settings_message = str(error)
            else:
                if self._save_settings_update(updated_settings):
                    self._settings_message = (
                        f"Removed the selected {MENU_LABELS[selected_item]} key."
                    )
            return True
        if input_frame.restart_pressed or input_frame.menu_activate:
            if selected_item in ("jump", "duck"):
                self._controls_listening = True
                self._settings_message = ""
            elif selected_item == "reset_to_defaults":
                updated_settings = reset_key_bindings(self._settings)
                if self._save_settings_update(updated_settings):
                    self._settings_message = "Controls reset to defaults."
            else:
                self._settings_message = ""
                self._state = "MENU"
        return True

    def _save_settings_update(self, settings: Settings) -> bool:
        """Persist settings before applying them to the running game."""
        if not self._persistence_enabled:
            self._settings_message = (
                "Could not save settings; the previous settings are unchanged."
            )
            return False
        try:
            save_settings(settings, self._settings_path)
        except OSError:
            self._persistence_enabled = False
            logger.warning(
                "Could not persist settings; disabling persistence",
                exc_info=True,
            )
            self._settings_message = (
                "Could not save settings; the previous settings are unchanged."
            )
            return False
        self._settings = settings
        self._window.set_key_bindings(settings.key_bindings)
        self._audio.set_volumes(
            music_volume_for_percentage(settings.music_volume),
            settings.effects_volume / VOLUME_MAX,
            settings.muted,
        )
        return True

    def _handle_sound_input(self, input_frame: InputFrame) -> bool:
        """Handle volume, mute, and navigation input on the sound screen."""
        if input_frame.pause_pressed:
            self._settings_message = ""
            self._state = "MENU"
            return True
        if input_frame.menu_selection is not None:
            self._sound_state = select_sound_item(input_frame.menu_selection)
        if input_frame.menu_direction:
            self._sound_state = move_sound_selection(
                self._sound_state,
                input_frame.menu_direction,
            )

        selected_item = activate_sound_selection(self._sound_state)
        if selected_item in ("music_volume", "effects_volume"):
            if input_frame.control_slot_direction:
                direction = input_frame.control_slot_direction
            elif input_frame.restart_pressed or input_frame.menu_activate:
                direction = 1
            else:
                return True
            updated_settings = adjust_volume(
                self._settings,
                selected_item,
                direction,
            )
            if updated_settings != self._settings:
                if self._save_settings_update(updated_settings):
                    self._settings_message = ""
            return True

        if selected_item == "muted":
            if input_frame.restart_pressed or input_frame.menu_activate:
                updated_settings = toggle_mute(self._settings)
                if self._save_settings_update(updated_settings):
                    self._settings_message = ""
            return True

        if input_frame.restart_pressed or input_frame.menu_activate:
            self._settings_message = ""
            self._state = "MENU"
        return True

    def _update_running(
        self,
        delta_seconds: float,
        jump_pressed: bool,
        duck_held: bool,
    ) -> None:
        """Advance all active game systems by one frame.

        Args:
            delta_seconds: Time elapsed since the previous frame, in seconds.
            jump_pressed: Whether the jump key was newly pressed.
            duck_held: Whether the duck key is held.
        """
        speed = speed_for_score(self._score.points)
        self._debug_world_speed = speed
        first_step = True
        for step_seconds in physics_time_steps(
            min(delta_seconds, MAX_FRAME_SECONDS)
        ):
            self._playtime_seconds += step_seconds
            self._advance_ground(step_seconds, speed)
            self._advance_obstacles(step_seconds, speed)
            previous_score = self._score.points
            self._score = advance_score(self._score, step_seconds, speed)
            if (
                self._score.points // POINT_SOUND_INTERVAL_POINTS
                > previous_score // POINT_SOUND_INTERVAL_POINTS
            ):
                self._audio.play_point()
            self._high_score = max(self._high_score, self._score.points)

            jump_started = (
                first_step and jump_pressed and self._player.grounded
            )
            self._player = update_player(
                self._player,
                step_seconds,
                jump_pressed and first_step,
                duck_held,
            )
            if jump_started:
                self._audio.play_jump()
            self._check_collisions()
            if self._state == "GAME_OVER":
                return
            first_step = False

    def _reset_run(self, next_state: GameState = "RUNNING") -> None:
        """Reset current-run state while retaining the saved high score.

        Args:
            next_state: Game screen to enter after resetting the run.
        """
        self._score = ScoreState()
        self._playtime_seconds = 0.0
        self._ground_offset = 0.0
        self._player = PlayerState()
        self._obstacles = ()
        self._next_spawn_distance = choose_obstacle_gap(
            speed_for_score(self._score.points),
            self._randomizer,
        )
        self._window.reset_animations()
        self._window.reset_theme_transition()
        self._state = next_state
        logger.info("Run state reset")

    def _advance_obstacles(self, delta_seconds: float, speed: float) -> None:
        """Move obstacles and create new ones when their gap expires.

        Args:
            delta_seconds: Time elapsed since the previous frame, in seconds.
            speed: Current world speed in pixels per second.
        """
        self._debug_obstacle_speed = speed
        update = update_obstacles(
            self._obstacles,
            delta_seconds,
            speed,
            self._next_spawn_distance,
            self._randomizer,
        )
        self._obstacles = update.obstacles
        self._next_spawn_distance = update.next_spawn_distance
        self._debug_spawn_gap_seconds = self._next_spawn_distance / speed

    def _check_collisions(self) -> None:
        """Enter game-over state if a tight player hitbox intersects an obstacle."""
        player_box = player_hitbox(
            self._player,
            DINO_CENTER_X,
            GROUND_LINE_Y - self._player.ground_offset,
        )
        for obstacle in self._obstacles:
            if hitboxes_overlap(
                player_box,
                obstacle_hitbox(obstacle, GROUND_LINE_Y),
            ):
                self._state = "GAME_OVER"
                self._audio.play_death()
                self._audio.fade_out_music()
                logger.info(
                    "Game over after collision with %s variant %d",
                    obstacle.kind,
                    obstacle.variant,
                )
                return

    def _save_high_score_if_new(self) -> None:
        """Persist the high score if this run improved the stored record."""
        if self._persistence_enabled and self._high_score > self._loaded_high_score:
            try:
                save_high_score(self._high_score_path, self._high_score)
            except HighScoreStorageError:
                self._persistence_enabled = False
                logger.warning(
                    "Could not save high score; disabling persistence",
                    exc_info=True,
                )
            else:
                self._loaded_high_score = self._high_score
