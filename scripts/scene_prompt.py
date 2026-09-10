#!/usr/bin/env python3
"""Build one prompt at a time and record explicit user decisions."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from common import atomic_write, read_json, verify_information_assets, verify_master


SKILL_DIR = Path(__file__).resolve().parent.parent
IMAGE_PROMPT_REFERENCE = SKILL_DIR / "references" / "image-gen-prompt.md"
VARIANT_REFERENCE = SKILL_DIR / "references" / "replace-variant-block.md"
ATTEMPT_STATE_NAME = "scene-attempts.json"
PROMPT_ADDITIONS_NAME = "prompt-additions.json"
SKU_TARGET_PATTERN = re.compile(r"SKU_VARIANT-([A-Z]+)")
FINAL_SAFE_ZONE_MARGIN = 0.05
PRODUCT_AREA_POLICY = """Product and shadow placement policy:
FINAL_INFORMATION_SAFE_ZONE is the only area that must be empty.
Do not create or interpret any product or shadow area as another empty or unobstructed safe zone, including any previous temporary correction that requested one.
Simple, low-detail MD3 cards and their restrained elevation shadows may appear behind the future local product and may receive its local cast shadow.
Avoid only dominant high-contrast edges or dense detail that visibly competes with the product after local compositing."""


def fenced_block(path: Path, heading: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"REFERENCE_UNREADABLE: {path}: {exc}") from exc
    match = re.search(
        rf"^#{{1,6}} {re.escape(heading)}\s*$.*?^```text\s*$\n(.*?)^```\s*$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError(f"REFERENCE_BLOCK_MISSING: {heading}")
    return match.group(1).rstrip()


def image_prompt() -> str:
    try:
        prompt = IMAGE_PROMPT_REFERENCE.read_text(encoding="utf-8").rstrip("\n")
    except OSError as exc:
        raise ValueError(
            f"REFERENCE_UNREADABLE: {IMAGE_PROMPT_REFERENCE}: {exc}"
        ) from exc
    if not prompt:
        raise ValueError("IMAGE_PROMPT_EMPTY")
    return prompt


def information_safe_zone_block(layout: dict) -> str:
    zones = layout.get("clear_zones")
    selected = [
        zone
        for zone in zones or []
        if zone.get("label") == "LOGO_RECT"
        or str(zone.get("label", "")).startswith("TITLE_LINE_RECT_")
        or zone.get("label") == "VERSION_TEXT_RECT"
    ]
    if not selected:
        raise ValueError("INFORMATION_SAFE_ZONES_MISSING")

    bounds = []
    for zone in selected:
        try:
            x0 = float(zone["x"])
            y0 = float(zone["y"])
            x1 = x0 + float(zone["w"])
            y1 = y0 + float(zone["h"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("INFORMATION_SAFE_ZONE_INVALID") from exc
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise ValueError("INFORMATION_SAFE_ZONE_OUT_OF_CANVAS")
        bounds.append((x0, y0, x1, y1))

    x0 = max(0, min(bound[0] for bound in bounds) - FINAL_SAFE_ZONE_MARGIN)
    y0 = max(0, min(bound[1] for bound in bounds) - FINAL_SAFE_ZONE_MARGIN)
    x1 = min(1, max(bound[2] for bound in bounds) + FINAL_SAFE_ZONE_MARGIN)
    y1 = min(1, max(bound[3] for bound in bounds) + FINAL_SAFE_ZONE_MARGIN)
    return "\n".join(
        (
            "Layout-only final information safe zone:",
            'Interpret any earlier "top-left negative space" instruction only as this one merged rectangle.',
            "This rectangle merges the measured Logo, title-line, and optional version safe zones, then expands the union by 5.0% of the canvas on every side, clipped to the canvas:",
            f"- FINAL_INFORMATION_SAFE_ZONE: x {x0 * 100:.1f}%-{x1 * 100:.1f}%, y {y0 * 100:.1f}%-{y1 * 100:.1f}%",
            "Keep the entire rectangle clear, calm, smooth, and empty, free of card edges, strong shadows, texture changes, or detailed geometry.",
        )
    )


def load_layout(path: Path) -> tuple[dict, Path]:
    layout_path = path.expanduser().resolve()
    if layout_path.name != "layout.json":
        raise ValueError("LAYOUT_PATH_INVALID")
    layout = read_json(layout_path)
    reusable_dir = layout_path.parent
    if reusable_dir.name != "reusable":
        raise ValueError("LAYOUT_PATH_INVALID: expected <product>/reusable/layout.json")
    product_dir = reusable_dir.parent
    if layout.get("product_directory") != str(product_dir):
        raise ValueError("PRODUCT_DIRECTORY_MISMATCH")
    verify_information_assets(layout, reusable_dir)
    zones = layout.get("clear_zones")
    if not isinstance(zones, list) or not zones:
        raise ValueError("CLEAR_ZONES_MISSING")
    return layout, product_dir


def additions_from(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = read_json(path)
    if not isinstance(data, list) or not all(
        isinstance(entry, str) and entry.strip() for entry in data
    ):
        raise ValueError("PROMPT_ADDITIONS_INVALID")
    return [entry.strip() for entry in data]


def additions_block(entries: list[str]) -> str | None:
    if not entries:
        return None
    lines = ["User-requested prompt additions accumulated for this product:"]
    lines.extend(f"{index}. {entry}" for index, entry in enumerate(entries, 1))
    return "\n".join(lines)


def attempt_state_path(product_dir: Path) -> Path:
    return product_dir / ATTEMPT_STATE_NAME


def new_attempt_state() -> dict:
    return {"schema": 1, "next_run": 1, "active_run_id": None, "runs": []}


def load_attempt_state(product_dir: Path) -> dict:
    path = attempt_state_path(product_dir)
    if not path.exists():
        return new_attempt_state()
    state = read_json(path)
    if (
        not isinstance(state, dict)
        or state.get("schema") != 1
        or not isinstance(state.get("runs"), list)
    ):
        raise ValueError("ATTEMPT_STATE_INVALID")
    return state


def active_run(state: dict) -> dict | None:
    run_id = state.get("active_run_id")
    if run_id is None:
        return None
    for run in state["runs"]:
        if isinstance(run, dict) and run.get("run_id") == run_id:
            return run
    raise ValueError("ACTIVE_ATTEMPT_RUN_MISSING")


def start_run(state: dict, mode: str, target: str) -> dict:
    run_number = int(state.get("next_run", len(state["runs"]) + 1))
    run = {
        "run_id": f"{mode}-RUN-{run_number}",
        "mode": mode,
        "target": target,
        "status": "ACTIVE",
        "attempts": [],
    }
    state["runs"].append(run)
    state["next_run"] = run_number + 1
    state["active_run_id"] = run["run_id"]
    return run


def prepare_run(state: dict, mode: str, target: str) -> dict:
    run = active_run(state)
    if run is None:
        return start_run(state, mode, target)
    if run.get("mode") != mode or run.get("target") != target:
        raise ValueError(
            "NEW_CANDIDATE_REQUIRED: active scene is "
            f"{run.get('mode')}/{run.get('target')}"
        )
    attempts = run.get("attempts")
    if not isinstance(attempts, list):
        raise ValueError("ATTEMPT_STATE_INVALID")
    if run.get("status") != "ACTIVE":
        raise ValueError("NEW_CANDIDATE_REQUIRED: active scene is closed")
    if attempts and attempts[-1].get("status") == "PENDING":
        raise ValueError("USER_DECISION_REQUIRED: accept or reject the current preview")
    return run


def prompt_file_path(
    product_dir: Path, mode: str, target: str, run: dict, attempt: int
) -> Path:
    target_hash = hashlib.sha256(target.encode("utf-8")).hexdigest()[:10]
    return product_dir / (
        f"scene-prompt-{mode.lower()}-{target_hash}-"
        f"run-{run['run_id'].rsplit('-', 1)[-1]}-attempt-{attempt}.md"
    )


def validate_target(value: str) -> str:
    value = value.strip()
    if not value or value in {".", ".."} or any(char in value for char in "/\\\x00"):
        raise ValueError("TARGET_INVALID")
    return value


def sku_letters(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def next_sku_target(product_dir: Path) -> str:
    existing = {
        match.group(1)
        for path in (product_dir / "output").glob("SKU_VARIANT-*.png")
        if (match := SKU_TARGET_PATTERN.fullmatch(path.stem))
    }
    number = 1
    while sku_letters(number) in existing:
        number += 1
    return f"SKU_VARIANT-{sku_letters(number)}"


def resolve_target(args: argparse.Namespace, state: dict, product_dir: Path) -> str:
    if args.mode == "MASTER":
        if not args.target:
            raise ValueError("TARGET_REQUIRED")
        return validate_target(args.target)
    if args.target:
        target = validate_target(args.target)
        if not args.redo or not SKU_TARGET_PATTERN.fullmatch(target):
            raise ValueError("SKU_TARGET_IS_AUTOMATIC")
        if not (product_dir / "output" / f"{target}.png").is_file():
            raise ValueError("SKU_REDO_TARGET_MISSING")
        return target
    if args.redo:
        existing = sorted(
            (
                path.stem
                for path in (product_dir / "output").glob("SKU_VARIANT-*.png")
                if SKU_TARGET_PATTERN.fullmatch(path.stem)
            ),
            key=lambda label: (len(SKU_TARGET_PATTERN.fullmatch(label).group(1)), label),
        )
        if not existing:
            raise ValueError("SKU_REDO_TARGET_MISSING")
        return existing[-1]
    run = active_run(state)
    if run and run.get("mode") == "SKU" and run.get("status") == "ACTIVE":
        return validate_target(run.get("target", ""))
    return next_sku_target(product_dir)


def resolve_active_target(args: argparse.Namespace, state: dict) -> str:
    if args.mode == "MASTER":
        if not args.target:
            raise ValueError("TARGET_REQUIRED")
        return validate_target(args.target)
    if args.target:
        raise ValueError("SKU_TARGET_IS_AUTOMATIC")
    run = active_run(state)
    if not run or run.get("mode") != "SKU":
        raise ValueError("ACTIVE_SKU_RUN_MISSING")
    return validate_target(run.get("target", ""))


def build_prompt(args: argparse.Namespace) -> None:
    layout, product_dir = load_layout(Path(args.layout))
    state = load_attempt_state(product_dir)
    target = resolve_target(args, state, product_dir)

    if args.mode == "SKU":
        if not args.master:
            raise ValueError("MASTER_MANIFEST_REQUIRED")
        if Path(args.master).expanduser().resolve() != product_dir / "reusable" / "master.json":
            raise ValueError("MASTER_MANIFEST_PATH_INVALID")
        verify_master(product_dir)
    elif args.master:
        raise ValueError("MASTER_MANIFEST_NOT_ALLOWED_FOR_MASTER_PROMPT")

    run = prepare_run(state, args.mode, target)
    run["redo"] = bool(args.redo)
    addition = (args.additional_prompt or "").strip()
    if addition and not (args.mode == "SKU" and args.redo):
        raise ValueError("ADDITIONAL_PROMPT_REQUIRES_SKU_REDO")
    additions_path = product_dir / "reusable" / PROMPT_ADDITIONS_NAME
    additions = additions_from(additions_path)
    if addition:
        additions.append(addition)
        atomic_write(additions_path, additions)
    attempts = run["attempts"]
    attempt_number = len(attempts) + 1
    parts = [image_prompt()]
    if args.mode == "SKU":
        parts.append(fenced_block(VARIANT_REFERENCE, "SKU edit block"))
    parts.append(information_safe_zone_block(layout))
    increment = additions_block(additions)
    if increment:
        parts.append(increment)
    parts.append(PRODUCT_AREA_POLICY)
    prompt = "\n\n".join(parts)
    prompt_path = prompt_file_path(product_dir, args.mode, target, run, attempt_number)
    attempts.append(
        {
            "attempt": attempt_number,
            "status": "PENDING",
            "prompt_path": prompt_path.name,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        }
    )
    atomic_write(prompt_path, prompt)
    atomic_write(attempt_state_path(product_dir), state)
    sys.stdout.write(prompt)


def record_rejection(args: argparse.Namespace) -> None:
    _, product_dir = load_layout(Path(args.layout))
    state = load_attempt_state(product_dir)
    target = resolve_active_target(args, state)
    run = active_run(state)
    if run is None:
        raise ValueError("REJECTION_WITHOUT_SCENE_ATTEMPT")
    if run.get("mode") != args.mode or run.get("target") != target:
        raise ValueError(
            "NEW_CANDIDATE_REQUIRED: active scene is "
            f"{run.get('mode')}/{run.get('target')}"
        )
    attempts = run.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ValueError("REJECTION_WITHOUT_SCENE_ATTEMPT")
    current = attempts[-1]
    if current.get("status") != "PENDING":
        raise ValueError("REJECTION_ALREADY_RECORDED")
    addition = (args.additional_prompt or "").strip()
    additions_path = product_dir / "reusable" / PROMPT_ADDITIONS_NAME
    additions = additions_from(additions_path)
    if addition:
        additions.append(addition)
        atomic_write(additions_path, additions)
    current["status"] = "USER_REJECTED"
    current["additional_prompt"] = addition or None
    atomic_write(attempt_state_path(product_dir), state)
    json.dump(
        {
            "mode": args.mode,
            "target": target,
            "attempt": int(current["attempt"]),
            "status": "USER_REJECTED",
            "additional_prompt": addition or None,
            "accumulated_additions": len(additions),
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    print()


def record_delivery_failure(args: argparse.Namespace) -> None:
    _, product_dir = load_layout(Path(args.layout))
    reason = args.reason.strip()
    if not reason:
        raise ValueError("DELIVERY_FAILURE_REASON_EMPTY")
    state = load_attempt_state(product_dir)
    target = resolve_active_target(args, state)
    run = active_run(state)
    if run is None or run.get("mode") != args.mode or run.get("target") != target:
        raise ValueError("DELIVERY_FAILURE_RUN_MISMATCH")
    attempts = run.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ValueError("DELIVERY_FAILURE_WITHOUT_ATTEMPT")
    current = attempts[-1]
    if current.get("status") != "PENDING":
        raise ValueError("DELIVERY_FAILURE_ALREADY_RECORDED")
    current["status"] = "DELIVERY_FAILED"
    current["reason"] = reason
    atomic_write(attempt_state_path(product_dir), state)
    json.dump(
        {
            "recorded": {
                "mode": args.mode,
                "target": target,
                "run_id": run["run_id"],
                "attempt": int(current["attempt"]),
                "status": "DELIVERY_FAILED",
                "reason": reason,
            },
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--mode", required=True, choices=("MASTER", "SKU"))
    build.add_argument("--layout", required=True)
    build.add_argument("--target")
    build.add_argument("--master")
    build.add_argument("--redo", action="store_true")
    build.add_argument("--additional-prompt")
    build.set_defaults(handler=build_prompt)

    record = subparsers.add_parser("reject")
    record.add_argument("--layout", required=True)
    record.add_argument("--mode", required=True, choices=("MASTER", "SKU"))
    record.add_argument("--target")
    record.add_argument("--additional-prompt")
    record.set_defaults(handler=record_rejection)

    delivery = subparsers.add_parser("record-delivery-failure")
    delivery.add_argument("--layout", required=True)
    delivery.add_argument("--mode", required=True, choices=("MASTER", "SKU"))
    delivery.add_argument("--target")
    delivery.add_argument("--reason", required=True)
    delivery.set_defaults(handler=record_delivery_failure)

    args = parser.parse_args()
    try:
        args.handler(args)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
