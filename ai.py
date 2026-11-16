from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter
from typing import TypeAlias

import constants

Point: TypeAlias = tuple[int, int]
Move: TypeAlias = tuple[Point, Point]
IndexMove: TypeAlias = tuple[int, int]
Board: TypeAlias = tuple[int, ...]
Successor: TypeAlias = tuple[IndexMove, int | None, Board]
PositionCounts: TypeAlias = dict[tuple[Board, int], int]


@dataclass(frozen=True)
class SearchStats:
    nodes: int = 0
    cache_hits: int = 0
    elapsed_ms: float = 0.0


class MorrisAI:
    """Pure move selection for Nine Men's Morris.

    Search operates on immutable 24-point board tuples, so it cannot mutate the
    live game while considering future positions.
    """

    WIN_SCORE = 100_000

    def __init__(self, depth_limit: int = 3) -> None:
        if depth_limit < 1:
            raise ValueError("depth_limit must be at least 1")
        self.depth_limit = depth_limit
        self.points: tuple[Point, ...] = tuple(constants.VALID_POINTS)
        self.point_index = {point: index for index, point in enumerate(self.points)}
        self.adjacency = tuple(
            tuple(self.point_index[neighbor] for neighbor in constants.ADJACENT_POSITIONS[point])
            for point in self.points
        )
        self.mills = tuple(
            tuple(self.point_index[point] for point in mill) for mill in constants.MILLS
        )
        self._movement_cache: dict[tuple[object, ...], int] = {}
        self._placement_cache: dict[tuple[Board, int, int, int], int] = {}
        self._nodes = 0
        self._cache_hits = 0
        self.last_search = SearchStats()

    def board_from_matrix(self, matrix: list[list[int]]) -> Board:
        return tuple(matrix[row][col] for row, col in self.points)

    def point_move(self, move: IndexMove) -> Move:
        return self.points[move[0]], self.points[move[1]]

    def point_at(self, index: int) -> Point:
        return self.points[index]

    @staticmethod
    def opponent(player: int) -> int:
        return constants.PLAY1 if player == constants.PLAY2 else constants.PLAY2

    def legal_moves(self, board: Board, player: int) -> list[IndexMove]:
        empty = [index for index, value in enumerate(board) if value == constants.BLANK]
        flying = board.count(player) == 3
        moves: list[IndexMove] = []
        for start, value in enumerate(board):
            if value != player:
                continue
            destinations = empty if flying else self.adjacency[start]
            moves.extend((start, end) for end in destinations if board[end] == constants.BLANK)
        return sorted(moves)

    def legal_placements(self, board: Board) -> list[int]:
        return [index for index, value in enumerate(board) if value == constants.BLANK]

    def choose_placement(
        self,
        board: Board,
        player: int,
        difficulty: int,
        rng: random.Random | None = None,
    ) -> Point:
        placements = self.legal_placements(board)
        if not placements:
            raise ValueError("No legal placement is available.")
        if difficulty == constants.EASY:
            return self.points[(rng or random).choice(placements)]

        winning = [
            index for index in placements if self._placement_forms_mill(board, index, player)
        ]
        if winning:
            return self.points[winning[0]]

        opponent = self.opponent(player)
        blocking = [
            index for index in placements if self._placement_forms_mill(board, index, opponent)
        ]
        if blocking:
            return self.points[blocking[0]]

        if difficulty == constants.NORMAL:
            return self.points[(rng or random).choice(placements)]

        started = perf_counter()
        self._start_search()
        best_index = placements[0]
        best_score = -self.WIN_SCORE * 2
        for index in placements:
            child_scores = [
                self._placement_minimax(
                    child,
                    self.opponent(player),
                    self.depth_limit - 1,
                    best_score,
                    self.WIN_SCORE * 2,
                    player,
                )
                for child in self._placement_outcomes(board, index, player)
            ]
            score = max(child_scores)
            if score > best_score:
                best_score = score
                best_index = index
        self._finish_search(started)
        return self.points[best_index]

    def choose_movement(
        self,
        board: Board,
        player: int,
        difficulty: int,
        rng: random.Random | None = None,
        *,
        position_counts: PositionCounts | None = None,
        moves_without_capture: int = 0,
    ) -> Move:
        legal = self.legal_moves(board, player)
        if not legal:
            raise ValueError("No legal movement is available.")
        if difficulty == constants.EASY:
            return self.point_move((rng or random).choice(legal))
        if difficulty == constants.NORMAL:
            return self.point_move(self._choose_normal_movement(board, player, legal))
        return self.point_move(
            self._choose_hard_movement(
                board,
                player,
                legal,
                position_counts=position_counts,
                moves_without_capture=moves_without_capture,
            )
        )

    def choose_capture(
        self,
        board: Board,
        player: int,
        difficulty: int,
        phase: int,
        rng: random.Random | None = None,
        *,
        position_counts: PositionCounts | None = None,
    ) -> Point:
        captures = self.removable_indices(board, self.opponent(player))
        if not captures:
            raise ValueError("No legal capture is available.")
        if difficulty == constants.EASY:
            return self.points[(rng or random).choice(captures)]

        if phase == constants.PHASE1 or difficulty == constants.NORMAL:
            best = max(
                captures,
                key=lambda index: (
                    self.evaluate(self._remove_at(board, index), player),
                    -index,
                ),
            )
            return self.points[best]

        started = perf_counter()
        self._start_search()
        best_index = captures[0]
        best_score = -self.WIN_SCORE * 2
        for index in captures:
            score = self._minimax(
                self._remove_at(board, index),
                self.opponent(player),
                self.depth_limit - 1,
                best_score,
                self.WIN_SCORE * 2,
                player,
                position_counts=position_counts,
                moves_without_capture=0,
            )
            if score > best_score:
                best_score = score
                best_index = index
        self._finish_search(started)
        return self.points[best_index]

    def _choose_normal_movement(
        self, board: Board, player: int, legal: list[IndexMove]
    ) -> IndexMove:
        mill_moves = [move for move in legal if self._move_forms_mill(board, move, player)]
        if mill_moves:
            return mill_moves[0]

        opponent = self.opponent(player)
        current_threats = len(self.immediate_mill_moves(board, opponent))
        scored: list[tuple[int, int, int, IndexMove]] = []
        for move in legal:
            moved = self._apply_move(board, move, player)
            remaining_threats = len(self.immediate_mill_moves(moved, opponent))
            score = self.evaluate(moved, player)
            scored.append((remaining_threats, -score, move[0] * len(board) + move[1], move))

        if current_threats:
            best = min(scored)
            if best[0] < current_threats:
                return best[3]

        return min(scored, key=lambda item: (item[1], item[2]))[3]

    def _choose_hard_movement(
        self,
        board: Board,
        player: int,
        legal: list[IndexMove],
        *,
        position_counts: PositionCounts | None = None,
        moves_without_capture: int = 0,
    ) -> IndexMove:
        started = perf_counter()
        self._start_search()
        best_move = legal[0]
        best_score = -self.WIN_SCORE * 2
        for move in legal:
            scores = []
            for _, capture, child in self._movement_outcomes(board, player, only_move=move):
                scores.append(
                    self._minimax(
                        child,
                        self.opponent(player),
                        self.depth_limit - 1,
                        best_score,
                        self.WIN_SCORE * 2,
                        player,
                        position_counts=position_counts,
                        moves_without_capture=(
                            0 if capture is not None else moves_without_capture + 1
                        ),
                    )
                )
            score = max(scores)
            if score > best_score:
                best_score = score
                best_move = move
        self._finish_search(started)
        return best_move

    def immediate_mill_moves(self, board: Board, player: int) -> list[IndexMove]:
        return [
            move
            for move in self.legal_moves(board, player)
            if self._move_forms_mill(board, move, player)
        ]

    def immediate_placement_mills(self, board: Board, player: int) -> list[int]:
        return [
            index
            for index in self.legal_placements(board)
            if self._placement_forms_mill(board, index, player)
        ]

    def removable_indices(self, board: Board, player: int) -> list[int]:
        pieces = [index for index, value in enumerate(board) if value == player]
        outside_mills = [index for index in pieces if not self._is_mill(board, index, player)]
        return outside_mills or pieces

    def evaluate(self, board: Board, ai_player: int) -> int:
        opponent = self.opponent(ai_player)
        piece_score = (board.count(ai_player) - board.count(opponent)) * 120
        mill_score = (self._mill_count(board, ai_player) - self._mill_count(board, opponent)) * 45
        potential_score = (
            self._potential_mills(board, ai_player) - self._potential_mills(board, opponent)
        ) * 18
        mobility_score = (
            len(self.legal_moves(board, ai_player)) - len(self.legal_moves(board, opponent))
        ) * 4
        return piece_score + mill_score + potential_score + mobility_score

    def _minimax(
        self,
        board: Board,
        player: int,
        depth: int,
        alpha: int,
        beta: int,
        ai_player: int,
        *,
        position_counts: PositionCounts | None = None,
        moves_without_capture: int = 0,
    ) -> int:
        self._nodes += 1
        history = dict(position_counts or {})
        state_key = (board, player)
        history[state_key] = history.get(state_key, 0) + 1
        winner = self._winner(board, player)
        if winner is not None:
            return self.WIN_SCORE + depth if winner == ai_player else -self.WIN_SCORE - depth
        if (
            history[state_key] >= constants.THREEFOLD_REPETITION_COUNT
            or moves_without_capture >= constants.MAX_MOVES_WITHOUT_CAPTURE
        ):
            return 0
        if depth == 0:
            return self.evaluate(board, ai_player)

        key = (
            board,
            player,
            depth,
            ai_player,
            moves_without_capture,
            self._history_signature(history),
        )
        cached = self._movement_cache.get(key)
        if cached is not None:
            self._cache_hits += 1
            return cached

        maximizing = player == ai_player
        value = -self.WIN_SCORE * 2 if maximizing else self.WIN_SCORE * 2
        completed = True
        for _, capture, child in self._movement_outcomes(board, player):
            score = self._minimax(
                child,
                self.opponent(player),
                depth - 1,
                alpha,
                beta,
                ai_player,
                position_counts=history,
                moves_without_capture=(0 if capture is not None else moves_without_capture + 1),
            )
            if maximizing:
                value = max(value, score)
                alpha = max(alpha, value)
            else:
                value = min(value, score)
                beta = min(beta, value)
            if beta <= alpha:
                completed = False
                break

        if completed:
            self._movement_cache[key] = value
        return value

    @staticmethod
    def _history_signature(position_counts: PositionCounts) -> tuple[tuple[Board, int, int], ...]:
        return tuple(
            sorted(
                (board, player, min(count, constants.THREEFOLD_REPETITION_COUNT))
                for (board, player), count in position_counts.items()
            )
        )

    def _placement_minimax(
        self,
        board: Board,
        player: int,
        depth: int,
        alpha: int,
        beta: int,
        ai_player: int,
    ) -> int:
        self._nodes += 1
        if depth == 0 or not self.legal_placements(board):
            return self.evaluate(board, ai_player)

        key = (board, player, depth, ai_player)
        cached = self._placement_cache.get(key)
        if cached is not None:
            self._cache_hits += 1
            return cached

        maximizing = player == ai_player
        value = -self.WIN_SCORE * 2 if maximizing else self.WIN_SCORE * 2
        completed = True
        for index in self.legal_placements(board):
            for child in self._placement_outcomes(board, index, player):
                score = self._placement_minimax(
                    child,
                    self.opponent(player),
                    depth - 1,
                    alpha,
                    beta,
                    ai_player,
                )
                if maximizing:
                    value = max(value, score)
                    alpha = max(alpha, value)
                else:
                    value = min(value, score)
                    beta = min(beta, value)
                if beta <= alpha:
                    completed = False
                    break
            if not completed:
                break

        if completed:
            self._placement_cache[key] = value
        return value

    def _movement_outcomes(
        self, board: Board, player: int, only_move: IndexMove | None = None
    ) -> list[Successor]:
        moves = [only_move] if only_move is not None else self.legal_moves(board, player)
        outcomes: list[Successor] = []
        for move in moves:
            moved = self._apply_move(board, move, player)
            captures = (
                self.removable_indices(moved, self.opponent(player))
                if self._is_mill(moved, move[1], player)
                else []
            )
            if captures:
                outcomes.extend(
                    (move, capture, self._remove_at(moved, capture)) for capture in captures
                )
            else:
                outcomes.append((move, None, moved))
        return outcomes

    def _placement_outcomes(self, board: Board, index: int, player: int) -> list[Board]:
        placed = self._place_at(board, index, player)
        captures = (
            self.removable_indices(placed, self.opponent(player))
            if self._is_mill(placed, index, player)
            else []
        )
        return [self._remove_at(placed, capture) for capture in captures] or [placed]

    def _winner(self, board: Board, player_to_move: int) -> int | None:
        for player in (constants.PLAY1, constants.PLAY2):
            if board.count(player) <= 2:
                return self.opponent(player)
        if not self.legal_moves(board, player_to_move):
            return self.opponent(player_to_move)
        return None

    def _placement_forms_mill(self, board: Board, index: int, player: int) -> bool:
        return self._is_mill(self._place_at(board, index, player), index, player)

    def _move_forms_mill(self, board: Board, move: IndexMove, player: int) -> bool:
        return self._is_mill(self._apply_move(board, move, player), move[1], player)

    def _is_mill(self, board: Board, index: int, player: int) -> bool:
        return any(
            index in mill and all(board[point] == player for point in mill) for mill in self.mills
        )

    def _mill_count(self, board: Board, player: int) -> int:
        return sum(all(board[index] == player for index in mill) for mill in self.mills)

    def _potential_mills(self, board: Board, player: int) -> int:
        return sum(
            values.count(player) == 2 and values.count(constants.BLANK) == 1
            for values in ([board[index] for index in mill] for mill in self.mills)
        )

    @staticmethod
    def _apply_move(board: Board, move: IndexMove, player: int) -> Board:
        start, end = move
        mutable = list(board)
        mutable[start] = constants.BLANK
        mutable[end] = player
        return tuple(mutable)

    @staticmethod
    def _place_at(board: Board, index: int, player: int) -> Board:
        mutable = list(board)
        mutable[index] = player
        return tuple(mutable)

    @staticmethod
    def _remove_at(board: Board, index: int) -> Board:
        mutable = list(board)
        mutable[index] = constants.BLANK
        return tuple(mutable)

    def _start_search(self) -> None:
        self._movement_cache.clear()
        self._placement_cache.clear()
        self._nodes = 0
        self._cache_hits = 0

    def _finish_search(self, started: float) -> None:
        self.last_search = SearchStats(
            nodes=self._nodes,
            cache_hits=self._cache_hits,
            elapsed_ms=(perf_counter() - started) * 1000,
        )
