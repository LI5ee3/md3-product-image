#!/usr/bin/env python3
"""Create or verify deterministic palette assets for MASTER and SKU references."""

from __future__ import annotations

import argparse
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


def run_extractor(source: Path, json_output: Path, reference_output: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(EXTRACTOR),
            "--source",
            str(source),
            "--json-output",
            str(json_output),
            "--reference-output",
            str(reference_output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(detail or "PALETTE_EXTRACTION_FAILED")


def output_paths(product_dir: Path, role: str, source_sha: str) -> tuple[Path, Path]:
    reusable = product_dir / "reusable"
    if role == "MASTER":
        return reusable / "palette.json", reusable / "palette-reference.png"
    palette_dir = reusable / "palettes"
    return palette_dir / f"{source_sha}.json", palette_dir / f"{source_sha}.png"


def migrate_legacy_cache(
    source: Path,
    json_path: Path,
    reference_path: Path,
    payload: dict,
) -> None:
    with tempfile.TemporaryDirectory(prefix="md3-palette-legacy-verify-") as temporary:
        root = Path(temporary)
        expected_json = root / "palette.json"
        expected_reference = root / "palette-reference.png"
        run_extractor(source, expected_json, expected_reference)
        expected_payload = read_json(expected_json)
        expected_reference_sha = expected_payload.pop(REFERENCE_HASH_FIELD, None)
        if expected_payload != payload:
            raise ValueError("PALETTE_JSON_HASH_MISMATCH")
        if (
            not isinstance(expected_reference_sha, str)
            or expected_reference_sha != sha256_file(reference_path)
        ):
            raise ValueError("PALETTE_REFERENCE_HASH_MISMATCH")

    payload = dict(payload)
    payload[REFERENCE_HASH_FIELD] = expected_reference_sha
    atomic_write(json_path, payload)


def verify_existing(source: Path, json_path: Path, reference_path: Path) -> None:
    if json_path.exists() != reference_path.exists():
        raise ValueError("PALETTE_CACHE_INCOMPLETE")
    if not json_path.exists():
        return

    source_sha = sha256_file(source)
    payload = read_json(json_path)
    if payload.get("source_sha256") != source_sha:
        raise ValueError("PALETTE_SOURCE_MISMATCH")

    expected_reference_sha = payload.get(REFERENCE_HASH_FIELD)
    if expected_reference_sha is None:
        migrate_legacy_cache(source, json_path, reference_path, payload)
        return
    if (
        not isinstance(expected_reference_sha, str)
        or expected_reference_sha != sha256_file(reference_path)
    ):
        raise ValueError("PALETTE_REFERENCE_HASH_MISMATCH")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--product-dir", required=True)
    parser.add_argument("--role", choices=("MASTER", "SKU"), required=True)
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    product_dir = Path(args.product_dir).expanduser().resolve()

    try:
        if not source.is_file():
            raise ValueError(f"SOURCE_FILE_MISSING: {source}")
        if not product_dir.is_dir():
            raise ValueError(f"PRODUCT_DIRECTORY_MISSING: {product_dir}")
        reusable = product_dir / "reusable"
        if not reusable.is_dir():
            raise ValueError(f"REUSABLE_DIRECTORY_MISSING: {reusable}")

        source_sha = sha256_file(source)
        json_path, reference_path = output_paths(product_dir, args.role, source_sha)
        json_path.parent.mkdir(parents=True, exist_ok=True)

        verify_existing(source, json_path, reference_path)
        created = False
        if not json_path.exists():
            with tempfile.TemporaryDirectory(prefix="md3-palette-create-") as temporary:
                root = Path(temporary)
                temporary_json = root / "palette.json"
                temporary_reference = root / "palette-reference.png"
                run_extractor(source, temporary_json, temporary_reference)
                payload = read_json(temporary_json)
                if payload.get("source_sha256") != source_sha:
                    raise ValueError("PALETTE_SOURCE_MISMATCH")
                if payload.get(REFERENCE_HASH_FIELD) != sha256_file(temporary_reference):
                    raise ValueError("PALETTE_REFERENCE_HASH_MISMATCH")
                shutil.copy2(temporary_json, json_path)
                shutil.copy2(temporary_reference, reference_path)
            created = True

        report = {
            "role": args.role,
            "source_sha256": source_sha,
            "created": created,
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
