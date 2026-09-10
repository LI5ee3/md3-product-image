#!/usr/bin/env python3
"""Create or verify deterministic material-palette assets for MASTER and SKU references."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import atomic_write, read_json, sha256_file


SCRIPTS_DIR = Path(__file__).resolve().parent
EXTRACTOR = SCRIPTS_DIR / "extract_palette.py"
REFERENCE_HASH_FIELD = "reference_sha256"
DEFAULT_EXCLUSION_MARGIN = 0.02
CURRENT_SKU_PALETTE_NAME = "current-sku-palette.json"



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


def exclusion_policy(
    boxes: list[tuple[float, float, float, float]],
    margin: float,
) -> dict:
    return {
        "coordinate_space": "source-normalized",
        "boxes": [list(box) for box in boxes],
        "margin_product_bbox_fraction": margin,
    }


def exclusion_policy_digest(policy: dict) -> str:
    encoded = json.dumps(policy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def payload_matches_exclusion_policy(payload: dict, requested: dict) -> bool:
    existing = payload.get("policy", {}).get("screen_exclusion")
    if existing is None:
        return not requested["boxes"]
    return (
        existing.get("coordinate_space") == requested["coordinate_space"]
        and existing.get("boxes") == requested["boxes"]
        and existing.get("margin_product_bbox_fraction")
        == requested["margin_product_bbox_fraction"]
    )


def run_extractor(
    source: Path,
    json_output: Path,
    reference_output: Path,
    *,
    exclude_boxes: list[tuple[float, float, float, float]],
    exclusion_margin: float,
) -> None:
    command = [
        sys.executable,
        str(EXTRACTOR),
        "--source",
        str(source),
        "--json-output",
        str(json_output),
        "--reference-output",
        str(reference_output),
        "--exclusion-margin",
        str(exclusion_margin),
    ]
    for box in exclude_boxes:
        command.extend(("--exclude-box", ",".join(f"{value:.8f}" for value in box)))
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(detail or "PALETTE_EXTRACTION_FAILED")


def output_paths(
    product_dir: Path,
    role: str,
    source_sha: str,
    policy_digest: str,
    has_exclusions: bool,
) -> tuple[Path, Path]:
    reusable = product_dir / "reusable"
    if role == "MASTER":
        return reusable / "palette.json", reusable / "palette-reference.png"
    palette_dir = reusable / "palettes"
    stem = f"{source_sha}-{policy_digest[:12]}" if has_exclusions else source_sha
    return palette_dir / f"{stem}.json", palette_dir / f"{stem}.png"


def migrate_legacy_cache(
    source: Path,
    json_path: Path,
    reference_path: Path,
    payload: dict,
    *,
    exclude_boxes: list[tuple[float, float, float, float]],
    exclusion_margin: float,
) -> None:
    with tempfile.TemporaryDirectory(prefix="md3-palette-legacy-verify-") as temporary:
        root = Path(temporary)
        expected_json = root / "palette.json"
        expected_reference = root / "palette-reference.png"
        run_extractor(
            source,
            expected_json,
            expected_reference,
            exclude_boxes=exclude_boxes,
            exclusion_margin=exclusion_margin,
        )
        expected_payload = read_json(expected_json)
        expected_reference_sha = expected_payload.get(REFERENCE_HASH_FIELD)
        if (
            not isinstance(expected_reference_sha, str)
            or expected_reference_sha != sha256_file(reference_path)
        ):
            raise ValueError("PALETTE_REFERENCE_HASH_MISMATCH")

    payload = dict(payload)
    payload[REFERENCE_HASH_FIELD] = expected_reference_sha
    atomic_write(json_path, payload)


def verify_existing(
    source: Path,
    json_path: Path,
    reference_path: Path,
    *,
    requested_policy: dict,
    exclude_boxes: list[tuple[float, float, float, float]],
    exclusion_margin: float,
) -> bool:
    if json_path.exists() != reference_path.exists():
        raise ValueError("PALETTE_CACHE_INCOMPLETE")
    if not json_path.exists():
        return False

    source_sha = sha256_file(source)
    payload = read_json(json_path)
    if payload.get("source_sha256") != source_sha:
        raise ValueError("PALETTE_SOURCE_MISMATCH")

    if not payload_matches_exclusion_policy(payload, requested_policy):
        return False

    expected_reference_sha = payload.get(REFERENCE_HASH_FIELD)
    if expected_reference_sha is None:
        migrate_legacy_cache(
            source,
            json_path,
            reference_path,
            payload,
            exclude_boxes=exclude_boxes,
            exclusion_margin=exclusion_margin,
        )
        return True
    if (
        not isinstance(expected_reference_sha, str)
        or expected_reference_sha != sha256_file(reference_path)
    ):
        raise ValueError("PALETTE_REFERENCE_HASH_MISMATCH")
    return True




def write_current_sku_pointer(
    product_dir: Path,
    *,
    source_sha: str,
    requested_policy: dict,
    json_path: Path,
    reference_path: Path,
) -> None:
    pointer_path = product_dir / "reusable" / CURRENT_SKU_PALETTE_NAME
    payload = {
        "source_sha256": source_sha,
        "screen_exclusion": requested_policy,
        "palette_json": str(json_path),
        "palette_reference": str(reference_path),
        "palette_json_sha256": sha256_file(json_path),
        "palette_reference_sha256": sha256_file(reference_path),
    }
    atomic_write(pointer_path, payload)

def replace_cache(source_json: Path, source_reference: Path, json_path: Path, reference_path: Path) -> None:
    json_tmp = json_path.with_name(f".{json_path.name}.tmp")
    reference_tmp = reference_path.with_name(f".{reference_path.name}.tmp")
    for path in (json_tmp, reference_tmp):
        if path.exists():
            path.unlink()
    try:
        shutil.copy2(source_json, json_tmp)
        shutil.copy2(source_reference, reference_tmp)
        reference_tmp.replace(reference_path)
        json_tmp.replace(json_path)
    finally:
        for path in (json_tmp, reference_tmp):
            if path.exists():
                path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--product-dir", required=True)
    parser.add_argument("--role", choices=("MASTER", "SKU"), required=True)
    parser.add_argument(
        "--exclude-box",
        action="append",
        default=[],
        type=parse_normalized_box,
        metavar="X0,Y0,X1,Y1",
        help="normalized display rectangle to exclude from palette analysis; repeatable",
    )
    parser.add_argument(
        "--exclusion-margin",
        type=float,
        default=DEFAULT_EXCLUSION_MARGIN,
    )
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    product_dir = Path(args.product_dir).expanduser().resolve()

    try:
        if not source.is_file():
            raise ValueError(f"SOURCE_FILE_MISSING: {source}")
        if not product_dir.is_dir():
            raise ValueError(f"PRODUCT_DIRECTORY_MISSING: {product_dir}")
        if not 0.0 <= args.exclusion_margin <= 0.10:
            raise ValueError("EXCLUSION_MARGIN_INVALID")
        reusable = product_dir / "reusable"
        if not reusable.is_dir():
            raise ValueError(f"REUSABLE_DIRECTORY_MISSING: {reusable}")

        source_sha = sha256_file(source)
        requested_policy = exclusion_policy(args.exclude_box, args.exclusion_margin)
        policy_digest = exclusion_policy_digest(requested_policy)
        json_path, reference_path = output_paths(
            product_dir,
            args.role,
            source_sha,
            policy_digest,
            bool(args.exclude_box),
        )
        json_path.parent.mkdir(parents=True, exist_ok=True)

        verified = verify_existing(
            source,
            json_path,
            reference_path,
            requested_policy=requested_policy,
            exclude_boxes=args.exclude_box,
            exclusion_margin=args.exclusion_margin,
        )
        created = not json_path.exists()
        refreshed = json_path.exists() and not verified
        if not verified:
            with tempfile.TemporaryDirectory(prefix="md3-palette-create-") as temporary:
                root = Path(temporary)
                temporary_json = root / "palette.json"
                temporary_reference = root / "palette-reference.png"
                run_extractor(
                    source,
                    temporary_json,
                    temporary_reference,
                    exclude_boxes=args.exclude_box,
                    exclusion_margin=args.exclusion_margin,
                )
                payload = read_json(temporary_json)
                if payload.get("source_sha256") != source_sha:
                    raise ValueError("PALETTE_SOURCE_MISMATCH")
                if payload.get(REFERENCE_HASH_FIELD) != sha256_file(temporary_reference):
                    raise ValueError("PALETTE_REFERENCE_HASH_MISMATCH")
                replace_cache(
                    temporary_json,
                    temporary_reference,
                    json_path,
                    reference_path,
                )

        if args.role == "SKU":
            write_current_sku_pointer(
                product_dir,
                source_sha=source_sha,
                requested_policy=requested_policy,
                json_path=json_path,
                reference_path=reference_path,
            )

        report = {
            "role": args.role,
            "source_sha256": source_sha,
            "created": created,
            "refreshed_for_policy": refreshed,
            "screen_exclusion": requested_policy,
            "palette_json": str(json_path),
            "palette_reference": str(reference_path),
            "palette_json_sha256": sha256_file(json_path),
            "palette_reference_sha256": sha256_file(reference_path),
        }
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
