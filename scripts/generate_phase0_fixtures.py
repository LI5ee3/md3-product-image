#!/usr/bin/env python3
"""Generate deterministic synthetic product fixtures for Phase 0 image evals."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


CANVAS = (768, 1024)
SPECS = [
    {
        "id": "light-product",
        "coverage": ["light products"],
        "shape": "rounded",
        "bbox": [210, 130, 558, 900],
        "master_colors": ["#E9EEF3", "#F8FAFC", "#C9D3DD"],
        "sku_colors": ["#F1E5D8", "#FFF8F0", "#D9C3AE"],
    },
    {
        "id": "dark-product",
        "coverage": ["dark products"],
        "shape": "rounded",
        "bbox": [190, 150, 578, 890],
        "master_colors": ["#202124", "#3C4043", "#5F6368"],
        "sku_colors": ["#24202B", "#433A4B", "#665C70"],
    },
    {
        "id": "saturated-product",
        "coverage": ["saturated products"],
        "shape": "rounded",
        "bbox": [205, 145, 563, 895],
        "master_colors": ["#1565C0", "#00ACC1", "#7B1FA2"],
        "sku_colors": ["#D81B60", "#F4511E", "#8E24AA"],
    },
    {
        "id": "low-saturation-product",
        "coverage": ["low-saturation products"],
        "shape": "rounded",
        "bbox": [200, 140, 568, 900],
        "master_colors": ["#A8B0B8", "#C4B8B0", "#B7C1B2"],
        "sku_colors": ["#B5AFA7", "#C7C0B8", "#AEB9BB"],
    },
    {
        "id": "wide-product",
        "coverage": ["wide products"],
        "shape": "wide",
        "bbox": [70, 350, 698, 720],
        "master_colors": ["#5C6BC0", "#90CAF9", "#283593"],
        "sku_colors": ["#43A047", "#A5D6A7", "#1B5E20"],
    },
    {
        "id": "tall-product",
        "coverage": ["tall products"],
        "shape": "tall",
        "bbox": [270, 55, 498, 955],
        "master_colors": ["#26A69A", "#80CBC4", "#00796B"],
        "sku_colors": ["#7E57C2", "#B39DDB", "#512DA8"],
    },
    {
        "id": "multi-dominant-color",
        "coverage": ["products with multiple dominant colors"],
        "shape": "multicolor",
        "bbox": [170, 145, 598, 895],
        "master_colors": ["#4285F4", "#EA4335", "#FBBC05", "#34A853"],
        "sku_colors": ["#00ACC1", "#EC407A", "#FFCA28", "#7CB342"],
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def draw_product(spec: dict, colors: list[str]) -> Image.Image:
    image = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = spec["bbox"]
    radius = max(24, min(right - left, bottom - top) // 9)

    if spec["shape"] in {"rounded", "tall"}:
        draw.rounded_rectangle((left, top, right, bottom), radius=radius, fill=colors[0])
        inset = max(18, (right - left) // 12)
        draw.rounded_rectangle(
            (left + inset, top + inset, right - inset, top + (bottom - top) * 0.28),
            radius=max(12, radius // 2),
            fill=colors[1],
        )
        draw.ellipse(
            (right - inset * 3, bottom - inset * 3, right - inset, bottom - inset),
            fill=colors[2],
        )
    elif spec["shape"] == "wide":
        draw.rounded_rectangle((left, top, right, bottom), radius=radius, fill=colors[0])
        mid = (left + right) // 2
        draw.rounded_rectangle(
            (left + 35, top + 40, mid - 15, bottom - 40),
            radius=28,
            fill=colors[1],
        )
        draw.rounded_rectangle(
            (mid + 15, top + 40, right - 35, bottom - 40),
            radius=28,
            fill=colors[2],
        )
    elif spec["shape"] == "multicolor":
        draw.rounded_rectangle((left, top, right, bottom), radius=radius, fill=colors[0])
        band_h = (bottom - top) // len(colors)
        for index, color in enumerate(colors):
            y0 = top + index * band_h
            y1 = bottom if index == len(colors) - 1 else top + (index + 1) * band_h
            draw.rectangle((left, y0, right, y1), fill=color)
        mask = Image.new("L", CANVAS, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (left, top, right, bottom), radius=radius, fill=255
        )
        image.putalpha(mask)
    else:
        raise ValueError(f"Unknown shape: {spec['shape']}")

    return image


def make_logo(path: Path) -> None:
    logo = Image.new("RGBA", (360, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo)
    draw.rounded_rectangle((0, 12, 96, 108), radius=26, fill="#2C2C2C")
    draw.ellipse((120, 18, 210, 108), fill="#5A5A5A")
    draw.rounded_rectangle((234, 30, 360, 96), radius=24, fill="#2C2C2C")
    logo.save(path, "PNG", optimize=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    logo_path = out / "baseline-logo.png"
    make_logo(logo_path)

    fixtures = []
    for spec in SPECS:
        master_path = out / f"{spec['id']}-master.png"
        sku_path = out / f"{spec['id']}-sku.png"
        draw_product(spec, spec["master_colors"]).save(master_path, "PNG", optimize=False)
        draw_product(spec, spec["sku_colors"]).save(sku_path, "PNG", optimize=False)
        fixtures.append(
            {
                "id": spec["id"],
                "coverage": spec["coverage"],
                "master_product": master_path.name,
                "master_product_sha256": sha256(master_path),
                "sku_product": sku_path.name,
                "sku_product_sha256": sha256(sku_path),
                "geometry_contract": "MASTER and SKU use identical alpha mask and geometry; palette differs only",
                "logo": logo_path.name,
                "logo_sha256": sha256(logo_path),
                "complete_name": f"Phase 0 {spec['id']}",
                "title_lines": 2,
                "title_line_1": "Phase 0",
                "title_line_2": spec["id"],
                "version": "Baseline",
                "source_canvas": {"width": CANVAS[0], "height": CANVAS[1]},
            }
        )

    manifest = {
        "schema": 2,
        "purpose": "fixed deterministic paired MASTER/SKU visual-evaluation inputs for Images 2.5 migration",
        "generator": "scripts/generate_phase0_fixtures.py",
        "pairing_policy": "Within each fixture, MASTER and SKU keep identical geometry and differ only in deterministic palette values.",
        "fixtures": fixtures,
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(manifest_path)


if __name__ == "__main__":
    main()
