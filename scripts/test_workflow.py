#!/usr/bin/env python3
"""End-to-end self-check for the user-controlled MD3 workflow."""

import hashlib
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


def scene_prompt(
    action: str, layout: Path, mode: str, *, target: str = "", master: Path | None = None,
    addition: str = "", fail: bool = False,
) -> str:
    args = [action, "--layout", str(layout), "--mode", mode]
    if target:
        args += ["--target", target]
    if master:
        args += ["--master", str(master)]
    if addition:
        args += ["--additional-prompt", addition]
    return (must_fail if fail else run)("scene_prompt.py", *args)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="md3-product-image-") as temp:
        root = Path(temp)
        product = root / "product.webp"
        sku_product = root / "sku.png"
        logo = root / "source-logo.png"
        background = root / "background.png"
        second_background = root / "background-2.png"
        product_image = Image.new("RGBA", (300, 400), (0, 0, 0, 0))
        ImageDraw.Draw(product_image).rounded_rectangle(
            (110, 60, 280, 350), radius=45, fill="#EA4335"
        )
        product_image.save(product, "WEBP", lossless=True)
        sku_image = Image.new("RGB", (300, 400), "#4285F4")
        sku_image.save(sku_product)
        logo_image = Image.new("RGB", (240, 80), "#202124")
        logo_image.save(logo)
        Image.new("RGB", (300, 400), "#F4F6F8").save(background)
        Image.new("RGB", (300, 400), "#EEF3F8").save(second_background)

        report = json.loads(run(
            "measure_text.py",
            "--complete-name", "Google Pixel",
            "--title-lines", "2",
            "--title-line-1", "Pixel by",
            "--title-line-2", "Google",
            "--version", "Глобальная версия",
            "--product-reference", str(product),
            "--logo", str(logo),
            "--output-root", str(root / "products"),
            "--canvas-height", "400",
        ))
        product_dir = Path(report["product_directory"])
        reusable = product_dir / "reusable"
        layout = reusable / "layout.json"
        assert layout.is_file() and (reusable / "logo.png").is_file()
        assert report["product_reference"]["format"] == "WEBP"
        assert report["title_lines"] == ["Pixel by", "Google"]
        assert report["version"] == "Глобальная версия"
        assert report["font"]["name"] == "Rubik Variable"
        assert report["font"]["weight"] == 700

        prompt = scene_prompt("build", layout, "MASTER", target="01")
        assert "FINAL_INFORMATION_SAFE_ZONE" in prompt
        state = json.loads((product_dir / "scene-attempts.json").read_text())
        prompt_path = product_dir / state["runs"][-1]["attempts"][-1]["prompt_path"]
        assert prompt_path.read_text() == prompt
        assert "USER_DECISION_REQUIRED" in scene_prompt(
            "build", layout, "MASTER", target="01", fail=True
        )
        preview = json.loads(run(
            "artifact_flow.py", "preview",
            "--generated-background", str(background),
            "--product", str(product),
            "--product-dir", str(product_dir),
            "--candidate-id", "01",
        ))
        assert preview["information"] == {
            "title_color": "2C2C2C",
            "version_color": "5A5A5A",
        }
        cached_product = reusable / "master-candidate-01-product.png"
        cached_shadow = reusable / "master-candidate-01-shadow.png"
        cached_hashes = (sha256(cached_product), sha256(cached_shadow))
        run(
            "artifact_flow.py", "discard-preview",
            "--product-dir", str(product_dir), "--candidate-id", "01",
        )
        scene_prompt(
            "reject", layout, "MASTER", target="01",
            addition="Keep the left side quieter",
        )

        for index in range(4):
            retry_prompt = scene_prompt("build", layout, "MASTER", target="01")
            assert retry_prompt.count("Keep the left side quieter") == 1
            if index < 3:
                scene_prompt("reject", layout, "MASTER", target="01")

        run(
            "artifact_flow.py", "preview",
            "--generated-background", str(second_background),
            "--product", str(product),
            "--product-dir", str(product_dir),
            "--candidate-id", "01",
        )
        assert cached_hashes == (sha256(cached_product), sha256(cached_shadow))
        run(
            "artifact_flow.py", "bind",
            "--product-dir", str(product_dir), "--candidate-id", "01",
        )
        master = reusable / "master.json"
        assert master.is_file()
        assert {path.name for path in (product_dir / "output").iterdir()} == {
            "ORIGINAL_MASTER_FINAL.png"
        }

        sku_prompt = scene_prompt("build", layout, "SKU", master=master)
        assert "Keep the left side quieter" in sku_prompt
        sku_report = json.loads(run(
            "artifact_flow.py", "sku",
            "--generated-background", str(background),
            "--product", str(sku_product),
            "--product-dir", str(product_dir),
        ))
        assert sku_report["information"] == {
            "title_color": "2C2C2C",
            "version_color": "5A5A5A",
        }
        sku_layers = (
            reusable / "SKU_VARIANT-A-product.png",
            reusable / "SKU_VARIANT-A-shadow.png",
        )
        sku_layer_hashes = tuple(sha256(path) for path in sku_layers)
        sku_final = product_dir / "output" / "SKU_VARIANT-A.png"
        assert sku_final.is_file()
        original_sku_hash = sha256(sku_final)
        sku_retry_prompt = run(
            "scene_prompt.py", "build", "--layout", str(layout), "--mode", "SKU",
            "--master", str(master), "--redo", "--target", "SKU_VARIANT-A",
            "--additional-prompt", "Use warmer accent cards",
        )
        assert "Keep the left side quieter" in sku_retry_prompt
        assert "Use warmer accent cards" in sku_retry_prompt
        assert original_sku_hash == sha256(sku_final)
        must_fail(
            "artifact_flow.py", "sku",
            "--generated-background", str(root / "missing-background.png"),
            "--product", str(sku_product),
            "--product-dir", str(product_dir),
        )
        assert original_sku_hash == sha256(sku_final)
        redo_report = json.loads(run(
            "artifact_flow.py", "sku",
            "--generated-background", str(second_background),
            "--product", str(sku_product),
            "--product-dir", str(product_dir),
        ))
        assert redo_report["sku_label"] == "SKU_VARIANT-A"
        assert sku_layer_hashes == tuple(sha256(path) for path in sku_layers)
        assert sha256(sku_final) != original_sku_hash

        scene_prompt("build", layout, "SKU", master=master)
        run(
            "artifact_flow.py", "sku",
            "--generated-background", str(background),
            "--product", str(sku_product),
            "--product-dir", str(product_dir),
        )
        assert (product_dir / "output" / "SKU_VARIANT-B.png").is_file()

        assert json.loads((reusable / "prompt-additions.json").read_text()) == [
            "Keep the left side quieter",
            "Use warmer accent cards",
        ]
        assert not list(product_dir.rglob("*thumb*"))
        print("md3-product-image workflow self-check passed")


def release_contract_checks() -> None:
    root = SCRIPTS.parent
    active_prompt = root / "references" / "image-gen-prompt.md"
    assert active_prompt.is_file()
    assert not (root / "references" / "image-gen-prompt.txt").exists()
    assert not (root / "references" / "image-gen-prompt-v2-baseline.txt").exists()
    prompt_text = active_prompt.read_text(encoding="utf-8")
    prompt_lines = prompt_text.splitlines()
    headings = [
        "DELIVERABLE",
        "REFERENCE ROLES",
        "VISUAL SYSTEM",
        "PALETTE",
        "COMPOSITION",
        "LIGHTING",
        "EXCLUSIONS",
        "OUTPUT CONTRACT",
    ]
    positions = []
    for heading in headings:
        markdown_heading = f"## {heading}"
        assert prompt_lines.count(markdown_heading) == 1
        positions.append(prompt_lines.index(markdown_heading))
    assert positions == sorted(positions)
    assert "PALETTE_REFERENCE: authoritative color-only palette reference." in prompt_text
    assert "Return exactly one empty 3:4 background plate." in prompt_text

    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    for needle in [
        "always use `referenced_image_paths`",
        "Omit `num_last_images_to_include` entirely",
        "mutually exclusive",
        "reusable/palette-reference.png",
        "reusable/ORIGINAL_MASTER_BACKGROUND.png",
        "current SKU `palette_reference`",
        "Do not send the authoritative product image to Image Gen",
        "Do not send the current SKU product artwork to Image Gen",
        "Public API capabilities are not production authority for this Skill",
    ]:
        assert needle in skill, needle
    assert "num_last_images_to_include =" not in skill

    with tempfile.TemporaryDirectory(prefix="md3-release-contract-") as temp:
        release_root = Path(temp)
        master = release_root / "master.png"
        sku_same = release_root / "sku-same.png"
        sku_other = release_root / "sku-other.png"
        wrong_ratio = release_root / "wrong-ratio.png"
        Image.new("RGB", (300, 400), "white").save(master)
        Image.new("RGBA", (300, 400), (230, 240, 255, 255)).save(sku_same)
        Image.new("RGB", (600, 800), "white").save(sku_other)
        Image.new("RGB", (400, 400), "white").save(wrong_ratio)

        raster = json.loads(run(
            "validate_raster.py", "master", "--generated-background", str(master)
        ))
        assert raster["status"] == "MASTER_RASTER_VALID"
        same = json.loads(run(
            "validate_raster.py", "sku",
            "--master-background", str(master),
            "--generated-background", str(sku_same),
        ))
        assert same["status"] == "SKU_RASTER_VALID"
        mismatch = must_fail(
            "validate_raster.py", "sku",
            "--master-background", str(master),
            "--generated-background", str(sku_other),
        )
        assert "SKU_BACKGROUND_SIZE_MISMATCH" in mismatch
        assert "MASTER_BACKGROUND_NOT_3_4" in must_fail(
            "validate_raster.py", "master", "--generated-background", str(wrong_ratio)
        )

        source = release_root / "palette-source.png"
        source_image = Image.new("RGBA", (160, 120), (0, 0, 0, 0))
        draw = ImageDraw.Draw(source_image)
        draw.rectangle((10, 10, 80, 110), fill=(245, 110, 35, 255))
        draw.rectangle((80, 10, 150, 110), fill=(245, 225, 185, 255))
        draw.rectangle((55, 35, 105, 85), fill=(25, 30, 35, 255))
        source_image.save(source)
        product_dir = release_root / "Palette Product"
        (product_dir / "reusable").mkdir(parents=True)
        first = json.loads(run(
            "palette_cache.py", "--source", str(source),
            "--product-dir", str(product_dir), "--role", "MASTER"
        ))
        second = json.loads(run(
            "palette_cache.py", "--source", str(source),
            "--product-dir", str(product_dir), "--role", "MASTER"
        ))
        assert first["created"] is True
        assert second["created"] is False
        assert first["palette_json_sha256"] == second["palette_json_sha256"]
        assert first["palette_reference_sha256"] == second["palette_reference_sha256"]

    print("md3-product-image release contract checks passed")


if __name__ == "__main__":
    main()
    release_contract_checks()
