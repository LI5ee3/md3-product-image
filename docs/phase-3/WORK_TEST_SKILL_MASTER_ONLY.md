---
name: md3-product-image
description: "Phase 3 MASTER-only ablation for md3-product-image. Generate the same structured MD3 MASTER while sending only a deterministic palette-reference image to Image Gen; keep the authoritative product image local for deterministic composition."
---

# MD3 Product Image — Phase 3 Palette-Only MASTER Test

This package exists only for the Phase 3 Gate B1 Work A/B. It is not the production Skill and must not be used for SKU generation.

## Fixed experiment rule

Change exactly one variable relative to the Phase 2 structured MASTER baseline:

- Phase 2 A: Image Gen receives the complete product image as palette reference.
- Phase 3 B1: Image Gen receives only deterministic `palette-reference.png`.

Everything else remains the same:

- same structured prompt
- same product image for local deterministic composition
- same Logo
- same title/version text
- same layout rules
- same local product placement
- same fixed 2D shadow
- one Image Gen operation
- one local composite
- user-controlled lock/redo

Do not send the authoritative product image to Image Gen in this test.

## Resolve inputs

Require:

- authoritative product PNG/WEBP
- original Logo PNG/WEBP
- exact complete product name
- exact title line 1
- exact title line 2 when `TITLE_LINES=2`
- optional exact version text
- explicit `TITLE_LINES`: `1` or `2`

Never infer `TITLE_LINES`.

Use `<output root>/<exact complete product name>` as `PRODUCT_DIRECTORY`.

## 1. Measure

Run the normal measurement step:

```text
python scripts/measure_text.py \
  --complete-name <complete-name> \
  --title-lines <1-or-2> \
  --title-line-1 <line-1> \
  [--title-line-2 <line-2>] \
  [--version <version>] \
  --product-reference <authoritative-product> \
  --logo <logo> \
  --output-root <output-root>
```

Reuse an existing layout only if its recorded source identity matches exactly.

## 2. Extract deterministic palette

Before building the MASTER prompt, create these reusable assets:

```text
python scripts/extract_palette.py \
  --source <authoritative-product> \
  --json-output <PRODUCT_DIRECTORY>/reusable/palette.json \
  --reference-output <PRODUCT_DIRECTORY>/reusable/palette-reference.png
```

The extractor is deterministic and outputs color information only.

If either output already exists, verify that `palette.json` records the same authoritative source SHA. Do not silently replace palette assets from another source.

## 3. Build the normal structured MASTER prompt

```text
python scripts/scene_prompt.py build \
  --mode MASTER \
  --layout <PRODUCT_DIRECTORY>/reusable/layout.json \
  --target <candidate-id>
```

Capture the successful stdout and pass it verbatim to Image Gen.

## 4. Image Gen reference role — the experiment variable

For this Gate B1 test, send exactly:

```text
<PRODUCT_DIRECTORY>/reusable/palette-reference.png
```

as the sole palette reference image.

Do **not** send the authoritative product image to Image Gen.
Do **not** send Logo, title masks, version masks, final composites, or any previous SKU.

The structured prompt still requires an empty background plate only.

Each user generation instruction permits exactly one Image Gen operation. Never automatically retry or visually reject a background.

## 5. Local deterministic composite

After the generated background raster is delivered, run:

```text
python scripts/artifact_flow.py preview \
  --generated-background <generated-background> \
  --product <authoritative-product> \
  --product-dir <PRODUCT_DIRECTORY> \
  --candidate-id <candidate-id>
```

The authoritative product image is used here locally and remains the source of truth for the product pixels.

Show the full MASTER preview and stop for the user's decision.

## 6. Lock or redo

Only after explicit `锁定母版`:

```text
python scripts/artifact_flow.py bind \
  --product-dir <PRODUCT_DIRECTORY> \
  --candidate-id <candidate-id>
```

The locked MASTER's actual raster becomes its recorded raster contract.

Only after explicit `重做母版`, follow the normal deterministic discard/reject flow and perform one new Image Gen operation.

## Stop after Gate B1

After the MASTER is locked, stop.

Do not generate orange, white, or any other SKU with this package. Gate B2 requires a separate palette-only SKU test so that the MASTER result can be judged first without conflating variables.

Report the locked `ORIGINAL_MASTER_FINAL.png` to the user for A/B review against the Phase 2 structured MASTER.
