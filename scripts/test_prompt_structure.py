#!/usr/bin/env python3
"""Self-check for the structured Images 2.5 background prompt."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ACTIVE = ROOT / "references" / "image-gen-prompt.txt"
BASELINE = ROOT / "references" / "image-gen-prompt-v2-baseline.txt"


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
        assert lines.count(heading) == 1, heading
        positions.append(lines.index(heading))
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

    print("md3-product-image structured palette-only prompt self-check passed")


if __name__ == "__main__":
    main()
