---
name: md3-product-image
description: "Phase 3 Gate B2 SKU ablation for md3-product-image. Continue from a locked palette-only MASTER and send only the locked master background plus a deterministic SKU palette-reference image to Image Gen; keep the authoritative SKU product image local for deterministic composition."
---

# MD3 Product Image — Phase 3 Palette-Only SKU Test

This package exists only for Phase 3 Gate B2. It is not the production Skill.

## Gate prerequisite

Continue from the same product directory in which Phase 3 Gate B1 locked the palette-only MASTER.

Require all of the following to exist and verify successfully:

- `reusable/master.json`
- `reusable/ORIGINAL_MASTER_BACKGROUND.png`
- `output/ORIGINAL_MASTER_FINAL.png`
- the original layout and information assets

Do not create a new MASTER with this package.

The Gate B2 fixed order is:

1. `橙.png` -> `SKU_VARIANT-A`
2. `白.png` -> `SKU_VARIANT-B`

Do not change this order for the controlled experiment.

## Experiment rule

Relative to the Phase 2 structured SKU baseline, change only the palette-reference representation.

Phase 2 A SKU Image Gen inputs:

- locked master background as composition reference
- complete current SKU product image as palette reference

Phase 3 B2 SKU Image Gen inputs:

- locked palette-only master background as composition reference
- deterministic current-SKU `palette-reference.png` as palette reference

The complete current SKU product image must not be sent to Image Gen. It remains authoritative only for local deterministic product composition.

## For each SKU

### 1. Extract deterministic palette

For orange:

```text
python scripts/extract_palette.py \
  --source <橙.png> \
  --json-output <PRODUCT_DIRECTORY>/reusable/SKU_VARIANT-A-palette.json \
  --reference-output <PRODUCT_DIRECTORY>/reusable/SKU_VARIANT-A-palette-reference.png
```

For white:

```text
python scripts/extract_palette.py \
  --source <白.png> \
  --json-output <PRODUCT_DIRECTORY>/reusable/SKU_VARIANT-B-palette.json \
  --reference-output <PRODUCT_DIRECTORY>/reusable/SKU_VARIANT-B-palette-reference.png
```

If the corresponding palette assets already exist, verify the recorded source SHA rather than silently replacing them.

### 2. Build the normal SKU prompt

```text
python scripts/scene_prompt.py build \
  --mode SKU \
  --layout <PRODUCT_DIRECTORY>/reusable/layout.json \
  --master <PRODUCT_DIRECTORY>/reusable/master.json
```

Capture successful stdout and pass it verbatim to Image Gen.

Do not reconstruct or paraphrase the generated prompt.

### 3. Send exactly two reference images to Image Gen

Reference 1:

```text
<PRODUCT_DIRECTORY>/reusable/ORIGINAL_MASTER_BACKGROUND.png
```

Role: authoritative composition reference.

Reference 2:

```text
<PRODUCT_DIRECTORY>/reusable/<SKU_VARIANT-X>-palette-reference.png
```

Role: palette reference only.

Do not send:

- the complete current SKU product image
- Logo
- title/version masks
- final composites
- any other SKU

Image Gen creates only the empty SKU background plate.

Each user generation instruction permits exactly one Image Gen operation. Never automatically retry or visually reject a background.

### 4. Local deterministic composition

After Image Gen returns an accessible raster, run:

```text
python scripts/artifact_flow.py sku \
  --generated-background <background> \
  --product <current-authoritative-SKU-product> \
  --product-dir <PRODUCT_DIRECTORY>
```

The authoritative SKU image is used here locally and must remain the exact source for product pixels.

The generated SKU background must match the locked MASTER raster exactly. A mismatch is a deterministic failure and must not trigger another Image Gen operation.

### 5. Return final SKU

On deterministic success, return the final `output/SKU_VARIANT-X.png` directly.

Do not ask the user to approve a successful SKU; Gate B2 follows the normal automatic SKU finalization behavior.

## Stop condition

After both `SKU_VARIANT-A` and `SKU_VARIANT-B` are generated, stop.

Return both final files for comparison against the Phase 2 structured SKU baseline.
