#!/usr/bin/env python3
"""Self-check for the Phase 4 background structure diagnostic."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
COMPARE = ROOT / "scripts" / "compare_background_structure.py"


def make_scene(path: Path, *, warm: bool = False, shifted: bool = False) -> None:
    bg = (248, 235, 220) if warm else (230, 240, 250)
    fg = (230, 170, 120) if warm else (150, 185, 225)
    image = Image.new("RGB", (300, 400), bg)
    draw = ImageDraw.Draw(image)
    offset = 24 if shifted else 0
    draw.rounded_rectangle((165 + offset, 30, 285 + offset, 240), radius=42, fill=fg)
    draw.ellipse((205 - offset, 265, 285 - offset, 345), fill=fg)
    draw.arc((20, 250 + offset, 250, 480 + offset), 190, 330, fill=(110, 130, 150), width=10)
    image.save(path, "PNG")


def compare(master: Path, candidate: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(COMPARE), "--master", str(master), "--candidate", str(candidate)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="md3-structure-test-") as temporary:
        root = Path(temporary)
        master = root / "master.png"
        recolored = root / "recolored.png"
        shifted = root / "shifted.png"
        make_scene(master)
        make_scene(recolored, warm=True)
        make_scene(shifted, warm=True, shifted=True)

        same_geometry = compare(master, recolored)
        changed_geometry = compare(master, shifted)

        assert same_geometry["automatic_acceptance"] is False
        assert same_geometry["edge_correlation"] > changed_geometry["edge_correlation"]
        assert same_geometry["edge_jaccard_top15pct"] > changed_geometry["edge_jaccard_top15pct"]
        assert same_geometry["edge_mae_normalized"] < changed_geometry["edge_mae_normalized"]

    print("md3-product-image background structure metric self-check passed")


if __name__ == "__main__":
    main()
