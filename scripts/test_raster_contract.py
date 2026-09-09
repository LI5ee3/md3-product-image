#!/usr/bin/env python3
"""Self-check for the Phase 1 native 3:4 raster contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


SCRIPTS = Path(__file__).resolve().parent


def run(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_raster.py"), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def must_fail(*args: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_raster.py"), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode
    return completed.stderr or completed.stdout


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="md3-raster-contract-") as temp:
        root = Path(temp)
        master = root / "master.png"
        sku_same = root / "sku-same.png"
        sku_other = root / "sku-other.png"
        wrong_ratio = root / "wrong-ratio.png"

        Image.new("RGB", (300, 400), "white").save(master)
        Image.new("RGBA", (300, 400), (230, 240, 255, 255)).save(sku_same)
        Image.new("RGB", (600, 800), "white").save(sku_other)
        Image.new("RGB", (400, 400), "white").save(wrong_ratio)

        master_report = run("master", "--generated-background", str(master))
        assert master_report["status"] == "MASTER_RASTER_VALID"
        assert master_report["raster"]["width"] == 300
        assert master_report["raster"]["height"] == 400

        sku_report = run(
            "sku",
            "--master-background", str(master),
            "--generated-background", str(sku_same),
        )
        assert sku_report["status"] == "SKU_RASTER_VALID"
        assert sku_report["master_raster"]["width"] == 300
        assert sku_report["sku_raster"]["height"] == 400

        mismatch = must_fail(
            "sku",
            "--master-background", str(master),
            "--generated-background", str(sku_other),
        )
        assert "SKU_BACKGROUND_SIZE_MISMATCH" in mismatch
        assert "master 300x400, got 600x800" in mismatch

        wrong_master = must_fail(
            "master", "--generated-background", str(wrong_ratio)
        )
        assert "MASTER_BACKGROUND_NOT_3_4" in wrong_master

        wrong_sku = must_fail(
            "sku",
            "--master-background", str(master),
            "--generated-background", str(wrong_ratio),
        )
        assert "SKU_BACKGROUND_NOT_3_4" in wrong_sku

        print("md3-product-image raster contract self-check passed")


if __name__ == "__main__":
    main()
