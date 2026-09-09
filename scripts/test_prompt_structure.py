#!/usr/bin/env python3
"""Self-check for the Phase 2 structured Images 2.5 background prompt."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ACTIVE = ROOT / "references" / "image-gen-prompt.txt"
BASELINE = ROOT / "references" / "image-gen-prompt-v2-baseline.txt"


def main() -> None:
    active = ACTIVE.read_text(encoding="utf-8")
    baseline = BASELINE.read_text(encoding="utf-8")

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
        assert active.count(heading) == 1, heading
        positions.append(active.index(heading))
    assert positions == sorted(positions)

    assert "PRODUCT_REFERENCE: authoritative palette reference only." in active
    assert "Do not reproduce, redraw, trace, imitate, or transfer the product itself" in active
    assert "Do not generate any product, product silhouette" in active
    assert "Return exactly one empty 3:4 background plate." in active
    assert "Google Material Design 3 Classic" in active
    assert "rather than M3 Expressive" in active

    assert baseline.startswith(
        "A 3:4 professional e-commerce product hero background plate"
    )
    assert "DELIVERABLE" not in baseline
    assert active != baseline

    print("md3-product-image structured prompt self-check passed")


if __name__ == "__main__":
    main()
