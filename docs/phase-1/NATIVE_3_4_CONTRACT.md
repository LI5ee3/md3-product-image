# Phase 1 — Native 3:4 Raster Contract

Status: **IMPLEMENTATION VALIDATED**

Date: 2026-09-09

## Decision

Phase 1 does not force the downloadable raster to `1536×2048`.

Real ChatGPT Work production evidence shows that the v2.0 Skill reports a logical `1536×2048` canvas while the downloaded MASTER and both tested SKU files are all `1086×1448`.

The existing repository already treats these as two separate concepts:

- `1536×2048` is the deterministic logical layout canvas used by `measure_text.py`;
- the generated background's actual exact-3:4 raster becomes the local composition canvas;
- normalized Logo/text rectangles scale to that actual raster.

The correct Phase 1 invariant is therefore:

> The locked MASTER background's actual width and height define the delivery raster contract for every later SKU of that product.

## New validator

Added:

`scripts/validate_raster.py`

### MASTER validation

```text
python scripts/validate_raster.py master \
  --generated-background <background.png>
```

Requirements:

- source exists and is readable;
- width and height are positive;
- raster is exactly 3:4.

The validator reports the actual raster rather than trusting UI text.

### SKU validation

```text
python scripts/validate_raster.py sku \
  --master-background <reusable/ORIGINAL_MASTER_BACKGROUND.png> \
  --generated-background <sku-background.png>
```

Requirements:

- both files are readable exact-3:4 rasters;
- SKU width must equal locked MASTER width;
- SKU height must equal locked MASTER height.

A same-ratio but different-size output fails with:

```text
SKU_BACKGROUND_SIZE_MISMATCH
```

No image-generation retry is implied or triggered by this validator.

## Regression test

Added:

`scripts/test_raster_contract.py`

The self-check verifies:

- valid MASTER 3:4 raster passes;
- same-size SKU passes;
- same-ratio but different-size SKU fails;
- non-3:4 MASTER fails;
- non-3:4 SKU fails.

GitHub Actions workflow:

`.github/workflows/phase1-raster-contract.yml`

Run ID:

`34339575613`

Result: **PASS**

The workflow also runs the pre-existing `scripts/test_workflow.py` deterministic baseline in the same job. Both tests passed.

## Real baseline evidence

The HUAWEI production outputs that motivated this contract are:

| Artifact | Actual raster |
| --- | --- |
| black locked MASTER | `1086×1448` |
| orange SKU_VARIANT-A | `1086×1448` |
| white SKU_VARIANT-B | `1086×1448` |

This is three independent real production outputs at the same raster.

## Production integration policy

During the upgrade branch, the validator is kept as an explicit deterministic primitive. The final public `SKILL.md` wiring is updated only after the later visual phases are accepted, as required by Phase 8.

The final workflow must place raster validation immediately after each image-model delivery and before local composition.

## Acceptance result

Phase 1 acceptance is satisfied at the deterministic implementation level:

- logical layout remains stable;
- actual raster is measured explicitly;
- mixed MASTER/SKU resolutions can be rejected deterministically;
- no implicit crop or rescale is introduced;
- existing deterministic workflow tests still pass;
- wrong-size SKU output does not justify an automatic image-generation retry.
