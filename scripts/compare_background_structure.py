#!/usr/bin/env python3
"""Compare background geometry using palette-tolerant edge metrics.

This is a diagnostic metric for visual ablation, not an automatic aesthetic gate.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


MAX_EDGE = 512
EDGE_PERCENTILE = 0.85


def load_edge_values(path: Path) -> tuple[list[int], tuple[int, int]]:
    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
            gray = image.convert("L").filter(ImageFilter.GaussianBlur(radius=1.5))
            edges = gray.filter(ImageFilter.FIND_EDGES)
            if edges.width > 4 and edges.height > 4:
                edges = edges.crop((2, 2, edges.width - 2, edges.height - 2))
            edges = ImageOps.autocontrast(edges)
            return list(edges.getdata()), edges.size
    except OSError as exc:
        raise ValueError(f"RASTER_UNREADABLE: {path}: {exc}") from exc


def pearson(left: list[int], right: list[int]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("EDGE_VECTOR_MISMATCH")
    count = len(left)
    mean_left = sum(left) / count
    mean_right = sum(right) / count
    numerator = 0.0
    left_power = 0.0
    right_power = 0.0
    for a, b in zip(left, right):
        da = a - mean_left
        db = b - mean_right
        numerator += da * db
        left_power += da * da
        right_power += db * db
    denominator = math.sqrt(left_power * right_power)
    if denominator == 0:
        return 1.0 if left == right else 0.0
    return numerator / denominator


def percentile_threshold(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def edge_jaccard(left: list[int], right: list[int]) -> float:
    left_threshold = percentile_threshold(left, EDGE_PERCENTILE)
    right_threshold = percentile_threshold(right, EDGE_PERCENTILE)
    intersection = 0
    union = 0
    for a, b in zip(left, right):
        left_edge = a >= left_threshold and a > 0
        right_edge = b >= right_threshold and b > 0
        if left_edge or right_edge:
            union += 1
            if left_edge and right_edge:
                intersection += 1
    return 1.0 if union == 0 else intersection / union


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()

    master = Path(args.master).expanduser().resolve()
    candidate = Path(args.candidate).expanduser().resolve()

    try:
        with Image.open(master) as master_image, Image.open(candidate) as candidate_image:
            master_image.load()
            candidate_image.load()
            master_size = master_image.size
            candidate_size = candidate_image.size
        if master_size != candidate_size:
            raise ValueError(
                "BACKGROUND_RASTER_MISMATCH: "
                f"master={master_size[0]}x{master_size[1]} "
                f"candidate={candidate_size[0]}x{candidate_size[1]}"
            )

        left, left_size = load_edge_values(master)
        right, right_size = load_edge_values(candidate)
        if left_size != right_size:
            raise ValueError("EDGE_RASTER_MISMATCH")

        correlation = pearson(left, right)
        jaccard = edge_jaccard(left, right)
        mae = sum(abs(a - b) for a, b in zip(left, right)) / (len(left) * 255)

        report = {
            "master": str(master),
            "candidate": str(candidate),
            "raster": {"width": master_size[0], "height": master_size[1]},
            "analysis_raster": {"width": left_size[0], "height": left_size[1]},
            "edge_correlation": round(correlation, 6),
            "edge_jaccard_top15pct": round(jaccard, 6),
            "edge_mae_normalized": round(mae, 6),
            "automatic_acceptance": False,
            "note": "Diagnostic structure metrics only; visual acceptance remains manual.",
        }
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
