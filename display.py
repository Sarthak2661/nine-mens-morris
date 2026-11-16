from __future__ import annotations

import os

import pygame

import constants


def create_window(caption: str) -> pygame.Surface:
    """Create a resizeable logical canvas that remains stable across Windows DPI settings."""
    flags = pygame.RESIZABLE
    if os.environ.get("SDL_VIDEODRIVER") != "dummy":
        flags |= pygame.SCALED
    screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), flags)
    pygame.display.set_caption(caption)
    return screen
