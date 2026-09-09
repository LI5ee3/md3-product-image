# Phase 4 — Constrained SKU Background Edit

Status: **IN PROGRESS / C0 RUNTIME PROBE NEXT**

Date: 2026-09-09

## Objective

Determine whether the real ChatGPT Work + Skill runtime can invoke a genuine existing-image edit for SKU palette changes, instead of regenerating a new background while using the locked MASTER only as a composition reference.

No production SKU behavior changes until this runtime gate passes.

## Public capability evidence

Current OpenAI Images 2.5 documentation confirms that image editing exists in both ChatGPT Images and the API. In the Responses API image-generation tool, `action: "edit"` can force editing when an image is in context.

This does not prove that the Work Skill surface exposes the same explicit control. Phase 4 therefore tests the actual Work runtime instead of assuming API parity.

## Authority state

Continue from the accepted Phase 3 palette-only product state:

- product: `HUAWEI WATCH FIT 5 Pro`
- locked palette-only MASTER: Gate B1 PASS
- orange palette-only regeneration baseline: Gate B2-A PASS
- white palette-only regeneration baseline: Gate B2-B PASS
- actual observed MASTER/SKU raster family: `1086 × 1448`

## C0 — Edit-interface proof

C0 tests one orange palette edit and does not create or replace a production SKU output.

### Inputs

1. `ORIGINAL_MASTER_BACKGROUND.png` — editable target
2. deterministic orange SKU `palette-reference.png` — color-only supporting reference
3. `references/phase4-edit-probe.txt` — exact edit contract

The complete orange product artwork remains local and must not be sent to the image model.

### Required runtime behavior

The Work agent must invoke a distinct existing-image edit operation.

If the callable image surface exposes an explicit action/mode selector, use the edit value.

If Work cannot distinguish an edit operation from normal generation/reference-image generation, stop with:

```text
IMAGE_EDIT_INTERFACE_UNAVAILABLE
```

Do not silently substitute the Phase 3 regeneration path.

### C0 output

Return for review:

- original `ORIGINAL_MASTER_BACKGROUND.png`,
- raw edited orange background,
- the exact edit prompt used,
- any runtime/tool metadata that explicitly identifies the operation as edit, if exposed,
- diagnostic structure metrics from `scripts/compare_background_structure.py`.

The structure metric is evidence only. It must never auto-accept or auto-reject visual quality.

## C1 / C2 — Visual SKU edit ablation

Run only if C0 proves genuine edit semantics.

### C1

Orange SKU using the edit path.

### C2

White SKU using the edit path.

Compare against the accepted Phase 3 regeneration outputs on:

- composition drift,
- palette harmony,
- background quality,
- safe-zone cleanliness,
- unwanted geometry changes,
- accidental generated objects/text/Logo,
- actual raster consistency.

## Decision rule

Adopt constrained edit only if:

1. real Work edit semantics are demonstrated rather than inferred,
2. orange and white edits both remain visually acceptable,
3. composition drift is materially lower than the Phase 3 regeneration path,
4. no deterministic contract regresses,
5. one user generation instruction still causes only one image-model operation.

Otherwise retain the accepted Phase 3 regeneration path.

## Production status during Phase 4

Current production candidate remains:

```text
MASTER:
  palette-reference.png -> Image Gen background generation

SKU:
  ORIGINAL_MASTER_BACKGROUND.png + SKU palette-reference.png
  -> Image Gen background regeneration with master composition reference
```

Phase 4 is an ablation only until all gates pass.
