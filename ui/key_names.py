"""Conversion between pygame key codes and stable settings key names."""

from __future__ import annotations

import pygame

from config import SUPPORTED_SETTING_KEY_NAMES

_NAMED_KEY_CODES: dict[str, int] = {
    "space": pygame.K_SPACE,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "tab": pygame.K_TAB,
    "backspace": pygame.K_BACKSPACE,
    "delete": pygame.K_DELETE,
    "insert": pygame.K_INSERT,
    "home": pygame.K_HOME,
    "end": pygame.K_END,
    "pageup": pygame.K_PAGEUP,
    "pagedown": pygame.K_PAGEDOWN,
    "capslock": pygame.K_CAPSLOCK,
    "f1": pygame.K_F1,
    "f2": pygame.K_F2,
    "f3": pygame.K_F3,
    "f4": pygame.K_F4,
    "f5": pygame.K_F5,
    "f6": pygame.K_F6,
    "f7": pygame.K_F7,
    "f8": pygame.K_F8,
    "f9": pygame.K_F9,
    "f10": pygame.K_F10,
    "f11": pygame.K_F11,
    "f12": pygame.K_F12,
}
_NAMED_KEY_CODES.update({
    "minus": pygame.K_MINUS,
    "equals": pygame.K_EQUALS,
    "leftbracket": pygame.K_LEFTBRACKET,
    "rightbracket": pygame.K_RIGHTBRACKET,
    "backslash": pygame.K_BACKSLASH,
    "semicolon": pygame.K_SEMICOLON,
    "apostrophe": pygame.K_QUOTE,
    "comma": pygame.K_COMMA,
    "period": pygame.K_PERIOD,
    "slash": pygame.K_SLASH,
    "grave": pygame.K_BACKQUOTE,
})


def _key_code_for_name(key_name: str) -> int:
    """Convert one supported stable name to its pygame key code."""
    if key_name in _NAMED_KEY_CODES:
        return _NAMED_KEY_CODES[key_name]
    if len(key_name) == 1 and key_name.isascii() and key_name.isalnum():
        return ord(key_name)
    raise ValueError(f"Unsupported stable key name: {key_name!r}")


_KEY_NAME_TO_CODE: dict[str, int] = {
    name: _key_code_for_name(name)
    for name in SUPPORTED_SETTING_KEY_NAMES
}
_KEY_CODE_TO_NAME: dict[int, str] = {
    key_code: key_name for key_name, key_code in _KEY_NAME_TO_CODE.items()
}
_KEY_CODE_TO_NAME.update(
    {
        pygame.K_ESCAPE: "escape",
        pygame.K_RETURN: "return",
        pygame.K_KP_ENTER: "enter",
    }
)
_READABLE_NAMES: dict[str, str] = {
    "space": "Space",
    "up": "Up Arrow",
    "down": "Down Arrow",
    "left": "Left Arrow",
    "right": "Right Arrow",
    "pageup": "Page Up",
    "pagedown": "Page Down",
    "capslock": "Caps Lock",
    "minus": "-",
    "equals": "=",
    "leftbracket": "[",
    "rightbracket": "]",
    "backslash": "\\",
    "semicolon": ";",
    "apostrophe": "'",
    "comma": ",",
    "period": ".",
    "slash": "/",
    "grave": "`",
    "escape": "Esc",
    "enter": "Keypad Enter",
    "return": "Enter",
}


def stable_key_name(pygame_key: int) -> str | None:
    """Return the stable settings name for a supported pygame key code."""
    return _KEY_CODE_TO_NAME.get(pygame_key)


def pygame_key_code(key_name: str) -> int:
    """Return the pygame key code for a known stable settings key name."""
    if key_name in ("escape", "return", "enter"):
        return {
            "escape": pygame.K_ESCAPE,
            "return": pygame.K_RETURN,
            "enter": pygame.K_KP_ENTER,
        }[key_name]
    try:
        return _KEY_NAME_TO_CODE[key_name]
    except KeyError as error:
        raise ValueError(f"Unknown stable key name: {key_name!r}") from error


def readable_key_name(key_name: str) -> str:
    """Format a stable key name for display in the controls screen."""
    if key_name in _READABLE_NAMES:
        return _READABLE_NAMES[key_name]
    if len(key_name) == 1 and key_name.isalpha():
        return key_name.upper()
    if key_name.startswith("f") and key_name[1:].isdigit():
        return key_name.upper()
    return key_name
