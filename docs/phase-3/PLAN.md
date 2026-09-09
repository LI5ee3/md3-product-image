# Phase 3 — Deterministic Palette Reference Ablation

Status: **COMPLETED / SEE `RESULTS.md`**

Date: 2026-09-09

## Objective

Determine whether Images 2.5 should continue receiving complete product artwork when only palette transfer is required, or whether a deterministic color-only reference can preserve palette quality while reducing product-semantic exposure.

## Fixed authority inputs

Use only the project Google Drive source set:

- MASTER: `黑.png`
- SKU A: `橙.png`
- SKU B: `白.png`
- Logo: `HUAWEI-LOGO.png`
- complete product name: `HUAWEI WATCH FIT 5 Pro`
- title line 1: `HUAWEI`
- title line 2: `WATCH FIT 5 Pro`
- version: `Глобальная версия`

The Phase 2 structured-prompt Work outputs were the A baseline.

## Extraction policy tested

`scripts/extract_palette.py` uses a deterministic local policy:

- 7 representative colors,
- nearest-neighbor source sampling, max edge 512,
- alpha threshold 32,
- 5-bit/channel RGB histogram,
- 4 dominant slots plus saturation-aware accent candidates,
- all visible histogram bins reassigned to the nearest selected representative,
- full visible-pixel coverage determines color-band widths,
- 1024 × 256 RGB palette-reference PNG,
- no text, Logo, product silhouette, label, icon, packaging, or hardware geometry.

The initial selected-bin-only weighting was rejected before visual A/B because it over-emphasized a dark screen bin in the orange source. The corrected full-coverage weighting was the version evaluated in Work.

## Ablation groups

### A — Full product reference

Image Gen received the complete authoritative product image as a palette reference.

### B — Palette-only reference

Image Gen received only deterministic `palette-reference.png`. The authoritative product artwork remained available only to deterministic local composition.

## Execution protocol

### Gate B1 — MASTER

- fresh Work test,
- same structured prompt,
- black source used locally for product composition,
- only black palette reference sent to Image Gen,
- one Image Gen operation,
- no automatic retry or correction,
- first acceptable candidate locked for comparison.

### Gate B2 — SKU

After B1 passed:

- orange: locked master background + orange palette reference,
- white: locked master background + white palette reference,
- original orange/white product images local only,
- one image-model operation per SKU,
- no automatic retry.

## Evaluation metrics

- background quality,
- Classic MD3 adherence,
- palette harmony,
- safe-zone cleanliness,
- SKU composition consistency,
- unwanted product copying,
- product-like geometry,
- accidental text / Logo / labels,
- unexpected physical environment.

## Adoption rule

Palette-only would be accepted only if palette/background quality did not materially regress, local deterministic composition remained unchanged, semantic/product-geometry leakage risk was no worse, and both tested SKUs remained acceptable.

## Outcome

All three B outputs passed:

- black MASTER: PASS,
- orange SKU: PASS,
- white SKU: PASS.

The palette-only path was promoted to the branch default. Full evidence, SHA values, scores, trade-offs, and the production decision are recorded in `docs/phase-3/RESULTS.md`.
