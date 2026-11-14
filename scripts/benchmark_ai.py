from __future__ import annotations

import random
import statistics
import sys
from math import ceil
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import constants  # noqa: E402
from ai import Board, MorrisAI, Move  # noqa: E402


def make_board(ai: MorrisAI, player1: set[tuple[int, int]], player2: set[tuple[int, int]]) -> Board:
    return tuple(
        constants.PLAY1
        if point in player1
        else constants.PLAY2
        if point in player2
        else constants.BLANK
        for point in ai.points
    )


def movement_scenarios(ai: MorrisAI) -> list[tuple[str, Board, Move]]:
    return [
        (
            "winning mill",
            make_board(
                ai,
                {(6, 0), (6, 3), (5, 5)},
                {(0, 0), (0, 3), (3, 6), (1, 1)},
            ),
            ((3, 6), (0, 6)),
        ),
        (
            "block immediate threat",
            make_board(
                ai,
                {(1, 1), (1, 5), (0, 3), (6, 6)},
                {(2, 3), (6, 0), (6, 3), (3, 4)},
            ),
            ((2, 3), (1, 3)),
        ),
        (
            "forced flying win",
            make_board(
                ai,
                {(6, 0), (6, 3), (5, 5)},
                {(0, 0), (0, 3), (6, 6)},
            ),
            ((6, 6), (0, 6)),
        ),
    ]


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]


def capture_scenario(ai: MorrisAI) -> tuple[Board, tuple[int, int]]:
    return (
        make_board(
            ai,
            {(1, 1), (1, 3), (3, 6), (6, 6)},
            {(0, 0), (0, 3), (0, 6), (3, 4)},
        ),
        (1, 3),
    )


def main() -> int:
    labels = {
        constants.EASY: "Easy",
        constants.NORMAL: "Normal",
        constants.HARD: "Hard",
    }
    repetitions = {constants.EASY: 12, constants.NORMAL: 4, constants.HARD: 1}
    print("Difficulty | Legal moves | Tactical matches | Mean ms | P95 ms")
    print("-----------|-------------|------------------|---------|-------")

    for difficulty in (constants.EASY, constants.NORMAL, constants.HARD):
        ai = MorrisAI(depth_limit=constants.HARD_AI_DEPTH)
        legal_count = 0
        tactical_count = 0
        total = 0
        latencies: list[float] = []
        for scenario_index, (_, board, expected) in enumerate(movement_scenarios(ai)):
            legal = {ai.point_move(move) for move in ai.legal_moves(board, constants.PLAY2)}
            for repetition in range(repetitions[difficulty]):
                started = perf_counter()
                selected = ai.choose_movement(
                    board,
                    constants.PLAY2,
                    difficulty,
                    random.Random(scenario_index * 100 + repetition),
                )
                latencies.append((perf_counter() - started) * 1000)
                total += 1
                legal_count += selected in legal
                tactical_count += selected == expected

        capture_board, expected_capture = capture_scenario(ai)
        legal_captures = {
            ai.point_at(index) for index in ai.removable_indices(capture_board, constants.PLAY1)
        }
        for repetition in range(repetitions[difficulty]):
            started = perf_counter()
            selected_capture = ai.choose_capture(
                capture_board,
                constants.PLAY2,
                difficulty,
                constants.PHASE2,
                random.Random(500 + repetition),
            )
            latencies.append((perf_counter() - started) * 1000)
            total += 1
            legal_count += selected_capture in legal_captures
            tactical_count += selected_capture == expected_capture

        legal_rate = legal_count / total * 100
        tactical_rate = tactical_count / total * 100
        print(
            f"{labels[difficulty]:10} | {legal_rate:10.1f}% | {tactical_rate:15.1f}% "
            f"| {statistics.mean(latencies):7.2f} | {percentile_95(latencies):6.2f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
