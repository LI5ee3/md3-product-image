# HUAWEI WATCH FIT 5 Pro — Black MASTER Baseline

Status: **VALID / LOCKED**

Date: 2026-09-09

## Authority

This baseline was produced by the real `md3-product-image v2.0` Skill in ChatGPT Work using the Phase 0 authority set:

- MASTER product: `黑.png`
- Logo: `HUAWEI-LOGO.png`
- complete product name: `HUAWEI WATCH FIT 5 Pro`
- `TITLE_LINES`: `2`
- title line 1: `HUAWEI`
- title line 2: `WATCH FIT 5 Pro`
- version: `Глобальная версия`

The user explicitly locked `MASTER-1`, after which Work produced `ORIGINAL_MASTER_FINAL.png`.

## Frozen prompt

Prompt SHA-256:

`12148360c40fe556ee8304c68a3914aa69e380d9fd75863b29809eac6a01a773`

## Delivered final artifact

The supplied locked final PNG was inspected directly:

- format: PNG
- mode: RGBA
- actual raster: `1086 × 1448`
- aspect ratio: exact `3:4`
- alpha: fully opaque (`255..255`)
- final composite SHA-256: `083d625d2a039ca565fbaf548c55e58714c6770601b1fcb1141f5360201f286f`

The Work UI reported `1536 × 2048 (3:4)`, so this baseline records a real UI/logical-canvas versus delivered-raster mismatch. See `docs/phase-0/NATIVE_SIZE_VALIDATION.md`.

The standalone generated background file was not supplied, so `generated_background_sha256` remains intentionally empty.

## Visual evaluation

Scale: positive metrics `1–5`; negative-event metrics use the current Phase 0 convention where `1` means none observed and `5` means severe.

| Metric | Score | Rationale |
| --- | ---: | --- |
| background quality | 4 | coherent, smooth, polished soft-surface composition with restrained depth |
| Classic MD3 adherence | 4 | rounded soft panels/discs and restrained elevation fit the intended Classic MD3/neumorphic direction; slightly more volumetric than a strict flat MD3 interpretation |
| palette harmony | 4 | cool blue/white macaron background complements the black/steel watch and blue watch face without literal dark background colors |
| safe-zone cleanliness | 5 | upper-left information area remains calm and visually clear; dominant geometry is pushed toward the right/lower regions |
| SKU composition consistency | N/A | MASTER row |
| unwanted product copying | 1 | no second/copied product visible in the final composite |
| product-like geometry | 1 | background shapes remain abstract and do not resemble a second watch/product |
| accidental text or Logo | 1 | only the intended locally composited HUAWEI Logo/title/version are visible; no duplicate branding or generated text is visible |
| unexpected physical environment | 1 | background reads as abstract soft UI geometry rather than a table, studio, pedestal, or realistic environment |

## Baseline decision

This locked black MASTER is accepted as the Phase 0 production visual baseline for subsequent SKU and Images 2.5 comparisons.

It is not an argument that the current design is optimal. Its purpose is to provide a fixed, real production reference against which later changes can be measured.

## Next comparison

Generate the orange SKU using the already locked black MASTER and the unchanged v2.0 SKU path. Inspect the delivered SKU raster directly and compare:

- background geometry / composition drift,
- palette adaptation,
- safe-zone behavior,
- accidental product/text/logo generation,
- delivered raster dimensions.

Then repeat for the white SKU.
