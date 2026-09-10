# Phase 2 — Structured Prompt Results

Status: **COMPLETED / PROMOTED TO DEFAULT**

Date: 2026-09-09

## Decision

The structured master prompt is promoted to the default prompt on the `images-2.5-roadmap` branch.

The v2.0 prompt remains preserved at:

```text
references/image-gen-prompt-v2-baseline.txt
```

It is retained only for regression, ablation, and fallback comparison. It is not the preferred default prompt.

## Controlled Work A/B

The comparison used the same authoritative Google Drive source set and the same product copy:

- MASTER product: `黑.png`
- SKU A: `橙.png`
- SKU B: `白.png`
- Logo: `HUAWEI-LOGO.png`
- complete product name: `HUAWEI WATCH FIT 5 Pro`
- title line 1: `HUAWEI`
- title line 2: `WATCH FIT 5 Pro`
- version: `Глобальная версия`

The v2.0 production run was used as the baseline. The Phase 2 Work test package changed the active background prompt to the structured candidate while keeping the local deterministic composition architecture unchanged.

## Structured prompt contract

The promoted prompt uses explicit sections:

1. `DELIVERABLE`
2. `REFERENCE ROLES`
3. `VISUAL SYSTEM`
4. `PALETTE`
5. `COMPOSITION`
6. `LIGHTING`
7. `EXCLUSIONS`
8. `OUTPUT CONTRACT`

The measured `FINAL_INFORMATION_SAFE_ZONE` and canonical product/shadow placement policy continue to be appended deterministically by `scene_prompt.py`.

## Real Work outputs

### Structured black MASTER

- result: PASS
- actual PNG raster: `1086 × 1448`
- mode: `RGBA`
- alpha: fully opaque
- final SHA-256: `372fd70aad99b4812ce026b37f4c3a051db253522872e70c9cee617d4ade9a4f`
- background quality: 5/5
- Classic MD3 adherence: 4/5
- palette harmony: 4/5
- safe-zone cleanliness: 5/5

Observed advantage over v2.0: the background is more restrained and behaves more like a reusable background system instead of a more decorative one-off scene.

### Structured orange SKU

- result: PASS
- actual PNG raster: `1086 × 1448`
- mode: `RGBA`
- alpha: fully opaque
- final SHA-256: `cc948573309fd750eca3fff050c56d1eeeded87f3a6fc0225d800ea63fe0f091`
- background quality: 5/5
- Classic MD3 adherence: 4/5
- palette harmony: 5/5
- safe-zone cleanliness: 5/5
- SKU composition consistency: 5/5

The locked master geometry remained recognizable while the palette moved cleanly into warm cream / apricot / orange tones. No visible product-copying or extra text/Logo contamination was observed.

### Structured white SKU

- result: PASS
- actual PNG raster: `1086 × 1448`
- mode: `RGBA`
- alpha: fully opaque
- final SHA-256: `172d48ef27136c43727e81e1ee0c910d6bfaed20960c784544f57bb6ba3ee19e`
- background quality: 5/5
- Classic MD3 adherence: 4/5
- palette harmony: 4/5
- safe-zone cleanliness: 5/5
- SKU composition consistency: 5/5

The white product remains readable against the pale blue/white background through local product edges, display contrast, and deterministic shadowing. The background remains quieter than the v2.0 white-SKU baseline.

## Negative checks

Across all three structured outputs:

- unwanted product copying: not observed
- product-like copied geometry: not observed
- accidental generated Logo/text: not observed in the background contract
- physical table/floor/display-stand scene: not observed
- safe-zone intrusion: not observed at a visually significant level

## A/B conclusion

Compared with the v2.0 baseline, the structured prompt is preferred because it produced:

1. a quieter and more reusable master background,
2. stronger information-safe-zone behavior,
3. cleaner SKU palette migration,
4. very high SKU composition consistency in both tested variants,
5. no regression in deterministic local product/Logo/text/shadow composition.

## Promotion decision

```text
Phase 2: PASS
Structured Prompt: PROMOTE TO DEFAULT
v2.0 Prompt: KEEP AS BASELINE / FALLBACK
MASTER visual result: PASS
Orange SKU visual result: PASS
White SKU visual result: PASS
```

Phase 2 is complete. The next visual ablation is Phase 3: full-product palette reference versus deterministic palette-only reference.
