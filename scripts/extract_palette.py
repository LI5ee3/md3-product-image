#!/usr/bin/env python3
"""Extract a deterministic material-color palette while excluding semantic display regions."""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image


SCHEMA = 2
DEFAULT_COLORS = 7
DEFAULT_DOMINANT_COLORS = 4
DEFAULT_ALPHA_THRESHOLD = 32
DEFAULT_SAMPLING_EDGE = 512
DEFAULT_DOMINANT_DISTANCE = 28
DEFAULT_ACCENT_DISTANCE = 36
DEFAULT_MIN_ACCENT_WEIGHT = 0.001
DEFAULT_EXCLUSION_MARGIN = 0.02
REFERENCE_WIDTH = 1024
REFERENCE_HEIGHT = 256
DEFAULT_BACKGROUND_MIN_LIGHTNESS_DELTA = 15.0
DEFAULT_BACKGROUND_SAME_HUE_MAX_DEGREES = 10.0
DEFAULT_BACKGROUND_AVOID_LIGHTNESS_WINDOW = 12.0


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



def parse_normalized_box(value: str) -> tuple[float, float, float, float]:
    try:
        parts = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("EXCLUDE_BOX_INVALID") from exc
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("EXCLUDE_BOX_INVALID")
    x0, y0, x1, y1 = parts
    if not (0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0):
        raise argparse.ArgumentTypeError("EXCLUDE_BOX_OUT_OF_RANGE")
    return x0, y0, x1, y1


def visible_bbox_normalized(
    image: Image.Image,
    *,
    alpha_threshold: int,
) -> tuple[float, float, float, float]:
    alpha = image.getchannel("A")
    thresholded = alpha.point(lambda value: 255 if value >= alpha_threshold else 0)
    bbox = thresholded.getbbox()
    if bbox is None:
        raise ValueError("NO_VISIBLE_PRODUCT_PIXELS")
    left, top, right, bottom = bbox
    return (
        left / image.width,
        top / image.height,
        right / image.width,
        bottom / image.height,
    )


def expand_exclusion_boxes(
    image: Image.Image,
    boxes: list[tuple[float, float, float, float]],
    *,
    alpha_threshold: int,
    margin: float,
) -> list[tuple[float, float, float, float]]:
    if not boxes:
        return []
    px0, py0, px1, py1 = visible_bbox_normalized(
        image, alpha_threshold=alpha_threshold
    )
    expand_x = (px1 - px0) * margin
    expand_y = (py1 - py0) * margin
    return [
        (
            max(0.0, x0 - expand_x),
            max(0.0, y0 - expand_y),
            min(1.0, x1 + expand_x),
            min(1.0, y1 + expand_y),
        )
        for x0, y0, x1, y1 in boxes
    ]


def point_in_any_box(
    x: float,
    y: float,
    boxes: list[tuple[float, float, float, float]],
) -> bool:
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes)


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{value:02X}" for value in rgb)


def rgb_to_hls(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    red_f, green_f, blue_f = (value / 255 for value in rgb)
    return colorsys.rgb_to_hls(red_f, green_f, blue_f)


def hls_to_rgb(hue: float, lightness: float, saturation: float) -> tuple[int, int, int]:
    red_f, green_f, blue_f = colorsys.hls_to_rgb(hue % 1.0, max(0.0, min(1.0, lightness)), max(0.0, min(1.0, saturation)))
    return tuple(round(value * 255) for value in (red_f, green_f, blue_f))


def rgb_lightness_lstar(rgb: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        encoded = value / 255
        return encoded / 12.92 if encoded <= 0.04045 else ((encoded + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(value) for value in rgb)
    y = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return 116.0 * (y ** (1.0 / 3.0)) - 16.0 if y > 0.008856 else 903.3 * y


def rgb_hue_degrees(rgb: tuple[int, int, int]) -> float:
    hue, _, _ = rgb_to_hls(rgb)
    return (hue * 360.0) % 360.0


def hue_distance_degrees(left: float, right: float) -> float:
    delta = abs(left - right) % 360.0
    return min(delta, 360.0 - delta)


def unique_color_entries(entries: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for entry in entries:
        color = entry["hex"]
        if color in seen:
            continue
        seen.add(color)
        unique.append(entry)
    return unique


def build_background_guidance(selected: list[dict]) -> dict:
    ranked = sorted(selected, key=lambda row: (-row["reference_weight"], row["rgb"]))
    dominant = ranked[0]
    dominant_rgb = dominant["rgb"]
    dominant_hue, dominant_lightness, dominant_saturation = rgb_to_hls(dominant_rgb)
    dominant_lstar = rgb_lightness_lstar(dominant_rgb)

    if dominant_lstar >= 65.0:
        safe_lightness = max(0.18, dominant_lightness - 0.26)
    elif dominant_lstar <= 40.0:
        safe_lightness = min(0.84, dominant_lightness + 0.26)
    else:
        safe_lightness = min(0.82, dominant_lightness + 0.20)
        if abs(rgb_lightness_lstar(hls_to_rgb(dominant_hue, safe_lightness, dominant_saturation * 0.30 + 0.03)) - dominant_lstar) < DEFAULT_BACKGROUND_MIN_LIGHTNESS_DELTA:
            safe_lightness = max(0.20, dominant_lightness - 0.22)

    safe_saturation = min(0.22, dominant_saturation * 0.35 + 0.03)
    same_hue_rgb = hls_to_rgb(dominant_hue, safe_lightness, safe_saturation)
    cooler_rgb = hls_to_rgb((dominant_hue - DEFAULT_BACKGROUND_SAME_HUE_MAX_DEGREES / 360.0) % 1.0, safe_lightness, safe_saturation)
    warmer_rgb = hls_to_rgb((dominant_hue + DEFAULT_BACKGROUND_SAME_HUE_MAX_DEGREES / 360.0) % 1.0, safe_lightness, safe_saturation)

    avoid_entries = []
    for row in ranked[:4]:
        lstar = rgb_lightness_lstar(row["rgb"])
        avoid_entries.append({
            "hex": rgb_hex(row["rgb"]),
            "hue_degrees": round(rgb_hue_degrees(row["rgb"]), 1),
            "lightness_lstar": round(lstar, 1),
            "reference_weight": round(row["reference_weight"], 8),
        })

    safe_entries = unique_color_entries([
        {
            "hex": rgb_hex(same_hue_rgb),
            "hue_degrees": round(rgb_hue_degrees(same_hue_rgb), 1),
            "lightness_lstar": round(rgb_lightness_lstar(same_hue_rgb), 1),
            "relationship": "same-hue-muted",
        },
        {
            "hex": rgb_hex(cooler_rgb),
            "hue_degrees": round(rgb_hue_degrees(cooler_rgb), 1),
            "lightness_lstar": round(rgb_lightness_lstar(cooler_rgb), 1),
            "relationship": f"hue-shift-minus-{DEFAULT_BACKGROUND_SAME_HUE_MAX_DEGREES:.0f}deg",
        },
        {
            "hex": rgb_hex(warmer_rgb),
            "hue_degrees": round(rgb_hue_degrees(warmer_rgb), 1),
            "lightness_lstar": round(rgb_lightness_lstar(warmer_rgb), 1),
            "relationship": f"hue-shift-plus-{DEFAULT_BACKGROUND_SAME_HUE_MAX_DEGREES:.0f}deg",
        },
    ])

    return {
        "dominant_material_color": {
            "hex": rgb_hex(dominant_rgb),
            "hue_degrees": round(rgb_hue_degrees(dominant_rgb), 1),
            "lightness_lstar": round(dominant_lstar, 1),
            "reference_weight": round(dominant["reference_weight"], 8),
        },
        "constraints": {
            "minimum_lightness_delta_lstar": DEFAULT_BACKGROUND_MIN_LIGHTNESS_DELTA,
            "same_hue_max_difference_degrees": DEFAULT_BACKGROUND_SAME_HUE_MAX_DEGREES,
            "avoid_lightness_window_lstar": DEFAULT_BACKGROUND_AVOID_LIGHTNESS_WINDOW,
            "same_hue_rule": "when the background stays near the product hue family, make it clearly lighter or darker and noticeably less saturated",
            "collision_rule": "avoid placing the product against a backdrop whose dominant tone is too close to the product material color",
        },
        "preferred_background_colors": safe_entries,
        "forbidden_background_colors": avoid_entries,
    }


def distance_sq(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    return sum((a - b) ** 2 for a, b in zip(left, right))


def build_histogram(
    image: Image.Image,
    *,
    alpha_threshold: int,
    sampling_edge: int,
    exclusion_boxes: list[tuple[float, float, float, float]],
) -> tuple[list[dict], tuple[int, int], int, int]:
    sample = image.copy()
    sample.thumbnail((sampling_edge, sampling_edge), Image.Resampling.NEAREST)
    raw = sample.tobytes()
    bins: dict[tuple[int, int, int], list[int]] = {}
    visible_count = 0
    excluded_visible_count = 0

    for index in range(0, len(raw), 4):
        red, green, blue, alpha = raw[index:index + 4]
        if alpha < alpha_threshold:
            continue
        pixel_index = index // 4
        x = ((pixel_index % sample.width) + 0.5) / sample.width
        y = ((pixel_index // sample.width) + 0.5) / sample.height
        if point_in_any_box(x, y, exclusion_boxes):
            excluded_visible_count += 1
            continue
        key = (red >> 3, green >> 3, blue >> 3)
        record = bins.setdefault(key, [0, 0, 0, 0])
        record[0] += 1
        record[1] += red
        record[2] += green
        record[3] += blue
        visible_count += 1

    if visible_count == 0:
        if excluded_visible_count:
            raise ValueError("NO_VISIBLE_PRODUCT_PIXELS_AFTER_EXCLUSION")
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
    return rows, sample.size, visible_count, excluded_visible_count


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
    parser.add_argument(
        "--exclude-box",
        action="append",
        default=[],
        type=parse_normalized_box,
        metavar="X0,Y0,X1,Y1",
        help="normalized source-image rectangle to exclude from palette analysis; repeatable",
    )
    parser.add_argument(
        "--exclusion-margin",
        type=float,
        default=DEFAULT_EXCLUSION_MARGIN,
        help="expand each exclusion by this fraction of the visible product bounding box",
    )
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
        if not 0.0 <= args.exclusion_margin <= 0.10:
            raise ValueError("EXCLUSION_MARGIN_INVALID")
        if json_output.exists():
            raise ValueError(f"REFUSE_OVERWRITE: {json_output}")

        image = load_rgba(source)
        exclusion_boxes = expand_exclusion_boxes(
            image,
            args.exclude_box,
            alpha_threshold=args.alpha_threshold,
            margin=args.exclusion_margin,
        )
        rows, sampled_dimensions, visible_count, excluded_visible_count = build_histogram(
            image,
            alpha_threshold=args.alpha_threshold,
            sampling_edge=args.sampling_edge,
            exclusion_boxes=exclusion_boxes,
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
                "excluded_visible_sample_pixels": excluded_visible_count,
                "rgb_bin_bits_per_channel": 5,
            },
            "policy": {
                "requested_colors": args.colors,
                "dominant_slots": min(DEFAULT_DOMINANT_COLORS, args.colors),
                "dominant_min_rgb_distance": DEFAULT_DOMINANT_DISTANCE,
                "accent_min_rgb_distance": DEFAULT_ACCENT_DISTANCE,
                "minimum_accent_source_weight": DEFAULT_MIN_ACCENT_WEIGHT,
                "reference_weighting": "nearest-selected-color assignment over eligible visible bins",
                "material_color_scope": "visible product pixels excluding caller-supplied semantic display regions",
                "screen_exclusion": {
                    "coordinate_space": "source-normalized",
                    "boxes": [list(box) for box in args.exclude_box],
                    "expanded_boxes": [list(box) for box in exclusion_boxes],
                    "margin_product_bbox_fraction": args.exclusion_margin,
                },
            },
            "selected_source_coverage": round(selected_source_coverage, 8),
            "reference_weight_sum": round(sum(row["reference_weight"] for row in selected), 8),
            "colors": palette_colors,
        }
        payload["background_guidance"] = build_background_guidance(selected)

        render_reference(selected, reference_output)
        payload["reference_sha256"] = sha256_file(reference_output)
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
            "reference_sha256": payload["reference_sha256"],
            "color_count": len(palette_colors),
            "colors": palette_colors,
        }
        payload["background_guidance"] = build_background_guidance(selected)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
