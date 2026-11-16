from __future__ import annotations

import ctypes
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import constants  # noqa: E402
from GUI import NineMensMorrisGUI  # noqa: E402
from logic import NineMensMorrisGame  # noqa: E402

OUTPUT = ROOT / "resources" / "display-verification"


def system_dpi() -> int | None:
    if os.name != "nt":
        return None
    try:
        return int(ctypes.windll.user32.GetDpiForSystem())
    except AttributeError, OSError:
        return None


def image_from_surface(surface: pygame.Surface) -> Image.Image:
    return Image.frombytes("RGB", surface.get_size(), pygame.image.tobytes(surface, "RGB"))


def letterbox(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = size
    ratio = min(width / image.width, height / image.height)
    scaled = image.resize((round(image.width * ratio), round(image.height * ratio)))
    canvas = Image.new("RGB", size, (8, 14, 24))
    canvas.paste(scaled, ((width - scaled.width) // 2, (height - scaled.height) // 2))
    return canvas


def annotated(image: Image.Image, label: str) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    draw.rectangle((0, 0, 330, 34), fill=(8, 14, 24))
    draw.text((12, 9), label, fill=(255, 255, 255))
    return result


def main() -> int:
    pygame.init()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    game = NineMensMorrisGame()
    for point in ((0, 0), (6, 6), (0, 3), (6, 3)):
        game.make_move(*point)
    gui = NineMensMorrisGUI(game)
    gui.board_keyboard_active = True
    gui.board_focus_index = 2

    frames: list[Image.Image] = []
    for high_contrast in (False, True):
        gui.high_contrast = high_contrast
        gui.draw_board()
        base = image_from_surface(gui.screen)
        for size in constants.SUPPORTED_WINDOW_SIZES:
            rendered = letterbox(base, size)
            name = "high-contrast" if high_contrast else "standard"
            path = OUTPUT / f"{name}-{size[0]}x{size[1]}.png"
            rendered.save(path, optimize=True)
            preview = letterbox(rendered, (480, 270))
            frames.append(annotated(preview, f"{name} | {size[0]} x {size[1]}"))

    matrix = Image.new("RGB", (960, 810), (8, 14, 24))
    for index, frame in enumerate(frames):
        matrix.paste(frame, ((index % 2) * 480, (index // 2) * 270))
    matrix.save(OUTPUT / "display-matrix.png", optimize=True)

    dpi = system_dpi()
    report = {
        "logical_canvas": [constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT],
        "system_dpi": dpi,
        "system_scale_percent": round(dpi / 96 * 100) if dpi is not None else None,
        "verified_scale_factors": list(constants.SUPPORTED_DISPLAY_SCALES),
        "verified_window_sizes": [list(size) for size in constants.SUPPORTED_WINDOW_SIZES],
        "modes": ["standard", "high-contrast"],
    }
    (OUTPUT / "display-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pygame.quit()
    print(f"Wrote display verification artifacts to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
