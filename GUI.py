import pygame

import constants
import ui_theme as theme
from display import create_window
from game_persistence import SaveGameError
from sound_feedback import SoundFeedback

pygame.init()


def get_coords(mouse_pos):
    col = int(mouse_pos[0] / constants.SQUARESIZE)
    row = int(mouse_pos[1] / constants.SQUARESIZE)
    return row, col


def point_center(row, col):
    return int(col * constants.SQUARESIZE + constants.SQUARESIZE / 2), int(
        row * constants.SQUARESIZE + constants.SQUARESIZE / 2
    )


class NineMensMorrisGUI:
    def __init__(self, game):
        self.screen = create_window("Nine Men's Morris")
        self.clock = pygame.time.Clock()
        self.game = game
        self.clicked_point = None
        self.valid_destinations = []

        self.font = theme.font(22, bold=True)
        self.small_font = theme.font(16)
        self.title_font = theme.font(30, bold=True)
        self.phase_font = theme.font(17, bold=True)

        self.history_rect = pygame.Rect(constants.SIDEBAR_X, 515, 250, 38)
        self.reset_rect = pygame.Rect(constants.SIDEBAR_X, 565, 120, 38)
        self.save_rect = pygame.Rect(constants.SIDEBAR_X + 130, 565, 120, 38)
        self.sound_rect = pygame.Rect(constants.SIDEBAR_X, 613, 120, 38)
        self.contrast_rect = pygame.Rect(constants.SIDEBAR_X + 130, 613, 120, 38)
        self.exit_rect = pygame.Rect(constants.SIDEBAR_X, 661, 250, 42)
        self.control_rects = [
            self.history_rect,
            self.reset_rect,
            self.save_rect,
            self.sound_rect,
            self.contrast_rect,
            self.exit_rect,
        ]
        self.focused_control = 0
        self.board_focus_index = 0
        self.board_keyboard_active = False
        self.high_contrast = False

        self.moving_piece = None
        self.piece_effect = None
        self.capture_effect = None
        self.mill_flash_until = 0
        self.mill_points: list[tuple[int, int]] = []
        self.ai_thinking = False
        self.confirm_action = None
        self.review_open = False
        self.review_index = 0
        self.review_message = ""
        self.return_to_menu = False
        self.sound = SoundFeedback()
        self.game_complete_announced = False

        self.confirm_yes_rect = pygame.Rect(335, 405, 105, 44)
        self.confirm_no_rect = pygame.Rect(460, 405, 105, 44)
        self.rematch_rect = pygame.Rect(220, 500, 140, 46)
        self.menu_rect = pygame.Rect(380, 500, 140, 46)
        self.review_rect = pygame.Rect(540, 500, 140, 46)
        self.review_previous_rect = pygame.Rect(constants.SIDEBAR_X, 555, 120, 42)
        self.review_next_rect = pygame.Rect(constants.SIDEBAR_X + 130, 555, 120, 42)
        self.review_copy_rect = pygame.Rect(constants.SIDEBAR_X, 610, 250, 42)
        self.review_close_rect = pygame.Rect(constants.SIDEBAR_X, 662, 250, 42)

    def draw_board(self):
        self.screen.fill(theme.APP_BACKGROUND)
        board_rect = pygame.Rect(0, 0, constants.BOARD_PIXELS, constants.BOARD_PIXELS)
        board_color = (8, 14, 24) if self.high_contrast else constants.BOARD_DARK
        line_color = (255, 224, 92) if self.high_contrast else constants.BOARD_LINE_COLOR
        pygame.draw.rect(self.screen, board_color, board_rect)

        pygame.draw.rect(self.screen, theme.SHADOW, board_rect, 5)
        pygame.draw.rect(self.screen, theme.BRASS, board_rect.inflate(-8, -8), 2)

        for line in constants.LINES:
            pygame.draw.line(
                self.screen,
                line_color,
                (line[0] * constants.SQUARESIZE, line[1] * constants.SQUARESIZE),
                (line[2] * constants.SQUARESIZE, line[3] * constants.SQUARESIZE),
                5,
            )

        destinations = [] if self.review_open else self.valid_destinations
        for row, col in destinations:
            x, y = point_center(row, col)
            pulse = abs(int(5 * pygame.time.get_ticks() / 500) % 10 - 5)
            pygame.draw.circle(
                self.screen,
                theme.TEAL_BRIGHT,
                (x, y),
                constants.CIRCLE_RADIUS + 7 + pulse,
                3,
            )
            pygame.draw.circle(self.screen, theme.TEXT_PRIMARY, (x, y), 4)

        if self.clicked_point is not None and not self.review_open:
            self.draw_highlight(*self.clicked_point)

        for row, col in constants.VALID_POINTS:
            self.draw_point(row, col)

        if self.board_keyboard_active and not self.review_open:
            self.draw_board_focus()

        if self.review_open:
            self.draw_review_changes()
            self.draw_review_sidebar()
            return

        self.draw_removable_highlights()
        self.draw_mill_feedback()
        self.draw_capture_animation()
        self.draw_sidebar()
        if self.confirm_action:
            self.draw_confirmation()
        elif self.game.over:
            self.draw_end_game_overlay()

    def draw_point(self, row, col):
        x, y = point_center(row, col)
        piece = self.visible_piece(row, col)

        if self.moving_piece and self.moving_piece[0] == row and self.moving_piece[1] == col:
            return

        moving_target = bool(
            self.moving_piece and self.moving_piece[2] == row and self.moving_piece[3] == col
        )

        if piece in (constants.PLAY1, constants.PLAY2) and not moving_target:
            radius = constants.CIRCLE_RADIUS
            if self.piece_effect and self.piece_effect[:3] == (row, col, piece):
                elapsed = pygame.time.get_ticks() - self.piece_effect[3]
                if elapsed < constants.PLACEMENT_ANIMATION_DURATION:
                    progress = max(0.2, elapsed / constants.PLACEMENT_ANIMATION_DURATION)
                    radius = max(4, round(constants.CIRCLE_RADIUS * progress))
                else:
                    self.piece_effect = None
            self.draw_piece(piece, x, y, radius)
        else:
            interactive = self.is_interactive_point(row, col)
            hovered = self.point_is_hovered(x, y)
            radius = 7 if interactive else 4
            color = theme.BRASS_BRIGHT if hovered and interactive else theme.BRASS
            pygame.draw.circle(self.screen, color, (x, y), radius)
            if interactive:
                pygame.draw.circle(self.screen, theme.BORDER_WARM, (x, y), 11, 1)

        if moving_target:
            self.draw_animated_piece()

    def visible_piece(self, row, col):
        if not self.review_open:
            return self.game.CURRENT_POSITION[row][col]
        point_index = constants.VALID_POINTS.index((row, col))
        return self.game.history[self.review_index]["board"][point_index]

    def draw_piece(self, piece, x, y, radius=None):
        radius = constants.CIRCLE_RADIUS if radius is None else radius
        if self.high_contrast and piece == constants.PLAY1:
            dark, main, light, outline = ((0, 0, 0), (12, 16, 24), (45, 55, 72), (0, 230, 255))
        elif self.high_contrast and piece == constants.PLAY2:
            dark, main, light, outline = (
                (255, 255, 255),
                (245, 245, 245),
                (255, 255, 255),
                (255, 70, 210),
            )
        elif piece == constants.PLAY1:
            dark, main, light, outline = (
                constants.PLAY1_COLOR_DARK,
                constants.PLAY1_COLOR_MAIN,
                constants.PLAY1_COLOR_LIGHT,
                theme.TEXT_PRIMARY,
            )
        else:
            dark, main, light, outline = (
                constants.PLAY2_COLOR_DARK,
                constants.PLAY2_COLOR_MAIN,
                constants.PLAY2_COLOR_LIGHT,
                (100, 100, 100),
            )
        pygame.draw.circle(self.screen, dark, (int(x), int(y)), radius + 5)
        pygame.draw.circle(self.screen, main, (int(x), int(y)), radius + 3)
        pygame.draw.circle(
            self.screen,
            light,
            (int(x) - max(2, radius // 4), int(y) - max(2, radius // 4)),
            max(2, radius - 2),
        )
        pygame.draw.circle(self.screen, outline, (int(x), int(y)), radius + 4, 2)
        marker = max(4, radius // 2)
        if piece == constants.PLAY1:
            pygame.draw.line(
                self.screen,
                outline,
                (int(x) - marker, int(y) - marker),
                (int(x) + marker, int(y) + marker),
                2,
            )
            pygame.draw.line(
                self.screen,
                outline,
                (int(x) + marker, int(y) - marker),
                (int(x) - marker, int(y) + marker),
                2,
            )
        else:
            pygame.draw.circle(self.screen, outline, (int(x), int(y)), marker, 2)

    def draw_board_focus(self):
        row, col = constants.VALID_POINTS[self.board_focus_index]
        x, y = point_center(row, col)
        pygame.draw.rect(
            self.screen,
            theme.TEXT_PRIMARY,
            pygame.Rect(x - 25, y - 25, 50, 50),
            width=3,
            border_radius=5,
        )

    @staticmethod
    def point_is_hovered(x, y):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        return (mouse_x - x) ** 2 + (mouse_y - y) ** 2 <= 18**2

    def is_interactive_point(self, row, col):
        if self.game.over or self.game.is_computer_turn() or self.confirm_action:
            return False
        point = (row, col)
        if self.game.is_remove_piece:
            return point in self.game.removable_pieces(self.game.get_opp())
        if self.game.phase == constants.PHASE1:
            return self.game.is_empty(row, col)
        if self.clicked_point is not None:
            return (
                point in self.valid_destinations
                or self.game.CURRENT_POSITION[row][col] == self.game.turn
            )
        return self.game.CURRENT_POSITION[row][col] == self.game.turn

    def draw_animated_piece(self):
        if not self.moving_piece:
            return

        from_row, from_col, to_row, to_col, start_time = self.moving_piece
        elapsed = pygame.time.get_ticks() - start_time
        duration = constants.ANIMATION_DURATION

        if elapsed >= duration:
            self.moving_piece = None
            return

        progress = elapsed / duration

        from_x, from_y = point_center(from_row, from_col)
        to_x, to_y = point_center(to_row, to_col)

        current_x = from_x + (to_x - from_x) * progress
        current_y = from_y + (to_y - from_y) * progress

        piece = self.game.CURRENT_POSITION[to_row][to_col]
        if piece in (constants.PLAY1, constants.PLAY2):
            self.draw_piece(piece, current_x, current_y)

    def draw_removable_highlights(self):
        if not self.game.is_remove_piece:
            return
        pulse = abs(int(5 * pygame.time.get_ticks() / 350) % 10 - 5)
        for row, col in self.game.removable_pieces(self.game.get_opp()):
            x, y = point_center(row, col)
            pygame.draw.circle(
                self.screen,
                theme.DANGER,
                (x, y),
                constants.CIRCLE_RADIUS + 11 + pulse,
                3,
            )
            pygame.draw.line(self.screen, theme.DANGER, (x - 9, y - 9), (x + 9, y + 9), 3)
            pygame.draw.line(self.screen, theme.DANGER, (x + 9, y - 9), (x - 9, y + 9), 3)

    def draw_mill_feedback(self):
        if pygame.time.get_ticks() >= self.mill_flash_until:
            return
        pulse = abs(int(6 * pygame.time.get_ticks() / 250) % 12 - 6)
        for row, col in self.mill_points:
            x, y = point_center(row, col)
            pygame.draw.circle(
                self.screen,
                theme.BRASS_BRIGHT,
                (x, y),
                constants.CIRCLE_RADIUS + 13 + pulse,
                3,
            )

    def draw_capture_animation(self):
        if not self.capture_effect:
            return
        row, col, piece, started = self.capture_effect
        elapsed = pygame.time.get_ticks() - started
        if elapsed >= constants.CAPTURE_ANIMATION_DURATION:
            self.capture_effect = None
            return
        progress = 1 - elapsed / constants.CAPTURE_ANIMATION_DURATION
        x, y = point_center(row, col)
        self.draw_piece(piece, x, y, max(3, round(constants.CIRCLE_RADIUS * progress)))

    def draw_highlight(self, row, col):
        x, y = point_center(row, col)
        pulse = abs(int(8 * pygame.time.get_ticks() / 600) % 12 - 6)
        pygame.draw.circle(
            self.screen, theme.BRASS_BRIGHT, (x, y), constants.CIRCLE_RADIUS + 14 + pulse, 4
        )
        pygame.draw.rect(
            self.screen,
            theme.BRASS_BRIGHT,
            pygame.Rect(x - 24, y - 24, 48, 48),
            width=2,
            border_radius=4,
        )

    def draw_sidebar(self):
        panel = pygame.Rect(
            constants.SIDEBAR_X - 25,
            0,
            constants.SCREEN_WIDTH - constants.SIDEBAR_X + 25,
            constants.SCREEN_HEIGHT,
        )
        pygame.draw.rect(self.screen, theme.SURFACE, panel)
        pygame.draw.line(
            self.screen,
            theme.BRASS,
            (constants.SIDEBAR_X - 25, 0),
            (constants.SIDEBAR_X - 25, constants.SCREEN_HEIGHT),
            4,
        )

        self.blit_text(
            "Nine Men's Morris",
            self.title_font,
            theme.TEXT_PRIMARY,
            constants.SIDEBAR_X + 10,
            12,
        )
        pygame.draw.line(
            self.screen,
            theme.BRASS,
            (constants.SIDEBAR_X + 5, 60),
            (constants.SCREEN_WIDTH - 15, 60),
            2,
        )

        phase_text = (
            "PHASE 1: PLACEMENT" if self.game.phase == constants.PHASE1 else "PHASE 2: MOVEMENT"
        )
        phase_color = (
            theme.BRASS_BRIGHT if self.game.phase == constants.PHASE1 else theme.TEAL_BRIGHT
        )
        phase_bg = pygame.Rect(
            constants.SIDEBAR_X + 8, 68, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 28
        )
        pygame.draw.rect(self.screen, theme.SURFACE_RAISED, phase_bg, border_radius=5)
        pygame.draw.rect(self.screen, phase_color, phase_bg, width=2, border_radius=5)
        self.blit_text(phase_text, self.phase_font, phase_color, constants.SIDEBAR_X + 15, 73)

        if self.game.phase == constants.PHASE2 and self.game.get_player_pieces(self.game.turn) == 3:
            self.blit_text(
                "FLYING MODE ACTIVE",
                self.small_font,
                theme.WARNING,
                constants.SIDEBAR_X + 10,
                100,
            )
            y_base = 130
        else:
            y_base = 110
        turn_color = (
            theme.TEXT_PRIMARY if self.game.turn == constants.PLAY1 else theme.TEXT_SECONDARY
        )
        turn_label = "PLAYER 1 (BLACK)" if self.game.turn == constants.PLAY1 else "PLAYER 2 (WHITE)"
        turn_rect = pygame.Rect(
            constants.SIDEBAR_X + 8, y_base, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 32
        )
        pygame.draw.rect(self.screen, theme.SURFACE_SOFT, turn_rect, border_radius=5)
        pygame.draw.rect(self.screen, turn_color, turn_rect, width=2, border_radius=5)
        self.blit_text(turn_label, self.font, turn_color, constants.SIDEBAR_X + 15, y_base + 5)
        msg_y = y_base + 45
        msg_rect = pygame.Rect(
            constants.SIDEBAR_X + 8, msg_y, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 50
        )
        pygame.draw.rect(self.screen, theme.SURFACE_RAISED, msg_rect, border_radius=5)
        action_color = theme.WARNING if self.ai_thinking else theme.SUCCESS
        pygame.draw.rect(self.screen, action_color, msg_rect, width=2, border_radius=5)
        self.blit_text(
            self.contextual_action(),
            self.phase_font,
            theme.TEXT_PRIMARY,
            constants.SIDEBAR_X + 15,
            msg_y + 14,
            max_width=225,
        )
        if self.game.last_error:
            error_y = msg_y + 55
            error_rect = pygame.Rect(
                constants.SIDEBAR_X + 8,
                error_y,
                constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30,
                35,
            )
            pygame.draw.rect(self.screen, theme.SURFACE_RAISED, error_rect, border_radius=5)
            pygame.draw.rect(self.screen, theme.DANGER, error_rect, width=2, border_radius=5)
            self.blit_text(
                self.game.last_error,
                self.small_font,
                theme.DANGER,
                constants.SIDEBAR_X + 15,
                error_y + 7,
                max_width=225,
            )
            status_y = error_y + 40
        else:
            status_y = msg_y + 55
        self.draw_status_card(
            "BLACK PIECES",
            self.game.get_on_board_count(constants.PLAY1),
            constants.TOTAL_MENS - self.game.play1_counter,
            theme.TEXT_PRIMARY,
            status_y,
        )
        self.draw_status_card(
            "WHITE PIECES",
            self.game.get_on_board_count(constants.PLAY2),
            constants.TOTAL_MENS - self.game.play2_counter,
            theme.TEXT_SECONDARY,
            status_y + 80,
        )
        self.blit_text(
            "Arrow keys: board  |  Tab: controls",
            theme.font(12),
            theme.TEXT_MUTED,
            constants.SIDEBAR_X,
            490,
        )
        self.draw_button(
            self.history_rect,
            "Move history",
            "secondary",
            enabled=len(self.game.history) > 1,
            control_index=0,
        )
        has_history = bool(self.game.moves_made)
        self.draw_button(
            self.reset_rect,
            "Reset",
            "warning",
            enabled=has_history,
            icon="reset",
            control_index=1,
        )
        self.draw_button(
            self.save_rect,
            "Save",
            "primary",
            enabled=has_history,
            icon="save",
            control_index=2,
        )
        sound_label = "Sound" if self.sound.enabled else "Muted"
        sound_icon = "sound" if self.sound.enabled else "mute"
        self.draw_button(
            self.sound_rect,
            sound_label,
            "secondary",
            icon=sound_icon,
            control_index=3,
        )
        self.draw_button(
            self.contrast_rect,
            "Contrast",
            "secondary",
            icon="contrast",
            control_index=4,
        )
        self.draw_button(self.exit_rect, "Exit", "danger", icon="exit", control_index=5)

    def contextual_action(self):
        if self.game.over:
            return "Game complete"
        if self.ai_thinking:
            return (
                "Hard AI is thinking..."
                if self.game.difficulty == constants.HARD
                else "Computer is thinking..."
            )
        current = "black" if self.game.turn == constants.PLAY1 else "white"
        opponent = "white" if self.game.turn == constants.PLAY1 else "black"
        if self.game.is_remove_piece:
            return f"Remove a {opponent} piece"
        if self.game.phase == constants.PHASE1:
            return f"Place a {current} piece"
        if self.clicked_point is not None:
            return "Choose a destination"
        return "Select a piece to move"

    def draw_status_card(self, title, on_board, unplaced, color, y):
        rect = pygame.Rect(
            constants.SIDEBAR_X + 8, y, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 70
        )
        pygame.draw.rect(self.screen, theme.SURFACE_RAISED, rect, border_radius=8)
        pygame.draw.rect(self.screen, color, rect, width=1, border_radius=8)

        self.blit_text(title, self.font, color, constants.SIDEBAR_X + 20, y + 8)

        left_column, right_column = self.status_card_columns(rect)
        on_board_text = self.small_font.render(f"On Board: {on_board}", True, theme.TEXT_SECONDARY)
        to_place_text = self.small_font.render(f"To Place: {unplaced}", True, theme.TEXT_SECONDARY)
        self.screen.blit(on_board_text, on_board_text.get_rect(midleft=left_column.midleft))
        self.screen.blit(to_place_text, to_place_text.get_rect(midright=right_column.midright))

    @staticmethod
    def status_card_columns(rect):
        inner = rect.inflate(-24, 0)
        gap = theme.SPACE_MEDIUM
        column_width = (inner.width - gap) // 2
        left = pygame.Rect(inner.left, rect.top + 34, column_width, 28)
        right = pygame.Rect(left.right + gap, rect.top + 34, column_width, 28)
        return left, right

    def draw_button(
        self,
        rect,
        text,
        variant="secondary",
        *,
        enabled=True,
        icon=None,
        control_index=None,
    ):
        theme.draw_button(
            self.screen,
            rect,
            text,
            theme.font(14, bold=True),
            variant=variant,
            enabled=enabled,
            icon=icon,
            focused=control_index == self.focused_control,
        )

    def draw_modal_backdrop(self):
        shade = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((*theme.OVERLAY, 210))
        self.screen.blit(shade, (0, 0))

    def draw_confirmation(self):
        self.draw_modal_backdrop()
        panel = pygame.Rect(250, 260, 400, 225)
        theme.draw_panel(
            self.screen,
            panel,
            fill=theme.SURFACE,
            border=theme.BRASS,
            radius=theme.RADIUS_LARGE,
            shadow=True,
        )
        title = "Reset this match?" if self.confirm_action == "reset" else "Exit the game?"
        detail = (
            "The current board will be cleared."
            if self.confirm_action == "reset"
            else "Move history will be exported before closing."
        )
        title_surface = self.title_font.render(title, True, theme.TEXT_PRIMARY)
        detail_surface = self.small_font.render(detail, True, theme.TEXT_SECONDARY)
        self.screen.blit(title_surface, title_surface.get_rect(center=(450, 315)))
        self.screen.blit(detail_surface, detail_surface.get_rect(center=(450, 360)))
        theme.draw_button(
            self.screen,
            self.confirm_yes_rect,
            "Confirm",
            self.small_font,
            variant="danger" if self.confirm_action == "exit" else "warning",
            focused=True,
        )
        theme.draw_button(
            self.screen,
            self.confirm_no_rect,
            "Cancel",
            self.small_font,
            variant="secondary",
        )

    def draw_end_game_overlay(self):
        if not self.game_complete_announced:
            self.sound.play("complete")
            self.game_complete_announced = True
        self.draw_modal_backdrop()
        panel = pygame.Rect(150, 90, 600, 475)
        theme.draw_panel(
            self.screen,
            panel,
            fill=theme.SURFACE,
            border=theme.BRASS,
            radius=theme.RADIUS_LARGE,
            shadow=True,
        )
        eyebrow = self.phase_font.render("MATCH COMPLETE", True, theme.BRASS_BRIGHT)
        result_font = self.title_font
        if result_font.size(self.game.message)[0] > 520:
            result_font = theme.font(23, bold=True)
        result = result_font.render(self.game.message, True, theme.TEXT_PRIMARY)
        self.screen.blit(eyebrow, eyebrow.get_rect(center=(450, 135)))
        self.screen.blit(result, result.get_rect(center=(450, 180)))

        times = self.game.stats["hard_ai_times_ms"]
        average_time = sum(times) / len(times) if times else 0
        stats = [
            ("MILLS FORMED", str(sum(self.game.stats["mills_formed"].values()))),
            ("PIECES CAPTURED", str(sum(self.game.stats["captures"].values()))),
            ("MISSED BLOCKS", str(sum(self.game.stats["missed_blocks"].values()))),
            ("HARD AI AVG", f"{average_time:.0f} ms" if times else "Not used"),
        ]
        for index, (label, value_text) in enumerate(stats):
            card = pygame.Rect(205 + (index % 2) * 255, 225 + (index // 2) * 105, 240, 85)
            theme.draw_panel(self.screen, card, fill=theme.SURFACE_RAISED)
            label_surface = theme.font(13, bold=True).render(label, True, theme.TEXT_MUTED)
            value = self.font.render(value_text, True, theme.TEXT_PRIMARY)
            self.screen.blit(
                label_surface, label_surface.get_rect(center=(card.centerx, card.y + 25))
            )
            self.screen.blit(value, value.get_rect(center=(card.centerx, card.y + 57)))

        theme.draw_button(
            self.screen, self.rematch_rect, "Rematch", self.small_font, variant="primary"
        )
        theme.draw_button(
            self.screen, self.menu_rect, "Main menu", self.small_font, variant="secondary"
        )
        theme.draw_button(
            self.screen, self.review_rect, "Review game", self.small_font, variant="brass"
        )

    def draw_review_changes(self):
        if self.review_index <= 0:
            return
        before = self.game.history[self.review_index - 1]["board"]
        after = self.game.history[self.review_index]["board"]
        for index, point in enumerate(constants.VALID_POINTS):
            if before[index] == after[index]:
                continue
            color = theme.DANGER if after[index] == constants.BLANK else theme.TEAL_BRIGHT
            pygame.draw.circle(
                self.screen,
                color,
                point_center(*point),
                constants.CIRCLE_RADIUS + 13,
                4,
            )

    def draw_review_sidebar(self):
        panel = pygame.Rect(
            constants.SIDEBAR_X - 25,
            0,
            constants.SCREEN_WIDTH - constants.SIDEBAR_X + 25,
            constants.SCREEN_HEIGHT,
        )
        pygame.draw.rect(self.screen, theme.SURFACE, panel)
        pygame.draw.line(
            self.screen,
            theme.BRASS,
            (constants.SIDEBAR_X - 25, 0),
            (constants.SIDEBAR_X - 25, constants.SCREEN_HEIGHT),
            4,
        )
        snapshot = self.game.history[self.review_index]
        self.blit_text("Move review", self.title_font, theme.TEXT_PRIMARY, constants.SIDEBAR_X, 18)
        self.blit_text(
            f"STEP {self.review_index} OF {len(self.game.history) - 1}",
            self.phase_font,
            theme.TEAL_BRIGHT,
            constants.SIDEBAR_X,
            65,
        )
        self.blit_text(
            snapshot["label"],
            self.font,
            theme.TEXT_PRIMARY,
            constants.SIDEBAR_X,
            105,
            max_width=250,
        )
        start = max(0, self.review_index - 3)
        end = min(len(self.game.history), start + 7)
        y = 190
        for index in range(start, end):
            item = self.game.history[index]
            color = theme.BRASS_BRIGHT if index == self.review_index else theme.TEXT_SECONDARY
            marker = ">" if index == self.review_index else " "
            self.blit_text(
                f"{marker} {index:02}  {item['label']}",
                self.small_font,
                color,
                constants.SIDEBAR_X,
                y,
                max_width=250,
            )
            y += 42
        if self.review_message:
            self.blit_text(
                self.review_message,
                self.small_font,
                theme.SUCCESS,
                constants.SIDEBAR_X,
                520,
                max_width=250,
            )
        theme.draw_button(
            self.screen,
            self.review_previous_rect,
            "Previous",
            self.small_font,
            enabled=self.review_index > 0,
        )
        theme.draw_button(
            self.screen,
            self.review_next_rect,
            "Next",
            self.small_font,
            enabled=self.review_index < len(self.game.history) - 1,
        )
        theme.draw_button(
            self.screen,
            self.review_copy_rect,
            "Copy game summary",
            self.small_font,
            variant="brass",
        )
        theme.draw_button(
            self.screen,
            self.review_close_rect,
            "Close review",
            self.small_font,
            variant="secondary",
            focused=True,
        )

    def blit_text(self, text, font, color, x, y, max_width=None):
        if max_width is None:
            self.screen.blit(font.render(text, True, color), (x, y))
            return
        words = text.split()
        line = ""
        offset = 0
        for word in words:
            test = (line + " " + word).strip()
            if font.size(test)[0] <= max_width:
                line = test
            else:
                self.screen.blit(font.render(line, True, color), (x, y + offset))
                offset += font.get_linesize()
                line = word
        if line:
            self.screen.blit(font.render(line, True, color), (x, y + offset))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.confirm_action = "exit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            if event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if key == pygame.K_F2:
            self.high_contrast = not self.high_contrast
            return
        if key == pygame.K_ESCAPE:
            if self.review_open:
                self.review_open = False
            elif self.confirm_action:
                self.confirm_action = None
            elif not self.game.over:
                self.confirm_action = "exit"
            return
        if self.review_open and key in (pygame.K_LEFT, pygame.K_RIGHT):
            step = -1 if key == pygame.K_LEFT else 1
            self.review_index = max(
                0,
                min(len(self.game.history) - 1, self.review_index + step),
            )
            self.review_message = ""
            return
        if (
            key in (pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN)
            and not self.confirm_action
            and not self.game.over
        ):
            step = -1 if key in (pygame.K_LEFT, pygame.K_UP) else 1
            self.board_focus_index = (self.board_focus_index + step) % len(constants.VALID_POINTS)
            self.board_keyboard_active = True
            return
        if key == pygame.K_TAB and not self.confirm_action and not self.game.over:
            self.board_keyboard_active = False
            self.focused_control = (self.focused_control + 1) % len(self.control_rects)
            return
        if key not in (pygame.K_RETURN, pygame.K_SPACE):
            return
        if self.review_open:
            self.close_review()
        elif self.confirm_action:
            self.execute_confirmation()
        elif self.game.over:
            self.reset_game()
        elif self.board_keyboard_active:
            self.handle_click(point_center(*constants.VALID_POINTS[self.board_focus_index]))
        else:
            self.handle_click(self.control_rects[self.focused_control].center)

    def handle_click(self, pos):
        if self.review_open:
            if self.review_previous_rect.collidepoint(pos) and self.review_index > 0:
                self.review_index -= 1
                self.review_message = ""
            elif (
                self.review_next_rect.collidepoint(pos)
                and self.review_index < len(self.game.history) - 1
            ):
                self.review_index += 1
                self.review_message = ""
            elif self.review_copy_rect.collidepoint(pos):
                self.copy_game_summary()
            elif self.review_close_rect.collidepoint(pos):
                self.close_review()
            return
        if self.confirm_action:
            if self.confirm_yes_rect.collidepoint(pos):
                self.execute_confirmation()
            elif self.confirm_no_rect.collidepoint(pos):
                self.confirm_action = None
            return
        if self.game.over:
            if self.rematch_rect.collidepoint(pos):
                self.reset_game()
            elif self.menu_rect.collidepoint(pos):
                self.return_to_menu = True
            elif self.review_rect.collidepoint(pos):
                self.open_review()
            return
        if self.sound_rect.collidepoint(pos):
            self.sound.toggle()
            return
        if self.contrast_rect.collidepoint(pos):
            self.high_contrast = not self.high_contrast
            return
        if self.save_rect.collidepoint(pos) and self.game.moves_made:
            try:
                path = self.game.save_game()
                self.game.message = f"Match saved to {path.name}."
            except SaveGameError as exc:
                self.game.last_error = str(exc)
            return
        if self.history_rect.collidepoint(pos) and len(self.game.history) > 1:
            self.open_review()
            return
        if self.reset_rect.collidepoint(pos) and self.game.moves_made:
            self.confirm_action = "reset"
            return
        if self.exit_rect.collidepoint(pos):
            self.confirm_action = "exit"
            return
        if self.game.is_computer_turn():
            return

        if pos[0] < constants.BOARD_PIXELS:
            self.board_keyboard_active = False

        row, col = get_coords(pos)
        if not (0 <= row < constants.ROWS and 0 <= col < constants.COLS):
            return
        if not self.game.is_valid_point(row, col) or not self.is_interactive_point(row, col):
            return

        if self.game.is_remove_piece:
            removed_piece = self.game.CURRENT_POSITION[row][col]
            if self.game.remove_piece(row, col, self.game.get_turn()):
                self.capture_effect = (row, col, removed_piece, pygame.time.get_ticks())
                self.sound.play("capture")
                self.clicked_point = None
                self.valid_destinations = []
                self.run_computer_until_human_turn()
            return

        if self.game.phase == constants.PHASE1:
            player = self.game.turn
            if self.game.make_move(row, col):
                self.piece_effect = (row, col, player, pygame.time.get_ticks())
                self.sound.play("move")
                if self.game.is_remove_piece:
                    self.start_mill_feedback(player)
                self.run_computer_until_human_turn()
            return

        if self.game.phase == constants.PHASE2:
            self.handle_phase2_click(row, col)
            self.run_computer_until_human_turn()

    def handle_phase2_click(self, row, col):
        if self.clicked_point is None:
            if self.game.CURRENT_POSITION[row][col] == self.game.get_turn():
                self.clicked_point = (row, col)
                self.valid_destinations = self.game.get_valid_destinations(row, col)
                self.game.last_error = ""
            else:
                self.game.last_error = "Select one of your own pieces."
            return

        if (row, col) == self.clicked_point:
            self.clicked_point = None
            self.valid_destinations = []
            return

        if self.game.CURRENT_POSITION[row][col] == self.game.get_turn():
            self.clicked_point = (row, col)
            self.valid_destinations = self.game.get_valid_destinations(row, col)
            return

        start = self.clicked_point
        player = self.game.turn
        if self.game.make_move(start[0], start[1], row, col):
            self.moving_piece = (start[0], start[1], row, col, pygame.time.get_ticks())
            self.sound.play("move")
            if self.game.is_remove_piece:
                self.start_mill_feedback(player)
            self.clicked_point = None
            self.valid_destinations = []
        else:
            self.valid_destinations = self.game.get_valid_destinations(*start)

    def run_computer_until_human_turn(self):
        guard = 0
        while self.game.is_computer_turn() and guard < 4:
            before = [row[:] for row in self.game.CURRENT_POSITION]
            self.ai_thinking = True
            self.draw_board()
            pygame.display.flip()
            pygame.event.pump()
            pygame.time.delay(constants.MINIMUM_THINKING_DISPLAY_MS)
            self.game.computer_move()
            self.ai_thinking = False
            self.apply_board_transition_feedback(before)
            self.draw_board()
            pygame.display.flip()
            pygame.event.pump()
            pygame.time.delay(constants.AI_MOVE_FEEDBACK_MS)
            guard += 1

    def start_mill_feedback(self, player):
        points = {
            point
            for mill in constants.MILLS
            if all(self.game.CURRENT_POSITION[row][col] == player for row, col in mill)
            for point in mill
        }
        self.mill_points = sorted(points)
        self.mill_flash_until = pygame.time.get_ticks() + constants.MILL_FEEDBACK_DURATION
        self.sound.play("mill")

    def apply_board_transition_feedback(self, before):
        changed = [
            (row, col, before[row][col], self.game.CURRENT_POSITION[row][col])
            for row, col in constants.VALID_POINTS
            if before[row][col] != self.game.CURRENT_POSITION[row][col]
        ]
        added = [change for change in changed if change[2] == constants.BLANK]
        removed = [change for change in changed if change[3] == constants.BLANK]
        now = pygame.time.get_ticks()
        if added and removed and added[0][3] == removed[0][2]:
            self.moving_piece = (
                removed[0][0],
                removed[0][1],
                added[0][0],
                added[0][1],
                now,
            )
            self.sound.play("move")
        elif added:
            row, col, _old, piece = added[0]
            self.piece_effect = (row, col, piece, now)
            self.sound.play("move")
        elif removed:
            row, col, piece, _new = removed[0]
            self.capture_effect = (row, col, piece, now)
            self.sound.play("capture")
        if self.game.is_remove_piece:
            self.start_mill_feedback(self.game.turn)

    def execute_confirmation(self):
        action = self.confirm_action
        self.confirm_action = None
        if action == "reset":
            self.reset_game()
        elif action == "exit":
            if self.game.moves_made:
                try:
                    self.game.save_game()
                except SaveGameError as exc:
                    self.game.last_error = str(exc)
                    return
            pygame.quit()
            raise SystemExit

    def open_review(self):
        self.review_open = True
        self.review_index = len(self.game.history) - 1
        self.review_message = ""
        self.clicked_point = None
        self.valid_destinations = []

    def close_review(self):
        self.review_open = False
        self.review_message = ""

    def copy_game_summary(self):
        summary = self.game.game_summary()
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, summary.encode("utf-8") + b"\x00")
            self.review_message = "Summary copied to clipboard."
        except pygame.error:
            self.review_message = "Clipboard is unavailable on this system."

    def reset_game(self):
        mode = self.game.game_mode
        difficulty = self.game.difficulty
        self.game.__init__(game_mode=mode, difficulty=difficulty)
        self.clicked_point = None
        self.valid_destinations = []
        self.moving_piece = None
        self.piece_effect = None
        self.capture_effect = None
        self.mill_points = []
        self.mill_flash_until = 0
        self.game_complete_announced = False
        self.review_open = False
        self.review_index = 0
        self.review_message = ""

    def main_loop(self):
        while not self.return_to_menu:
            while self.moving_piece:
                self.draw_board()
                self.handle_events()
                pygame.display.flip()
                self.clock.tick(60)

            self.run_computer_until_human_turn()
            self.draw_board()
            self.handle_events()
            pygame.display.flip()
            self.clock.tick(60)
        return "menu"
