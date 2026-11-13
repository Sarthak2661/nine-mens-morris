import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest
import pygame

import constants
from GUI import NineMensMorrisGUI, get_coords
from logic import NineMensMorrisGame
from menu import Menu


class TestNineMensMorrisGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()

    def setUp(self):
        self.game = NineMensMorrisGame()
        self.gui = NineMensMorrisGUI(self.game)

    def tearDown(self):
        pygame.event.clear()

    def test_get_coords(self):
        self.assertEqual(get_coords((45, 45)), (0, 0))
        self.assertEqual(get_coords((245, 365)), (4, 3))

    def test_draw_board_smoke(self):
        self.gui.draw_board()
        pygame.display.flip()
        self.assertIsNotNone(self.gui.screen)

    def test_phase2_selection_shows_valid_destinations(self):
        self.game.phase = constants.PHASE2
        self.game.turn = constants.PLAY1
        self.game.play1_pieces = 4
        self.game.CURRENT_POSITION[0][0] = constants.PLAY1
        self.gui.handle_phase2_click(0, 0)
        self.assertEqual(self.gui.clicked_point, (0, 0))
        self.assertIn((0, 3), self.gui.valid_destinations)
        self.assertIn((3, 0), self.gui.valid_destinations)

    def test_menu_human_vs_computer_enabled(self):
        menu = Menu()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": menu.human_vs_computer_button_rect.center}))
        # Process exactly one frame worth of events instead of entering the infinite menu loop.
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and menu.human_vs_computer_button_rect.collidepoint(event.pos):
                menu.selected_option = constants.H_VS_C
        self.assertEqual(menu.get_selected_option(), constants.H_VS_C)

    def test_reset_preserves_mode_and_difficulty(self):
        self.game.game_mode = constants.H_VS_C
        self.game.difficulty = constants.HARD
        self.game.make_move(4, 3)

        self.gui.handle_click(self.gui.reset_rect.center)

        self.assertEqual(self.game.game_mode, constants.H_VS_C)
        self.assertEqual(self.game.difficulty, constants.HARD)
        self.assertEqual(self.game.get_on_board_count(constants.PLAY1), 0)


if __name__ == '__main__':
    unittest.main()
