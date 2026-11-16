from copy import deepcopy
from pathlib import Path
from time import perf_counter
from typing import Any

import constants
from ai import MorrisAI
from game_persistence import SaveGameError, load_payload, save_payload


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
        self.ai = MorrisAI(depth_limit=constants.HARD_AI_DEPTH)
        self.stats = self._empty_stats()
        self.history = [self._history_snapshot("Match started")]

    @staticmethod
    def _empty_stats():
        return {
            "mills_formed": {"1": 0, "2": 0},
            "captures": {"1": 0, "2": 0},
            "missed_blocks": {"1": 0, "2": 0},
            "hard_ai_times_ms": [],
        }

    def board_tuple(self):
        return tuple(self.CURRENT_POSITION[row][col] for row, col in constants.VALID_POINTS)

    def _history_snapshot(self, label):
        return {
            "label": label,
            "board": list(self.board_tuple()),
            "phase": self.phase,
            "turn": self.turn,
            "is_remove_piece": self.is_remove_piece,
            "play1_pieces": self.play1_pieces,
            "play2_pieces": self.play2_pieces,
            "play1_counter": self.play1_counter,
            "play2_counter": self.play2_counter,
            "over": self.over,
            "message": self.message,
            "draw_reason": self.draw_reason,
        }

    def _append_history_snapshot(self, label=None):
        self.history.append(self._history_snapshot(label or self.move_made or "Position updated"))

    def _immediate_threat_count(self, board, player):
        if self.phase == constants.PHASE1:
            return len(self.ai.immediate_placement_mills(board, player))
        return len(self.ai.immediate_mill_moves(board, player))

    def _record_missed_block(self, before_board, player):
        opponent = constants.PLAY2 if player == constants.PLAY1 else constants.PLAY1
        before = self._immediate_threat_count(before_board, opponent)
        after = self._immediate_threat_count(self.board_tuple(), opponent)
        if before and after:
            key = str(player)
            self.stats["missed_blocks"][key] += 1

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

        before_board = self.board_tuple()
        acting_player = self.turn
        if self.phase == constants.PHASE1:
            moved = self.place_piece(row, col, self.turn)
            if not moved:
                return False
            self.record_move(self.get_move(row, col))
            if self.is_mill(row, col, self.turn):
                self.stats["mills_formed"][str(self.turn)] += 1
                self.message = (
                    self.get_player_from_const(self.turn) + ": " + constants.REMOVE_MESSAGE
                )
                self.is_remove_piece = True
                self._record_missed_block(before_board, acting_player)
                self._append_history_snapshot()
                return True
            self.change_turn()
            self._record_missed_block(before_board, acting_player)
            self._append_history_snapshot()
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
                self.stats["mills_formed"][str(self.turn)] += 1
                self.message = (
                    self.get_player_from_const(self.turn) + ": " + constants.REMOVE_MESSAGE
                )
                self.is_remove_piece = True
                self._record_missed_block(before_board, acting_player)
                self._append_history_snapshot()
                return True
            self.change_turn()
            self._record_missed_block(before_board, acting_player)
            self._append_history_snapshot()
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
        self.stats["captures"][str(remover)] += 1
        self.is_remove_piece = False
        self.moves_without_capture = 0
        self.record_move("x" + self.get_move(row, col))
        self.change_turn()
        self._append_history_snapshot()
        return True

    def is_computer_turn(self):
        return self.game_mode == constants.H_VS_C and self.turn == constants.PLAY2 and not self.over

    def computer_move(self):
        if not self.is_computer_turn():
            return False

        started = perf_counter()
        if self.is_remove_piece:
            pieces = self.removable_pieces(constants.PLAY1)
            if pieces:
                row, col = self.ai.choose_capture(
                    self.ai.board_from_matrix(self.CURRENT_POSITION),
                    constants.PLAY2,
                    self.difficulty,
                    self.phase,
                    position_counts=self.position_counts,
                )
                moved = self.remove_piece(row, col, player=constants.PLAY2)
                self._record_hard_ai_time(started)
                return moved
            return False

        if self.phase == constants.PHASE1:
            move = self._best_placement(constants.PLAY2)
            moved = self.make_move(*move)
            self._record_hard_ai_time(started)
            return moved

        if self.phase == constants.PHASE2:
            legal_moves = self.get_all_legal_moves(constants.PLAY2)
            if not legal_moves:
                self.over = True
                self.message = "Player 1 wins the game!"
                return False
            start, end = self._best_movement(legal_moves, constants.PLAY2)
            moved = self.make_move(start[0], start[1], end[0], end[1])
            self._record_hard_ai_time(started)
            return moved

        return False

    def _best_placement(self, player):
        return self.ai.choose_placement(
            self.ai.board_from_matrix(self.CURRENT_POSITION),
            player,
            self.difficulty,
        )

    def _best_movement(self, legal_moves, player):
        if not legal_moves:
            raise ValueError("No legal movement is available.")
        return self.ai.choose_movement(
            self.ai.board_from_matrix(self.CURRENT_POSITION),
            player,
            self.difficulty,
            position_counts=self.position_counts,
            moves_without_capture=self.moves_without_capture,
        )

    def _record_hard_ai_time(self, started):
        if self.difficulty == constants.HARD:
            self.stats["hard_ai_times_ms"].append(round((perf_counter() - started) * 1000, 2))

    def _serializable_position_counts(self):
        return [
            {"board": list(board), "turn": turn, "count": count}
            for (board, turn), count in self.position_counts.items()
        ]

    def to_save_data(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "turn": self.turn,
            "game_mode": self.game_mode,
            "difficulty": self.difficulty,
            "board": list(self.board_tuple()),
            "is_remove_piece": self.is_remove_piece,
            "counter": self.counter,
            "play1_pieces": self.play1_pieces,
            "play2_pieces": self.play2_pieces,
            "play1_counter": self.play1_counter,
            "play2_counter": self.play2_counter,
            "message": self.message,
            "move_made": self.move_made,
            "over": self.over,
            "moves_made": list(self.moves_made),
            "draw_reason": self.draw_reason,
            "moves_without_capture": self.moves_without_capture,
            "position_counts": self._serializable_position_counts(),
            "history": deepcopy(self.history),
            "stats": deepcopy(self.stats),
        }

    def save_game(self, path: str | Path | None = None):
        return save_payload(self.to_save_data(), path)

    @classmethod
    def load_game(cls, path: str | Path | None = None):
        data = load_payload(path)
        game = cls(game_mode=data["game_mode"], difficulty=data["difficulty"])
        game.phase = data["phase"]
        game.turn = data["turn"]
        game.CURRENT_POSITION = deepcopy(constants.CURRENT_POSITION)
        for point, value in zip(constants.VALID_POINTS, data["board"], strict=True):
            game.CURRENT_POSITION[point[0]][point[1]] = value
        game.is_remove_piece = data["is_remove_piece"]
        game.counter = data["counter"]
        game.play1_pieces = data["play1_pieces"]
        game.play2_pieces = data["play2_pieces"]
        game.play1_counter = data["play1_counter"]
        game.play2_counter = data["play2_counter"]
        game.message = data["message"]
        game.move_made = data["move_made"]
        game.over = data["over"]
        game.moves_made = list(data["moves_made"])
        game.last_error = ""
        game.draw_reason = data["draw_reason"]
        game.moves_without_capture = data["moves_without_capture"]
        game.position_counts = {
            (tuple(item["board"]), item["turn"]): item["count"] for item in data["position_counts"]
        }
        game.history = deepcopy(data["history"])
        game.stats = deepcopy(data["stats"])
        game._validate_loaded_invariants()
        return game

    def _validate_loaded_invariants(self):
        for player, pieces, counter in (
            (constants.PLAY1, self.play1_pieces, self.play1_counter),
            (constants.PLAY2, self.play2_pieces, self.play2_counter),
        ):
            unplaced = constants.TOTAL_MENS - counter
            if self.get_on_board_count(player) + unplaced != pieces:
                raise SaveGameError("The saved match has inconsistent piece counts.")

    def game_summary(self):
        if self.draw_reason:
            result = self.draw_reason
        elif self.over:
            result = self.message
        else:
            result = "Match in progress"
        times = self.stats["hard_ai_times_ms"]
        average_time = sum(times) / len(times) if times else 0
        return "\n".join(
            (
                "Nine Men's Morris match summary",
                f"Result: {result}",
                f"Recorded actions: {len(self.moves_made)}",
                f"Player 1 mills formed: {self.stats['mills_formed']['1']}",
                f"Player 2 mills formed: {self.stats['mills_formed']['2']}",
                f"Player 1 captures: {self.stats['captures']['1']}",
                f"Player 2 captures: {self.stats['captures']['2']}",
                f"Missed immediate blocks: {sum(self.stats['missed_blocks'].values())}",
                f"Average Hard AI response: {average_time:.0f} ms",
            )
        )
