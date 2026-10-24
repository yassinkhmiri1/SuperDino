"""Pure navigation rules for the main menu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from config import MAX_KEYS_PER_ACTION


MenuItem = Literal["start", "controls", "sound", "reset_high_score", "quit"]
MENU_ITEMS: Final[tuple[MenuItem, ...]] = (
    "start",
    "controls",
    "sound",
    "reset_high_score",
    "quit",
)
PauseItem = Literal["resume", "back_to_menu"]
PAUSE_ITEMS: Final[tuple[PauseItem, ...]] = ("resume", "back_to_menu")
ControlsItem = Literal["jump", "duck", "reset_to_defaults", "back_to_menu"]
CONTROLS_ITEMS: Final[tuple[ControlsItem, ...]] = (
    "jump",
    "duck",
    "reset_to_defaults",
    "back_to_menu",
)
ResetConfirmationItem = Literal["yes", "no"]
RESET_CONFIRMATION_ITEMS: Final[
    tuple[ResetConfirmationItem, ResetConfirmationItem]
] = ("yes", "no")


@dataclass(frozen=True, slots=True)
class MenuState:
    """Selected item in the main menu."""

    selected_index: int = 0


@dataclass(frozen=True, slots=True)
class PauseMenuState:
    """Selected action in the in-game pause menu."""

    selected_index: int = 0


def move_pause_selection(state: PauseMenuState, direction: int) -> PauseMenuState:
    """Move the pause-menu selection vertically with wraparound."""
    if direction == 0:
        return state
    step = 1 if direction > 0 else -1
    return PauseMenuState((state.selected_index + step) % len(PAUSE_ITEMS))


def select_pause_item(index: int) -> PauseMenuState:
    """Select a pause-menu item by its zero-based index."""
    if not 0 <= index < len(PAUSE_ITEMS):
        raise ValueError(f"Pause menu item index is out of range: {index}")
    return PauseMenuState(index)


def activate_pause_selection(state: PauseMenuState) -> PauseItem:
    """Return the action represented by the selected pause-menu item."""
    return PAUSE_ITEMS[state.selected_index]


def move_selection(state: MenuState, direction: int) -> MenuState:
    """Move the selection up or down, wrapping at either end."""
    if direction == 0:
        return state
    step = 1 if direction > 0 else -1
    return MenuState((state.selected_index + step) % len(MENU_ITEMS))


def select_item(index: int) -> MenuState:
    """Select a menu item by its zero-based index."""
    if not 0 <= index < len(MENU_ITEMS):
        raise ValueError(f"Menu item index is out of range: {index}")
    return MenuState(index)


def activate_selection(state: MenuState) -> MenuItem:
    """Return the action represented by the currently selected item."""
    return MENU_ITEMS[state.selected_index]


@dataclass(frozen=True, slots=True)
class ResetConfirmationState:
    """Selected answer for the high-score reset confirmation."""

    selected_index: int = 1


@dataclass(frozen=True, slots=True)
class ControlsMenuState:
    """Selected controls-screen action and binding slot."""

    selected_index: int = 0
    binding_slot: int = 0


@dataclass(frozen=True, slots=True)
class SoundMenuState:
    """Selected row on the sound settings screen."""

    selected_index: int = 0


SOUND_ITEMS: Final[tuple[str, str, str, str]] = (
    "music_volume",
    "effects_volume",
    "muted",
    "back_to_menu",
)


def move_sound_selection(
    state: SoundMenuState,
    direction: int,
) -> SoundMenuState:
    """Move the sound-screen selection up or down with wraparound."""
    if direction == 0:
        return state
    step = 1 if direction > 0 else -1
    return SoundMenuState((state.selected_index + step) % len(SOUND_ITEMS))


def select_sound_item(index: int) -> SoundMenuState:
    """Select a sound-screen row by its zero-based index."""
    if not 0 <= index < len(SOUND_ITEMS):
        raise ValueError(f"Sound item index is out of range: {index}")
    return SoundMenuState(index)


def activate_sound_selection(state: SoundMenuState) -> str:
    """Return the selected sound-screen action."""
    return SOUND_ITEMS[state.selected_index]


def move_controls_selection(
    state: ControlsMenuState,
    direction: int,
) -> ControlsMenuState:
    """Move the controls-screen selection up or down with wraparound."""
    if direction == 0:
        return state
    step = 1 if direction > 0 else -1
    return ControlsMenuState(
        (state.selected_index + step) % len(CONTROLS_ITEMS),
        0,
    )


def select_controls_item(index: int) -> ControlsMenuState:
    """Select a controls-screen item by its zero-based index."""
    if not 0 <= index < len(CONTROLS_ITEMS):
        raise ValueError(f"Controls item index is out of range: {index}")
    return ControlsMenuState(index)


def move_controls_binding_slot(
    state: ControlsMenuState,
    direction: int,
) -> ControlsMenuState:
    """Switch between the primary and secondary key slots."""
    if direction == 0:
        return state
    step = 1 if direction > 0 else -1
    return ControlsMenuState(
        state.selected_index,
        (state.binding_slot + step) % MAX_KEYS_PER_ACTION,
    )


def activate_controls_selection(state: ControlsMenuState) -> ControlsItem:
    """Return the selected controls-screen action."""
    return CONTROLS_ITEMS[state.selected_index]


def move_confirmation_selection(
    state: ResetConfirmationState,
    direction: int,
) -> ResetConfirmationState:
    """Move the reset answer selection up or down, wrapping at either end."""
    if direction == 0:
        return state
    step = 1 if direction > 0 else -1
    return ResetConfirmationState(
        (state.selected_index + step) % len(RESET_CONFIRMATION_ITEMS)
    )


def select_confirmation_item(index: int) -> ResetConfirmationState:
    """Select a reset confirmation answer by its zero-based index."""
    if not 0 <= index < len(RESET_CONFIRMATION_ITEMS):
        raise ValueError(f"Confirmation item index is out of range: {index}")
    return ResetConfirmationState(index)


def activate_confirmation_selection(
    state: ResetConfirmationState,
) -> ResetConfirmationItem:
    """Return the selected reset confirmation answer."""
    return RESET_CONFIRMATION_ITEMS[state.selected_index]
