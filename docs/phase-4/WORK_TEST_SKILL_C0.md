---
name: md3-product-image
description: "Phase 4 C0 runtime probe for md3-product-image. Verify that ChatGPT Work can perform a genuine edit of the locked MASTER background using an SKU palette-only reference. This package must not silently fall back to normal image generation."
---

# MD3 Product Image — Phase 4 C0 Edit Probe

This package is only for the Phase 4 C0 runtime capability test. It must not create, replace, redo, or renumber production SKU outputs.

## Scope

Continue from the existing Phase 3 palette-only HUAWEI WATCH FIT 5 Pro Work state.

Require an already bound MASTER with:

```text
PRODUCT_DIRECTORY/reusable/master.json
PRODUCT_DIRECTORY/reusable/ORIGINAL_MASTER_BACKGROUND.png
```

Use `橙.png` as the C0 SKU palette source.

The purpose of C0 is to answer one question only:

> Can this real Work + Skill runtime invoke a distinct existing-image edit operation on `ORIGINAL_MASTER_BACKGROUND.png`?

## Invariant

C0 permits exactly one image-model operation.

That operation must be an **edit of the existing MASTER background**.

A normal generation call that merely receives the MASTER as a reference is not acceptable evidence.

If the available image surface cannot explicitly distinguish edit from generation, print/report:

```text
IMAGE_EDIT_INTERFACE_UNAVAILABLE
```

and stop before any image-model operation.

Do not use automatic fallback, retry, or regeneration.

## 1. Verify the bound MASTER

Use the existing product directory for the exact complete product name:

```text
HUAWEI WATCH FIT 5 Pro
```

Verify `reusable/master.json` and its hash-bound files using the repository helpers. The MASTER must already be bound.

Do not create a new MASTER.

## 2. Prepare the orange deterministic palette reference

Run:

```text
python scripts/palette_cache.py \
  --source <橙.png> \
  --product-dir <PRODUCT_DIRECTORY> \
  --role SKU
```

Capture the returned `palette_reference` path.

The complete orange product image is used only by this deterministic local palette extraction step. Do not send `橙.png` itself to the image model.

## 3. Use the exact C0 edit prompt

Read and use exactly:

```text
references/phase4-edit-probe.txt
```

Do not reconstruct, shorten, extend, or correct the prompt.

Reference roles are fixed:

```text
IMAGE_1 = PRODUCT_DIRECTORY/reusable/ORIGINAL_MASTER_BACKGROUND.png
IMAGE_2 = current orange palette_reference returned by palette_cache.py
```

## 4. Invoke genuine edit semantics

Invoke the runtime's distinct existing-image **edit** operation with IMAGE_1 as the editable target and IMAGE_2 as the supporting palette-only reference.

If the callable image interface exposes an explicit action/mode selector, set it to the edit value.

Do not invoke a generate/new-image action.
Do not treat IMAGE_1 merely as a composition reference for a new generation.
Do not use the complete orange product image as an image-model input.

Only perform the call if the operation is explicitly an edit based on the callable interface/tool invocation itself. Do not infer that an operation was an edit merely because the prompt says "edit".

If explicit edit semantics are unavailable, stop with `IMAGE_EDIT_INTERFACE_UNAVAILABLE`.

## 5. Persist only diagnostic evidence

After a successful edit operation, create:

```text
PRODUCT_DIRECTORY/phase4-probe/
```

Save the returned raw edited background as:

```text
PRODUCT_DIRECTORY/phase4-probe/orange-edited-background.png
```

Do not put anything in `PRODUCT_DIRECTORY/output/`.
Do not call `artifact_flow.py sku`.
Do not modify existing `SKU_VARIANT-A` or `SKU_VARIANT-B`.

## 6. Run deterministic structure diagnostics

Run:

```text
python scripts/compare_background_structure.py \
  --master <PRODUCT_DIRECTORY>/reusable/ORIGINAL_MASTER_BACKGROUND.png \
  --candidate <PRODUCT_DIRECTORY>/phase4-probe/orange-edited-background.png
```

The candidate must have exactly the same pixel dimensions as the MASTER or the diagnostic fails.

The returned edge metrics are diagnostic only. Do not automatically accept or reject the edit from these numbers.

## 7. Return evidence to the user

Return or expose all of the following:

1. `ORIGINAL_MASTER_BACKGROUND.png`
2. `phase4-probe/orange-edited-background.png`
3. the structure-diagnostic JSON output
4. the exact `phase4-edit-probe.txt` prompt used
5. explicit runtime/tool evidence identifying that the image operation was an edit, if such metadata is exposed

State one of exactly these runtime conclusions:

```text
EDIT_OPERATION_CONFIRMED
```

only when the actual callable operation was explicitly an edit, or:

```text
IMAGE_EDIT_INTERFACE_UNAVAILABLE
```

when no distinct edit operation can be invoked.

Do not claim `EDIT_OPERATION_CONFIRMED` from visual similarity alone.

## Stop after C0

Do not generate a final orange SKU and do not test white in this package.

C1/C2 visual SKU edit testing begins only after C0 evidence is reviewed outside Work.
