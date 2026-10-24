"""Screen drawing helpers."""

from collections.abc import Callable

import pygame

from config import (
    MENU_HIGH_SCORE_TOP,
    MENU_LABELS,
    PAUSE_INSTRUCTIONS,
    PAUSE_INSTRUCTIONS_TOP,
    PAUSE_MESSAGE,
    PAUSE_MESSAGE_TOP,
    RESET_CONFIRMATION_MESSAGE_TOP,
    TITLE_MESSAGE,
    TITLE_MESSAGE_TOP,
)
from core.menu import MENU_ITEMS, PAUSE_ITEMS, RESET_CONFIRMATION_ITEMS
from core.themes import Theme


def draw_menu(
    surface: pygame.Surface,
    title_font: pygame.font.Font,
    menu_font: pygame.font.Font,
    menu_item_rects: tuple[pygame.Rect, ...],
    theme: Theme,
    high_score: int,
    selected_index: int,
    theme_text_color: Callable[
        [Theme, int, tuple[int, int, int]],
        tuple[int, int, int],
    ],
) -> None:
    title_surface = title_font.render(
        TITLE_MESSAGE,
        True,
        theme_text_color(theme, TITLE_MESSAGE_TOP, theme.text_color),
    )
    title_rect = title_surface.get_rect(
        midtop=(surface.get_width() // 2, TITLE_MESSAGE_TOP)
    )
    surface.blit(title_surface, title_rect)
    high_score_surface = menu_font.render(
        f"{MENU_LABELS['high_score']}: {high_score}",
        True,
        theme_text_color(theme, MENU_HIGH_SCORE_TOP, theme.text_color),
    )
    high_score_rect = high_score_surface.get_rect(
        midtop=(
            surface.get_width() // 2,
            MENU_HIGH_SCORE_TOP,
        )
    )
    surface.blit(high_score_surface, high_score_rect)
    for item_index, item in enumerate(MENU_ITEMS):
        item_surface = menu_font.render(
            MENU_LABELS[item],
            True,
            theme_text_color(
                theme,
                menu_item_rects[item_index].centery,
                theme.secondary_text_color
                if item_index == selected_index
                else theme.text_color,
            ),
        )
        item_rect = item_surface.get_rect(
            center=menu_item_rects[item_index].center
        )
        surface.blit(item_surface, item_rect)


def draw_confirm(
    surface: pygame.Surface,
    title_font: pygame.font.Font,
    menu_font: pygame.font.Font,
    confirmation_item_rects: tuple[pygame.Rect, ...],
    theme: Theme,
    selected_index: int,
    theme_text_color: Callable[
        [Theme, int, tuple[int, int, int]],
        tuple[int, int, int],
    ],
) -> None:
    confirmation_surface = title_font.render(
        MENU_LABELS["confirm_reset"],
        True,
        theme_text_color(
            theme,
            RESET_CONFIRMATION_MESSAGE_TOP,
            theme.text_color,
        ),
    )
    confirmation_rect = confirmation_surface.get_rect(
        midtop=(
            surface.get_width() // 2,
            RESET_CONFIRMATION_MESSAGE_TOP,
        )
    )
    surface.blit(confirmation_surface, confirmation_rect)
    for item_index, item in enumerate(RESET_CONFIRMATION_ITEMS):
        item_surface = menu_font.render(
            MENU_LABELS[item],
            True,
            theme_text_color(
                theme,
                confirmation_item_rects[item_index].centery,
                theme.secondary_text_color
                if item_index == selected_index
                else theme.text_color,
            ),
        )
        item_rect = item_surface.get_rect(
            center=confirmation_item_rects[item_index].center
        )
        surface.blit(item_surface, item_rect)


def draw_pause(
    surface: pygame.Surface,
    pause_font: pygame.font.Font,
    controls_instruction_font: pygame.font.Font,
    menu_font: pygame.font.Font,
    pause_item_rects: tuple[pygame.Rect, ...],
    theme: Theme,
    selected_index: int,
    theme_text_color: Callable[
        [Theme, int, tuple[int, int, int]],
        tuple[int, int, int],
    ],
) -> None:
    pause_surface = pause_font.render(
        PAUSE_MESSAGE,
        True,
        theme_text_color(theme, PAUSE_MESSAGE_TOP, theme.text_color),
    )
    pause_rect = pause_surface.get_rect(
        midtop=(surface.get_width() // 2, PAUSE_MESSAGE_TOP)
    )
    surface.blit(pause_surface, pause_rect)
    instructions_surface = controls_instruction_font.render(
        PAUSE_INSTRUCTIONS,
        True,
        theme_text_color(
            theme,
            PAUSE_INSTRUCTIONS_TOP,
            theme.text_color,
        ),
    )
    surface.blit(
        instructions_surface,
        instructions_surface.get_rect(
            midtop=(
                surface.get_width() // 2,
                PAUSE_INSTRUCTIONS_TOP,
            )
        ),
    )
    for item_index, item in enumerate(PAUSE_ITEMS):
        item_surface = menu_font.render(
            MENU_LABELS[item],
            True,
            theme_text_color(
                theme,
                pause_item_rects[item_index].centery,
                theme.secondary_text_color
                if item_index == selected_index
                else theme.text_color,
            ),
        )
        surface.blit(
            item_surface,
            item_surface.get_rect(
                center=pause_item_rects[item_index].center
            ),
        )
