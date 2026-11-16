import json
import os
import unittest

import constants
from logic import NineMensMorrisGame


class TestNineMensMorrisGame(unittest.TestCase):
    def setUp(self):
        self.game = NineMensMorrisGame()

    def assert_state_invariants(self, game):
        self.assertGreaterEqual(game.play1_pieces, 0)
        self.assertGreaterEqual(game.play2_pieces, 0)
        self.assertLessEqual(game.play1_counter, constants.TOTAL_MENS)
        self.assertLessEqual(game.play2_counter, constants.TOTAL_MENS)
        play1_unplaced = constants.TOTAL_MENS - game.play1_counter
        play2_unplaced = constants.TOTAL_MENS - game.play2_counter
        self.assertEqual(
            game.get_on_board_count(constants.PLAY1) + play1_unplaced,
            game.play1_pieces,
        )
        self.assertEqual(
            game.get_on_board_count(constants.PLAY2) + play2_unplaced,
            game.play2_pieces,
        )
        for row in range(constants.ROWS):
            for col in range(constants.COLS):
                value = game.CURRENT_POSITION[row][col]
                self.assertIn(value, (constants.BLANK, constants.PLAY1, constants.PLAY2))
                if (row, col) not in constants.VALID_POINTS:
                    self.assertEqual(value, constants.BLANK)

    def configure_movement_game(self):
        game = NineMensMorrisGame()
        game.phase = constants.PHASE2
        game.turn = constants.PLAY1
        game.play1_counter = constants.TOTAL_MENS
        game.play2_counter = constants.TOTAL_MENS
        game.play1_pieces = 4
        game.play2_pieces = 4
        for point in ((0, 0), (1, 1), (2, 2), (3, 2)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        for point in ((6, 6), (5, 5), (4, 4), (3, 4)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        return game

    def test_initial_board_state(self):
        self.assertEqual(self.game.turn, constants.PLAY1)
        self.assertEqual(self.game.phase, constants.PHASE1)
        self.assertEqual(self.game.counter, 0)
        self.assertEqual(self.game.play1_counter, 0)
        self.assertEqual(self.game.play2_counter, 0)
        for row in range(constants.ROWS):
            for col in range(constants.COLS):
                self.assertEqual(self.game.CURRENT_POSITION[row][col], constants.BLANK)

    def test_game_instances_do_not_share_board_state(self):
        self.game.make_move(4, 3)
        another_game = NineMensMorrisGame()
        self.assertEqual(another_game.CURRENT_POSITION[4][3], constants.BLANK)

    def test_change_turn(self):
        self.assertTrue(self.game.make_move(4, 4))
        self.assertEqual(self.game.get_turn(), constants.PLAY2)
        self.assertTrue(self.game.make_move(4, 3))
        self.assertEqual(self.game.get_turn(), constants.PLAY1)

    def test_place_piece(self):
        self.assertTrue(self.game.make_move(4, 3))
        self.assertEqual(self.game.CURRENT_POSITION[4][3], constants.PLAY1)
        self.assertFalse(self.game.make_move(4, 3))

    def test_on_board_count_uses_board_occupancy(self):
        self.assertEqual(self.game.get_on_board_count(constants.PLAY1), 0)
        self.assertTrue(self.game.make_move(4, 3))
        self.assertEqual(self.game.get_on_board_count(constants.PLAY1), 1)
        self.assertEqual(self.game.play1_pieces, constants.TOTAL_MENS)

    def test_move_piece_phase2_adjacent_only(self):
        self.game.phase = constants.PHASE2
        self.game.turn = constants.PLAY1
        self.game.CURRENT_POSITION[0][0] = constants.PLAY1
        self.game.CURRENT_POSITION[6][6] = constants.PLAY2
        self.game.play1_pieces = 4
        self.game.play2_pieces = 4

        self.assertFalse(self.game.make_move(0, 0, 6, 0))  # non-adjacent while not flying
        self.assertTrue(self.game.make_move(0, 0, 0, 3))
        self.assertEqual(self.game.CURRENT_POSITION[0][0], constants.BLANK)
        self.assertEqual(self.game.CURRENT_POSITION[0][3], constants.PLAY1)
        self.assertEqual(self.game.get_turn(), constants.PLAY2)

    def test_flying_allowed_when_player_has_three_pieces(self):
        self.game.phase = constants.PHASE2
        self.game.turn = constants.PLAY1
        self.game.play1_pieces = 3
        self.game.play2_pieces = 4
        self.game.CURRENT_POSITION[0][0] = constants.PLAY1
        self.assertTrue(self.game.make_move(0, 0, 6, 6))
        self.assertEqual(self.game.CURRENT_POSITION[0][0], constants.BLANK)
        self.assertEqual(self.game.CURRENT_POSITION[6][6], constants.PLAY1)

    def test_horizontal_and_vertical_mills(self):
        for point in [(0, 0), (0, 3), (0, 6)]:
            self.game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        self.assertTrue(self.game.is_mill(0, 3, constants.PLAY1))

        game2 = NineMensMorrisGame()
        for point in [(0, 0), (3, 0), (6, 0)]:
            game2.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        self.assertTrue(game2.is_mill(3, 0, constants.PLAY2))

    def test_diagonal_is_not_a_mill(self):
        for point in [(0, 0), (1, 1), (2, 2)]:
            self.game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        self.assertFalse(self.game.is_mill_at_position(1, 1))

    def test_remove_piece_prefers_non_mill_piece(self):
        self.game.turn = constants.PLAY1
        self.game.is_remove_piece = True
        # Player 2 has a mill and one free piece. Only free piece should be removable.
        for point in [(0, 0), (0, 3), (0, 6), (6, 6)]:
            self.game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        self.assertFalse(self.game.remove_piece(0, 3, constants.PLAY1))
        self.assertTrue(self.game.remove_piece(6, 6, constants.PLAY1))
        self.assertEqual(self.game.CURRENT_POSITION[6][6], constants.BLANK)
        self.assertEqual(self.game.play2_pieces, constants.TOTAL_MENS - 1)

    def test_remove_from_mill_allowed_when_all_opponent_pieces_are_in_mills(self):
        self.game.turn = constants.PLAY1
        self.game.is_remove_piece = True
        for point in [(0, 0), (0, 3), (0, 6)]:
            self.game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2
        self.assertTrue(self.game.remove_piece(0, 3, constants.PLAY1))

    def test_remove_piece_rejected_outside_capture_turn(self):
        self.game.CURRENT_POSITION[0][0] = constants.PLAY2
        self.assertFalse(self.game.remove_piece(0, 0, constants.PLAY1))
        self.assertEqual(self.game.CURRENT_POSITION[0][0], constants.PLAY2)
        self.assertEqual(self.game.last_error, "No capture is currently available.")

    def test_complete_placement_transitions_to_movement(self):
        game = NineMensMorrisGame()
        while game.phase == constants.PHASE1:
            empty_points = [point for point in constants.VALID_POINTS if game.is_empty(*point)]
            selected = empty_points[0]
            for point in empty_points:
                game.CURRENT_POSITION[point[0]][point[1]] = game.turn
                forms_mill = game.is_mill(*point, game.turn)
                game.CURRENT_POSITION[point[0]][point[1]] = constants.BLANK
                if not forms_mill:
                    selected = point
                    break

            self.assertTrue(game.make_move(*selected))
            if game.is_remove_piece:
                self.assertTrue(game.remove_piece(*game.removable_pieces()[0]))

        self.assertEqual(game.play1_counter, constants.TOTAL_MENS)
        self.assertEqual(game.play2_counter, constants.TOTAL_MENS)
        self.assertEqual(game.turn, constants.PLAY1)
        self.assertEqual(len(game.position_counts), 1)
        self.assert_state_invariants(game)

    def test_capture_reducing_opponent_to_two_ends_game(self):
        game = NineMensMorrisGame()
        game.phase = constants.PHASE2
        game.turn = constants.PLAY1
        game.play1_counter = constants.TOTAL_MENS
        game.play2_counter = constants.TOTAL_MENS
        game.play1_pieces = 4
        game.play2_pieces = 3
        game.is_remove_piece = True
        for point in ((6, 0), (6, 3), (6, 6), (5, 1)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        for point in ((0, 0), (0, 3), (0, 6)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2

        self.assertTrue(game.remove_piece(0, 3))
        self.assertTrue(game.over)
        self.assertEqual(game.play2_pieces, 2)
        self.assertEqual(game.message, "Player 1 wins the game!")
        self.assert_state_invariants(game)

    def test_blocked_player_loses_after_completed_turn(self):
        game = NineMensMorrisGame()
        game.phase = constants.PHASE2
        game.turn = constants.PLAY1
        game.play1_counter = constants.TOTAL_MENS
        game.play2_counter = constants.TOTAL_MENS
        game.play1_pieces = 5
        game.play2_pieces = 4

        for point in ((0, 3), (3, 0), (3, 6), (6, 3), (1, 1)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY1
        for point in ((0, 0), (0, 6), (6, 0), (6, 6)):
            game.CURRENT_POSITION[point[0]][point[1]] = constants.PLAY2

        self.assertTrue(game.make_move(1, 1, 1, 3))
        self.assertTrue(game.over)
        self.assertEqual(game.message, "Player 1 wins the game!")
        self.assertEqual(game.get_all_legal_moves(constants.PLAY2), [])
        self.assert_state_invariants(game)

    def test_threefold_repetition_ends_in_draw(self):
        game = self.configure_movement_game()
        game.position_counts[game._position_key()] = 1

        cycle = (
            (0, 0, 0, 3),
            (6, 6, 6, 3),
            (0, 3, 0, 0),
            (6, 3, 6, 6),
        )
        for _ in range(2):
            for move in cycle:
                self.assertTrue(game.make_move(*move))

        self.assertTrue(game.over)
        self.assertEqual(game.draw_reason, "Draw by threefold repetition.")
        self.assert_state_invariants(game)

    def test_move_limit_without_capture_ends_in_draw(self):
        game = self.configure_movement_game()
        game.moves_without_capture = constants.MAX_MOVES_WITHOUT_CAPTURE - 1

        self.assertTrue(game.make_move(0, 0, 0, 3))
        self.assertTrue(game.over)
        self.assertIn("moves without a capture", game.draw_reason)
        self.assert_state_invariants(game)

    def test_capture_resets_no_capture_counter(self):
        game = self.configure_movement_game()
        game.moves_without_capture = constants.MAX_MOVES_WITHOUT_CAPTURE - 1
        game.is_remove_piece = True

        self.assertTrue(game.remove_piece(6, 6, constants.PLAY1))
        self.assertEqual(game.moves_without_capture, 0)
        self.assertFalse(game.over)
        self.assert_state_invariants(game)

    def test_save_game(self):
        self.assertTrue(self.game.make_move(4, 3))
        self.game.save_game()
        with open(constants.GAME_STATE_FILE, "r", encoding="utf-8") as state_file:
            data = json.load(state_file)
        self.assertEqual(data["schema_version"], constants.SAVE_SCHEMA_VERSION)
        self.assertEqual(data["game"]["moves_made"], ["d3"])
        resumed = NineMensMorrisGame.load_game()
        self.assertEqual(resumed.to_save_data(), self.game.to_save_data())
        os.remove(constants.GAME_STATE_FILE)

    def test_game_over_by_piece_count(self):
        self.game.phase = constants.PHASE2
        self.game.play1_pieces = 2
        self.assertEqual(self.game.is_game_over(), constants.PLAY2)
        self.game.play1_pieces = 4
        self.game.play2_pieces = 2
        self.assertEqual(self.game.is_game_over(), constants.PLAY1)

    def test_computer_mode_makes_a_move(self):
        game = NineMensMorrisGame(game_mode=constants.H_VS_C)
        game.turn = constants.PLAY2
        self.assertTrue(game.computer_move())
        self.assertEqual(game.play2_counter, 1)
        self.assertEqual(game.turn, constants.PLAY1)


if __name__ == "__main__":
    unittest.main()
