"""Tests for pygame-free main-menu navigation."""

from __future__ import annotations

import unittest

from core.menu import (
    MENU_ITEMS,
    CONTROLS_ITEMS,
    ControlsMenuState,
    MenuState,
    PAUSE_ITEMS,
    PauseMenuState,
    ResetConfirmationState,
    SOUND_ITEMS,
    SoundMenuState,
    activate_sound_selection,
    activate_confirmation_selection,
    activate_selection,
    activate_pause_selection,
    move_confirmation_selection,
    move_controls_binding_slot,
    move_controls_selection,
    move_selection,
    move_pause_selection,
    move_sound_selection,
    select_confirmation_item,
    select_controls_item,
    select_item,
    select_pause_item,
    select_sound_item,
)

class MenuNavigationTests(unittest.TestCase):
    """Tests for moving through and activating main-menu items."""

    def test_selection_wraps_in_both_directions(self) -> None:
        """Moving past either end selects the opposite end."""
        first_item = MenuState()

        self.assertEqual(
            move_selection(first_item, -1).selected_index,
            len(MENU_ITEMS) - 1,
        )
        self.assertEqual(
            move_selection(MenuState(len(MENU_ITEMS) - 1), 1).selected_index,
            0,
        )
        self.assertEqual(move_selection(first_item, 0), first_item)

    def test_mouse_selection_validates_item_index(self) -> None:
        """Mouse-selected item indexes are range checked."""
        self.assertEqual(select_item(1), MenuState(1))
        with self.assertRaises(ValueError):
            select_item(len(MENU_ITEMS))

    def test_activation_returns_selected_action(self) -> None:
        """Activating the selected item returns its main-menu action."""
        self.assertEqual(activate_selection(MenuState(0)), "start")
        self.assertEqual(activate_selection(MenuState(1)), "controls")
        self.assertEqual(activate_selection(MenuState(2)), "sound")
        self.assertEqual(activate_selection(MenuState(3)), "reset_high_score")
        self.assertEqual(activate_selection(MenuState(4)), "quit")

    def test_pause_menu_navigation_and_actions(self) -> None:
        """Pause-menu selection wraps and exposes resume/back actions."""
        self.assertEqual(
            move_pause_selection(PauseMenuState(), -1).selected_index,
            len(PAUSE_ITEMS) - 1,
        )
        self.assertEqual(
            move_pause_selection(PauseMenuState(1), 1).selected_index,
            0,
        )
        self.assertEqual(select_pause_item(1), PauseMenuState(1))
        self.assertEqual(activate_pause_selection(PauseMenuState()), "resume")
        self.assertEqual(activate_pause_selection(PauseMenuState(1)), "back_to_menu")

    def test_sound_menu_navigation_and_selection(self) -> None:
        """Sound menu wraps its four rows and reports the selected action."""
        self.assertEqual(
            move_sound_selection(SoundMenuState(), -1).selected_index,
            len(SOUND_ITEMS) - 1,
        )
        self.assertEqual(select_sound_item(1), SoundMenuState(1))
        self.assertEqual(activate_sound_selection(SoundMenuState(2)), "muted")

    def test_controls_navigation_wraps_and_selects_binding_slots(self) -> None:
        """Controls selection wraps while binding slots switch left and right."""
        self.assertEqual(
            move_controls_selection(ControlsMenuState(), -1).selected_index,
            len(CONTROLS_ITEMS) - 1,
        )
        self.assertEqual(select_controls_item(1), ControlsMenuState(1, 0))
        self.assertEqual(
            move_controls_binding_slot(ControlsMenuState(), 1).binding_slot,
            1,
        )

    def test_reset_confirmation_defaults_to_no(self) -> None:
        """Reset confirmation starts on No and moves to Yes with Up."""
        state = ResetConfirmationState()

        self.assertEqual(activate_confirmation_selection(state), "no")
        state = move_confirmation_selection(state, -1)
        self.assertEqual(activate_confirmation_selection(state), "yes")
        self.assertEqual(select_confirmation_item(1), ResetConfirmationState())


if __name__ == "__main__":
    unittest.main()
