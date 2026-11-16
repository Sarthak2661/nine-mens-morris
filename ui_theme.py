from __future__ import annotations

import pygame

# Warm wood and brass connect every screen to the physical board. Charcoal
# surfaces keep the interface calm and preserve contrast around the play area.
APP_BACKGROUND = (12, 17, 23)
SURFACE = (24, 31, 39)
SURFACE_RAISED = (33, 42, 51)
SURFACE_SOFT = (42, 51, 60)
OVERLAY = (7, 10, 14)

TEXT_PRIMARY = (244, 240, 232)
TEXT_SECONDARY = (190, 184, 172)
TEXT_MUTED = (139, 146, 151)

BRASS = (205, 158, 72)
BRASS_BRIGHT = (232, 193, 111)
TEAL = (62, 169, 158)
TEAL_BRIGHT = (88, 194, 181)
SUCCESS = (82, 164, 118)
WARNING = (214, 156, 70)
DANGER = (185, 78, 72)
DISABLED = (55, 62, 68)

BORDER = (74, 82, 89)
BORDER_WARM = (111, 83, 54)
SHADOW = (5, 8, 11)

FONT_FAMILY = "Segoe UI"
RADIUS_SMALL = 6
RADIUS_MEDIUM = 10
RADIUS_LARGE = 14
SPACE_SMALL = 8
SPACE_MEDIUM = 12
SPACE_LARGE = 20


def font(size: int, *, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(FONT_FAMILY, size, bold=bold)


def mix(color: tuple[int, int, int], target: tuple[int, int, int], amount: float):
    return tuple(
        round(value + (goal - value) * amount) for value, goal in zip(color, target, strict=True)
    )


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill: tuple[int, int, int] = SURFACE,
    border: tuple[int, int, int] = BORDER,
    radius: int = RADIUS_MEDIUM,
    shadow: bool = False,
) -> None:
    if shadow:
        shadow_rect = rect.move(0, 4)
        pygame.draw.rect(surface, SHADOW, shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)


def draw_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    text_font: pygame.font.Font,
    *,
    variant: str = "primary",
    hovered: bool | None = None,
    pressed: bool | None = None,
    focused: bool = False,
    enabled: bool = True,
    icon: str | None = None,
) -> None:
    styles = {
        "primary": (TEAL, TEAL_BRIGHT, (10, 27, 27)),
        "secondary": (SURFACE_RAISED, mix(SURFACE_RAISED, BRASS, 0.18), TEXT_PRIMARY),
        "brass": (BRASS, BRASS_BRIGHT, (30, 23, 12)),
        "danger": (DANGER, mix(DANGER, TEXT_PRIMARY, 0.16), TEXT_PRIMARY),
        "success": (SUCCESS, mix(SUCCESS, TEXT_PRIMARY, 0.14), (11, 29, 20)),
        "warning": (WARNING, mix(WARNING, TEXT_PRIMARY, 0.12), (34, 23, 9)),
    }
    base, hover, text_color = styles[variant]
    if hovered is None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
    if pressed is None:
        pressed = hovered and pygame.mouse.get_pressed()[0]
    if not enabled:
        hovered = False
        pressed = False
        fill = DISABLED
        text_color = TEXT_MUTED
    else:
        fill = hover if hovered else base
        if pressed:
            fill = mix(fill, SHADOW, 0.22)

    draw_rect = rect.move(0, 1) if pressed else rect
    pygame.draw.rect(surface, SHADOW, rect.move(0, 3), border_radius=RADIUS_MEDIUM)
    pygame.draw.rect(surface, fill, draw_rect, border_radius=RADIUS_MEDIUM)
    border = BRASS_BRIGHT if hovered or focused else mix(fill, TEXT_PRIMARY, 0.35)
    border_width = 2 if focused else 1
    pygame.draw.rect(surface, border, draw_rect, width=border_width, border_radius=RADIUS_MEDIUM)

    label = text_font.render(text, True, text_color)
    label_rect = label.get_rect(center=draw_rect.center)
    if icon:
        label_rect.x += 9
        draw_icon(surface, icon, (draw_rect.left + 17, draw_rect.centery), text_color)
    surface.blit(label, label_rect)


def draw_icon(
    surface: pygame.Surface,
    icon: str,
    center: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    x, y = center
    if icon == "reset":
        pygame.draw.arc(surface, color, pygame.Rect(x - 8, y - 8, 16, 16), 0.5, 5.6, 2)
        pygame.draw.polygon(surface, color, [(x + 6, y - 7), (x + 10, y - 6), (x + 8, y - 2)])
    elif icon == "export":
        pygame.draw.line(surface, color, (x, y - 8), (x, y + 3), 2)
        pygame.draw.polygon(surface, color, [(x - 4, y), (x + 4, y), (x, y + 5)])
        pygame.draw.line(surface, color, (x - 7, y + 8), (x + 7, y + 8), 2)
    elif icon == "save":
        pygame.draw.rect(surface, color, pygame.Rect(x - 8, y - 8, 16, 16), width=2)
        pygame.draw.rect(surface, color, pygame.Rect(x - 4, y - 7, 8, 5), width=2)
        pygame.draw.rect(surface, color, pygame.Rect(x - 4, y + 2, 8, 5), width=2)
    elif icon in {"sound", "mute"}:
        pygame.draw.polygon(
            surface,
            color,
            [
                (x - 8, y - 3),
                (x - 4, y - 3),
                (x + 1, y - 8),
                (x + 1, y + 8),
                (x - 4, y + 3),
                (x - 8, y + 3),
            ],
        )
        if icon == "sound":
            pygame.draw.arc(surface, color, pygame.Rect(x - 1, y - 7, 13, 14), -0.9, 0.9, 2)
        else:
            pygame.draw.line(surface, color, (x + 4, y - 5), (x + 11, y + 5), 2)
            pygame.draw.line(surface, color, (x + 11, y - 5), (x + 4, y + 5), 2)
    elif icon == "exit":
        pygame.draw.rect(surface, color, pygame.Rect(x - 8, y - 8, 10, 16), width=2)
        pygame.draw.line(surface, color, (x - 1, y), (x + 9, y), 2)
        pygame.draw.polygon(surface, color, [(x + 5, y - 4), (x + 10, y), (x + 5, y + 4)])


def draw_setup_backdrop(surface: pygame.Surface, title: str, subtitle: str) -> None:
    surface.fill(APP_BACKGROUND)
    pygame.draw.rect(surface, SURFACE, pygame.Rect(0, 0, surface.get_width(), 92))
    pygame.draw.line(surface, BRASS, (64, 91), (surface.get_width() - 64, 91), 2)

    title_font = font(50, bold=True)
    subtitle_font = font(19)
    title_surface = title_font.render(title, True, TEXT_PRIMARY)
    subtitle_surface = subtitle_font.render(subtitle, True, TEXT_SECONDARY)
    surface.blit(title_surface, title_surface.get_rect(center=(surface.get_width() // 2, 150)))
    surface.blit(
        subtitle_surface, subtitle_surface.get_rect(center=(surface.get_width() // 2, 205))
    )

    panel = pygame.Rect(150, 245, surface.get_width() - 300, 370)
    draw_panel(surface, panel, fill=SURFACE, border=BORDER_WARM, radius=RADIUS_LARGE, shadow=True)
