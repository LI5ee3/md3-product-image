#!/usr/bin/env python3
"""End-to-end self-check for the stateless user-controlled MD3 workflow."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPTS = Path(__file__).resolve().parent


def run(script: str, *args: str) -> str:
    completed = subprocess.run([sys.executable, str(SCRIPTS / script), *args], text=True, capture_output=True, check=False)
    if completed.returncode:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout


def must_fail(script: str, *args: str) -> str:
    completed = subprocess.run([sys.executable, str(SCRIPTS / script), *args], text=True, capture_output=True, check=False)
    assert completed.returncode
    return completed.stderr or completed.stdout


def scene_prompt(layout: Path, mode: str, *, master: Path | None = None, redo: bool = False, addition: str = "", fail: bool = False) -> str:
    args = ["build", "--layout", str(layout), "--mode", mode]
    if master:
        args += ["--master", str(master)]
    if redo:
        args.append("--redo")
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
        ImageDraw.Draw(product_image).rounded_rectangle((110, 60, 280, 350), radius=45, fill="#EA4335")
        product_image.save(product, "WEBP", lossless=True)
        Image.new("RGB", (300, 400), "#4285F4").save(sku_product)
        Image.new("RGB", (240, 80), "#202124").save(logo)
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
        assert not (product_dir / "scene-attempts.json").exists()
        reusable = product_dir / "reusable"
        layout = reusable / "layout.json"
        assert layout.is_file() and (reusable / "logo.png").is_file()
        assert report["product_reference"]["format"] == "WEBP"
        assert report["title_lines"] == ["Pixel by", "Google"]
        assert report["version"] == "Глобальная версия"
        assert report["font"]["name"] == "Rubik Variable"
        assert report["font"]["weight"] == 700

        prompt = scene_prompt(layout, "MASTER")
        assert "FINAL_INFORMATION_SAFE_ZONE" in prompt
        assert scene_prompt(layout, "MASTER") == prompt
        assert not (product_dir / "scene-attempts.json").exists()
        assert not list(product_dir.glob("scene-prompt-*.md"))

        preview = json.loads(run("artifact_flow.py", "preview", "--generated-background", str(background), "--product", str(product), "--product-dir", str(product_dir), "--candidate-id", "01"))
        assert "information" not in preview and "scene_composite" not in preview
        assert "scene_attempt" not in preview
        preview_manifest = json.loads((product_dir / "master-candidate-01-preview.json").read_text(encoding="utf-8"))
        assert "files" not in preview_manifest
        assert preview_manifest["background_sha256"] == sha256(product_dir / "master-candidate-01-preview-background.png")
        assert preview_manifest["final_sha256"] == sha256(product_dir / "master-candidate-01-preview.png")
        cached_product = reusable / "master-candidate-01-product.png"
        cached_shadow = reusable / "master-candidate-01-shadow.png"
        cached_hashes = (sha256(cached_product), sha256(cached_shadow))
        run("artifact_flow.py", "discard-preview", "--product-dir", str(product_dir), "--candidate-id", "01")

        retry_prompt = scene_prompt(layout, "MASTER", redo=True, addition="Keep the left side quieter")
        assert retry_prompt.count("Keep the left side quieter") == 1
        for _ in range(3):
            repeated_prompt = scene_prompt(layout, "MASTER", redo=True)
            assert repeated_prompt.count("Keep the left side quieter") == 1

        run("artifact_flow.py", "preview", "--generated-background", str(second_background), "--product", str(product), "--product-dir", str(product_dir), "--candidate-id", "01")
        assert cached_hashes == (sha256(cached_product), sha256(cached_shadow))
        final_preview = product_dir / "master-candidate-01-preview.png"
        final_preview_bytes = final_preview.read_bytes()
        Image.new("RGB", (300, 400), "black").save(final_preview)
        assert "PREVIEW_FINAL_HASH_MISMATCH" in must_fail("artifact_flow.py", "bind", "--product-dir", str(product_dir), "--candidate-id", "01")
        final_preview.write_bytes(final_preview_bytes)
        run("artifact_flow.py", "bind", "--product-dir", str(product_dir), "--candidate-id", "01")
        master = reusable / "master.json"
        assert master.is_file()
        master_payload = json.loads(master.read_text(encoding="utf-8"))
        assert "scene" not in master_payload["files"]
        assert "information" not in master_payload and "scene_composite" not in master_payload
        assert not list(product_dir.glob("*-scene.png"))
        assert not (reusable / "ORIGINAL_MASTER_SCENE.png").exists()
        assert {path.name for path in (product_dir / "output").iterdir()} == {"ORIGINAL_MASTER_FINAL.png"}

        sku_prompt = scene_prompt(layout, "SKU", master=master)
        assert "Keep the left side quieter" in sku_prompt
        sku_report = json.loads(run("artifact_flow.py", "sku", "--generated-background", str(background), "--product", str(sku_product), "--product-dir", str(product_dir)))
        assert sku_report["sku_label"] == "SKU_VARIANT-A"
        assert "information" not in sku_report and "scene_composite" not in sku_report
        assert "master_verified" not in sku_report
        assert "scene_attempt" not in sku_report

        sku_layers = (reusable / "SKU_VARIANT-A-product.png", reusable / "SKU_VARIANT-A-shadow.png")
        sku_layer_hashes = tuple(sha256(path) for path in sku_layers)
        sku_final = product_dir / "output" / "SKU_VARIANT-A.png"
        assert sku_final.is_file()
        original_sku_hash = sha256(sku_final)

        sku_retry_prompt = scene_prompt(layout, "SKU", master=master, redo=True, addition="Use warmer accent cards")
        assert "Keep the left side quieter" in sku_retry_prompt
        assert "Use warmer accent cards" in sku_retry_prompt
        assert original_sku_hash == sha256(sku_final)

        must_fail("artifact_flow.py", "sku", "--generated-background", str(root / "missing-background.png"), "--product", str(sku_product), "--product-dir", str(product_dir), "--redo", "--target", "SKU_VARIANT-A")
        assert original_sku_hash == sha256(sku_final)

        redo_report = json.loads(run("artifact_flow.py", "sku", "--generated-background", str(second_background), "--product", str(sku_product), "--product-dir", str(product_dir), "--redo", "--target", "SKU_VARIANT-A"))
        assert redo_report["sku_label"] == "SKU_VARIANT-A"
        assert sku_layer_hashes == tuple(sha256(path) for path in sku_layers)
        assert sha256(sku_final) != original_sku_hash

        scene_prompt(layout, "SKU", master=master)
        run("artifact_flow.py", "sku", "--generated-background", str(background), "--product", str(sku_product), "--product-dir", str(product_dir))
        assert (product_dir / "output" / "SKU_VARIANT-B.png").is_file()

        assert json.loads((reusable / "prompt-additions.json").read_text()) == ["Keep the left side quieter", "Use warmer accent cards"]
        assert not (product_dir / "scene-attempts.json").exists()
        assert not list(product_dir.glob("scene-prompt-*.md"))
        assert not list(product_dir.rglob("*thumb*"))
        print("md3-product-image workflow self-check passed")


if __name__ == "__main__":
    main()
