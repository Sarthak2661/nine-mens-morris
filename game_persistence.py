from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import constants


class SaveGameError(ValueError):
    """Raised when a saved match is missing, corrupt, or unsupported."""


def save_payload(game_data: dict[str, Any], path: str | Path | None = None) -> Path:
    destination = Path(path or constants.GAME_STATE_FILE)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": constants.SAVE_SCHEMA_VERSION,
        "saved_at": datetime.now(UTC).isoformat(),
        "game": game_data,
    }
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temporary, destination)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise SaveGameError(f"Could not save this match: {exc}") from exc
    return destination


def load_payload(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path or constants.GAME_STATE_FILE)
    if not source.is_file():
        raise SaveGameError("No saved match was found.")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SaveGameError("The saved match is corrupt or unreadable.") from exc
    if not isinstance(payload, dict):
        raise SaveGameError("The saved match has an invalid structure.")
    if payload.get("schema_version") != constants.SAVE_SCHEMA_VERSION:
        raise SaveGameError("This saved match uses an unsupported version.")
    game = payload.get("game")
    if not isinstance(game, dict):
        raise SaveGameError("The saved match does not contain game data.")
    _validate_game(game)
    return game


def save_status(path: str | Path | None = None) -> tuple[bool, str]:
    try:
        load_payload(path)
    except SaveGameError as exc:
        return False, str(exc)
    return True, "Saved match ready"


def _validate_game(game: dict[str, Any]) -> None:
    required = {
        "phase",
        "turn",
        "game_mode",
        "difficulty",
        "board",
        "is_remove_piece",
        "counter",
        "play1_pieces",
        "play2_pieces",
        "play1_counter",
        "play2_counter",
        "message",
        "move_made",
        "over",
        "moves_made",
        "draw_reason",
        "moves_without_capture",
        "position_counts",
        "history",
        "stats",
    }
    missing = required - game.keys()
    if missing:
        raise SaveGameError(f"The saved match is missing: {', '.join(sorted(missing))}.")

    board = game["board"]
    if not isinstance(board, list) or len(board) != len(constants.VALID_POINTS):
        raise SaveGameError("The saved board must contain exactly 24 points.")
    if any(value not in (constants.BLANK, constants.PLAY1, constants.PLAY2) for value in board):
        raise SaveGameError("The saved board contains an invalid piece value.")
    if game["phase"] not in (constants.PHASE1, constants.PHASE2):
        raise SaveGameError("The saved phase is invalid.")
    if game["turn"] not in (constants.PLAY1, constants.PLAY2):
        raise SaveGameError("The saved player turn is invalid.")
    if game["game_mode"] not in (constants.H_VS_H, constants.H_VS_C):
        raise SaveGameError("The saved game mode is invalid.")
    if game["difficulty"] not in (constants.EASY, constants.NORMAL, constants.HARD):
        raise SaveGameError("The saved difficulty is invalid.")

    integer_fields = (
        "counter",
        "play1_pieces",
        "play2_pieces",
        "play1_counter",
        "play2_counter",
        "moves_without_capture",
    )
    if any(not isinstance(game[field], int) or game[field] < 0 for field in integer_fields):
        raise SaveGameError("The saved match contains an invalid counter.")
    if any(game[field] > constants.TOTAL_MENS for field in ("play1_pieces", "play2_pieces")):
        raise SaveGameError("The saved match contains too many pieces.")
    if any(game[field] > constants.TOTAL_MENS for field in ("play1_counter", "play2_counter")):
        raise SaveGameError("The saved placement counter is invalid.")
    if not isinstance(game["moves_made"], list) or not all(
        isinstance(item, str) for item in game["moves_made"]
    ):
        raise SaveGameError("The saved move history is invalid.")
    if not isinstance(game["history"], list) or not game["history"]:
        raise SaveGameError("The saved replay timeline is invalid.")
    for snapshot in game["history"]:
        if not isinstance(snapshot, dict):
            raise SaveGameError("A replay snapshot is invalid.")
        snapshot_board = snapshot.get("board")
        if not isinstance(snapshot_board, list) or len(snapshot_board) != len(
            constants.VALID_POINTS
        ):
            raise SaveGameError("A replay snapshot has an invalid board.")
        if any(
            value not in (constants.BLANK, constants.PLAY1, constants.PLAY2)
            for value in snapshot_board
        ):
            raise SaveGameError("A replay snapshot contains an invalid piece value.")
        if not isinstance(snapshot.get("label"), str):
            raise SaveGameError("A replay snapshot has an invalid label.")
    if not isinstance(game["position_counts"], list):
        raise SaveGameError("The saved repetition history is invalid.")
    for item in game["position_counts"]:
        if not isinstance(item, dict) or set(item) != {"board", "turn", "count"}:
            raise SaveGameError("A saved repetition entry is invalid.")
        if (
            not isinstance(item["board"], list)
            or len(item["board"]) != len(constants.VALID_POINTS)
            or item["turn"] not in (constants.PLAY1, constants.PLAY2)
            or not isinstance(item["count"], int)
            or item["count"] < 1
        ):
            raise SaveGameError("A saved repetition entry is invalid.")
    stats = game["stats"]
    expected_stats = {"mills_formed", "captures", "missed_blocks", "hard_ai_times_ms"}
    if not isinstance(stats, dict) or set(stats) != expected_stats:
        raise SaveGameError("The saved match statistics are invalid.")
    for name in ("mills_formed", "captures", "missed_blocks"):
        values = stats[name]
        if (
            not isinstance(values, dict)
            or set(values) != {"1", "2"}
            or any(not isinstance(value, int) or value < 0 for value in values.values())
        ):
            raise SaveGameError("The saved match statistics are invalid.")
    times = stats["hard_ai_times_ms"]
    if not isinstance(times, list) or any(
        not isinstance(value, (int, float)) or value < 0 for value in times
    ):
        raise SaveGameError("The saved AI timing statistics are invalid.")
