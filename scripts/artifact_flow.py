#!/usr/bin/env python3
"""Preview, create, bind, and verify candidate and SKU artifacts."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
SCENE_COMPOSE_SCRIPT = SCRIPTS_DIR / "compose_scene.py"
COMPOSE_SCRIPT = SCRIPTS_DIR / "compose_image.py"
ATTEMPT_STATE_NAME = "scene-attempts.json"
TITLE_COLOR = "2C2C2C"
VERSION_COLOR = "5A5A5A"


from common import (
    atomic_write,
    normalize_raster_contract,
    read_json,
    require_matching_raster,
    require_three_four_raster,
    resolve_entry,
    sha256_file,
    verify_information_assets,
    verify_master,
)


def safe_component(value: str, label: str) -> str:
    value = value.strip()
    if not value or value in {".", ".."} or any(char in value for char in "/\\\x00"):
        raise ValueError(f"{label}_INVALID")
    return value


def load_product(product_dir_arg: str) -> tuple[Path, Path, dict]:
    product_dir = Path(product_dir_arg).expanduser().resolve()
    reusable_dir = product_dir / "reusable"
    layout_path = reusable_dir / "layout.json"
    if not product_dir.is_dir():
        raise ValueError(f"PRODUCT_DIRECTORY_MISSING: {product_dir}")
    layout = read_json(layout_path)
    if layout.get("product_directory") != str(product_dir):
        raise ValueError("PRODUCT_DIRECTORY_MISMATCH")
    verify_information_assets(layout, reusable_dir)
    output_dir = product_dir / "output"
    output_dir.mkdir(exist_ok=True)
    return product_dir, layout_path, layout


def ensure_output_allowed(product_dir: Path) -> None:
    output_dir = product_dir / "output"
    for path in output_dir.iterdir():
        allowed = path.name == "ORIGINAL_MASTER_FINAL.png" or (
            path.is_file()
            and path.name.startswith("SKU_VARIANT-")
            and path.name != "SKU_VARIANT-.png"
            and path.suffix.lower() == ".png"
        )
        if not allowed or not path.is_file():
            raise ValueError(f"OUTPUT_CONTAINS_FORBIDDEN_FILE: {path.name}")


def relative_entry(path: Path, product_dir: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(product_dir).as_posix(),
        "sha256": sha256_file(path),
    }


def copy_new(source_arg: str | Path, destination: Path) -> None:
    source = Path(source_arg).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"SOURCE_FILE_MISSING: {source}")
    if destination.exists():
        raise ValueError(f"REFUSE_OVERWRITE: {destination}")
    shutil.copy2(source, destination)


def run_script(arguments: list[str]) -> dict:
    completed = subprocess.run(
        [sys.executable, *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(detail or f"SCRIPT_FAILED: {arguments[0]}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"SCRIPT_OUTPUT_INVALID: {arguments[0]}") from exc


def run_compose(
    scene: Path,
    layout: Path,
    output: Path,
    output_kind: str,
) -> dict:
    command = [
        str(COMPOSE_SCRIPT),
        "--scene",
        str(scene),
        "--layout",
        str(layout),
        "--output",
        str(output),
        "--output-kind",
        output_kind,
    ]
    return run_script(command)


def run_scene_compose(
    background: Path,
    product: Path,
    scene: Path,
    product_layer: Path,
    shadow_mask: Path,
) -> dict:
    if product_layer.exists() != shadow_mask.exists():
        raise ValueError("CACHED_PRODUCT_SHADOW_INCOMPLETE")
    command = [
        str(SCENE_COMPOSE_SCRIPT),
        "--background", str(background),
        "--product", str(product),
        "--output", str(scene),
        "--product-layer", str(product_layer),
        "--shadow-mask", str(shadow_mask),
    ]
    if product_layer.exists():
        command.append("--reuse-layers")
    return run_script(command)


def scene_composite_info(report: dict) -> dict:
    product_box = report.get("product_box")
    shadow = report.get("shadow")
    if not isinstance(product_box, dict) or not isinstance(shadow, dict):
        raise ValueError("SCENE_COMPOSITE_REPORT_INVALID")
    return {"product_box": product_box, "shadow": shadow}


def scene_attempt_path(product_dir: Path) -> Path:
    return product_dir / ATTEMPT_STATE_NAME


def scene_attempt(product_dir: Path, mode: str, target: str) -> tuple[dict, dict]:
    path = scene_attempt_path(product_dir)
    if not path.is_file():
        raise ValueError("SCENE_ATTEMPT_STATE_MISSING: build the scene prompt first")
    state = read_json(path)
    run_id = state.get("active_run_id")
    runs = state.get("runs")
    if not run_id or not isinstance(runs, list):
        raise ValueError("ATTEMPT_STATE_INVALID")
    run = next((item for item in runs if item.get("run_id") == run_id), None)
    if not isinstance(run, dict):
        raise ValueError("ACTIVE_ATTEMPT_RUN_MISSING")
    if run.get("mode") != mode or run.get("target") != target:
        raise ValueError(
            "SCENE_TARGET_MISMATCH: expected "
            f"{run.get('mode')}/{run.get('target')}"
        )
    attempts = run.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ValueError("SCENE_ATTEMPT_MISSING")
    current = attempts[-1]
    if current.get("status") != "PENDING":
        raise ValueError("SCENE_ATTEMPT_NOT_PENDING")
    return state, {"run": run, "attempt": current}


def accept_scene_attempt(
    product_dir: Path, mode: str, target: str
) -> dict[str, str | int]:
    state, info = scene_attempt(product_dir, mode, target)
    run = info["run"]
    attempt = info["attempt"]
    result = attempt_record(info)
    attempt["status"] = "ACCEPTED"
    run["status"] = "ACCEPTED"
    state["active_run_id"] = None
    atomic_write(scene_attempt_path(product_dir), state)
    return result


def validate_information_colors(layout: dict, information: dict) -> None:
    elements = layout.get("elements")
    if not isinstance(elements, dict):
        raise ValueError("LAYOUT_ELEMENTS_INVALID")
    expected_version = VERSION_COLOR if "VERSION_TEXT_RECT" in elements else None
    if information.get("title_color") != TITLE_COLOR or information.get("version_color") != expected_version:
        raise ValueError("FIXED_INFORMATION_COLOR_MISMATCH")


def cleanup(paths: list[Path]) -> None:
    for path in paths:
        if path.is_file():
            path.unlink()


def preview_paths(product_dir: Path, candidate_id: str) -> dict[str, Path]:
    if candidate_id.endswith(("-scene", "-preview")):
        raise ValueError("CANDIDATE_ID_RESERVED")
    prefix = f"master-candidate-{candidate_id}-preview"
    reusable_dir = product_dir / "reusable"
    return {
        "background": product_dir / f"{prefix}-background.png",
        "product": reusable_dir / f"master-candidate-{candidate_id}-product.png",
        "shadow": reusable_dir / f"master-candidate-{candidate_id}-shadow.png",
        "scene": product_dir / f"{prefix}-scene.png",
        "final": product_dir / f"{prefix}.png",
        "manifest": product_dir / f"{prefix}.json",
    }


def attempt_record(info: dict) -> dict[str, str | int]:
    run, attempt = info["run"], info["attempt"]
    return {
        "run_id": run["run_id"],
        "attempt": int(attempt["attempt"]),
        "prompt_path": str(attempt.get("prompt_path", "")),
        "prompt_sha256": str(attempt.get("prompt_sha256", "")),
    }


def current_attempt_info(product_dir: Path, candidate_id: str) -> dict:
    return attempt_record(scene_attempt(product_dir, "MASTER", candidate_id)[1])


def create_preview(args: argparse.Namespace) -> None:
    product_dir, layout_path, layout = load_product(args.product_dir)
    candidate_id = safe_component(args.candidate_id, "CANDIDATE_ID")
    attempt_info = current_attempt_info(product_dir, candidate_id)
    paths = preview_paths(product_dir, candidate_id)
    if any(
        path.exists()
        for label, path in paths.items()
        if label not in {"product", "shadow"}
    ):
        raise ValueError("PREVIEW_ALREADY_EXISTS")
    ensure_output_allowed(product_dir)
    layers_existed = paths["product"].exists() and paths["shadow"].exists()
    created = [
        path for label, path in paths.items()
        if label not in {"product", "shadow"}
    ]
    if not layers_existed:
        created.extend((paths["product"], paths["shadow"]))
    try:
        product_source = Path(args.product).expanduser().resolve()
        expected_product_hash = layout.get("product_reference", {}).get("sha256")
        if not product_source.is_file() or sha256_file(product_source) != expected_product_hash:
            raise ValueError("MASTER_PRODUCT_REFERENCE_MISMATCH")
        copy_new(args.generated_background, paths["background"])
        background_raster = require_three_four_raster(paths["background"], "MASTER_BACKGROUND")
        raster = {
            "width": int(background_raster["width"]),
            "height": int(background_raster["height"]),
            "ratio": "3:4",
        }
        scene_render = scene_composite_info(run_scene_compose(
            paths["background"],
            product_source,
            paths["scene"],
            paths["product"],
            paths["shadow"],
        ))
        require_matching_raster(paths["product"], raster, "MASTER_PRODUCT_LAYER")
        require_matching_raster(paths["shadow"], raster, "MASTER_SHADOW")
        require_matching_raster(paths["scene"], raster, "MASTER_SCENE")
        render = run_compose(
            paths["scene"],
            layout_path,
            paths["final"],
            "CANDIDATE",
        )
        require_matching_raster(paths["final"], raster, "MASTER_FINAL")
        information = {
            "title_color": render.get("title_color"),
            "version_color": render.get("version_color"),
        }
        validate_information_colors(layout, information)
        manifest = {
            "schema": 1,
            "kind": "MASTER_CANDIDATE_PREVIEW",
            "candidate_id": candidate_id,
            "files": {
                "layout": relative_entry(layout_path, product_dir),
                "background": relative_entry(paths["background"], product_dir),
                "product": relative_entry(paths["product"], product_dir),
                "shadow": relative_entry(paths["shadow"], product_dir),
                "scene": relative_entry(paths["scene"], product_dir),
                "final": relative_entry(paths["final"], product_dir),
            },
            "raster": raster,
            "information": information,
            "scene_composite": scene_render,
            "scene_attempt": attempt_info,
        }
        atomic_write(paths["manifest"], manifest, new=True)
    except Exception:
        cleanup(created)
        raise
    json.dump(manifest, sys.stdout, ensure_ascii=False, indent=2)
    print()


def load_preview(product_dir: Path, candidate_id: str) -> tuple[dict, dict[str, Path]]:
    paths = preview_paths(product_dir, candidate_id)
    manifest = read_json(paths["manifest"])
    if (
        manifest.get("kind") != "MASTER_CANDIDATE_PREVIEW"
        or manifest.get("candidate_id") != candidate_id
    ):
        raise ValueError("PREVIEW_MANIFEST_INVALID")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("PREVIEW_MANIFEST_INVALID")
    expected = {
        "layout": product_dir / "reusable" / "layout.json",
        "background": paths["background"],
        "product": paths["product"],
        "shadow": paths["shadow"],
        "scene": paths["scene"],
        "final": paths["final"],
    }
    for label, path in expected.items():
        resolve_entry(files.get(label), product_dir, path, label)
    raster = normalize_raster_contract(manifest.get("raster"), "PREVIEW_RASTER")
    for label in ("background", "product", "shadow", "scene", "final"):
        require_matching_raster(expected[label], raster, f"PREVIEW_{label.upper()}")
    manifest = dict(manifest)
    manifest["raster"] = raster
    return manifest, paths


def discard_preview(args: argparse.Namespace) -> None:
    product_dir, _, _ = load_product(args.product_dir)
    candidate_id = safe_component(args.candidate_id, "CANDIDATE_ID")
    current_attempt_info(product_dir, candidate_id)
    paths = preview_paths(product_dir, candidate_id)
    if not any(path.exists() for path in paths.values()):
        raise ValueError("PREVIEW_MISSING")
    cleanup([
        path for label, path in paths.items()
        if label not in {"product", "shadow"}
    ])
    json.dump(
        {"discarded": True, "candidate_id": candidate_id},
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    print()


def bind_candidate(args: argparse.Namespace) -> None:
    product_dir, layout_path, layout = load_product(args.product_dir)
    reusable_dir = product_dir / "reusable"
    candidate_id = safe_component(args.candidate_id, "CANDIDATE_ID")
    ensure_output_allowed(product_dir)
    if any((product_dir / "output").iterdir()):
        raise ValueError("BIND_REQUIRES_EMPTY_OUTPUT_DIRECTORY")
    preview, preview_files = load_preview(product_dir, candidate_id)
    attempt_info = current_attempt_info(product_dir, candidate_id)
    if preview.get("scene_attempt") != attempt_info:
        raise ValueError("PREVIEW_ATTEMPT_MISMATCH")
    raster = normalize_raster_contract(preview.get("raster"), "PREVIEW_RASTER")
    targets = {
        "background": reusable_dir / "ORIGINAL_MASTER_BACKGROUND.png",
        "product": reusable_dir / "ORIGINAL_MASTER_PRODUCT.png",
        "shadow": reusable_dir / "ORIGINAL_MASTER_SHADOW.png",
        "scene": reusable_dir / "ORIGINAL_MASTER_SCENE.png",
        "final": product_dir / "output" / "ORIGINAL_MASTER_FINAL.png",
        "manifest": reusable_dir / "master.json",
    }
    if any(path.exists() for path in targets.values()):
        raise ValueError("MASTER_ALREADY_EXISTS")

    created = list(targets.values())
    try:
        for label in ("background", "product", "shadow", "scene", "final"):
            copy_new(preview_files[label], targets[label])
            require_matching_raster(targets[label], raster, f"MASTER_{label.upper()}")
        information = preview.get("information")
        if not isinstance(information, dict):
            raise ValueError("CANDIDATE_INFORMATION_INVALID")
        validate_information_colors(layout, information)
        master = {
            "schema": 1,
            "state": "BOUND",
            "source_candidate_id": candidate_id,
            "files": {
                "layout": relative_entry(layout_path, product_dir),
                "background": relative_entry(targets["background"], product_dir),
                "product": relative_entry(targets["product"], product_dir),
                "shadow": relative_entry(targets["shadow"], product_dir),
                "scene": relative_entry(targets["scene"], product_dir),
                "final": relative_entry(targets["final"], product_dir),
            },
            "raster": raster,
            "information": {
                "title_color": information["title_color"],
                "version_color": information["version_color"],
                "title_line_count": layout.get("title_line_count"),
            },
            "scene_composite": preview.get("scene_composite"),
        }
        atomic_write(targets["manifest"], master, new=True)
        accept_scene_attempt(product_dir, "MASTER", candidate_id)
    except Exception:
        cleanup(created)
        raise

    cleanup(list(preview_files.values()))
    json.dump(master, sys.stdout, ensure_ascii=False, indent=2)
    print()


def sku_preview_paths(product_dir: Path, sku_label: str) -> dict[str, Path]:
    reusable_dir = product_dir / "reusable"
    prefix = f"{sku_label}-preview"
    return {
        "background": product_dir / f"{prefix}-background.png",
        "product": reusable_dir / f"{sku_label}-product.png",
        "shadow": reusable_dir / f"{sku_label}-shadow.png",
        "layers": reusable_dir / f"{sku_label}-layers.json",
        "scene": product_dir / f"{prefix}-scene.png",
        "final": product_dir / f"{prefix}.png",
        "manifest": product_dir / f"{prefix}.json",
    }


def pending_sku(product_dir: Path) -> tuple[str, dict]:
    state = read_json(scene_attempt_path(product_dir))
    run_id = state.get("active_run_id")
    runs = state.get("runs")
    if not run_id or not isinstance(runs, list):
        raise ValueError("ATTEMPT_STATE_INVALID")
    run = next(
        (item for item in runs if isinstance(item, dict) and item.get("run_id") == run_id),
        None,
    )
    if not isinstance(run, dict) or run.get("mode") != "SKU":
        raise ValueError("ACTIVE_SKU_RUN_MISSING")
    sku_label = safe_component(run.get("target", ""), "SKU_LABEL")
    if not sku_label.startswith("SKU_VARIANT-") or not sku_label.removeprefix("SKU_VARIANT-").isalpha():
        raise ValueError("SKU_LABEL_INVALID")
    _, pending_info = scene_attempt(product_dir, "SKU", sku_label)
    return sku_label, pending_info


def create_sku(args: argparse.Namespace) -> None:
    product_dir, layout_path, layout = load_product(args.product_dir)
    ensure_output_allowed(product_dir)
    master = verify_master(product_dir)
    expected_raster = normalize_raster_contract(master.get("raster"), "MASTER_RASTER")
    generated_background = Path(args.generated_background).expanduser().resolve()
    require_matching_raster(generated_background, expected_raster, "SKU_BACKGROUND")
    sku_label, pending_info = pending_sku(product_dir)
    redo = bool(pending_info["run"].get("redo"))
    attempt_info = attempt_record(pending_info)

    paths = sku_preview_paths(product_dir, sku_label)
    cleanup([paths[label] for label in ("background", "scene", "final", "manifest")])
    product_source = Path(args.product).expanduser().resolve()
    product_hash = sha256_file(product_source)
    layers_exist = paths["product"].exists() and paths["shadow"].exists()
    if layers_exist:
        layers = read_json(paths["layers"])
        if layers.get("source_sha256") != product_hash:
            raise ValueError("CACHED_PRODUCT_SOURCE_MISMATCH")
    elif any(paths[label].exists() for label in ("product", "shadow", "layers")):
        raise ValueError("CACHED_PRODUCT_SHADOW_INCOMPLETE")
    created = [paths[label] for label in ("background", "scene", "final", "manifest")]
    if not layers_exist:
        created.extend(paths[label] for label in ("product", "shadow", "layers"))
    final_output = product_dir / "output" / f"{sku_label}.png"
    replacement = final_output.with_name(f".{final_output.name}.tmp")
    backup = final_output.with_name(f".{final_output.name}.previous")
    cleanup([replacement, backup])
    try:
        copy_new(generated_background, paths["background"])
        scene_render = scene_composite_info(run_scene_compose(
            paths["background"], product_source, paths["scene"],
            paths["product"], paths["shadow"],
        ))
        require_matching_raster(paths["product"], expected_raster, "SKU_PRODUCT_LAYER")
        require_matching_raster(paths["shadow"], expected_raster, "SKU_SHADOW")
        require_matching_raster(paths["scene"], expected_raster, "SKU_SCENE")
        if not layers_exist:
            atomic_write(paths["layers"], {"source_sha256": product_hash}, new=True)
        render = run_compose(
            paths["scene"], layout_path, paths["final"], "SKU_PREVIEW",
        )
        require_matching_raster(paths["final"], expected_raster, "SKU_FINAL")
        information = {
            "title_color": render.get("title_color"),
            "version_color": render.get("version_color"),
        }
        validate_information_colors(layout, information)
        manifest = {
            "kind": "SKU_VARIANT",
            "sku_label": sku_label,
            "files": {
                label: relative_entry(paths[label], product_dir)
                for label in ("background", "product", "shadow", "scene", "final")
            },
            "raster": expected_raster,
            "information": information,
            "scene_composite": scene_render,
            "scene_attempt": attempt_info,
            "master_verified": True,
        }
        if final_output.exists() and not redo:
            raise ValueError("SKU_ALREADY_EXISTS")
        shutil.copy2(paths["final"], replacement)
        if final_output.exists():
            shutil.copy2(final_output, backup)
        replacement.replace(final_output)
        manifest["files"]["final"] = relative_entry(final_output, product_dir)
        atomic_write(paths["manifest"], manifest)
        accept_scene_attempt(product_dir, "SKU", sku_label)
        cleanup([backup])
    except Exception:
        if backup.exists():
            backup.replace(final_output)
        elif final_output.exists() and not redo:
            cleanup([final_output])
        cleanup([replacement])
        cleanup(created)
        raise
    json.dump(manifest, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview = subparsers.add_parser("preview")
    preview.add_argument("--generated-background", required=True)
    preview.add_argument("--product", required=True)
    preview.add_argument("--product-dir", required=True)
    preview.add_argument("--candidate-id", required=True)
    preview.set_defaults(handler=create_preview)

    discard = subparsers.add_parser("discard-preview")
    discard.add_argument("--product-dir", required=True)
    discard.add_argument("--candidate-id", required=True)
    discard.set_defaults(handler=discard_preview)

    bind = subparsers.add_parser("bind")
    bind.add_argument("--product-dir", required=True)
    bind.add_argument("--candidate-id", required=True)
    bind.set_defaults(handler=bind_candidate)

    sku = subparsers.add_parser("sku")
    sku.add_argument("--generated-background", required=True)
    sku.add_argument("--product", required=True)
    sku.add_argument("--product-dir", required=True)
    sku.set_defaults(handler=create_sku)

    args = parser.parse_args()
    try:
        args.handler(args)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
