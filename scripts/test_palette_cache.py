#!/usr/bin/env python3
"""Self-check for deterministic MASTER/SKU palette asset caching."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "scripts" / "palette_cache.py"


def run_cache(source: Path, product_dir: Path, role: str, *, expect_ok: bool = True):
    completed = subprocess.run(
        [
            sys.executable,
            str(CACHE),
            "--source",
            str(source),
            "--product-dir",
            str(product_dir),
            "--role",
            role,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if expect_ok:
        assert completed.returncode == 0, completed.stderr or completed.stdout
        return json.loads(completed.stdout)
    assert completed.returncode != 0
    return completed.stderr.strip() or completed.stdout.strip()


def make_source(path: Path) -> None:
    image = Image.new("RGBA", (160, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 80, 110), fill=(245, 110, 35, 255))
    draw.rectangle((80, 10, 150, 110), fill=(245, 225, 185, 255))
    draw.rectangle((55, 35, 105, 85), fill=(25, 30, 35, 255))
    image.save(path, "PNG")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="md3-palette-cache-test-") as temporary:
        root = Path(temporary)
        product_dir = root / "Product"
        reusable = product_dir / "reusable"
        reusable.mkdir(parents=True)
        source = root / "source.png"
        make_source(source)

        first_master = run_cache(source, product_dir, "MASTER")
        assert first_master["created"] is True
        master_json = Path(first_master["palette_json"])
        master_reference = Path(first_master["palette_reference"])
        assert master_json == reusable / "palette.json"
        assert master_reference == reusable / "palette-reference.png"
        assert master_json.is_file() and master_reference.is_file()

        second_master = run_cache(source, product_dir, "MASTER")
        assert second_master["created"] is False
        assert second_master["palette_json_sha256"] == first_master["palette_json_sha256"]
        assert second_master["palette_reference_sha256"] == first_master["palette_reference_sha256"]

        first_sku = run_cache(source, product_dir, "SKU")
        assert first_sku["created"] is True
        source_sha = first_sku["source_sha256"]
        assert Path(first_sku["palette_json"]) == reusable / "palettes" / f"{source_sha}.json"
        assert Path(first_sku["palette_reference"]) == reusable / "palettes" / f"{source_sha}.png"

        second_sku = run_cache(source, product_dir, "SKU")
        assert second_sku["created"] is False
        assert second_sku["palette_reference_sha256"] == first_sku["palette_reference_sha256"]

        master_reference.write_bytes(master_reference.read_bytes() + b"tamper")
        failure = run_cache(source, product_dir, "MASTER", expect_ok=False)
        assert "PALETTE_REFERENCE_HASH_MISMATCH" in failure

    print("md3-product-image palette cache self-check passed")


if __name__ == "__main__":
    main()
