import json
import tempfile
import unittest
from pathlib import Path

import constants
from game_persistence import SaveGameError, load_payload, save_status
from logic import NineMensMorrisGame


class SaveAndResumeTests(unittest.TestCase):
    def game_waiting_for_capture(self):
        game = NineMensMorrisGame(game_mode=constants.H_VS_C, difficulty=constants.HARD)
        for point in ((0, 0), (6, 6), (0, 3), (6, 3), (0, 6)):
            self.assertTrue(game.make_move(*point))
        self.assertTrue(game.is_remove_piece)
        return game

    def test_versioned_json_round_trip_restores_exact_pending_state(self):
        game = self.game_waiting_for_capture()
        game.moves_without_capture = 7
        game.position_counts[(game.board_tuple(), game.turn)] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "match.json"
            game.save_game(path)
            resumed = NineMensMorrisGame.load_game(path)

        self.assertEqual(resumed.to_save_data(), game.to_save_data())
        self.assertTrue(resumed.is_remove_piece)
        self.assertEqual(resumed.game_mode, constants.H_VS_C)
        self.assertEqual(resumed.difficulty, constants.HARD)

    def test_corrupt_json_is_rejected_without_partial_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaisesRegex(SaveGameError, "corrupt or unreadable"):
                NineMensMorrisGame.load_game(path)
            self.assertEqual(
                save_status(path), (False, "The saved match is corrupt or unreadable.")
            )

    def test_future_schema_version_is_rejected(self):
        game = NineMensMorrisGame()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.json"
            game.save_game(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["schema_version"] = constants.SAVE_SCHEMA_VERSION + 1
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SaveGameError, "unsupported version"):
                load_payload(path)

    def test_inconsistent_piece_counts_are_rejected(self):
        game = NineMensMorrisGame()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            game.save_game(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["game"]["play1_pieces"] = 3
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SaveGameError, "inconsistent piece counts"):
                NineMensMorrisGame.load_game(path)

    def test_malformed_nested_repetition_data_is_rejected(self):
        game = NineMensMorrisGame()
        game.position_counts[(game.board_tuple(), game.turn)] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-nested.json"
            game.save_game(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["game"]["position_counts"][0].pop("turn")
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SaveGameError, "repetition entry"):
                NineMensMorrisGame.load_game(path)

    def test_replay_timeline_records_each_board_change(self):
        game = NineMensMorrisGame()
        self.assertTrue(game.make_move(0, 0))
        self.assertTrue(game.make_move(6, 6))
        self.assertEqual(len(game.history), 3)
        self.assertNotEqual(game.history[0]["board"], game.history[1]["board"])
        self.assertNotEqual(game.history[1]["board"], game.history[2]["board"])

    def test_summary_reports_match_statistics(self):
        game = self.game_waiting_for_capture()
        self.assertTrue(game.remove_piece(6, 6))
        summary = game.game_summary()
        self.assertIn("Player 1 mills formed: 1", summary)
        self.assertIn("Player 1 captures: 1", summary)


if __name__ == "__main__":
    unittest.main()
