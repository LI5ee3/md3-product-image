#!/usr/bin/env python3
"""Validate generated background raster dimensions for MASTER and SKU flows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image



def inspect_raster(path_arg: str, label: str) -> dict:
    path = Path(path_arg).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"{label}_MISSING: {path}")
    try:
        with Image.open(path) as source:
            source.load()
            width, height = source.size
            image_format = source.format
            mode = source.mode
    except OSError as exc:
        raise ValueError(f"{label}_UNREADABLE: {exc}") from exc

    if width <= 0 or height <= 0:
        raise ValueError(f"{label}_SIZE_INVALID: got {width}x{height}")
    if width * 4 != height * 3:
        raise ValueError(f"{label}_NOT_3_4: got {width}x{height}")

    return {
        "path": str(path),
        "width": width,
        "height": height,
        "ratio": "3:4",
        "format": image_format,
        "mode": mode,
    }


def validate_master(args: argparse.Namespace) -> dict:
    raster = inspect_raster(args.generated_background, "MASTER_BACKGROUND")
    return {
        "status": "MASTER_RASTER_VALID",
        "raster": raster,
    }


def validate_sku(args: argparse.Namespace) -> dict:
    master = inspect_raster(args.master_background, "MASTER_BACKGROUND")
    sku = inspect_raster(args.generated_background, "SKU_BACKGROUND")
    if (master["width"], master["height"]) != (sku["width"], sku["height"]):
        raise ValueError(
            "SKU_BACKGROUND_SIZE_MISMATCH: "
            f"master {master['width']}x{master['height']}, "
            f"got {sku['width']}x{sku['height']}"
        )
    return {
        "status": "SKU_RASTER_VALID",
        "master_raster": master,
        "sku_raster": sku,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    master = subparsers.add_parser("master")
    master.add_argument("--generated-background", required=True)
    master.set_defaults(handler=validate_master)

    sku = subparsers.add_parser("sku")
    sku.add_argument("--master-background", required=True)
    sku.add_argument("--generated-background", required=True)
    sku.set_defaults(handler=validate_sku)

    args = parser.parse_args()
    try:
        result = args.handler(args)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
