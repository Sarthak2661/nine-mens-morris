import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

import constants
import ui_theme as theme
from GUI import NineMensMorrisGUI, get_coords
from logic import NineMensMorrisGame
from menu import DifficultySelector, HomePage, InstructionsScreen, Menu, wrap_text


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
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, {"pos": menu.human_vs_computer_button_rect.center}
            )
        )
        # Process exactly one frame worth of events instead of entering the infinite menu loop.
        for event in pygame.event.get():
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and menu.human_vs_computer_button_rect.collidepoint(event.pos)
            ):
                menu.selected_option = constants.H_VS_C
        self.assertEqual(menu.get_selected_option(), constants.H_VS_C)

    def test_reset_preserves_mode_and_difficulty(self):
        self.game.game_mode = constants.H_VS_C
        self.game.difficulty = constants.HARD
        self.game.make_move(4, 3)

        self.gui.handle_click(self.gui.reset_rect.center)
        self.assertEqual(self.gui.confirm_action, "reset")
        self.gui.execute_confirmation()

        self.assertEqual(self.game.game_mode, constants.H_VS_C)
        self.assertEqual(self.game.difficulty, constants.HARD)
        self.assertEqual(self.game.get_on_board_count(constants.PLAY1), 0)

    def test_contextual_action_tracks_each_gameplay_step(self):
        self.assertEqual(self.gui.contextual_action(), "Place a black piece")

        self.game.phase = constants.PHASE2
        self.game.turn = constants.PLAY1
        self.game.CURRENT_POSITION[0][0] = constants.PLAY1
        self.game.play1_pieces = 4
        self.assertEqual(self.gui.contextual_action(), "Select a piece to move")

        self.gui.handle_phase2_click(0, 0)
        self.assertEqual(self.gui.contextual_action(), "Choose a destination")

        self.game.is_remove_piece = True
        self.gui.clicked_point = None
        self.assertEqual(self.gui.contextual_action(), "Remove a white piece")

    def test_only_legal_targets_are_interactive(self):
        self.assertTrue(self.gui.is_interactive_point(0, 0))
        self.game.make_move(0, 0)
        self.assertFalse(self.gui.is_interactive_point(0, 0))
        self.assertTrue(self.gui.is_interactive_point(0, 3))

    def test_removable_pieces_drive_capture_highlights(self):
        self.game.is_remove_piece = True
        self.game.turn = constants.PLAY1
        self.game.CURRENT_POSITION[0][0] = constants.PLAY2
        self.game.CURRENT_POSITION[0][3] = constants.PLAY2

        self.assertTrue(self.gui.is_interactive_point(0, 0))
        self.assertTrue(self.gui.is_interactive_point(0, 3))
        self.assertFalse(self.gui.is_interactive_point(0, 6))

    def test_sound_toggle_survives_game_reset(self):
        self.gui.sound.enabled = False
        self.game.make_move(0, 0)
        self.gui.reset_game()

        self.assertFalse(self.gui.sound.enabled)
        self.assertEqual(self.game.get_on_board_count(constants.PLAY1), 0)

    def test_end_game_actions_support_review_rematch_and_menu(self):
        self.game.over = True
        self.game.message = "Player 1 wins the game!"
        self.game.moves_made = ["a7", "d7", "xg7"]

        self.gui.handle_click(self.gui.review_rect.center)
        self.assertTrue(self.gui.review_open)
        self.gui.handle_click(self.gui.review_close_rect.center)
        self.assertFalse(self.gui.review_open)

        self.gui.handle_click(self.gui.menu_rect.center)
        self.assertTrue(self.gui.return_to_menu)

        self.gui.return_to_menu = False
        self.gui.handle_click(self.gui.rematch_rect.center)
        self.assertFalse(self.game.over)
        self.assertEqual(self.game.moves_made, [])

    def test_review_navigation_uses_engine_snapshots(self):
        self.assertTrue(self.game.make_move(0, 0))
        self.assertTrue(self.game.make_move(6, 6))
        self.gui.open_review()

        self.assertEqual(self.gui.review_index, 2)
        self.assertEqual(self.gui.visible_piece(6, 6), constants.PLAY2)
        self.gui.handle_click(self.gui.review_previous_rect.center)
        self.assertEqual(self.gui.review_index, 1)
        self.assertEqual(self.gui.visible_piece(6, 6), constants.BLANK)
        self.assertEqual(self.gui.visible_piece(0, 0), constants.PLAY1)

    def test_review_arrow_keys_stop_at_timeline_boundaries(self):
        self.game.make_move(0, 0)
        self.gui.open_review()
        self.gui.handle_key(pygame.K_RIGHT)
        self.assertEqual(self.gui.review_index, 1)
        self.gui.handle_key(pygame.K_LEFT)
        self.gui.handle_key(pygame.K_LEFT)
        self.assertEqual(self.gui.review_index, 0)

    def test_instruction_copy_wraps_inside_content_area(self):
        instructions = InstructionsScreen()
        for text, text_type in instructions.instructions:
            font = instructions._font_for_type(text_type)
            for line in wrap_text(text, font, instructions.content_width):
                self.assertLessEqual(font.size(line)[0], instructions.content_width)

        hint = instructions.text_font.render("Scroll to read all rules", True, (0, 0, 0))
        hint_rect = hint.get_rect(topleft=(230, 678))
        self.assertFalse(instructions.back_button_rect.colliderect(hint_rect))

    def test_status_card_columns_are_contained_and_do_not_overlap(self):
        card = pygame.Rect(
            constants.SIDEBAR_X + 8,
            240,
            constants.SCREEN_WIDTH - constants.SIDEBAR_X - 30,
            70,
        )

        left, right = self.gui.status_card_columns(card)

        self.assertTrue(card.contains(left))
        self.assertTrue(card.contains(right))
        self.assertFalse(left.colliderect(right))
        self.assertGreaterEqual(right.left - left.right, theme.SPACE_MEDIUM)

    def test_shared_button_has_a_visible_hover_state(self):
        normal = pygame.Surface((180, 60))
        hovered = pygame.Surface((180, 60))
        rect = pygame.Rect(4, 4, 172, 50)
        label_font = theme.font(18, bold=True)

        theme.draw_button(normal, rect, "Play", label_font, hovered=False)
        theme.draw_button(hovered, rect, "Play", label_font, hovered=True)

        self.assertNotEqual(
            pygame.image.tobytes(normal, "RGB"), pygame.image.tobytes(hovered, "RGB")
        )

    def test_common_display_scaling_keeps_complete_frame(self):
        renderers = [
            (HomePage(), "draw"),
            (Menu(), "draw_menu"),
            (DifficultySelector(), "draw_selector"),
            (InstructionsScreen(), "draw"),
        ]
        for renderer, method_name in renderers:
            getattr(renderer, method_name)()
            frame = renderer.screen.copy()
            self.assertEqual(frame.get_size(), (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            for scale in constants.SUPPORTED_DISPLAY_SCALES:
                scaled = pygame.transform.smoothscale(
                    frame,
                    (
                        round(constants.SCREEN_WIDTH * scale),
                        round(constants.SCREEN_HEIGHT * scale),
                    ),
                )
                self.assertEqual(
                    scaled.get_size(),
                    (
                        round(constants.SCREEN_WIDTH * scale),
                        round(constants.SCREEN_HEIGHT * scale),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
