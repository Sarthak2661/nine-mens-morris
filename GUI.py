import sys

import pygame

import constants
import ui_theme as theme

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
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption("Nine Men's Morris")
        self.clock = pygame.time.Clock()
        self.game = game
        self.clicked_point = None
        self.valid_destinations = []

        self.font = theme.font(22, bold=True)
        self.small_font = theme.font(16)
        self.title_font = theme.font(30, bold=True)
        self.phase_font = theme.font(17, bold=True)

        self.reset_rect = pygame.Rect(constants.SIDEBAR_X, 620, 75, 45)
        self.save_rect = pygame.Rect(constants.SIDEBAR_X + 80, 620, 75, 45)
        self.exit_rect = pygame.Rect(constants.SIDEBAR_X + 160, 620, 75, 45)

        self.moving_piece = None

    def draw_board(self):
        self.screen.fill(theme.APP_BACKGROUND)
        board_rect = pygame.Rect(0, 0, constants.BOARD_PIXELS, constants.BOARD_PIXELS)
        pygame.draw.rect(self.screen, constants.BOARD_DARK, board_rect)

        pygame.draw.rect(self.screen, theme.SHADOW, board_rect, 5)
        pygame.draw.rect(self.screen, theme.BRASS, board_rect.inflate(-8, -8), 2)

        for line in constants.LINES:
            pygame.draw.line(
                self.screen,
                constants.BOARD_LINE_COLOR,
                (line[0] * constants.SQUARESIZE, line[1] * constants.SQUARESIZE),
                (line[2] * constants.SQUARESIZE, line[3] * constants.SQUARESIZE),
                5,
            )

        for row, col in self.valid_destinations:
            x, y = point_center(row, col)
            pulse = abs(int(5 * pygame.time.get_ticks() / 500) % 10 - 5)
            pygame.draw.circle(
                self.screen,
                theme.TEAL_BRIGHT,
                (x, y),
                constants.CIRCLE_RADIUS + 7 + pulse,
                3,
            )

        if self.clicked_point is not None:
            self.draw_highlight(*self.clicked_point)

        for row, col in constants.VALID_POINTS:
            self.draw_point(row, col)

        self.draw_sidebar()

    def draw_point(self, row, col):
        x, y = point_center(row, col)
        piece = self.game.CURRENT_POSITION[row][col]

        if self.moving_piece and self.moving_piece[0] == row and self.moving_piece[1] == col:
            return

        if piece == constants.PLAY1:
            pygame.draw.circle(
                self.screen, constants.PLAY1_COLOR_DARK, (x, y), constants.CIRCLE_RADIUS + 5
            )
            pygame.draw.circle(
                self.screen, constants.PLAY1_COLOR_MAIN, (x, y), constants.CIRCLE_RADIUS + 3
            )
            pygame.draw.circle(
                self.screen,
                constants.PLAY1_COLOR_LIGHT,
                (x - 4, y - 4),
                constants.CIRCLE_RADIUS - 2,
            )
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), constants.CIRCLE_RADIUS + 4, 2)

        elif piece == constants.PLAY2:
            pygame.draw.circle(
                self.screen, constants.PLAY2_COLOR_DARK, (x, y), constants.CIRCLE_RADIUS + 5
            )
            pygame.draw.circle(
                self.screen, constants.PLAY2_COLOR_MAIN, (x, y), constants.CIRCLE_RADIUS + 3
            )
            pygame.draw.circle(
                self.screen,
                constants.PLAY2_COLOR_LIGHT,
                (x - 4, y - 4),
                constants.CIRCLE_RADIUS - 2,
            )
            pygame.draw.circle(self.screen, (100, 100, 100), (x, y), constants.CIRCLE_RADIUS + 4, 2)
        else:
            pygame.draw.circle(self.screen, theme.BRASS, (x, y), 4)

        if self.moving_piece and self.moving_piece[2] == row and self.moving_piece[3] == col:
            self.draw_animated_piece()

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

        if piece == constants.PLAY1:
            pygame.draw.circle(
                self.screen,
                constants.PLAY1_COLOR_DARK,
                (int(current_x), int(current_y)),
                constants.CIRCLE_RADIUS + 5,
            )
            pygame.draw.circle(
                self.screen,
                constants.PLAY1_COLOR_MAIN,
                (int(current_x), int(current_y)),
                constants.CIRCLE_RADIUS + 3,
            )
            pygame.draw.circle(
                self.screen,
                constants.PLAY1_COLOR_LIGHT,
                (int(current_x) - 4, int(current_y) - 4),
                constants.CIRCLE_RADIUS - 2,
            )
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (int(current_x), int(current_y)),
                constants.CIRCLE_RADIUS + 4,
                2,
            )
        elif piece == constants.PLAY2:
            pygame.draw.circle(
                self.screen,
                constants.PLAY2_COLOR_DARK,
                (int(current_x), int(current_y)),
                constants.CIRCLE_RADIUS + 5,
            )
            pygame.draw.circle(
                self.screen,
                constants.PLAY2_COLOR_MAIN,
                (int(current_x), int(current_y)),
                constants.CIRCLE_RADIUS + 3,
            )
            pygame.draw.circle(
                self.screen,
                constants.PLAY2_COLOR_LIGHT,
                (int(current_x) - 4, int(current_y) - 4),
                constants.CIRCLE_RADIUS - 2,
            )
            pygame.draw.circle(
                self.screen,
                (100, 100, 100),
                (int(current_x), int(current_y)),
                constants.CIRCLE_RADIUS + 4,
                2,
            )

    def draw_highlight(self, row, col):
        x, y = point_center(row, col)
        pulse = abs(int(8 * pygame.time.get_ticks() / 600) % 12 - 6)
        pygame.draw.circle(
            self.screen, theme.BRASS_BRIGHT, (x, y), constants.CIRCLE_RADIUS + 14 + pulse, 4
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
        pygame.draw.rect(self.screen, theme.BORDER, msg_rect, width=1, border_radius=5)

        msg_lines = self.game.message.split("\n") if self.game.message else []
        if not msg_lines or (len(msg_lines) == 1 and not msg_lines[0]):
            msg_lines = ["Waiting for action..."]

        msg_line_y = msg_y + 8
        for msg_line in msg_lines[:2]:
            if msg_line.strip():
                self.blit_text(
                    msg_line,
                    self.small_font,
                    theme.TEXT_SECONDARY,
                    constants.SIDEBAR_X + 15,
                    msg_line_y,
                    max_width=225,
                )
                msg_line_y += 20
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
        instr_y = status_y + 165
        if self.game.phase == constants.PHASE1:
            instruction = "Click empty points to place pieces"
        else:
            instruction = "Click piece, then destination"

        instr_rect = pygame.Rect(
            constants.SIDEBAR_X + 8, instr_y, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 28
        )
        pygame.draw.rect(self.screen, theme.SURFACE_RAISED, instr_rect, border_radius=5)
        pygame.draw.rect(self.screen, theme.SUCCESS, instr_rect, width=2, border_radius=5)
        self.blit_text(
            instruction,
            self.small_font,
            theme.TEXT_PRIMARY,
            constants.SIDEBAR_X + 15,
            instr_y + 5,
            max_width=225,
        )
        self.draw_button(self.reset_rect, "Reset", "warning")
        self.draw_button(self.save_rect, "Export", "primary")
        self.draw_button(self.exit_rect, "Exit", "danger")

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

    def draw_button(self, rect, text, variant="secondary"):
        theme.draw_button(self.screen, rect, text, self.small_font, variant=variant)

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
                self.game.save_game()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event.pos)

    def handle_click(self, pos):
        if self.save_rect.collidepoint(pos):
            self.game.save_game()
            self.game.message = "Move history exported."
            return
        if self.reset_rect.collidepoint(pos):
            mode = self.game.game_mode
            difficulty = self.game.difficulty
            self.game.__init__(game_mode=mode, difficulty=difficulty)
            self.clicked_point = None
            self.valid_destinations = []
            return
        if self.exit_rect.collidepoint(pos):
            self.game.save_game()
            pygame.quit()
            sys.exit()
            return
        if self.game.over or self.game.is_computer_turn():
            return

        row, col = get_coords(pos)
        if not (0 <= row < constants.ROWS and 0 <= col < constants.COLS):
            return
        if not self.game.is_valid_point(row, col):
            self.game.last_error = "Click one of the marked board points."
            return

        if self.game.is_remove_piece:
            if self.game.remove_piece(row, col, self.game.get_turn()):
                self.clicked_point = None
                self.valid_destinations = []
                self.run_computer_until_human_turn()
            return

        if self.game.phase == constants.PHASE1:
            if self.game.make_move(row, col):
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

        start = self.clicked_point
        if self.game.make_move(start[0], start[1], row, col):
            self.moving_piece = (start[0], start[1], row, col, pygame.time.get_ticks())
            self.clicked_point = None
            self.valid_destinations = []
        else:
            self.valid_destinations = self.game.get_valid_destinations(*start)

    def run_computer_until_human_turn(self):
        guard = 0
        while self.game.is_computer_turn() and guard < 4:
            self.game.computer_move()
            guard += 1

    def main_loop(self):
        while True:
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
