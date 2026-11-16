from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import imageio_ffmpeg  # noqa: E402
import pygame  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import constants  # noqa: E402
from GUI import NineMensMorrisGUI  # noqa: E402
from logic import NineMensMorrisGame  # noqa: E402
from menu import DifficultySelector, HomePage, InstructionsScreen, Menu  # noqa: E402

SCREENSHOTS = ROOT / "resources"
DEMO_GIF = SCREENSHOTS / "demo.gif"
DEMO_VIDEO = SCREENSHOTS / "nine-mens-morris-demo.mp4"
FPS = 12


def image_from_surface(surface: pygame.Surface) -> Image.Image:
    return Image.frombytes("RGB", surface.get_size(), pygame.image.tobytes(surface, "RGB"))


def save_surface(surface: pygame.Surface, name: str) -> Image.Image:
    image = image_from_surface(surface)
    image.save(SCREENSHOTS / name, optimize=True)
    return image


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_name = "segoeuib.ttf" if bold else "segoeui.ttf"
    font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / font_name
    if font_path.exists():
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def caption(image: Image.Image, title: str, detail: str) -> Image.Image:
    framed = image.copy().convert("RGB")
    overlay = Image.new("RGBA", framed.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((28, 596, 872, 696), radius=18, fill=(10, 18, 33, 226))
    draw.text((52, 615), title, font=font(26, bold=True), fill=(255, 255, 255, 255))
    draw.text((52, 654), detail, font=font(17), fill=(205, 219, 238, 255))
    return Image.alpha_composite(framed.convert("RGBA"), overlay).convert("RGB")


def set_board(
    game: NineMensMorrisGame, player1: set[tuple[int, int]], player2: set[tuple[int, int]]
) -> None:
    game.CURRENT_POSITION = [row[:] for row in constants.CURRENT_POSITION]
    for row, col in player1:
        game.CURRENT_POSITION[row][col] = constants.PLAY1
    for row, col in player2:
        game.CURRENT_POSITION[row][col] = constants.PLAY2
    game.play1_pieces = len(player1)
    game.play2_pieces = len(player2)
    game.play1_counter = constants.TOTAL_MENS
    game.play2_counter = constants.TOTAL_MENS
    game.phase = constants.PHASE2


def render_screens() -> list[tuple[Image.Image, str, str, int]]:
    pygame.init()
    slides: list[tuple[Image.Image, str, str, int]] = []

    demo_save = NineMensMorrisGame(game_mode=constants.H_VS_C, difficulty=constants.NORMAL)
    demo_save.make_move(0, 0)
    demo_save.save_game()
    home = HomePage()
    home.draw()
    home_image = save_surface(home.screen, "main.png")
    Path(constants.GAME_STATE_FILE).unlink(missing_ok=True)
    slides.append((home_image, "Nine Men's Morris", "A complete desktop strategy game", 8))

    mode = Menu()
    mode.draw_menu()
    mode_image = save_surface(mode.screen, "mode.png")
    slides.append((mode_image, "Choose how to play", "Local multiplayer or computer opponent", 7))

    difficulty = DifficultySelector()
    difficulty.draw_selector()
    difficulty_image = save_surface(difficulty.screen, "levels.png")
    slides.append(
        (difficulty_image, "Three meaningful levels", "Random, tactical, and minimax play", 7)
    )

    empty_game = NineMensMorrisGame(game_mode=constants.H_VS_C, difficulty=constants.HARD)
    empty_gui = NineMensMorrisGUI(empty_game)
    empty_gui.draw_board()
    empty_image = save_surface(empty_gui.screen, "empty board.png")
    slides.append(
        (empty_image, "Placement phase", "Place pieces and form horizontal or vertical mills", 7)
    )

    accessible_gui = NineMensMorrisGUI(empty_game)
    accessible_gui.high_contrast = True
    accessible_gui.board_keyboard_active = True
    accessible_gui.board_focus_index = 4
    accessible_gui.draw_board()
    accessible_image = save_surface(accessible_gui.screen, "high-contrast.png")
    slides.append(
        (
            accessible_image,
            "Accessible by design",
            "High contrast, shape markers, and keyboard board focus",
            7,
        )
    )

    tactical_game = NineMensMorrisGame(game_mode=constants.H_VS_C, difficulty=constants.HARD)
    set_board(
        tactical_game,
        {(1, 1), (1, 5), (0, 3), (6, 6)},
        {(2, 3), (6, 0), (6, 3), (3, 4)},
    )
    tactical_game.turn = constants.PLAY2
    tactical_game.message = "Hard AI is evaluating an immediate mill threat."
    tactical_gui = NineMensMorrisGUI(tactical_game)
    tactical_gui.draw_board()
    thinking_image = save_surface(tactical_gui.screen, "full board.png")
    slides.append(
        (thinking_image, "Tactical position", "Player 1 threatens a mill on the next move", 9)
    )

    tactical_game.computer_move()
    tactical_game.message = "Hard AI blocked the immediate mill threat."
    tactical_gui.draw_board()
    result_image = save_surface(tactical_gui.screen, "ai-hard.png")
    slides.append(
        (result_image, "Hard AI responds", "Depth-limited minimax selects the defensive move", 9)
    )

    capture_game = NineMensMorrisGame(game_mode=constants.H_VS_H)
    set_board(
        capture_game,
        {(0, 0), (0, 3), (0, 6), (6, 6)},
        {(1, 1), (1, 3), (3, 1), (5, 5)},
    )
    capture_game.turn = constants.PLAY1
    capture_game.is_remove_piece = True
    capture_game.message = "Player 1: Remove one opponent piece"
    capture_gui = NineMensMorrisGUI(capture_game)
    capture_gui.start_mill_feedback(constants.PLAY1)
    capture_gui.draw_board()
    capture_image = save_surface(capture_gui.screen, "capture.png")
    slides.append(
        (capture_image, "Clear capture choices", "Eligible opponent pieces are highlighted", 7)
    )

    confirm_game = NineMensMorrisGame(game_mode=constants.H_VS_H)
    confirm_game.make_move(0, 0)
    confirm_gui = NineMensMorrisGUI(confirm_game)
    confirm_gui.confirm_action = "reset"
    confirm_gui.draw_board()
    confirm_image = save_surface(confirm_gui.screen, "confirmation.png")
    slides.append(
        (confirm_image, "Protected controls", "Reset and exit actions require confirmation", 7)
    )

    complete_game = NineMensMorrisGame(game_mode=constants.H_VS_H)
    set_board(
        complete_game,
        {(0, 0), (0, 3), (0, 6), (6, 6)},
        {(1, 1), (1, 3)},
    )
    complete_game.over = True
    complete_game.message = "Player 1 wins the game!"
    complete_game.moves_made = ["a7", "d7", "a4", "d6", "g7", "xb6"]
    complete_game.stats["mills_formed"] = {"1": 2, "2": 1}
    complete_game.stats["captures"] = {"1": 2, "2": 0}
    complete_game.stats["missed_blocks"] = {"1": 0, "2": 1}
    complete_game.stats["hard_ai_times_ms"] = [84.0, 106.0, 95.0]
    complete_gui = NineMensMorrisGUI(complete_game)
    complete_gui.draw_board()
    complete_image = save_surface(complete_gui.screen, "game-over.png")
    slides.append(
        (complete_image, "Match summary", "Rematch, menu, and move review remain one click away", 8)
    )

    review_game = NineMensMorrisGame(game_mode=constants.H_VS_H)
    review_game.make_move(0, 0)
    review_game.make_move(6, 6)
    review_game.make_move(0, 3)
    review_gui = NineMensMorrisGUI(review_game)
    review_gui.open_review()
    review_gui.review_index = 2
    review_gui.draw_board()
    review_image = save_surface(review_gui.screen, "review.png")
    slides.append(
        (
            review_image,
            "Visual move review",
            "Step through the match and see exactly what changed",
            8,
        )
    )

    instructions = InstructionsScreen()
    instructions.draw()
    instructions_image = save_surface(instructions.screen, "howtoplay.png")
    slides.append(
        (
            instructions_image,
            "Rules included",
            "Placement, movement, flying, captures, wins, and draws",
            8,
        )
    )

    return slides


def write_gif(slides: list[tuple[Image.Image, str, str, int]]) -> None:
    frames = [
        caption(image, title, detail).quantize(colors=192) for image, title, detail, _ in slides
    ]
    durations = [duration * 1000 for _, _, _, duration in slides]
    frames[0].save(
        DEMO_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )


def video_frames(slides: list[tuple[Image.Image, str, str, int]]):
    prepared = [caption(image, title, detail) for image, title, detail, _ in slides]
    transition_frames = round(FPS * 0.5)
    for index, (_image, _, _, duration) in enumerate(slides):
        current = prepared[index]
        for _ in range(round(duration * FPS)):
            yield current
        if index + 1 < len(prepared):
            upcoming = prepared[index + 1]
            for step in range(1, transition_frames + 1):
                yield Image.blend(current, upcoming, step / (transition_frames + 1))


def write_video(slides: list[tuple[Image.Image, str, str, int]]) -> None:
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{constants.SCREEN_WIDTH}x{constants.SCREEN_HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(DEMO_VIDEO),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
    if process.stdin is None:
        raise RuntimeError("Could not open the video encoder input stream.")
    try:
        for frame in video_frames(slides):
            process.stdin.write(frame.tobytes())
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("Video encoding failed.")


def main() -> int:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    slides = render_screens()
    write_gif(slides)
    write_video(slides)
    pygame.quit()
    print(f"Wrote {len(slides)} screenshots, {DEMO_GIF.name}, and {DEMO_VIDEO.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
