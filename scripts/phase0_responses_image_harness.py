#!/usr/bin/env python3
"""Phase 0 external image-generation harness.

This harness exists only to validate exact prompt delivery with an explicit image
reference when the ChatGPT project-conversation image surface cannot reproduce the
repository Skill transport contract.

It deliberately performs at most one OpenAI Responses API call per invocation and
never retries automatically.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_required(path: Path, label: str) -> bytes:
    try:
        data = path.expanduser().resolve().read_bytes()
    except OSError as exc:
        raise ValueError(f"{label}_UNREADABLE: {exc}") from exc
    if not data:
        raise ValueError(f"{label}_EMPTY")
    return data


def verify_hash(actual: str, expected: str | None, label: str) -> None:
    if expected and actual.lower() != expected.lower():
        raise ValueError(
            f"{label}_SHA256_MISMATCH: expected {expected.lower()}, got {actual.lower()}"
        )


def image_data_url(image_bytes: bytes, image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(suffix)
    if mime is None:
        raise ValueError("REFERENCE_IMAGE_TYPE_UNSUPPORTED: use PNG, WEBP, JPG, or JPEG")
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inspect_output(image_bytes: bytes) -> dict:
    try:
        from PIL import Image
        from io import BytesIO

        with Image.open(BytesIO(image_bytes)) as image:
            image.load()
            return {
                "format": image.format,
                "mode": image.mode,
                "width": image.width,
                "height": image.height,
            }
    except ImportError:
        return {"format": None, "mode": None, "width": None, "height": None}
    except OSError as exc:
        raise ValueError(f"GENERATED_IMAGE_UNREADABLE: {exc}") from exc


def build_tool(args: argparse.Namespace) -> dict:
    tool = {
        "type": "image_generation",
        "model": args.image_model,
        "action": "generate",
    }
    if args.size != "auto":
        tool["size"] = args.size
    if args.quality != "auto":
        tool["quality"] = args.quality
    if args.background != "auto":
        tool["background"] = args.background
    return tool


def run(args: argparse.Namespace) -> dict:
    prompt_path = Path(args.prompt)
    reference_path = Path(args.reference_image)
    output_path = Path(args.output).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve()

    prompt_bytes = read_required(prompt_path, "PROMPT")
    reference_bytes = read_required(reference_path, "REFERENCE_IMAGE")

    try:
        prompt = prompt_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("PROMPT_NOT_UTF8") from exc

    prompt_sha = sha256_bytes(prompt_bytes)
    reference_sha = sha256_bytes(reference_bytes)
    verify_hash(prompt_sha, args.expected_prompt_sha256, "PROMPT")
    verify_hash(reference_sha, args.expected_reference_sha256, "REFERENCE_IMAGE")

    request_record = {
        "schema": 1,
        "purpose": "Phase 0 exact-prompt / explicit-reference image-generation harness",
        "api": "Responses API",
        "main_model": args.main_model,
        "image_tool": build_tool(args),
        "prompt_path": str(prompt_path),
        "prompt_sha256": prompt_sha,
        "reference_image_path": str(reference_path),
        "reference_image_sha256": reference_sha,
        "output_path": str(output_path),
        "metadata_path": str(metadata_path),
        "automatic_retry": False,
    }

    if args.dry_run:
        request_record["status"] = "DRY_RUN_VALIDATED"
        return request_record

    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY_UNAVAILABLE")
    if output_path.exists():
        raise ValueError(f"OUTPUT_ALREADY_EXISTS: {output_path}")
    if metadata_path.exists():
        raise ValueError(f"METADATA_ALREADY_EXISTS: {metadata_path}")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError("OPENAI_SDK_UNAVAILABLE: install the current openai package") from exc

    client = OpenAI()
    response = client.responses.create(
        model=args.main_model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": image_data_url(reference_bytes, reference_path),
                        "detail": "auto",
                    },
                ],
            }
        ],
        tools=[build_tool(args)],
    )

    image_calls = [item for item in response.output if item.type == "image_generation_call"]
    if len(image_calls) != 1:
        raise ValueError(
            f"IMAGE_GENERATION_CALL_COUNT_INVALID: expected 1, got {len(image_calls)}"
        )

    call = image_calls[0]
    encoded = getattr(call, "result", None)
    if not encoded:
        raise ValueError("GENERATED_IMAGE_MISSING")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("GENERATED_IMAGE_BASE64_INVALID") from exc
    if not image_bytes:
        raise ValueError("GENERATED_IMAGE_EMPTY")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)

    request_record.update(
        {
            "status": "COMPLETED",
            "response_id": response.id,
            "image_call_id": getattr(call, "id", None),
            "revised_prompt": getattr(call, "revised_prompt", None),
            "generated_image_sha256": sha256_bytes(image_bytes),
            "generated_image": inspect_output(image_bytes),
        }
    )
    metadata_path.write_text(
        json.dumps(request_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return request_record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--reference-image", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--expected-prompt-sha256")
    parser.add_argument("--expected-reference-sha256")
    parser.add_argument("--main-model", default="gpt-6-astra")
    parser.add_argument("--image-model", default="gpt-image-2.5-sunburst")
    parser.add_argument("--size", default="auto")
    parser.add_argument(
        "--quality",
        default="auto",
        choices=("auto", "low", "medium", "high", "xhigh", "max"),
    )
    parser.add_argument(
        "--background",
        default="auto",
        choices=("auto", "opaque", "transparent"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        result = run(args)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
