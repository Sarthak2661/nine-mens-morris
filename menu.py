import os
import sys

import pygame

import constants
import ui_theme as theme
from display import create_window
from game_persistence import save_status


def wrap_text(text, font, max_width):
    if not text:
        return [""]
    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class HomePage:
    def __init__(self):
        self.screen = create_window("Nine Men's Morris")
        self.clock = pygame.time.Clock()
        self.started = False
        self.selected_action = None
        self.show_instructions = False
        self.title_font = theme.font(72, bold=True)
        self.subtitle_font = theme.font(28)
        self.button_font = theme.font(22, bold=True)
        self.start_button_rect = pygame.Rect(80, 480, 230, 70)
        self.resume_button_rect = pygame.Rect(335, 480, 230, 70)
        self.how_to_play_button_rect = pygame.Rect(590, 480, 230, 70)
        self.button_rects = [
            self.start_button_rect,
            self.resume_button_rect,
            self.how_to_play_button_rect,
        ]
        self.resume_enabled, self.resume_status = save_status()
        self.focused_index = 0

        self.background = None
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "resources", "background.png")
            if os.path.exists(bg_path):
                self.background = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(
                    self.background, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
                )
        except Exception as e:
            print(f"Could not load background: {e}")

    def display(self):
        while not self.started:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.start_button_rect.collidepoint(event.pos):
                        self.started = True
                        self.selected_action = "new"
                    elif self.resume_button_rect.collidepoint(event.pos) and self.resume_enabled:
                        self.started = True
                        self.selected_action = "resume"
                    elif self.how_to_play_button_rect.collidepoint(event.pos):
                        instructions = InstructionsScreen()
                        instructions.display()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        self.focused_index = (self.focused_index + 1) % len(self.button_rects)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.focused_index == 0:
                            self.started = True
                            self.selected_action = "new"
                        elif self.focused_index == 1 and self.resume_enabled:
                            self.started = True
                            self.selected_action = "resume"
                        else:
                            InstructionsScreen().display()

            self.draw()
            pygame.display.flip()
            self.clock.tick(30)
        return self.selected_action or "new"

    def draw(self):
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(constants.BOARD_DARK)

        overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        overlay.set_alpha(80)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        title = self.title_font.render("Nine Men's Morris", True, theme.TEXT_PRIMARY)
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 120))

        shadow = self.title_font.render("Nine Men's Morris", True, (0, 0, 0))
        self.screen.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title, title_rect)

        subtitle = self.subtitle_font.render("An Ancient Strategy Game", True, theme.BRASS_BRIGHT)
        self.screen.blit(subtitle, subtitle.get_rect(center=(constants.SCREEN_WIDTH // 2, 220)))

        pygame.draw.line(self.screen, theme.BRASS, (150, 280), (750, 280), 2)

        desc_font = theme.font(18)
        desc = desc_font.render(
            "Place, move, and capture your opponent's pieces to win", True, theme.TEXT_SECONDARY
        )
        self.screen.blit(desc, desc.get_rect(center=(constants.SCREEN_WIDTH // 2, 330)))

        self.draw_button(self.start_button_rect, "START GAME", "primary", focused_index=0)
        theme.draw_button(
            self.screen,
            self.resume_button_rect,
            "RESUME MATCH",
            self.button_font,
            variant="brass",
            focused=self.focused_index == 1,
            enabled=self.resume_enabled,
        )
        self.draw_button(
            self.how_to_play_button_rect,
            "HOW TO PLAY",
            "secondary",
            focused_index=2,
        )
        if not self.resume_enabled and self.resume_status != "No saved match was found.":
            status = theme.font(14).render(self.resume_status, True, theme.WARNING)
            self.screen.blit(status, status.get_rect(center=(450, 575)))

    def draw_button(self, rect, text, variant, *, focused_index):
        theme.draw_button(
            self.screen,
            rect,
            text,
            self.button_font,
            variant=variant,
            focused=focused_index == self.focused_index,
        )


class InstructionsScreen:
    def __init__(self):
        self.screen = create_window("Nine Men's Morris - How to Play")
        self.clock = pygame.time.Clock()
        self.done = False
        self.scroll_offset = 0
        self.title_font = theme.font(48, bold=True)
        self.heading_font = theme.font(26, bold=True)
        self.text_font = theme.font(18)
        self.back_button_rect = pygame.Rect(50, 665, 150, 40)
        self.focused = True
        self.instructions = self._prepare_instructions()
        self.content_width = constants.SCREEN_WIDTH - 140
        self.visible_content_height = 535
        self.max_scroll = max(0, self._content_height() - self.visible_content_height)

    def _font_for_type(self, text_type):
        if text_type in {"heading", "subheading"}:
            return self.heading_font
        return self.text_font

    def _content_height(self):
        total = 0
        for text, text_type in self.instructions:
            font = self._font_for_type(text_type)
            total += len(wrap_text(text, font, self.content_width)) * (font.get_height() + 5)
        return total

    def _prepare_instructions(self):
        lines = [
            ("ABOUT NINE MEN'S MORRIS", "heading"),
            ("A strategy game where both players can see the full board.", "text"),
            ("", "text"),
            ("OBJECTIVE", "heading"),
            ("Win by reducing your opponent to 2 pieces or blocking all their moves.", "text"),
            ("", "text"),
            ("GAME PHASES", "heading"),
            ("PHASE 1: PLACEMENT", "subheading"),
            ("- Take turns placing 9 pieces on empty board points", "text"),
            ("- Form a mill, which is 3 pieces in one line", "text"),
            ("- After a mill, remove one eligible opponent piece", "text"),
            ("", "text"),
            ("PHASE 2: MOVEMENT", "subheading"),
            ("- Move pieces to adjacent empty points only (no jumping)", "text"),
            ("- Form mills to capture pieces as before", "text"),
            ("- You can break and reform mills later in the game", "text"),
            ("", "text"),
            ("PHASE 3: FLYING (When you have 3 pieces)", "subheading"),
            ("- Move pieces to any empty point on the board", "text"),
            ("- This keeps the endgame from getting stuck too quickly", "text"),
            ("", "text"),
            ("WIN CONDITIONS", "heading"),
            ("- Opponent reduced to 2 pieces or fewer", "text"),
            ("- Opponent with 3+ pieces has no legal adjacent moves", "text"),
            ("- The game stops once a win condition is reached", "text"),
            ("", "text"),
            ("KEY RULES", "heading"),
            ("- Mills are horizontal or vertical, not diagonal", "text"),
            ("- Pieces slide along board lines; no jumping", "text"),
            ("- Captured pieces are permanently removed", "text"),
            ("- With perfect play from both sides, the game is usually a draw", "text"),
            ("", "text"),
            ("GAME MODES", "heading"),
            ("HUMAN VS HUMAN: Two players on one computer", "text"),
            ("EASY: Computer plays random legal moves", "text"),
            ("NORMAL: Computer tries to make and block mills", "text"),
            ("HARD: Computer searches future moves with minimax", "text"),
            ("", "text"),
            ("WINNING STRATEGY", "heading"),
            ("- Control the center for flexibility", "text"),
            ("- Create more than one possible mill", "text"),
            ("- Keep pieces connected for defense", "text"),
            ("- Avoid leaving isolated pieces trapped", "text"),
            ("- Watch the opponent's next mill threat", "text"),
        ]
        return lines

    def display(self):
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.back_button_rect.collidepoint(event.pos):
                        self.done = True
                    # Mouse wheel scroll down
                    elif event.button == 4:  # Scroll up
                        self.scroll_offset = max(0, self.scroll_offset - 40)
                    elif event.button == 5:  # Scroll down
                        self.scroll_offset = min(self.max_scroll, self.scroll_offset + 40)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.scroll_offset = max(0, self.scroll_offset - 30)
                    elif event.key == pygame.K_DOWN:
                        self.scroll_offset = min(self.max_scroll, self.scroll_offset + 30)
                    elif event.key == pygame.K_ESCAPE:
                        self.done = True
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.done = True

            self.draw()
            pygame.display.flip()
            self.clock.tick(30)

    def draw(self):
        self.screen.fill(theme.APP_BACKGROUND)

        title_bar = pygame.Rect(0, 0, constants.SCREEN_WIDTH, 80)
        pygame.draw.rect(self.screen, theme.SURFACE, title_bar)
        pygame.draw.line(
            self.screen,
            theme.BRASS,
            (48, title_bar.bottom - 1),
            (constants.SCREEN_WIDTH - 48, title_bar.bottom - 1),
            2,
        )

        title_text = "How to Play"
        title = self.title_font.render(title_text, True, theme.TEXT_PRIMARY)
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 42))

        title_shadow = self.title_font.render(title_text, True, theme.SHADOW)
        shadow_rect = title_shadow.get_rect(center=(constants.SCREEN_WIDTH // 2 + 2, 42 + 2))
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title, title_rect)

        content_area = pygame.Rect(30, 95, constants.SCREEN_WIDTH - 60, 555)
        theme.draw_panel(
            self.screen,
            content_area,
            fill=theme.SURFACE,
            border=theme.BORDER_WARM,
            radius=theme.RADIUS_LARGE,
            shadow=True,
        )
        y = 110 - self.scroll_offset
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(content_area.inflate(-12, -12))

        for text, text_type in self.instructions:
            if text_type == "heading":
                font = self.heading_font
                color = theme.BRASS_BRIGHT
            elif text_type == "subheading":
                font = self.heading_font
                color = theme.TEAL_BRIGHT
            else:
                font = self.text_font
                color = theme.TEXT_SECONDARY

            for wrapped_line in wrap_text(text, font, self.content_width):
                line = font.render(wrapped_line, True, color)
                if y + font.get_height() > content_area.top and y < content_area.bottom:
                    self.screen.blit(line, (70, y))
                y += font.get_height() + 5
        self.screen.set_clip(previous_clip)
        theme.draw_button(
            self.screen,
            self.back_button_rect,
            "< BACK",
            self.text_font,
            variant="secondary",
            focused=self.focused,
        )
        hint_font = theme.font(14)
        hint = hint_font.render(
            "Use UP/DOWN arrows or mouse wheel to scroll | ESC to go back",
            True,
            theme.TEXT_MUTED,
        )
        self.screen.blit(hint, (230, 678))


class Menu:
    def __init__(self):
        self.screen = create_window("Nine Men's Morris - Game Mode")
        self.clock = pygame.time.Clock()
        self.selected_option = None
        self.title_font = theme.font(52, bold=True)
        self.font = theme.font(24, bold=True)
        self.small_font = theme.font(20)
        self.human_vs_human_button_rect = pygame.Rect(200, 300, 500, 70)
        self.human_vs_computer_button_rect = pygame.Rect(200, 420, 500, 70)
        self.button_rects = [self.human_vs_human_button_rect, self.human_vs_computer_button_rect]
        self.focused_index = 0

    def display_menu(self):
        while self.selected_option is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.human_vs_human_button_rect.collidepoint(event.pos):
                        self.selected_option = constants.H_VS_H
                    elif self.human_vs_computer_button_rect.collidepoint(event.pos):
                        self.selected_option = constants.H_VS_C
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        self.focused_index = (self.focused_index + 1) % len(self.button_rects)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.selected_option = (
                            constants.H_VS_H if self.focused_index == 0 else constants.H_VS_C
                        )

            self.draw_menu()
            pygame.display.flip()
            self.clock.tick(30)

    def draw_menu(self):
        theme.draw_setup_backdrop(self.screen, "Select Game Mode", "Choose how you want to play")
        self.draw_button(
            self.human_vs_human_button_rect, "Human vs Human", "primary", focused_index=0
        )
        self.draw_button(
            self.human_vs_computer_button_rect,
            "Human vs Computer",
            "secondary",
            focused_index=1,
        )

    def draw_button(self, rect, text, variant, *, focused_index):
        theme.draw_button(
            self.screen,
            rect,
            text,
            self.font,
            variant=variant,
            focused=focused_index == self.focused_index,
        )

    def get_selected_option(self):
        return self.selected_option


class DifficultySelector:
    def __init__(self):
        self.screen = create_window("Nine Men's Morris - Select Difficulty")
        self.clock = pygame.time.Clock()
        self.selected_difficulty = None
        self.title_font = theme.font(52, bold=True)
        self.font = theme.font(23, bold=True)
        self.small_font = theme.font(20)
        self.easy_button_rect = pygame.Rect(200, 245, 500, 88)
        self.normal_button_rect = pygame.Rect(200, 365, 500, 88)
        self.hard_button_rect = pygame.Rect(200, 485, 500, 88)
        self.button_rects = [self.easy_button_rect, self.normal_button_rect, self.hard_button_rect]
        self.focused_index = 1

    def display_selector(self):
        while self.selected_difficulty is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.easy_button_rect.collidepoint(event.pos):
                        self.selected_difficulty = constants.EASY
                    elif self.normal_button_rect.collidepoint(event.pos):
                        self.selected_difficulty = constants.NORMAL
                    elif self.hard_button_rect.collidepoint(event.pos):
                        self.selected_difficulty = constants.HARD
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        self.focused_index = (self.focused_index + 1) % len(self.button_rects)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.selected_difficulty = (
                            constants.EASY,
                            constants.NORMAL,
                            constants.HARD,
                        )[self.focused_index]

            self.draw_selector()
            pygame.display.flip()
            self.clock.tick(30)

    def draw_selector(self):
        theme.draw_setup_backdrop(
            self.screen,
            "Select Difficulty",
            "How challenging should your opponent be?",
        )
        descriptions = (
            (self.easy_button_rect, "EASY", "Casual play with random legal moves", "success", 0),
            (
                self.normal_button_rect,
                "NORMAL",
                "Recognizes immediate mills and blocking threats",
                "warning",
                1,
            ),
            (
                self.hard_button_rect,
                "HARD",
                "Searches multiple moves ahead and respects draw risk",
                "danger",
                2,
            ),
        )
        for rect, title, description, variant, index in descriptions:
            theme.draw_button(
                self.screen,
                rect,
                "",
                self.font,
                variant=variant,
                focused=index == self.focused_index,
            )
            title_surface = self.font.render(title, True, theme.TEXT_PRIMARY)
            detail = self.small_font.render(description, True, theme.TEXT_PRIMARY)
            self.screen.blit(
                title_surface, title_surface.get_rect(center=(rect.centerx, rect.y + 29))
            )
            self.screen.blit(detail, detail.get_rect(center=(rect.centerx, rect.y + 61)))

    def draw_button(self, rect, text, variant, *, focused_index):
        theme.draw_button(
            self.screen,
            rect,
            text,
            theme.font(21, bold=True),
            variant=variant,
            focused=focused_index == self.focused_index,
        )

    def get_selected_difficulty(self):
        return self.selected_difficulty
