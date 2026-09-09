---
name: phase6-reference-isolation-probe-c1
description: "Phase 6 C1 runtime probe. Validate that Work accepts num_last_images_to_include=0 together with one explicit palette reference path. Uses one Image Gen call only and never writes production MASTER/SKU files."
---

# MD3 Product Image — Phase 6 C1 Reference Isolation Probe

PROBE_PACKAGE_ID: `PHASE6-C1-REFERENCE-ISOLATION-20260910`

This package is only for the Phase 6 C1 callable-boundary test.

It permits exactly **one** image-model operation.

It must not create, replace, bind, redo, or renumber production MASTER/SKU outputs.

## Identity gate

Before doing anything else, verify that the active Skill instructions contain both:

```text
phase6-reference-isolation-probe-c1
PHASE6-C1-REFERENCE-ISOLATION-20260910
```

If not, return:

```text
PHASE6_C1_WRONG_SKILL_INSTANCE
```

and stop with zero image-model operations.

## Input

Use the real uploaded HUAWEI black product source:

```text
黑.png
```

Do not send `黑.png` itself to Image Gen.

The purpose of keeping `黑.png` in the conversation is deliberate: it is a recent conversation image and therefore represents the exact context-leakage risk that C1 is testing.

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

## 2. Read the exact C1 prompt

Read exactly:

```text
references/phase6-c1-reference-isolation.txt
```

Use its full contents verbatim as the Image Gen `prompt` argument.

Do not add or remove prompt text.

## 3. Perform exactly one Image Gen call

Invoke the callable Image Gen interface with these explicit arguments:

```text
prompt = <exact prompt file contents>
num_last_images_to_include = 0
referenced_image_paths = [<TEMP_DIR>/palette-reference.png]
```

The list must contain exactly one path.

Do not include `黑.png` in `referenced_image_paths`.
Do not pass null for `num_last_images_to_include`.
Do not omit `num_last_images_to_include`.
Do not invoke another image call if the call fails.
Do not retry with a different value.

If the callable rejects this argument combination, return:

```text
REFERENCE_ISOLATION_CALL_REJECTED
```

and include the surfaced tool/runtime error text if available.

If the callable accepts the operation and returns an accessible generated image, return:

```text
REFERENCE_ISOLATION_CALL_ACCEPTED
```

## 4. Return evidence

Return:

1. `PROBE_PACKAGE_ID`
2. `image_model_operations: 1`
3. the exact callable argument values used for:
   - `num_last_images_to_include`
   - `referenced_image_paths`
4. the generated raw background image
5. the deterministic palette-reference image if practical
6. one of the two exact conclusions above

Do not claim that recent images were excluded based only on visual appearance. The primary C1 evidence is that the actual callable accepted `num_last_images_to_include=0` with the explicit reference path.

## Stop after C1

Do not create a final product image.
Do not lock a MASTER.
Do not generate an SKU.
Do not run another image-model operation.
