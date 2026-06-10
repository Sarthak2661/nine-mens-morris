import os
import unittest

import constants
from logic import NineMensMorrisGame


class TestNineMensMorrisGame(unittest.TestCase):
    def setUp(self):
        self.game = NineMensMorrisGame()

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

    def test_save_game(self):
        self.assertTrue(self.game.make_move(4, 3))
        self.game.save_game()
        with open(constants.GAME_STATE_FILE, "r", encoding="utf-8") as state_file:
            data = state_file.read()
        self.assertEqual(data, "d3")
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


if __name__ == '__main__':
    unittest.main()
