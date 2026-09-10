#!/usr/bin/env python3
"""Deterministic self-checks for extract_palette.py."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPTS = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(source: Path, json_output: Path, reference_output: Path, *, fail: bool = False) -> str:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "extract_palette.py"),
            "--source", str(source),
            "--json-output", str(json_output),
            "--reference-output", str(reference_output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if fail:
        assert completed.returncode
        return completed.stderr or completed.stdout
    if completed.returncode:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout


def build_source(path: Path, transparent_rgb: tuple[int, int, int]) -> None:
    image = Image.new("RGBA", (320, 480), transparent_rgb + (0,))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 90, 250, 410), radius=55, fill=(33, 36, 42, 255))
    draw.rectangle((96, 128, 224, 260), fill=(50, 92, 152, 255))
    draw.rectangle((110, 150, 205, 185), fill=(232, 92, 25, 255))
    draw.ellipse((120, 285, 210, 375), fill=(218, 218, 220, 255))
    image.save(path)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="md3-palette-test-") as temp:
        root = Path(temp)
        source = root / "source.png"
        source_transparent_variant = root / "source-transparent-variant.png"
        fully_transparent = root / "fully-transparent.png"
        build_source(source, (0, 255, 0))
        build_source(source_transparent_variant, (255, 0, 255))
        Image.new("RGBA", (320, 480), (10, 200, 30, 0)).save(fully_transparent)

        json_a = root / "a.json"
        ref_a = root / "a.png"
        json_b = root / "b.json"
        ref_b = root / "b.png"
        run(source, json_a, ref_a)
        run(source, json_b, ref_b)

        assert sha256(json_a) == sha256(json_b)
        assert sha256(ref_a) == sha256(ref_b)
        payload_a = json.loads(json_a.read_text(encoding="utf-8"))
        payload_b = json.loads(json_b.read_text(encoding="utf-8"))
        assert payload_a == payload_b
        assert payload_a["schema"] == 1
        assert payload_a["policy"]["requested_colors"] == 7
        assert 1 <= len(payload_a["colors"]) <= 7
        assert all(color["hex"].startswith("#") for color in payload_a["colors"])
        assert payload_a["reference_sha256"] == sha256(ref_a)

        with Image.open(ref_a) as reference:
            assert reference.size == (1024, 256)
            assert reference.mode == "RGB"

        variant_json = root / "variant.json"
        variant_ref = root / "variant.png"
        run(source_transparent_variant, variant_json, variant_ref)
        payload_variant = json.loads(variant_json.read_text(encoding="utf-8"))

        # Transparent RGB values may change source identity, but they must not change
        # the visible palette selection or the color-only reference pixels.
        assert payload_variant["source_sha256"] != payload_a["source_sha256"]
        assert payload_variant["colors"] == payload_a["colors"]
        assert payload_variant["reference_sha256"] == payload_a["reference_sha256"]
        assert sha256(variant_ref) == sha256(ref_a)

        error = run(
            fully_transparent,
            root / "transparent.json",
            root / "transparent-reference.png",
            fail=True,
        )
        assert "NO_VISIBLE_PRODUCT_PIXELS" in error

        print("deterministic palette extraction self-check passed")


if __name__ == "__main__":
    main()
