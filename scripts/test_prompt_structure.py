#!/usr/bin/env python3
"""Self-check for the structured Images 2.5 background prompt."""

from __future__ import annotations

from pathlib import Path

from scene_prompt import SKU_EDIT_BLOCK


ROOT = Path(__file__).resolve().parent.parent
ACTIVE = ROOT / "references" / "image-gen-prompt.md"
BASELINE = ROOT / "references" / "image-gen-prompt-v2-baseline.txt"
LEGACY_SKU_EDIT_BLOCK = """Use ORIGINAL_MASTER_BACKGROUND as the authoritative composition reference and SKU_PALETTE_REFERENCE only as the authoritative color reference. Keep the background composition unchanged and adapt only its colors to SKU_PALETTE_REFERENCE. Do not infer or copy any product identity, geometry, silhouette, screen, strap, label, icon, branding, text, or packaging from the palette reference. Generate the empty background plate only. Do not add any product, product shadow, Logo, or text."""


def main() -> None:
    active = ACTIVE.read_text(encoding="utf-8")
    baseline = BASELINE.read_text(encoding="utf-8")
    lines = active.splitlines()

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
        assert lines.count(markdown_heading) == 1, heading
        positions.append(lines.index(markdown_heading))
    assert positions == sorted(positions)

    assert "PALETTE_REFERENCE: authoritative color-only palette reference." in active
    assert "must not be treated as a source of product identity" in active
    assert "Do not infer or invent a product silhouette" in active
    assert "Do not generate any product, product silhouette" in active
    assert "Return exactly one empty 3:4 background plate." in active
    assert "Google Material Design 3 Classic" in active
    assert "rather than M3 Expressive" in active

    assert baseline.startswith(
        "A 3:4 professional e-commerce product hero background plate"
    )
    assert "DELIVERABLE" not in baseline
    assert active != baseline

    assert SKU_EDIT_BLOCK == LEGACY_SKU_EDIT_BLOCK
    assert not (ROOT / "references" / "replace-variant-block.md").exists()

    print("md3-product-image structured palette-only prompt self-check passed")


if __name__ == "__main__":
    main()
