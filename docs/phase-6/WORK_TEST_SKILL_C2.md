---
name: phase6-explicit-reference-path-probe-c2
description: "Phase 6 C2 runtime probe. Validate that Work accepts one explicit local palette reference path while num_last_images_to_include is omitted entirely. Uses exactly one Image Gen call and never writes production MASTER/SKU files."
---

# MD3 Product Image — Phase 6 C2 Explicit Reference Path Probe

PROBE_PACKAGE_ID: `PHASE6-C2-EXPLICIT-REFERENCE-PATH-20260910`

This package is only for the Phase 6 C2 callable-boundary test.

It permits exactly **one** image-model operation.

It must not create, replace, bind, redo, or renumber production MASTER/SKU outputs.

## Identity gate

Before doing anything else, verify that the active Skill instructions contain both:

```text
phase6-explicit-reference-path-probe-c2
PHASE6-C2-EXPLICIT-REFERENCE-PATH-20260910
```

If not, return:

```text
PHASE6_C2_WRONG_SKILL_INSTANCE
```

and stop with zero image-model operations.

## Input

Use the real uploaded HUAWEI black product source:

```text
黑.png
```

Do not send `黑.png` itself to Image Gen.

## 1. Build the deterministic palette reference locally

Create a temporary probe directory that is not a production product directory.

Run:

```text
python scripts/extract_palette.py \
  --source <黑.png> \
  --json-output <TEMP_DIR>/palette.json \
  --reference-output <TEMP_DIR>/palette-reference.png
```

If palette extraction fails, report the deterministic failure and stop before Image Gen.

## 2. Read the exact C2 prompt

Read exactly:

```text
references/phase6-c2-explicit-reference-path.txt
```

Use its full contents verbatim as the Image Gen `prompt` argument.

Do not add or remove prompt text.

## 3. Perform exactly one Image Gen call

Invoke the callable Image Gen interface with these explicit arguments:

```text
prompt = <exact prompt file contents>
referenced_image_paths = [<TEMP_DIR>/palette-reference.png]
```

The list must contain exactly one path.

Critical requirement:

```text
num_last_images_to_include
```

must be **omitted entirely** from the callable invocation.

Do not pass `0`.
Do not pass `null`.
Do not pass any other value.
Do not include `黑.png` in `referenced_image_paths`.
Do not invoke another image call if the call fails.
Do not retry with a different argument combination.

If the callable rejects the invocation, return:

```text
EXPLICIT_REFERENCE_PATH_CALL_REJECTED
```

and include the surfaced tool/runtime error text if available.

If the callable accepts the operation and returns an accessible generated image, return:

```text
EXPLICIT_REFERENCE_PATH_CALL_ACCEPTED
```

## 4. Return evidence

Return:

1. `PROBE_PACKAGE_ID`
2. `image_model_operations: 1`
3. confirmation that `num_last_images_to_include` was omitted
4. the exact `referenced_image_paths` value used
5. the generated raw background image
6. the deterministic palette-reference image if practical
7. one of the two exact conclusions above

The generated image should be an empty abstract palette-driven background. Visual appearance is supporting evidence only; callable acceptance of explicit-path mode is the primary gate.

## Stop after C2

Do not create a final product image.
Do not lock a MASTER.
Do not generate an SKU.
Do not run another image-model operation.
