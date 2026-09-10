#!/usr/bin/env python3
"""Integration checks for the master-bound production raster contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPTS = Path(__file__).resolve().parent


def run(script: str, *args: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout


def must_fail(script: str, *args: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode
    return completed.stderr or completed.stdout


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="md3-raster-integration-") as temp:
        root = Path(temp)
        product = root / "product.png"
        sku_product = root / "sku.png"
        logo = root / "logo.png"
        master_background = root / "master-background.png"
        sku_background = root / "sku-background.png"
        mismatched_background = root / "sku-background-mismatch.png"

        product_image = Image.new("RGBA", (300, 400), (0, 0, 0, 0))
        ImageDraw.Draw(product_image).rounded_rectangle(
            (105, 55, 280, 355), radius=45, fill="#202124"
        )
        product_image.save(product)
        Image.new("RGBA", (300, 400), "#F57C00").save(sku_product)
        Image.new("RGBA", (240, 80), "#D71920").save(logo)
        Image.new("RGB", (300, 400), "#EEF3F8").save(master_background)
        Image.new("RGB", (300, 400), "#FFF0E4").save(sku_background)
        Image.new("RGB", (600, 800), "#FFF0E4").save(mismatched_background)

        report = json.loads(run(
            "measure_text.py",
            "--complete-name", "Raster Contract Product",
            "--title-lines", "2",
            "--title-line-1", "Raster",
            "--title-line-2", "Contract",
            "--version", "Test",
            "--product-reference", str(product),
            "--logo", str(logo),
            "--output-root", str(root / "products"),
            "--canvas-height", "400",
        ))
        product_dir = Path(report["product_directory"])
        reusable = product_dir / "reusable"
        layout = reusable / "layout.json"

        run(
            "scene_prompt.py", "build",
            "--mode", "MASTER",
            "--layout", str(layout),
        )
        preview = json.loads(run(
            "artifact_flow.py", "preview",
            "--generated-background", str(master_background),
            "--product", str(product),
            "--product-dir", str(product_dir),
            "--candidate-id", "01",
        ))
        assert preview["raster"] == {"width": 300, "height": 400, "ratio": "3:4"}

        master = json.loads(run(
            "artifact_flow.py", "bind",
            "--product-dir", str(product_dir),
            "--candidate-id", "01",
        ))
        assert master["raster"] == {"width": 300, "height": 400, "ratio": "3:4"}

        run(
            "scene_prompt.py", "build",
            "--mode", "SKU",
            "--layout", str(layout),
            "--master", str(reusable / "master.json"),
        )
        error = must_fail(
            "artifact_flow.py", "sku",
            "--generated-background", str(mismatched_background),
            "--product", str(sku_product),
            "--product-dir", str(product_dir),
        )
        assert "SKU_BACKGROUND_RASTER_MISMATCH" in error
        assert not (product_dir / "output" / "SKU_VARIANT-A.png").exists()

        sku = json.loads(run(
            "artifact_flow.py", "sku",
            "--generated-background", str(sku_background),
            "--product", str(sku_product),
            "--product-dir", str(product_dir),
        ))
        assert sku["sku_label"] == "SKU_VARIANT-A"
        assert sku["raster"] == {"width": 300, "height": 400, "ratio": "3:4"}
        with Image.open(product_dir / "output" / "SKU_VARIANT-A.png") as image:
            assert image.size == (300, 400)

        # Backward compatibility: old bound masters did not persist a raster field.
        master_path = reusable / "master.json"
        legacy_master = json.loads(master_path.read_text(encoding="utf-8"))
        legacy_master.pop("raster")
        master_path.write_text(
            json.dumps(legacy_master, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        run(
            "scene_prompt.py", "build",
            "--mode", "SKU",
            "--layout", str(layout),
            "--master", str(master_path),
        )
        sku_b = json.loads(run(
            "artifact_flow.py", "sku",
            "--generated-background", str(sku_background),
            "--product", str(sku_product),
            "--product-dir", str(product_dir),
        ))
        assert sku_b["sku_label"] == "SKU_VARIANT-B"
        assert sku_b["raster"] == {"width": 300, "height": 400, "ratio": "3:4"}

        print("production raster integration self-check passed")


if __name__ == "__main__":
    main()
