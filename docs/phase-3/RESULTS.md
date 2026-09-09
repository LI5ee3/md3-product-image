# Phase 3 — Palette Reference Ablation Results

Status: **GATE B1 PASS / GATE B2 PENDING**

Date: 2026-09-09

## Gate B1 — Palette-only MASTER

The Phase 3 MASTER-only Work package was executed with the same authoritative HUAWEI WATCH FIT 5 Pro inputs used in Phase 2.

The only intended generation-variable change was:

- Phase 2 A: Image Gen received the complete black product image as palette reference.
- Phase 3 B1: Image Gen received only the deterministic black `palette-reference.png`.

The authoritative black product image remained local and was used only for deterministic product composition.

## Delivered result

`ORIGINAL_MASTER_FINAL.png`

- result: PASS
- actual raster: `1086 × 1448`
- aspect ratio: `3:4`
- mode: `RGBA`
- alpha: fully opaque
- SHA-256: `3debf82941e63cc6ab78108f659e65aef975915e8365e2f0f32ebf6622847c4c`

## Visual review

Scores:

- background quality: 4/5
- Classic MD3 adherence: 4/5
- palette harmony: 5/5
- safe-zone cleanliness: 5/5
- unwanted product copying: not observed
- product-like copied geometry: not observed
- accidental generated text / Logo: not observed in the background contract
- physical table / floor / display stand: not observed

## Comparison with Phase 2 A

The palette-only MASTER did not materially regress visual quality and therefore passes Gate B1.

Observed trade-off:

- Phase 2 A is visually quieter and more restrained.
- Phase 3 B1 is darker, more blue-gray, and visually heavier, with stronger sweeping geometry.
- Phase 3 B1 has very strong palette harmony with the black product.
- The information safe zone remains clean.
- No visible semantic/product-geometry leakage was introduced.

This is not yet sufficient to promote palette-only reference as the default. The goal of Phase 3 is to validate the complete MASTER + SKU path, not one MASTER sample.

## Decision

```text
Gate B1 MASTER: PASS
Palette-only quality regression: NO MATERIAL REGRESSION
Promote palette-only to production default: NOT YET
Proceed to Gate B2 SKU: YES
```

## Gate B2

Next test:

1. continue from the locked palette-only MASTER,
2. orange SKU: locked master background + orange palette-reference only,
3. white SKU: locked master background + white palette-reference only,
4. original orange/white product images remain local-composition inputs only,
5. one Image Gen operation per SKU,
6. no automatic retry or corrective prompt.

Phase 3 will be accepted or rejected only after both SKU results are reviewed against the Phase 2 A baseline.
