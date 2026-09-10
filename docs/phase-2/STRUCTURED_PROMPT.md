# Phase 2 — Structured Master Prompt

Status: **DETERMINISTIC VALIDATION PASS / REAL WORK A-B PENDING**

Date: 2026-09-09

## Goal

Evaluate whether a structured Images 2.5 prompt improves MASTER background instruction following without changing the existing Classic MD3 visual direction or deterministic local-composition architecture.

## Official guidance applied

The candidate follows the current GPT Image 2.5 prompting guidance:

- organize complex requests with labeled sections;
- explicitly assign roles to reference images;
- separate desired output from constraints and exclusions;
- state unwanted text, logos, watermarks, and copied geometry explicitly.

## Baseline preservation

The original v2.0 prompt is preserved at:

`references/image-gen-prompt-v2-baseline.txt`

The active upgrade-branch candidate is:

`references/image-gen-prompt.txt`

No baseline prompt text was discarded.

## Structured candidate sections

The candidate contains these ordered sections:

1. `DELIVERABLE`
2. `REFERENCE ROLES`
3. `VISUAL SYSTEM`
4. `PALETTE`
5. `COMPOSITION`
6. `LIGHTING`
7. `EXCLUSIONS`
8. `OUTPUT CONTRACT`

The existing measured information-safe-zone block is still appended deterministically by `scene_prompt.py`.

## Semantic invariants preserved

The candidate keeps the existing visual/product contract:

- portrait 3:4 background plate;
- Google Material Design 3 Classic, not M3 Expressive;
- refined neumorphic soft UI;
- light macaron palette derived from the supplied product palette;
- minimal rounded panels, capsules, discs, and soft elevation;
- bright high-key diffused lighting;
- no generated product;
- no generated product shadow;
- no generated Logo or text;
- no physical floor, table, stand, studio set, or realistic environment;
- product / Logo / typography / fixed shadow remain local deterministic composition responsibilities.

## Reference-role change in wording

The new prompt names the supplied product explicitly as:

`PRODUCT_REFERENCE: authoritative palette reference only.`

It also explicitly forbids transferring product silhouette, hardware geometry, screen contents, strap shape, packaging, labels, icons, branding, or other recognizable object details into the background.

This is a prompt-clarity change only. Phase 3 will separately test replacing the full product reference with a deterministic palette-only image.

## Deterministic tests

Added:

`scripts/test_prompt_structure.py`

The test verifies:

- all structured sections exist exactly once and in the intended order;
- `PRODUCT_REFERENCE` has an explicit palette-only role;
- product-copy exclusions exist;
- empty-background output contract exists;
- Classic MD3 remains explicit;
- the v2.0 baseline copy remains different and intact.

GitHub Actions workflow:

`.github/workflows/phase2-structured-prompt.yml`

Run ID:

`34339804934`

Result: **PASS**

The same CI job also reran `scripts/test_workflow.py`; the pre-existing deterministic workflow remains **PASS**.

## Work A/B test package

A production-like test ZIP is built by:

`.github/workflows/phase2-work-test-package.yml`

Run ID:

`34339913364`

Artifact:

`md3-product-image-phase2-structured`

Artifact ID:

`10099278893`

The package intentionally excludes docs, CI, Phase 0 harnesses, test scripts, and the new Phase 1 validator. It contains the same production runtime components as the v2.0 baseline package, with the structured `references/image-gen-prompt.txt` as the tested variable.

## Required real Work A/B protocol

Use a fresh ChatGPT Work conversation/environment so no previously bound product directory is reused.

Use exactly the same authoritative Phase 0 input set:

- product: `黑.png`
- Logo: `HUAWEI-LOGO.png`
- complete product name: `HUAWEI WATCH FIT 5 Pro`
- title lines: `2`
- line 1: `HUAWEI`
- line 2: `WATCH FIT 5 Pro`
- version: `Глобальная версия`

Rules:

1. Install the Phase 2 structured test ZIP, not v2.0.
2. Generate exactly one MASTER candidate.
3. Do not request a redo or add any correction text.
4. Lock that first candidate only to obtain the exact final PNG; the lock is for test capture and does not mean the candidate is preferred.
5. Export/upload `ORIGINAL_MASTER_FINAL.png` for direct raster and visual inspection.
6. Do not generate SKU variants until the MASTER A/B result has been scored.

## Comparison metrics

Compare the Phase 2 MASTER directly against the locked v2.0 black MASTER baseline:

- background quality;
- Classic MD3 adherence;
- palette harmony;
- information-safe-zone cleanliness;
- unwanted product copying;
- product-like geometry;
- accidental text or Logo;
- unexpected physical environment;
- actual downloaded raster dimensions.

The structured prompt is accepted only if it is at least equivalent on the baseline strengths and materially improves instruction clarity or failure resistance. One prettier image alone is not sufficient evidence for later workflow replacement.
