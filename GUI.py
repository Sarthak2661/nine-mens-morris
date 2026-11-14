import sys

import pygame

import constants

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

        self.font = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.small_font = pygame.font.SysFont("Segoe UI", 16)
        self.title_font = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.phase_font = pygame.font.SysFont("Segoe UI", 18, bold=True)

        self.reset_rect = pygame.Rect(constants.SIDEBAR_X, 620, 75, 45)
        self.save_rect = pygame.Rect(constants.SIDEBAR_X + 80, 620, 75, 45)
        self.exit_rect = pygame.Rect(constants.SIDEBAR_X + 160, 620, 75, 45)

        self.moving_piece = None

    def draw_board(self):
        self.screen.fill((245, 245, 245))
        board_rect = pygame.Rect(0, 0, constants.BOARD_PIXELS, constants.BOARD_PIXELS)
        pygame.draw.rect(self.screen, constants.BOARD_DARK, board_rect)

        pygame.draw.rect(self.screen, (0, 0, 0), board_rect, 5)
        pygame.draw.rect(self.screen, (100, 70, 40), board_rect.inflate(-8, -8), 2)

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
                self.screen, (100, 200, 100), (x, y), constants.CIRCLE_RADIUS + 7 + pulse, 3
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
            pygame.draw.circle(self.screen, (150, 120, 80), (x, y), 4)

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
            self.screen, constants.GOLD, (x, y), constants.CIRCLE_RADIUS + 14 + pulse, 4
        )

    def draw_sidebar(self):
        panel = pygame.Rect(
            constants.SIDEBAR_X - 25,
            0,
            constants.SCREEN_WIDTH - constants.SIDEBAR_X + 25,
            constants.SCREEN_HEIGHT,
        )
        pygame.draw.rect(self.screen, (245, 245, 250), panel)
        pygame.draw.line(
            self.screen,
            (180, 140, 100),
            (constants.SIDEBAR_X - 25, 0),
            (constants.SIDEBAR_X - 25, constants.SCREEN_HEIGHT),
            4,
        )

        self.blit_text(
            "Nine Men's Morris", self.title_font, (30, 30, 60), constants.SIDEBAR_X + 10, 12
        )
        pygame.draw.line(
            self.screen,
            (200, 150, 100),
            (constants.SIDEBAR_X + 5, 60),
            (constants.SCREEN_WIDTH - 15, 60),
            2,
        )

        phase_text = (
            "PHASE 1: PLACEMENT" if self.game.phase == constants.PHASE1 else "PHASE 2: MOVEMENT"
        )
        phase_color = (40, 40, 40) if self.game.phase == constants.PHASE1 else (60, 100, 140)
        phase_bg = pygame.Rect(
            constants.SIDEBAR_X + 8, 68, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 28
        )
        pygame.draw.rect(self.screen, (240, 240, 245), phase_bg, border_radius=5)
        pygame.draw.rect(self.screen, phase_color, phase_bg, width=2, border_radius=5)
        self.blit_text(phase_text, self.phase_font, phase_color, constants.SIDEBAR_X + 15, 73)

        if self.game.phase == constants.PHASE2 and self.game.get_player_pieces(self.game.turn) == 3:
            self.blit_text(
                "FLYING MODE ACTIVE", self.small_font, (220, 80, 0), constants.SIDEBAR_X + 10, 100
            )
            y_base = 130
        else:
            y_base = 110
        turn_color = (40, 40, 40) if self.game.turn == constants.PLAY1 else (100, 100, 100)
        turn_label = "PLAYER 1 (BLACK)" if self.game.turn == constants.PLAY1 else "PLAYER 2 (WHITE)"
        turn_rect = pygame.Rect(
            constants.SIDEBAR_X + 8, y_base, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 32
        )
        pygame.draw.rect(self.screen, (220, 220, 225), turn_rect, border_radius=5)
        pygame.draw.rect(self.screen, turn_color, turn_rect, width=2, border_radius=5)
        self.blit_text(turn_label, self.font, turn_color, constants.SIDEBAR_X + 15, y_base + 5)
        msg_y = y_base + 45
        msg_rect = pygame.Rect(
            constants.SIDEBAR_X + 8, msg_y, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 50
        )
        pygame.draw.rect(self.screen, (255, 255, 255), msg_rect, border_radius=5)
        pygame.draw.rect(self.screen, (200, 200, 200), msg_rect, width=1, border_radius=5)

        msg_lines = self.game.message.split("\n") if self.game.message else []
        if not msg_lines or (len(msg_lines) == 1 and not msg_lines[0]):
            msg_lines = ["Waiting for action..."]

        msg_line_y = msg_y + 8
        for msg_line in msg_lines[:2]:
            if msg_line.strip():
                self.blit_text(
                    msg_line,
                    self.small_font,
                    (30, 30, 60),
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
            pygame.draw.rect(self.screen, (255, 240, 240), error_rect, border_radius=5)
            pygame.draw.rect(self.screen, (200, 50, 50), error_rect, width=2, border_radius=5)
            self.blit_text(
                self.game.last_error,
                self.small_font,
                (150, 30, 30),
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
            (60, 60, 70),
            status_y,
        )
        self.draw_status_card(
            "WHITE PIECES",
            self.game.get_on_board_count(constants.PLAY2),
            constants.TOTAL_MENS - self.game.play2_counter,
            (150, 150, 160),
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
        pygame.draw.rect(self.screen, (240, 250, 240), instr_rect, border_radius=5)
        pygame.draw.rect(self.screen, (80, 140, 80), instr_rect, width=2, border_radius=5)
        self.blit_text(
            instruction,
            self.small_font,
            (40, 100, 40),
            constants.SIDEBAR_X + 15,
            instr_y + 5,
            max_width=225,
        )
        self.draw_button(self.reset_rect, "Reset", (220, 180, 40))
        self.draw_button(self.save_rect, "Save", (80, 120, 180))
        self.draw_button(self.exit_rect, "Exit", (160, 60, 60))

    def draw_status_card(self, title, on_board, unplaced, color, y):
        rect = pygame.Rect(
            constants.SIDEBAR_X + 8, y, constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30, 70
        )
        pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=8)
        pygame.draw.rect(self.screen, color, rect, width=2, border_radius=8)

        self.blit_text(title, self.font, color, constants.SIDEBAR_X + 20, y + 8)

        on_board_text = f"On Board: {on_board}"
        to_place_text = f"To Place: {unplaced}"
        self.blit_text(
            on_board_text, self.small_font, (30, 30, 30), constants.SIDEBAR_X + 20, y + 38
        )
        self.blit_text(
            to_place_text, self.small_font, (30, 30, 30), constants.SIDEBAR_X + 210, y + 38
        )

    def draw_button(self, rect, text, color=constants.GRAY):
        shadow_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height)
        pygame.draw.rect(self.screen, (200, 200, 200), shadow_rect, border_radius=8)

        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 100, 100), rect, width=2, border_radius=8)

        label = self.small_font.render(text, True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=rect.center))

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
            self.game.message = "Game saved."
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
