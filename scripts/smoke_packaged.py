from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE = ROOT / "dist" / "nine-mens-morris-windows-x64.exe"
STARTUP_SECONDS = 5


def main() -> int:
    if not EXECUTABLE.is_file():
        raise FileNotFoundError(f"Packaged executable not found: {EXECUTABLE}")

    environment = os.environ.copy()
    environment["SDL_VIDEODRIVER"] = "dummy"
    environment["SDL_AUDIODRIVER"] = "dummy"
    process = subprocess.Popen([EXECUTABLE], env=environment)

    try:
        deadline = time.monotonic() + STARTUP_SECONDS
        while time.monotonic() < deadline:
            return_code = process.poll()
            if return_code is not None:
                raise RuntimeError(f"Packaged game exited during startup with code {return_code}.")
            time.sleep(0.25)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    print(f"Packaged game remained healthy for {STARTUP_SECONDS} seconds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
