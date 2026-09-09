#!/usr/bin/env python3
"""Self-check the validated Work Image Gen callable reference contract."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"MISSING_RUNTIME_CONTRACT_TEXT: {needle}")


def main() -> None:
    text = SKILL.read_text(encoding="utf-8")

    require(text, "always use `referenced_image_paths`")
    require(text, "Omit `num_last_images_to_include` entirely")
    require(text, "mutually exclusive")
    require(text, "reusable/palette-reference.png")
    require(text, "reusable/ORIGINAL_MASTER_BACKGROUND.png")
    require(text, "current SKU `palette_reference`")
    require(text, "Do not send the authoritative product image to Image Gen")
    require(text, "Do not send the current SKU product artwork to Image Gen")
    require(text, "Do not set or infer Image Gen parameters for model selection")
    require(text, "Public API capabilities are not production authority for this Skill")

    assignments = re.findall(
        r"(?m)^\s*num_last_images_to_include\s*=\s*.+$",
        text,
    )
    if assignments:
        raise AssertionError(
            "NUM_LAST_IMAGES_MUST_BE_OMITTED: " + " | ".join(assignments)
        )

    print("md3-product-image runtime reference contract self-check passed")


if __name__ == "__main__":
    main()
