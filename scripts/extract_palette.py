#!/usr/bin/env python3
"""Extract a deterministic palette-only reference from an authoritative product image."""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image


SCHEMA = 1
DEFAULT_COLORS = 7
DEFAULT_DOMINANT_COLORS = 4
DEFAULT_ALPHA_THRESHOLD = 32
DEFAULT_SAMPLING_EDGE = 512
DEFAULT_DOMINANT_DISTANCE = 28
DEFAULT_ACCENT_DISTANCE = 36
DEFAULT_MIN_ACCENT_WEIGHT = 0.001
REFERENCE_WIDTH = 1024
REFERENCE_HEIGHT = 256


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ValueError(f"FILE_UNREADABLE: {path}: {exc}") from exc
    return digest.hexdigest()


def load_rgba(path: Path) -> Image.Image:
    try:
        with Image.open(path) as source:
            image = source.convert("RGBA")
            image.load()
            return image
    except OSError as exc:
        raise ValueError(f"IMAGE_UNREADABLE: {path}: {exc}") from exc


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{value:02X}" for value in rgb)


def distance_sq(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    return sum((a - b) ** 2 for a, b in zip(left, right))


def build_histogram(
    image: Image.Image,
    *,
    alpha_threshold: int,
    sampling_edge: int,
) -> tuple[list[dict], tuple[int, int], int]:
    sample = image.copy()
    sample.thumbnail((sampling_edge, sampling_edge), Image.Resampling.NEAREST)
    raw = sample.tobytes()
    bins: dict[tuple[int, int, int], list[int]] = {}
    visible_count = 0

    for index in range(0, len(raw), 4):
        red, green, blue, alpha = raw[index:index + 4]
        if alpha < alpha_threshold:
            continue
        key = (red >> 3, green >> 3, blue >> 3)
        record = bins.setdefault(key, [0, 0, 0, 0])
        record[0] += 1
        record[1] += red
        record[2] += green
        record[3] += blue
        visible_count += 1

    if visible_count == 0:
        raise ValueError("NO_VISIBLE_PRODUCT_PIXELS")

    rows: list[dict] = []
    for count, red_sum, green_sum, blue_sum in bins.values():
        rgb = (
            round(red_sum / count),
            round(green_sum / count),
            round(blue_sum / count),
        )
        red_f, green_f, blue_f = (value / 255 for value in rgb)
        _, saturation, value = colorsys.rgb_to_hsv(red_f, green_f, blue_f)
        rows.append(
            {
                "count": count,
                "source_weight": count / visible_count,
                "rgb": rgb,
                "saturation": saturation,
                "value": value,
            }
        )

    rows.sort(key=lambda row: (-row["count"], row["rgb"]))
    return rows, sample.size, visible_count


def select_palette(
    rows: list[dict],
    *,
    colors: int,
    dominant_colors: int,
    dominant_distance: int,
    accent_distance: int,
    min_accent_weight: float,
) -> list[dict]:
    selected: list[dict] = []
    dominant_distance_sq = dominant_distance ** 2
    accent_distance_sq = accent_distance ** 2

    for row in rows:
        if all(
            distance_sq(row["rgb"], existing["rgb"]) >= dominant_distance_sq
            for existing in selected
        ):
            selected.append(row)
            if len(selected) >= dominant_colors:
                break

    if len(selected) < dominant_colors:
        for row in rows:
            if row not in selected:
                selected.append(row)
                if len(selected) >= dominant_colors:
                    break

    accent_candidates = [
        row for row in rows
        if row not in selected and row["source_weight"] >= min_accent_weight
    ]
    accent_candidates.sort(
        key=lambda row: (
            -(row["saturation"] * math.sqrt(row["source_weight"])),
            -row["source_weight"],
            row["rgb"],
        )
    )

    for row in accent_candidates:
        if all(
            distance_sq(row["rgb"], existing["rgb"]) >= accent_distance_sq
            for existing in selected
        ):
            selected.append(row)
            if len(selected) >= colors:
                break

    remaining = [row for row in rows if row not in selected]
    while len(selected) < colors and remaining:
        def fallback_score(row: dict) -> tuple[float, float, tuple[int, int, int]]:
            minimum_distance = min(
                distance_sq(row["rgb"], existing["rgb"])
                for existing in selected
            )
            diversity = math.sqrt(minimum_distance) * math.sqrt(row["source_weight"])
            return diversity, row["source_weight"], tuple(-value for value in row["rgb"])

        best = max(remaining, key=fallback_score)
        selected.append(best)
        remaining.remove(best)

    return selected[:colors]


def assign_reference_weights(rows: list[dict], selected: list[dict]) -> list[dict]:
    if not selected:
        raise ValueError("PALETTE_EMPTY")
    assigned = [0.0] * len(selected)
    for row in rows:
        nearest_index = min(
            range(len(selected)),
            key=lambda index: (
                distance_sq(row["rgb"], selected[index]["rgb"]),
                index,
            ),
        )
        assigned[nearest_index] += row["source_weight"]

    weighted = []
    for index, row in enumerate(selected):
        copy = dict(row)
        copy["reference_weight"] = assigned[index]
        weighted.append(copy)
    weighted.sort(key=lambda row: (-row["reference_weight"], row["rgb"]))
    return weighted


def render_reference(colors: list[dict], output: Path) -> None:
    if output.exists():
        raise ValueError(f"REFUSE_OVERWRITE: {output}")
    total = sum(row["reference_weight"] for row in colors)
    if total <= 0:
        raise ValueError("PALETTE_WEIGHT_INVALID")

    image = Image.new("RGB", (REFERENCE_WIDTH, REFERENCE_HEIGHT))
    cumulative = 0.0
    left = 0
    for index, row in enumerate(colors):
        cumulative += row["reference_weight"] / total
        right = REFERENCE_WIDTH if index == len(colors) - 1 else round(cumulative * REFERENCE_WIDTH)
        right = max(left + 1, min(REFERENCE_WIDTH, right))
        band = Image.new("RGB", (right - left, REFERENCE_HEIGHT), row["rgb"])
        image.paste(band, (left, 0))
        left = right

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--reference-output", required=True)
    parser.add_argument("--colors", type=int, default=DEFAULT_COLORS)
    parser.add_argument("--alpha-threshold", type=int, default=DEFAULT_ALPHA_THRESHOLD)
    parser.add_argument("--sampling-edge", type=int, default=DEFAULT_SAMPLING_EDGE)
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    json_output = Path(args.json_output).expanduser().resolve()
    reference_output = Path(args.reference_output).expanduser().resolve()

    try:
        if not 1 <= args.colors <= 12:
            raise ValueError("COLOR_COUNT_INVALID")
        if not 0 <= args.alpha_threshold <= 255:
            raise ValueError("ALPHA_THRESHOLD_INVALID")
        if args.sampling_edge < 64:
            raise ValueError("SAMPLING_EDGE_INVALID")
        if json_output.exists():
            raise ValueError(f"REFUSE_OVERWRITE: {json_output}")

        image = load_rgba(source)
        rows, sampled_dimensions, visible_count = build_histogram(
            image,
            alpha_threshold=args.alpha_threshold,
            sampling_edge=args.sampling_edge,
        )
        selected = select_palette(
            rows,
            colors=args.colors,
            dominant_colors=min(DEFAULT_DOMINANT_COLORS, args.colors),
            dominant_distance=DEFAULT_DOMINANT_DISTANCE,
            accent_distance=DEFAULT_ACCENT_DISTANCE,
            min_accent_weight=DEFAULT_MIN_ACCENT_WEIGHT,
        )
        selected = assign_reference_weights(rows, selected)

        selected_source_coverage = sum(row["source_weight"] for row in selected)
        palette_colors = []
        for rank, row in enumerate(selected, 1):
            palette_colors.append(
                {
                    "rank": rank,
                    "hex": rgb_hex(row["rgb"]),
                    "rgb": list(row["rgb"]),
                    "source_weight": round(row["source_weight"], 8),
                    "reference_weight": round(row["reference_weight"], 8),
                }
            )

        payload = {
            "schema": SCHEMA,
            "source_sha256": sha256_file(source),
            "source_dimensions": {"width": image.width, "height": image.height},
            "sampling": {
                "method": "nearest",
                "max_edge": args.sampling_edge,
                "sampled_width": sampled_dimensions[0],
                "sampled_height": sampled_dimensions[1],
                "alpha_threshold": args.alpha_threshold,
                "visible_sample_pixels": visible_count,
                "rgb_bin_bits_per_channel": 5,
            },
            "policy": {
                "requested_colors": args.colors,
                "dominant_slots": min(DEFAULT_DOMINANT_COLORS, args.colors),
                "dominant_min_rgb_distance": DEFAULT_DOMINANT_DISTANCE,
                "accent_min_rgb_distance": DEFAULT_ACCENT_DISTANCE,
                "minimum_accent_source_weight": DEFAULT_MIN_ACCENT_WEIGHT,
                "reference_weighting": "nearest-selected-color assignment over all visible bins",
            },
            "selected_source_coverage": round(selected_source_coverage, 8),
            "reference_weight_sum": round(sum(row["reference_weight"] for row in selected), 8),
            "colors": palette_colors,
        }

        render_reference(selected, reference_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        report = {
            "json_output": str(json_output),
            "reference_output": str(reference_output),
            "source_sha256": payload["source_sha256"],
            "palette_sha256": sha256_file(json_output),
            "reference_sha256": sha256_file(reference_output),
            "color_count": len(palette_colors),
            "colors": palette_colors,
        }
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
