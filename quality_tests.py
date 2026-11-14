import os
import tempfile
import unittest
from unittest.mock import patch

import constants
from logic import NineMensMorrisGame


class LogicQualityTests(unittest.TestCase):
    def movement_game(self, turn=constants.PLAY1, difficulty=constants.NORMAL):
        game = NineMensMorrisGame(game_mode=constants.H_VS_C, difficulty=difficulty)
        game.phase = constants.PHASE2
        game.turn = turn
        game.play1_counter = constants.TOTAL_MENS
        game.play2_counter = constants.TOTAL_MENS
        game.play1_pieces = 4
        game.play2_pieces = 4
        for point in ((0, 0), (1, 1), (2, 2), (3, 2)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        for point in ((6, 6), (5, 5), (4, 4), (3, 4)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        return game

    def assert_valid_state(self, game):
        self.assertGreaterEqual(game.play1_pieces, 0)
        self.assertGreaterEqual(game.play2_pieces, 0)
        for row in range(constants.ROWS):
            for col in range(constants.COLS):
                value = game.CURRENT_POSITION[row][col]
                self.assertIn(value, (constants.BLANK, constants.PLAY1, constants.PLAY2))
                if (row, col) not in constants.VALID_POINTS:
                    self.assertEqual(value, constants.BLANK)

    def test_move_notation_helpers_cover_placement_and_movement(self):
        game = NineMensMorrisGame()
        self.assertEqual(game.get_move_text(0, 0), "a7")
        self.assertEqual(game.get_move_text(0, 0, 0, 3), "a7->d7")

    def test_piece_counts_cannot_become_negative(self):
        game = NineMensMorrisGame()
        game.play1_pieces = 0
        game.play2_pieces = 0
        with self.assertRaisesRegex(ValueError, "Player 1"):
            game.update_pieces(constants.PLAY1)
        with self.assertRaisesRegex(ValueError, "Player 2"):
            game.update_pieces(constants.PLAY2)
        game.update_pieces(999)
        self.assertEqual((game.play1_pieces, game.play2_pieces), (0, 0))

    def test_change_turn_handles_flying_and_invalid_phase_messages(self):
        game = self.movement_game()
        game.play2_pieces = 3
        game.CURRENT_POSITION[6][6] = constants.BLANK
        game.change_turn()
        self.assertIn("flying", game.message)

        game = NineMensMorrisGame()
        game.phase = 999
        game.change_turn()
        self.assertEqual(game.message, "Invalid phase")

    def test_make_move_rejects_finished_and_unsupported_games(self):
        game = NineMensMorrisGame()
        game.over = True
        self.assertFalse(game.make_move(0, 0))
        self.assertEqual(game.last_error, "Game is already over.")

        game = NineMensMorrisGame()
        game.phase = 999
        self.assertFalse(game.make_move(0, 0))
        self.assertEqual(game.last_error, "Unsupported game phase.")

    def test_placement_mill_allows_exactly_one_capture(self):
        game = NineMensMorrisGame()
        game.CURRENT_POSITION[0][0] = constants.PLAY1
        game.CURRENT_POSITION[0][3] = constants.PLAY1
        game.CURRENT_POSITION[6][6] = constants.PLAY2
        game.play1_counter = 2
        game.play2_counter = 1

        self.assertTrue(game.make_move(0, 6))
        self.assertTrue(game.is_remove_piece)
        self.assertTrue(game.remove_piece(6, 6))
        self.assertFalse(game.is_remove_piece)
        self.assertFalse(game.remove_piece(0, 0))
        self.assert_valid_state(game)

    def test_movement_mill_enters_capture_mode(self):
        game = self.movement_game()
        game.CURRENT_POSITION = [row[:] for row in constants.CURRENT_POSITION]
        game.play1_pieces = 4
        game.play2_pieces = 4
        for point in ((0, 0), (0, 3), (3, 6), (1, 1)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        for point in ((6, 0), (6, 3), (6, 6), (5, 1)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2

        self.assertTrue(game.make_move(3, 6, 0, 6))
        self.assertTrue(game.is_remove_piece)
        self.assertEqual(game.turn, constants.PLAY1)

    def test_failed_and_legal_moves_preserve_piece_totals(self):
        game = self.movement_game()
        before_counts = (game.play1_pieces, game.play2_pieces)
        before_occupied = sum(game.get_on_board_count(player) for player in (1, 2))

        self.assertFalse(game.make_move(0, 0, 6, 0))
        self.assertEqual((game.play1_pieces, game.play2_pieces), before_counts)
        self.assertEqual(
            sum(game.get_on_board_count(player) for player in (1, 2)),
            before_occupied,
        )

        self.assertTrue(game.make_move(0, 0, 0, 3))
        self.assertEqual((game.play1_pieces, game.play2_pieces), before_counts)
        self.assertEqual(
            sum(game.get_on_board_count(player) for player in (1, 2)),
            before_occupied,
        )
        self.assert_valid_state(game)

    def test_place_piece_rejects_every_invalid_case(self):
        game = NineMensMorrisGame()
        self.assertFalse(game.place_piece(3, 3, constants.PLAY1))
        self.assertTrue(game.place_piece(0, 0, constants.PLAY1))
        self.assertFalse(game.place_piece(0, 0, constants.PLAY2))

        game.play1_counter = constants.TOTAL_MENS
        self.assertFalse(game.place_piece(0, 3, constants.PLAY1))
        game.play2_counter = constants.TOTAL_MENS
        self.assertFalse(game.place_piece(0, 3, constants.PLAY2))

    def test_is_move_valid_covers_all_rule_branches(self):
        game = NineMensMorrisGame()
        self.assertTrue(game.is_move_valid(0, 0))
        self.assertFalse(game.is_move_valid(3, 3))

        game = self.movement_game()
        self.assertFalse(game.is_move_valid(0, 0))
        self.assertFalse(game.is_move_valid(3, 3, 0, 3))
        self.assertFalse(game.is_move_valid(0, 0, 3, 3))
        self.assertFalse(game.is_move_valid(6, 6, 6, 3))
        self.assertFalse(game.is_move_valid(0, 0, 1, 1))
        self.assertTrue(game.is_move_valid(0, 0, 0, 3))
        self.assertFalse(game.is_move_valid(0, 0, 6, 0))

        game.play1_pieces = 3
        self.assertTrue(game.is_move_valid(0, 0, 6, 0))
        game.phase = 999
        self.assertFalse(game.is_move_valid(0, 0, 0, 3))

    def test_direct_move_and_fly_validation_errors(self):
        game = self.movement_game()
        self.assertFalse(game.move_piece(6, 6, 6, 3, constants.PLAY2))
        self.assertFalse(game.move_piece(0, 0, 6, 0, constants.PLAY1))

        self.assertFalse(game.fly_piece(0, 0, 6, 0, constants.PLAY2))
        self.assertFalse(game.fly_piece(0, 0, 6, 0, constants.PLAY1))
        game.play1_pieces = 3
        self.assertFalse(game.fly_piece(0, 0, 1, 1, constants.PLAY1))
        self.assertTrue(game.fly_piece(0, 0, 6, 0, constants.PLAY1))

    def test_valid_destination_queries_cover_all_phases(self):
        game = NineMensMorrisGame()
        self.assertEqual(game.get_valid_destinations(3, 3), [])
        self.assertEqual(game.get_valid_destinations(0, 0), [])
        game.CURRENT_POSITION[0][0] = constants.PLAY1
        self.assertEqual(game.get_valid_destinations(0, 0), [])

        game.phase = constants.PHASE2
        game.play1_pieces = 4
        self.assertEqual(game.get_valid_destinations(0, 0), [(0, 3), (3, 0)])
        game.play1_pieces = 3
        destinations = game.get_valid_destinations(0, 0)
        self.assertIn((6, 6), destinations)

    def test_mill_queries_reject_invalid_wrong_and_empty_points(self):
        game = NineMensMorrisGame()
        self.assertFalse(game.is_mill(3, 3, constants.PLAY1))
        self.assertFalse(game.is_mill(0, 0, constants.PLAY1))
        self.assertFalse(game.is_mill_at_position(0, 0))
        for point in ((0, 0), (0, 3), (0, 6)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        self.assertTrue(game.is_mill_at_position(0, 3))

    def test_remove_piece_reports_invalid_empty_own_and_protected_targets(self):
        game = NineMensMorrisGame()
        game.is_remove_piece = True
        self.assertFalse(game.remove_piece(3, 3))
        self.assertFalse(game.remove_piece(0, 0))

        game.CURRENT_POSITION[0][0] = constants.PLAY1
        self.assertFalse(game.remove_piece(0, 0))

        for point in ((0, 0), (0, 3), (0, 6), (6, 6)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        self.assertFalse(game.remove_piece(0, 3))

    def test_computer_move_handles_non_turn_capture_and_unknown_phase(self):
        game = NineMensMorrisGame(game_mode=constants.H_VS_C)
        self.assertFalse(game.computer_move())

        game.turn = constants.PLAY2
        game.is_remove_piece = True
        game.CURRENT_POSITION[0][0] = constants.PLAY1
        self.assertTrue(game.computer_move())

        game = NineMensMorrisGame(game_mode=constants.H_VS_C)
        game.turn = constants.PLAY2
        game.is_remove_piece = True
        self.assertFalse(game.computer_move())

        game.is_remove_piece = False
        game.phase = 999
        self.assertFalse(game.computer_move())

    def test_computer_movement_handles_legal_and_blocked_positions(self):
        game = self.movement_game(turn=constants.PLAY2, difficulty=constants.EASY)
        before = tuple(tuple(row) for row in game.CURRENT_POSITION)
        self.assertTrue(game.computer_move())
        self.assertNotEqual(tuple(tuple(row) for row in game.CURRENT_POSITION), before)
        self.assert_valid_state(game)

        blocked = NineMensMorrisGame(game_mode=constants.H_VS_C)
        blocked.phase = constants.PHASE2
        blocked.turn = constants.PLAY2
        blocked.play2_pieces = 4
        for point in ((0, 0), (0, 6), (6, 0), (6, 6)):
            blocked.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        for point in ((0, 3), (3, 0), (3, 6), (6, 3)):
            blocked.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        self.assertFalse(blocked.computer_move())
        self.assertTrue(blocked.over)

    def test_generated_ai_placements_are_legal_for_every_difficulty(self):
        for difficulty in (constants.EASY, constants.NORMAL, constants.HARD):
            with self.subTest(difficulty=difficulty):
                game = NineMensMorrisGame(difficulty=difficulty)
                game.CURRENT_POSITION[0][0] = constants.PLAY1
                game.CURRENT_POSITION[6][6] = constants.PLAY2
                legal = {tuple(move) for move in game.get_valid_moves()}
                self.assertIn(game._best_placement(constants.PLAY2), legal)

    def test_best_placement_wins_blocks_and_scores(self):
        game = NineMensMorrisGame(difficulty=constants.NORMAL)
        game.CURRENT_POSITION[0][0] = constants.PLAY2
        game.CURRENT_POSITION[0][3] = constants.PLAY2
        self.assertEqual(game._best_placement(constants.PLAY2), (0, 6))

        game = NineMensMorrisGame(difficulty=constants.NORMAL)
        game.CURRENT_POSITION[1][1] = constants.PLAY1
        game.CURRENT_POSITION[1][3] = constants.PLAY1
        self.assertEqual(game._best_placement(constants.PLAY2), (1, 5))

        game = NineMensMorrisGame(difficulty=constants.HARD)
        game.CURRENT_POSITION[1][1] = constants.PLAY2
        game.CURRENT_POSITION[1][5] = constants.PLAY1
        self.assertEqual(game._score_placement_hard(1, 3, 2, 1), 1)

    def test_generated_ai_movements_are_legal_for_every_difficulty(self):
        for difficulty in (constants.EASY, constants.NORMAL, constants.HARD):
            with self.subTest(difficulty=difficulty):
                game = self.movement_game(turn=constants.PLAY2, difficulty=difficulty)
                legal = game.get_all_legal_moves(constants.PLAY2)
                self.assertIn(game._best_movement(legal, constants.PLAY2), legal)

    def test_best_movement_takes_mill_and_hard_scoring_branches(self):
        game = NineMensMorrisGame(difficulty=constants.NORMAL)
        game.phase = constants.PHASE2
        for point in ((0, 0), (0, 3), (3, 6), (1, 1)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        legal = game.get_all_legal_moves(constants.PLAY2)
        self.assertEqual(game._best_movement(legal, constants.PLAY2), ((3, 6), (0, 6)))

        game = self.movement_game(turn=constants.PLAY2, difficulty=constants.HARD)
        legal = game.get_all_legal_moves(constants.PLAY2)
        selected = game._best_movement(legal, constants.PLAY2)
        self.assertIn(selected, legal)
        score_with_neighbor = game._score_movement_hard((6, 6), (6, 3), 2, 1)
        game.CURRENT_POSITION[5][5] = constants.BLANK
        score_without_neighbor = game._score_movement_hard((6, 6), (6, 3), 2, 1)
        self.assertGreaterEqual(score_with_neighbor, score_without_neighbor)

    def test_save_overwrites_existing_move_history(self):
        game = NineMensMorrisGame()
        with tempfile.TemporaryDirectory() as directory:
            state_file = os.path.join(directory, "state.txt")
            with patch.object(constants, "GAME_STATE_FILE", state_file):
                game.record_move("a7")
                game.save_game()
                game.record_move("d7")
                game.save_game()
                with open(state_file, encoding="utf-8") as saved:
                    self.assertEqual(saved.read(), "a7,d7")


if __name__ == "__main__":
    unittest.main()
