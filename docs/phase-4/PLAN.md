# Phase 4 — Constrained SKU Background Edit

Status: **COMPLETED / NOT ADOPTED**

Date: 2026-09-09

## Objective

Determine whether the real ChatGPT Work + Skill runtime can invoke a genuine existing-image edit for SKU palette changes, instead of regenerating a new background while using the locked MASTER only as a composition reference.

No production SKU behavior was allowed to change until this runtime gate passed.

## Public capability evidence

Current OpenAI Images 2.5 documentation confirms that image editing exists in both ChatGPT Images and the API. In the Responses API image-generation tool, `action: "edit"` can force editing when an image is in context.

This does not prove that the Work Skill surface exposes the same explicit control. Phase 4 therefore tested the actual Work runtime instead of assuming API parity.

## Authority state

The Phase 4 probe continued from the accepted Phase 3 palette-only product state:

- product: `HUAWEI WATCH FIT 5 Pro`
- locked palette-only MASTER: Gate B1 PASS
- orange palette-only regeneration baseline: Gate B2-A PASS
- white palette-only regeneration baseline: Gate B2-B PASS
- actual observed MASTER/SKU raster family: `1086 × 1448`

## C0 — Edit-interface proof

C0 tested whether one orange palette change could be executed through a distinct existing-image edit operation without creating or replacing a production SKU output.

### Inputs

1. `ORIGINAL_MASTER_BACKGROUND.png` — intended editable target
2. deterministic orange SKU `palette-reference.png` — color-only supporting reference
3. `references/phase4-edit-probe.txt` — exact edit contract

The complete orange product artwork remained local and was not sent to the image model.

### Required runtime behavior

The Work agent was required to invoke a distinct existing-image edit operation.

If the callable image surface exposed an explicit action/mode selector, it had to use the edit value.

If Work could not distinguish an edit operation from normal generation/reference-image generation, it had to stop with:

```text
IMAGE_EDIT_INTERFACE_UNAVAILABLE
```

It was forbidden to silently substitute the Phase 3 regeneration path.

### C0 result

The real Work + Skill probe returned:

```text
IMAGE_EDIT_INTERFACE_UNAVAILABLE
```

The callable Image Gen surface exposed ordinary generation capability but no explicit existing-image edit operation or equivalent verifiable edit selector.

Per contract, the probe stopped before any image-model operation.

No production SKU or MASTER file was generated, modified, or replaced.

## C1 / C2 — Not executed

C1 orange edit and C2 white edit were not run because C0 did not prove genuine edit semantics.

Running visual ablations without a verified edit operation would not distinguish constrained editing from ordinary regeneration and therefore would not be valid evidence.

## Decision rule outcome

The Phase 4 adoption criteria were not met because requirement 1 failed:

1. real Work edit semantics demonstrated rather than inferred — **FAIL**
2. orange and white edits visually acceptable — **NOT TESTED**
3. composition drift materially lower than Phase 3 regeneration — **NOT TESTED**
4. no deterministic contract regression — **PASS / unchanged**
5. one user generation instruction causes only one image-model operation — **PASS / zero model operations after gate failure**

Decision:

```text
Adopt constrained SKU edit: NO
Retain Phase 3 regeneration path: YES
```

## Production status after Phase 4

The accepted production path remains:

```text
MASTER:
  palette-reference.png -> Image Gen background generation

SKU:
  ORIGINAL_MASTER_BACKGROUND.png + SKU palette-reference.png
  -> Image Gen background regeneration with master composition reference
```

The authoritative product artwork remains local and is not sent to Image Gen for palette transfer.

## Reopen condition

Phase 4 may be reopened only if the Work/Skill runtime later exposes an explicit edit operation or equivalent edit semantics that can be verified directly.

Detailed result evidence is recorded in `docs/phase-4/RESULTS.md`.
