import random
import time
import unittest

import constants
from ai import MorrisAI


class MorrisAITacticalTests(unittest.TestCase):
    def setUp(self):
        self.ai = MorrisAI(depth_limit=3)

    def board(self, player1, player2):
        return tuple(
            constants.PLAY1
            if point in player1
            else constants.PLAY2
            if point in player2
            else constants.BLANK
            for point in self.ai.points
        )

    def blocking_position(self):
        return self.board(
            {(1, 1), (1, 5), (0, 3), (6, 6)},
            {(2, 3), (6, 0), (6, 3), (3, 4)},
        )

    def forced_flying_win(self):
        return self.board(
            {(6, 0), (6, 3), (5, 5)},
            {(0, 0), (0, 3), (6, 6)},
        )

    def test_depth_limit_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            MorrisAI(depth_limit=0)

    def test_easy_movement_is_random_but_always_legal(self):
        board = self.blocking_position()
        legal = {self.ai.point_move(move) for move in self.ai.legal_moves(board, constants.PLAY2)}
        choices = {
            self.ai.choose_movement(
                board,
                constants.PLAY2,
                constants.EASY,
                random.Random(seed),
            )
            for seed in range(12)
        }
        self.assertTrue(choices <= legal)
        self.assertGreater(len(choices), 1)

    def test_normal_takes_an_immediate_mill(self):
        board = self.board(
            {(6, 0), (6, 3), (5, 5), (3, 4)},
            {(0, 0), (0, 3), (3, 6), (1, 1)},
        )
        self.assertEqual(
            self.ai.choose_movement(board, constants.PLAY2, constants.NORMAL),
            ((3, 6), (0, 6)),
        )

    def test_normal_blocks_an_immediate_movement_threat(self):
        board = self.blocking_position()
        self.assertEqual(
            self.ai.choose_movement(board, constants.PLAY2, constants.NORMAL),
            ((2, 3), (1, 3)),
        )

    def test_hard_blocks_threat_deterministically(self):
        board = self.blocking_position()
        original = board
        first = self.ai.choose_movement(board, constants.PLAY2, constants.HARD)
        second = self.ai.choose_movement(board, constants.PLAY2, constants.HARD)
        self.assertEqual(first, ((2, 3), (1, 3)))
        self.assertEqual(first, second)
        self.assertEqual(board, original)

    def test_hard_finds_forced_flying_win(self):
        board = self.forced_flying_win()
        move = self.ai.choose_movement(board, constants.PLAY2, constants.HARD)
        self.assertEqual(move, ((6, 6), (0, 6)))
        self.assertGreater(self.ai.last_search.nodes, 0)

    def test_hard_selects_tactical_capture(self):
        board = self.board(
            {(1, 1), (1, 3), (3, 6), (6, 6)},
            {(0, 0), (0, 3), (0, 6), (3, 4)},
        )
        capture = self.ai.choose_capture(
            board,
            constants.PLAY2,
            constants.HARD,
            constants.PHASE2,
        )
        self.assertEqual(capture, (1, 3))

    def test_hard_placement_is_legal_and_deterministic(self):
        board = self.board({(1, 1), (5, 5)}, {(0, 0), (6, 6)})
        first = self.ai.choose_placement(board, constants.PLAY2, constants.HARD)
        second = self.ai.choose_placement(board, constants.PLAY2, constants.HARD)
        self.assertEqual(first, second)
        self.assertEqual(board[self.ai.point_index[first]], constants.BLANK)

    def test_capture_choices_are_legal_for_every_difficulty(self):
        board = self.board(
            {(1, 1), (1, 3), (3, 6), (6, 6)},
            {(0, 0), (0, 3), (0, 6), (3, 4)},
        )
        legal = {
            self.ai.point_at(index) for index in self.ai.removable_indices(board, constants.PLAY1)
        }
        for difficulty in (constants.EASY, constants.NORMAL, constants.HARD):
            with self.subTest(difficulty=difficulty):
                capture = self.ai.choose_capture(
                    board,
                    constants.PLAY2,
                    difficulty,
                    constants.PHASE2,
                    random.Random(7),
                )
                self.assertIn(capture, legal)

    def test_hard_search_meets_interactive_latency_budget(self):
        board = self.blocking_position()
        started = time.perf_counter()
        move = self.ai.choose_movement(board, constants.PLAY2, constants.HARD)
        elapsed = time.perf_counter() - started
        legal = {self.ai.point_move(item) for item in self.ai.legal_moves(board, constants.PLAY2)}
        self.assertIn(move, legal)
        self.assertLess(elapsed, 5.0)


if __name__ == "__main__":
    unittest.main()
