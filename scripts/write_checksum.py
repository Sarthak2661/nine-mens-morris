from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EXECUTABLE = DIST / "nine-mens-morris-windows-x64.exe"
CHECKSUMS = DIST / "SHA256SUMS.txt"


def main() -> int:
    if not EXECUTABLE.is_file():
        raise FileNotFoundError(f"Release executable not found: {EXECUTABLE}")
    digest = hashlib.sha256(EXECUTABLE.read_bytes()).hexdigest()
    CHECKSUMS.write_text(f"{digest}  {EXECUTABLE.name}\n", encoding="ascii")
    print(f"Wrote {CHECKSUMS}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
