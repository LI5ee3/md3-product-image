#!/usr/bin/env python3
"""Prepare one reusable information-group layout for md3-product-image."""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import atomic_write, sha256_file

FONT_DEFAULT = Path(__file__).resolve().parent.parent / "assets" / "Rubik[wght].ttf"
FONT_WEIGHT_DEFAULT = 700


def load_font(
    font_path: Path, size: int, weight: int
) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(font_path), size)
    try:
        axes = font.get_variation_axes()
    except OSError:
        axes = []
    if axes:
        if len(axes) != 1:
            raise ValueError(
                f"FONT_VARIATION_UNSUPPORTED: expected one axis, found {len(axes)}"
            )
        axis = axes[0]
        minimum = int(axis["minimum"])
        maximum = int(axis["maximum"])
        if not minimum <= weight <= maximum:
            raise ValueError(
                f"FONT_WEIGHT_OUT_OF_RANGE: {weight} not in {minimum}..{maximum}"
            )
        font.set_variation_by_axes([weight])
    return font


def mask_signature(font: ImageFont.FreeTypeFont, text: str) -> tuple:
    mask = font.getmask(text, mode="L")
    return mask.size, mask.getbbox(), bytes(mask)


def check_glyph_coverage(font_path: Path, weight: int, *texts: str) -> None:
    """Reject characters rendered as the font's missing-glyph box."""
    font = load_font(font_path, 96, weight)
    missing = mask_signature(font, "\U0010ffff")
    absent = sorted(
        {
            ch
            for text in texts
            for ch in text
            if not ch.isspace() and mask_signature(font, ch) == missing
        }
    )
    if absent:
        raise ValueError(
            f"GLYPH_MISSING: {font_path} cannot render: {''.join(absent)}"
        )


def render_text_mask(font: ImageFont.FreeTypeFont, text: str) -> Image.Image:
    bbox = font.getbbox(text)
    width = max(1, bbox[2] - bbox[0])
    height = max(1, bbox[3] - bbox[1])
    probe = Image.new("L", (width + 16, height + 16), 0)
    ImageDraw.Draw(probe).text(
        (8 - bbox[0], 8 - bbox[1]), text, font=font, fill=255
    )
    ink = probe.getbbox()
    if ink is None:
        raise ValueError(f"TEXT_EMPTY: {text!r} has no visible glyphs")
    return probe.crop(ink)


def font_for_lines_height(
    font_path: Path, lines: list[str], target_height: int, weight: int
) -> ImageFont.FreeTypeFont:
    lo, hi = 1, max(16, target_height * 4)
    candidates: list[tuple[int, int, ImageFont.FreeTypeFont]] = []
    while lo <= hi:
        size = (lo + hi) // 2
        font = load_font(font_path, size, weight)
        height = max(render_text_mask(font, line).height for line in lines)
        candidates.append((abs(height - target_height), size, font))
        if height < target_height:
            lo = size + 1
        elif height > target_height:
            hi = size - 1
        else:
            hi = size - 1
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def image_metadata(image_path: Path) -> dict:
    try:
        with Image.open(image_path) as source:
            source.load()
            width, height = source.size
            mode = source.mode
            image_format = source.format
            rgba = source.convert("RGBA")
    except OSError as exc:
        raise ValueError(f"PRODUCT_REFERENCE_UNREADABLE: {exc}") from exc
    visible_bbox = rgba.getchannel("A").point(
        lambda value: 255 if value >= 224 else 0
    ).getbbox() or (0, 0, width, height)
    return {
        "path": str(image_path),
        "sha256": sha256_file(image_path),
        "width": width,
        "height": height,
        "mode": mode,
        "format": image_format,
        "ratio_exact_3_4": width * 4 == height * 3,
        "visible_bbox": {
            "left": visible_bbox[0],
            "top": visible_bbox[1],
            "right": visible_bbox[2],
            "bottom": visible_bbox[3],
        },
    }


def visible_logo(logo_path: Path) -> tuple[Image.Image, dict]:
    try:
        with Image.open(logo_path) as source:
            source.load()
            source_width, source_height = source.size
            source_mode = source.mode
            source_format = source.format
            logo = source.convert("RGBA")
    except OSError as exc:
        raise ValueError(f"LOGO_UNREADABLE: {exc}") from exc
    bbox = logo.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"LOGO_EMPTY: no visible artwork in {logo_path}")
    cropped = logo.crop(bbox)
    return cropped, {
        "source_path": str(logo_path),
        "sha256": sha256_file(logo_path),
        "source_width": source_width,
        "source_height": source_height,
        "source_mode": source_mode,
        "source_format": source_format,
        "visible_bbox": {
            "left": bbox[0],
            "top": bbox[1],
            "right": bbox[2],
            "bottom": bbox[3],
        },
        "cropped_width": cropped.width,
        "cropped_height": cropped.height,
        "cropped_asset": "logo.png",
    }


def resolve_product_directory(output_root: Path, complete_name: str) -> Path:
    if (
        not complete_name
        or complete_name in {".", ".."}
        or "/" in complete_name
        or "\x00" in complete_name
    ):
        raise ValueError(
            "PRODUCT_FOLDER_NAME_INVALID: complete name must be one exact folder name"
        )
    root = output_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / complete_name
    candidate.mkdir(exist_ok=True)
    product_dir = candidate.resolve()
    if product_dir.parent != root or product_dir.name != complete_name:
        raise ValueError("PRODUCT_FOLDER_OUTSIDE_ROOT")
    (product_dir / "output").mkdir(exist_ok=True)
    return product_dir


@dataclass
class LayoutOptions:
    title_height_frac: float = 0.045
    version_height_frac: float = 0.0285
    logo_height_frac: float = 0.073
    logo_width_cap_frac: float = 0.30
    left_margin_frac: float = 0.05
    top_margin_frac: float = 0.05
    title_top_frac: float = 0.18
    title_version_gap_frac: float = 0.025
    clearance_w_frac: float = 0.02
    clearance_h_frac: float = 0.015
    max_title_width_frac: float = 0.90
    line_gap_factor: float = 0.45
    font_path: Path = field(default_factory=lambda: FONT_DEFAULT)
    font_weight: int = FONT_WEIGHT_DEFAULT


def resolve_title_lines(
    title_line_1: str,
    title_line_2: str | None,
    title_line_count: int,
    canvas_width: int,
    canvas_height: int,
    opts: LayoutOptions,
) -> tuple[str, list[str], ImageFont.FreeTypeFont]:
    if title_line_count == 1:
        if title_line_2 is not None:
            raise ValueError("TITLE_LINE_2_UNEXPECTED: omit it for a one-line title")
        lines = [title_line_1]
    else:
        lines = [title_line_1, title_line_2]

    if any(not line for line in lines):
        raise ValueError("TITLE_LINE_COUNT_MISMATCH")

    rendered_title = "\n".join(lines)
    target_height = round(opts.title_height_frac * canvas_height)
    title_font = font_for_lines_height(
        opts.font_path, lines, target_height, opts.font_weight
    )
    if any(
        render_text_mask(title_font, line).width
        > opts.max_title_width_frac * canvas_width
        for line in lines
    ):
        raise ValueError("TITLE_LINE_OVERFLOW: user-selected line count does not fit")
    return rendered_title, lines, title_font


def normalized_rect(rect: tuple[float, float, float, float], width: int, height: int) -> dict:
    left, top, right, bottom = rect
    return {
        "x": round(left / width, 6),
        "y": round(top / height, 6),
        "w": round((right - left) / width, 6),
        "h": round((bottom - top) / height, 6),
    }


def clear_zones(
    labeled_rects: list[tuple[str, tuple[float, float, float, float]]],
    width: int,
    height: int,
    opts: LayoutOptions,
) -> list[dict]:
    pad_w = opts.clearance_w_frac * width
    pad_h = opts.clearance_h_frac * height
    padded = [
        (
            label,
            (rect[0] - pad_w, rect[1] - pad_h, rect[2] + pad_w, rect[3] + pad_h),
        )
        for label, rect in labeled_rects
    ]
    zones = []
    for label, rect in padded:
        zones.append({"label": label, **normalized_rect(rect, width, height)})
    for (_, upper), (_, lower) in zip(padded, padded[1:]):
        left = max(upper[0], lower[0])
        right = min(upper[2], lower[2])
        top, bottom = upper[3], lower[1]
        if bottom > top and right > left:
            zones.append(
                {
                    "label": "CONNECTOR",
                    **normalized_rect((left, top, right, bottom), width, height),
                }
            )
    for zone in zones:
        if (
            zone["x"] < 0
            or zone["y"] < 0
            or zone["x"] + zone["w"] > 1
            or zone["y"] + zone["h"] > 1
        ):
            raise ValueError(f"CLEAR_ZONE_OUT_OF_CANVAS: {zone['label']}")
    return zones


def prepare_layout(args: argparse.Namespace) -> dict:
    opts = LayoutOptions(
        font_path=Path(args.font_path), font_weight=args.font_weight
    )
    if not opts.font_path.is_file():
        raise FileNotFoundError(f"FONT_UNAVAILABLE: {opts.font_path}")
    if args.canvas_height <= 0 or args.canvas_height % 4:
        raise ValueError("CANVAS_HEIGHT_INVALID: use a positive multiple of 4")

    width, height = args.canvas_height * 3 // 4, args.canvas_height
    check_glyph_coverage(
        opts.font_path,
        opts.font_weight,
        args.title_line_1,
        args.title_line_2 or "",
        args.version or "",
    )
    rendered_title, title_lines, title_font = resolve_title_lines(
        args.title_line_1,
        args.title_line_2,
        args.title_lines,
        width,
        height,
        opts,
    )

    product_reference = Path(args.product_reference).expanduser().resolve()
    logo_path = Path(args.logo).expanduser().resolve()
    product_metadata = image_metadata(product_reference)
    product_dir = resolve_product_directory(Path(args.output_root), args.complete_name)
    reusable_dir = product_dir / "reusable"
    reusable_dir.mkdir(exist_ok=True)
    layout_path = reusable_dir / "layout.json"
    if layout_path.exists():
        raise ValueError(f"REFUSE_REMEASURE: reuse existing {layout_path}")
    logo_art, logo_metadata = visible_logo(logo_path)
    logo_art.save(reusable_dir / "logo.png")

    x0 = opts.left_margin_frac * width
    logo_height = opts.logo_height_frac * height
    logo_width = logo_art.width * logo_height / logo_art.height
    if logo_width > opts.logo_width_cap_frac * width:
        scale = opts.logo_width_cap_frac * width / logo_width
        logo_width *= scale
        logo_height *= scale
    logo_rect = (
        x0,
        opts.top_margin_frac * height,
        x0 + logo_width,
        opts.top_margin_frac * height + logo_height,
    )

    title_masks = [render_text_mask(title_font, line) for line in title_lines]
    title_top = max(opts.title_top_frac * height, logo_rect[3] + 0.02 * height)
    title_rects = []
    for index, (line, mask) in enumerate(zip(title_lines, title_masks), start=1):
        mask_path = reusable_dir / f"title-{index}-mask.png"
        mask.save(mask_path)
        rect = (x0, title_top, x0 + mask.width, title_top + mask.height)
        title_rects.append((line, rect, mask_path.name))
        title_top += mask.height * (1 + opts.line_gap_factor)

    version_rect = None
    version_asset = None
    version_font_size = None
    if args.version:
        version_font = font_for_lines_height(
            opts.font_path,
            [args.version],
            round(opts.version_height_frac * height),
            opts.font_weight,
        )
        version_mask = render_text_mask(version_font, args.version)
        version_asset = "version-mask.png"
        version_mask.save(reusable_dir / version_asset)
        gap = opts.title_version_gap_frac * height
        top = title_rects[-1][1][3] + gap
        version_rect = (x0, top, x0 + version_mask.width, top + version_mask.height)
        version_font_size = version_font.size

    labeled_rects = [("LOGO_RECT", logo_rect)]
    labeled_rects.extend(
        (f"TITLE_LINE_RECT_{index}", rect)
        for index, (_, rect, _) in enumerate(title_rects, start=1)
    )
    if version_rect:
        labeled_rects.append(("VERSION_TEXT_RECT", version_rect))

    elements = {
        "LOGO_RECT": {**normalized_rect(logo_rect, width, height), "asset": "logo.png"},
        "TITLE_LINE_RECT": [
            {
                "line": line,
                **normalized_rect(rect, width, height),
                "asset": asset,
            }
            for line, rect, asset in title_rects
        ],
        "TITLE_FONT_SIZE": title_font.size,
    }
    if version_rect:
        elements["VERSION_TEXT_RECT"] = {
            "text": args.version,
            **normalized_rect(version_rect, width, height),
            "asset": version_asset,
        }
        elements["VERSION_FONT_SIZE"] = version_font_size

    information_assets = {
        "logo": {
            "path": "logo.png",
            "sha256": sha256_file(reusable_dir / "logo.png"),
        }
    }
    for index, (_, _, asset) in enumerate(title_rects, start=1):
        information_assets[f"title_{index}"] = {
            "path": asset,
            "sha256": sha256_file(reusable_dir / asset),
        }
    if version_asset:
        information_assets["version"] = {
            "path": version_asset,
            "sha256": sha256_file(reusable_dir / version_asset),
        }

    report = {
        "product_directory": str(product_dir),
        "canvas": {
            "width": width,
            "height": height,
            "ratio": "3:4",
            "purpose": "logical layout only",
        },
        "font": {
            "path": str(opts.font_path),
            "name": "Rubik Variable",
            "weight": opts.font_weight,
        },
        "product_reference": product_metadata,
        "logo": logo_metadata,
        "title_line_count": args.title_lines,
        "complete_name": args.complete_name,
        "rendered_title": rendered_title,
        "title_lines": title_lines,
        "version": args.version,
        "elements": elements,
        "information_assets": information_assets,
        "clear_zones": clear_zones(labeled_rects, width, height, opts),
    }
    atomic_write(layout_path, report, new=True)
    atomic_write(
        product_dir / "scene-attempts.json",
        {"schema": 1, "next_run": 1, "active_run_id": None, "runs": []},
        new=True,
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complete-name", required=True)
    parser.add_argument("--title-lines", required=True, type=int, choices=(1, 2))
    parser.add_argument("--title-line-1", required=True)
    parser.add_argument("--title-line-2")
    parser.add_argument("--version", default=None)
    parser.add_argument("--product-reference", required=True)
    parser.add_argument("--logo", required=True)
    parser.add_argument(
        "--output-root",
        required=True,
        help="parent directory; the exact complete product name is appended automatically",
    )
    parser.add_argument("--canvas-height", type=int, default=2048)
    parser.add_argument("--font-path", default=str(FONT_DEFAULT))
    parser.add_argument("--font-weight", type=int, default=FONT_WEIGHT_DEFAULT)
    args = parser.parse_args()

    try:
        report = prepare_layout(args)
    except (FileNotFoundError, ValueError) as exc:
        sys.exit(str(exc))
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
