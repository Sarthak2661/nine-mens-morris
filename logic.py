import os
import random
from copy import deepcopy

import constants


class NineMensMorrisGame:
    def __init__(self, game_mode=constants.H_VS_H, difficulty=None):
        self.phase = constants.PHASE1
        self.turn = constants.PLAY1
        self.game_mode = game_mode
        self.difficulty = difficulty if difficulty is not None else constants.NORMAL
        self.CURRENT_POSITION = deepcopy(constants.CURRENT_POSITION)
        self.is_remove_piece = False
        self.counter = 0
        self.play1_pieces = constants.TOTAL_MENS
        self.play2_pieces = constants.TOTAL_MENS
        self.play1_counter = 0
        self.play2_counter = 0
        self.message = constants.PLAYER1_MESSAGE
        self.move_made = ""
        self.over = False
        self.moves_made = []
        self.last_error = ""
        self.draw_reason = ""
        self.moves_without_capture = 0
        self.position_counts = {}

    def get_turn(self):
        return self.turn

    def get_opp(self):
        return constants.PLAY2 if self.turn == constants.PLAY1 else constants.PLAY1

    def get_player_from_const(self, player):
        return "Player 1" if player == constants.PLAY1 else "Player 2"

    def get_player_pieces(self, player=None):
        player = self.turn if player is None else player
        return self.play1_pieces if player == constants.PLAY1 else self.play2_pieces

    def get_on_board_count(self, player):
        return sum(self.CURRENT_POSITION[row][col] == player for row, col in constants.VALID_POINTS)

    def is_valid_point(self, row, col):
        return (row, col) in constants.VALID_POINTS

    def is_empty(self, row, col):
        return self.CURRENT_POSITION[row][col] == constants.BLANK

    def get_move(self, row, col):
        return constants.POSITIONS[col] + str(abs(row - 7))

    def get_move_text(self, start_row, start_col, end_row=None, end_col=None):
        start = self.get_move(start_row, start_col)
        if end_row is None or end_col is None:
            return start
        return f"{start}->{self.get_move(end_row, end_col)}"

    def record_move(self, text):
        self.move_made = text
        self.moves_made.append(text)
        self.counter += 1

    def update_pieces(self, removed_player):
        if removed_player == constants.PLAY1:
            if self.play1_pieces <= 0:
                raise ValueError("Player 1 piece count cannot become negative.")
            self.play1_pieces -= 1
        elif removed_player == constants.PLAY2:
            if self.play2_pieces <= 0:
                raise ValueError("Player 2 piece count cannot become negative.")
            self.play2_pieces -= 1

    def change_turn(self):
        if self.phase == constants.PHASE1:
            if (
                self.play1_counter == constants.TOTAL_MENS
                and self.play2_counter == constants.TOTAL_MENS
            ):
                self.phase = constants.PHASE2
                self.turn = constants.PLAY1
                self.message = constants.PLAY1_MOVE_MESSAGE
            else:
                self.turn = self.get_opp()
                self.message = (
                    constants.PLAYER1_MESSAGE
                    if self.turn == constants.PLAY1
                    else constants.PLAYER2_MESSAGE
                )
        elif self.phase == constants.PHASE2:
            self.turn = self.get_opp()
            self.message = (
                constants.PLAY1_MOVE_MESSAGE
                if self.turn == constants.PLAY1
                else constants.PLAY2_MOVE_MESSAGE
            )
        else:
            self.message = "Invalid phase"

        if self.phase == constants.PHASE2 and self.get_player_pieces(self.turn) == 3:
            self.message = self.get_player_from_const(self.turn) + constants.FLY_MESSAGE

        winner = self.is_game_over()
        if winner is not None:
            self.over = True
            winner_name = self.get_player_from_const(winner)
            self.message = f"{winner_name} wins the game!"
            return

        self._record_position_and_check_draw()

    def is_game_over(self):
        if self.play1_pieces <= 2:
            return constants.PLAY2
        if self.play2_pieces <= 2:
            return constants.PLAY1

        if self.phase == constants.PHASE2 and not self.get_all_legal_moves(self.turn):
            return self.get_opp()

        return None

    def _position_key(self):
        board = tuple(self.CURRENT_POSITION[row][col] for row, col in constants.VALID_POINTS)
        return board, self.turn

    def _record_position_and_check_draw(self):
        if self.phase != constants.PHASE2 or self.over:
            return

        key = self._position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

        if self.position_counts[key] >= constants.THREEFOLD_REPETITION_COUNT:
            self._declare_draw("Draw by threefold repetition.")
        elif self.moves_without_capture >= constants.MAX_MOVES_WITHOUT_CAPTURE:
            self._declare_draw(
                f"Draw after {constants.MAX_MOVES_WITHOUT_CAPTURE} moves without a capture."
            )

    def _declare_draw(self, reason):
        self.over = True
        self.draw_reason = reason
        self.message = reason

    def make_move(self, row, col, new_row=None, new_col=None):
        self.last_error = ""
        if self.over:
            self.last_error = "Game is already over."
            return False

        if self.phase == constants.PHASE1:
            moved = self.place_piece(row, col, self.turn)
            if not moved:
                return False
            self.record_move(self.get_move(row, col))
            if self.is_mill(row, col, self.turn):
                self.message = (
                    self.get_player_from_const(self.turn) + ": " + constants.REMOVE_MESSAGE
                )
                self.is_remove_piece = True
                return True
            self.change_turn()
            return True

        if self.phase == constants.PHASE2:
            if self.get_player_pieces(self.turn) == 3:
                moved = self.fly_piece(row, col, new_row, new_col, self.turn)
            else:
                moved = self.move_piece(row, col, new_row, new_col, self.turn)
            if not moved:
                return False
            self.record_move(self.get_move_text(row, col, new_row, new_col))
            self.moves_without_capture += 1
            if self.is_mill(new_row, new_col, self.turn):
                self.message = (
                    self.get_player_from_const(self.turn) + ": " + constants.REMOVE_MESSAGE
                )
                self.is_remove_piece = True
                return True
            self.change_turn()
            return True

        self.last_error = "Unsupported game phase."
        return False

    def place_piece(self, row, col, player):
        if not self.is_valid_point(row, col):
            self.last_error = "Select a valid board point."
            return False
        if not self.is_empty(row, col):
            self.last_error = "That point is already occupied."
            return False
        if player == constants.PLAY1 and self.play1_counter >= constants.TOTAL_MENS:
            self.last_error = "Player 1 has no pieces left to place."
            return False
        if player == constants.PLAY2 and self.play2_counter >= constants.TOTAL_MENS:
            self.last_error = "Player 2 has no pieces left to place."
            return False

        self.CURRENT_POSITION[row][col] = player
        if player == constants.PLAY1:
            self.play1_counter += 1
        else:
            self.play2_counter += 1
        return True

    def is_move_valid(self, row, col, new_row=None, new_col=None):
        if self.phase == constants.PHASE1:
            return self.is_valid_point(row, col) and self.is_empty(row, col)

        if self.phase == constants.PHASE2:
            if None in (new_row, new_col):
                return False
            if not self.is_valid_point(row, col) or not self.is_valid_point(new_row, new_col):
                return False
            if self.CURRENT_POSITION[row][col] != self.turn:
                return False
            if not self.is_empty(new_row, new_col):
                return False
            if self.get_player_pieces(self.turn) == 3:
                return True  # Flying rule
            return (new_row, new_col) in constants.ADJACENT_POSITIONS[(row, col)]

        return False

    def move_piece(self, start_row, start_col, end_row, end_col, player):
        if player != self.turn:
            self.last_error = "It is not this player's turn."
            return False
        if not self.is_move_valid(start_row, start_col, end_row, end_col):
            self.last_error = "Move must go to an adjacent empty point."
            return False
        self.CURRENT_POSITION[start_row][start_col] = constants.BLANK
        self.CURRENT_POSITION[end_row][end_col] = player
        return True

    def fly_piece(self, start_row, start_col, end_row, end_col, player):
        if player != self.turn:
            self.last_error = "It is not this player's turn."
            return False
        if self.get_player_pieces(player) != 3:
            self.last_error = "Flying is only allowed with exactly three pieces."
            return False
        if not self.is_move_valid(start_row, start_col, end_row, end_col):
            self.last_error = "Flying move must land on an empty valid point."
            return False
        self.CURRENT_POSITION[start_row][start_col] = constants.BLANK
        self.CURRENT_POSITION[end_row][end_col] = player
        return True

    def get_valid_moves(self):
        return [[r, c] for r, c in constants.VALID_POINTS if self.is_empty(r, c)]

    def get_valid_destinations(self, row, col):
        if not self.is_valid_point(row, col) or self.CURRENT_POSITION[row][col] != self.turn:
            return []
        if self.phase != constants.PHASE2:
            return []
        if self.get_player_pieces(self.turn) == 3:
            return [point for point in constants.VALID_POINTS if self.is_empty(*point)]
        return [
            point for point in constants.ADJACENT_POSITIONS[(row, col)] if self.is_empty(*point)
        ]

    def get_all_legal_moves(self, player):
        moves: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for row, col in constants.VALID_POINTS:
            if self.CURRENT_POSITION[row][col] != player:
                continue
            if self.get_player_pieces(player) == 3:
                destinations = [point for point in constants.VALID_POINTS if self.is_empty(*point)]
            else:
                destinations = [
                    point
                    for point in constants.ADJACENT_POSITIONS[(row, col)]
                    if self.is_empty(*point)
                ]
            moves.extend(((row, col), dest) for dest in destinations)
        return moves

    def is_mill(self, row, col, player):
        if not self.is_valid_point(row, col):
            return False
        if self.CURRENT_POSITION[row][col] != player:
            return False
        return any(
            (row, col) in mill and all(self.CURRENT_POSITION[r][c] == player for r, c in mill)
            for mill in constants.MILLS
        )

    def is_mill_at_position(self, row, col):
        player = self.CURRENT_POSITION[row][col]
        if player == constants.BLANK:
            return False
        return self.is_mill(row, col, player)

    def removable_pieces(self, player_to_remove=None):
        player_to_remove = self.get_opp() if player_to_remove is None else player_to_remove
        pieces = [
            (r, c)
            for r, c in constants.VALID_POINTS
            if self.CURRENT_POSITION[r][c] == player_to_remove
        ]
        non_mill_pieces = [(r, c) for r, c in pieces if not self.is_mill_at_position(r, c)]
        return non_mill_pieces or pieces

    def remove_piece(self, row, col, player=None):
        if not self.is_remove_piece:
            self.last_error = "No capture is currently available."
            return False
        if not self.is_valid_point(row, col):
            self.last_error = "Select a valid point to remove."
            return False

        remover = self.turn if player is None else player
        target = self.CURRENT_POSITION[row][col]
        if target == constants.BLANK:
            self.last_error = "Cannot remove an empty point."
            return False
        if target == remover:
            self.last_error = "You must remove an opponent piece."
            return False
        if (row, col) not in self.removable_pieces(target):
            self.last_error = (
                "You cannot remove a piece from a mill while other opponent pieces are free."
            )
            return False

        self.CURRENT_POSITION[row][col] = constants.BLANK
        self.update_pieces(target)
        self.is_remove_piece = False
        self.moves_without_capture = 0
        self.record_move("x" + self.get_move(row, col))
        self.change_turn()
        return True

    def is_computer_turn(self):
        return self.game_mode == constants.H_VS_C and self.turn == constants.PLAY2 and not self.over

    def computer_move(self):
        if not self.is_computer_turn():
            return False

        if self.is_remove_piece:
            pieces = self.removable_pieces(constants.PLAY1)
            if pieces:
                row, col = pieces[0]
                return self.remove_piece(row, col, player=constants.PLAY2)
            return False

        if self.phase == constants.PHASE1:
            move = self._best_placement(constants.PLAY2)
            return self.make_move(*move)

        if self.phase == constants.PHASE2:
            legal_moves = self.get_all_legal_moves(constants.PLAY2)
            if not legal_moves:
                self.over = True
                self.message = "Player 1 wins the game!"
                return False
            start, end = self._best_movement(legal_moves, constants.PLAY2)
            return self.make_move(start[0], start[1], end[0], end[1])

        return False

    def _best_placement(self, player):
        empty_points = [tuple(move) for move in self.get_valid_moves()]

        if self.difficulty == constants.EASY:
            return random.choice(empty_points)

        opponent = constants.PLAY1 if player == constants.PLAY2 else constants.PLAY2

        for row, col in empty_points:
            self.CURRENT_POSITION[row][col] = player
            forms_mill = self.is_mill(row, col, player)
            self.CURRENT_POSITION[row][col] = constants.BLANK
            if forms_mill:
                return row, col

        for row, col in empty_points:
            self.CURRENT_POSITION[row][col] = opponent
            blocks = self.is_mill(row, col, opponent)
            self.CURRENT_POSITION[row][col] = constants.BLANK
            if blocks:
                return row, col

        if self.difficulty == constants.HARD:
            scoring_positions = []
            for row, col in empty_points:
                score = self._score_placement_hard(row, col, player, opponent)
                scoring_positions.append((score, (row, col)))
            if scoring_positions:
                scoring_positions.sort(reverse=True, key=lambda x: x[0])
                return scoring_positions[0][1]

        return random.choice(empty_points)

    def _score_placement_hard(self, row, col, player, opponent):
        score = 0

        adjacent_positions = constants.ADJACENT_POSITIONS.get((row, col), [])
        for adj_row, adj_col in adjacent_positions:
            if self.CURRENT_POSITION[adj_row][adj_col] == player:
                score += 2

        for adj_row, adj_col in adjacent_positions:
            if self.CURRENT_POSITION[adj_row][adj_col] == opponent:
                score -= 1

        return score

    def _best_movement(self, legal_moves, player):
        if self.difficulty == constants.EASY:
            return random.choice(legal_moves)

        opponent = constants.PLAY1 if player == constants.PLAY2 else constants.PLAY2

        for start, end in legal_moves:
            self.CURRENT_POSITION[start[0]][start[1]] = constants.BLANK
            self.CURRENT_POSITION[end[0]][end[1]] = player
            forms_mill = self.is_mill(end[0], end[1], player)
            self.CURRENT_POSITION[end[0]][end[1]] = constants.BLANK
            self.CURRENT_POSITION[start[0]][start[1]] = player
            if forms_mill:
                return start, end

        if self.difficulty == constants.HARD:
            scored_moves = []
            for start, end in legal_moves:
                score = self._score_movement_hard(start, end, player, opponent)
                scored_moves.append((score, start, end))

            if scored_moves:
                scored_moves.sort(reverse=True, key=lambda x: x[0])
                _, start, end = scored_moves[0]
                return start, end

        return random.choice(legal_moves)

    def _score_movement_hard(self, start, end, player, opponent):
        score = 0

        end_row, end_col = end

        center_distance = abs(end_row - 3) + abs(end_col - 3)
        score += (6 - center_distance) * 2

        adjacent_positions = constants.ADJACENT_POSITIONS.get(end, [])
        same_player_adjacent = sum(
            1 for r, c in adjacent_positions if self.CURRENT_POSITION[r][c] == player
        )
        score += same_player_adjacent * 2

        start_row, start_col = start
        start_adjacent = sum(
            1
            for r, c in constants.ADJACENT_POSITIONS.get(start, [])
            if self.CURRENT_POSITION[r][c] == player
        )
        if start_adjacent > 0:
            score -= 1

        return score

    def save_game(self):
        if os.path.exists(constants.GAME_STATE_FILE):
            os.remove(constants.GAME_STATE_FILE)
        with open(constants.GAME_STATE_FILE, "w", encoding="utf-8") as state_file:
            state_file.write(",".join(self.moves_made))
