# Phase 3 — Palette Reference Ablation Results

Status: **COMPLETED / PALETTE-ONLY PROMOTED TO DEFAULT**

Date: 2026-09-09

## Decision

The deterministic color-only palette reference is accepted and promoted as the default Image Gen palette input on the `images-2.5-roadmap` branch.

The authoritative product artwork remains the source of truth for deterministic local product composition, but it is no longer sent to Image Gen merely to communicate color palette.

The Phase 2 full-product-reference path remains documented as the A baseline and may be retained only for regression/fallback comparison.

## Controlled Work A/B

The same HUAWEI WATCH FIT 5 Pro authority inputs were used throughout:

- MASTER: `黑.png`
- SKU A: `橙.png`
- SKU B: `白.png`
- Logo: `HUAWEI-LOGO.png`
- title line 1: `HUAWEI`
- title line 2: `WATCH FIT 5 Pro`
- version: `Глобальная версия`

The structured Phase 2 prompt and deterministic local composition rules were unchanged. The generation-variable difference was only the palette reference:

- **A — Phase 2 baseline:** complete product image sent to Image Gen as palette reference.
- **B — Phase 3:** deterministic `palette-reference.png` containing color bands only.

## Gate B1 — Palette-only MASTER

`ORIGINAL_MASTER_FINAL.png`

- result: PASS
- actual raster: `1086 × 1448`
- aspect ratio: `3:4`
- mode: `RGBA`
- alpha: fully opaque
- SHA-256: `3debf82941e63cc6ab78108f659e65aef975915e8365e2f0f32ebf6622847c4c`
- background quality: 4/5
- Classic MD3 adherence: 4/5
- palette harmony: 5/5
- safe-zone cleanliness: 5/5

Compared with Phase 2 A, the palette-only MASTER is darker and more blue-gray with stronger sweeping geometry. Phase 2 A is visually quieter, but the B result did not materially regress quality and showed very strong harmony with the black product.

No product copying, product-like copied geometry, accidental generated Logo/text, or physical table/floor/display-stand environment was observed.

## Gate B2-A — Orange SKU

- result: PASS
- reviewed raster: `1086 × 1448`
- shared review file mode: `RGB`
- shared review file format: JPEG
- shared review file SHA-256: `81e936300a5d8da3d14d9f7d52ec4c04096ed5db62fdbdc131b08d7e79bd3d6e`
- background quality: 5/5
- Classic MD3 adherence: 4/5
- palette harmony: 5/5
- safe-zone cleanliness: 5/5
- SKU composition consistency: 5/5

The locked B1 composition remained recognizable while the palette moved cleanly to warm cream / apricot / orange. Product position and scale remained stable, and no semantic/product-geometry leakage was observed.

Because the user-provided review copy was JPEG, the SHA above identifies the reviewed evidence file rather than claiming identity with the Work output PNG.

## Gate B2-B — White SKU

- result: PASS
- actual raster: `1086 × 1448`
- aspect ratio: `3:4`
- mode: `RGBA`
- alpha: fully opaque
- SHA-256: `1bb8269afa96c6de2e8f9591825d82ac828d1f1ade686a49dca2c76bbad4beee`
- background quality: 5/5
- Classic MD3 adherence: 4/5
- palette harmony: 5/5
- safe-zone cleanliness: 5/5
- SKU composition consistency: 5/5

The palette returned naturally to cool white / light blue while preserving the B1 composition family. The white product remained visually separated by its display, edge contrast, and deterministic local shadow.

No product copying, generated branding/text contamination, or unexpected physical environment was observed.

## A/B conclusion

Palette-only passes the complete MASTER + SKU path.

Observed advantages:

1. Image Gen no longer receives the authoritative product silhouette, screen, strap, hardware geometry, labels, or other product semantics when only palette information is needed.
2. Palette harmony remained excellent for black, orange, and white.
3. Background quality remained acceptable or excellent.
4. Safe-zone behavior remained stable.
5. SKU composition consistency remained excellent.
6. Deterministic local product/Logo/text/shadow composition was unchanged.

Observed trade-off:

- the black MASTER became somewhat darker and visually heavier than the Phase 2 full-product-reference MASTER.

This trade-off was judged non-material relative to the architectural benefit of eliminating an unnecessary semantic product-reference channel.

## Adoption decision

```text
Gate B1 MASTER: PASS
Gate B2-A orange SKU: PASS
Gate B2-B white SKU: PASS
Palette quality regression: NO MATERIAL REGRESSION
Background quality regression: NO MATERIAL REGRESSION
Semantic product-reference exposure: REDUCED BY DESIGN
Palette-only reference: PROMOTE TO DEFAULT
Full-product palette reference: KEEP AS ABLATION BASELINE / FALLBACK ONLY
```

## Production contract after Phase 3

For MASTER generation:

```text
authoritative product
  -> deterministic local palette extraction
  -> reusable/palette.json
  -> reusable/palette-reference.png
  -> Image Gen sees palette-reference.png only

authoritative product
  -> deterministic local product composition only
```

For SKU generation under the current regeneration path:

```text
current SKU product
  -> deterministic local palette extraction
  -> SKU palette-reference.png

Image Gen sees:
  ORIGINAL_MASTER_BACKGROUND.png  (composition reference)
  + SKU palette-reference.png      (palette reference only)

current SKU product
  -> deterministic local product composition only
```

Phase 3 is complete. The next phase is Phase 4: verify whether the real Work/Skill runtime exposes sufficiently constrained image-edit semantics before replacing the current master-reference regeneration path.
