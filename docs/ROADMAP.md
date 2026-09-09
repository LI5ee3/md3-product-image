# ROADMAP

## Purpose

This roadmap defines the Images 2.5 upgrade path for `md3-product-image` while preserving its deterministic architecture.

The architectural rule remains fixed:

> Image generation is responsible only for the visual background layer. Product artwork, Logo, title/version text, product placement, fixed 2D shadow, file identity, master binding, SKU naming, and final composition remain deterministic and locally controlled.

The upgrade is an evolution of the current workflow, not a rewrite.

---

# Current status

| Phase | Status | Decision |
| --- | --- | --- |
| Phase 0 — Baseline and runtime verification | **COMPLETED** | Real Work baseline established with HUAWEI WATCH FIT 5 Pro |
| Phase 1 — Production raster contract | **COMPLETED** | Logical 1536×2048 layout retained; locked MASTER actual raster becomes SKU hard contract |
| Phase 2 — Structured prompt | **COMPLETED** | Structured prompt promoted to default; v2.0 prompt retained as baseline/fallback |
| Phase 3 — Deterministic palette-reference ablation | **IN PROGRESS** | Extractor implemented and deterministic; real Work A/B pending |
| Phase 4 — Constrained SKU image edit | **PLANNED / RUNTIME-GATED** | Do not replace current path until real edit semantics are verified |
| Phase 5 — Optional layout guide | **PLANNED / P2** | Run only if safe-zone evidence justifies it |
| Phase 6 — Model / quality policy | **PLANNED** | Runtime controls must be verified before hard-coding |
| Phase 7 — Consolidated regression suite | **PLANNED** | Merge deterministic and visual ablation evidence |
| Phase 8 — Public contract / README / release | **PLANNED** | Only after accepted behavior is stable |

---

# Goals

1. Improve master-background quality and instruction following.
2. Improve SKU background consistency relative to the locked master.
3. Reduce unwanted product-like geometry or copied product details in generated backgrounds.
4. Keep logical layout and actual delivery raster semantics explicit and deterministic.
5. Make prompts structured, testable, and Images 2.5-aware.
6. Preserve the user-controlled master approval flow.
7. Preserve deterministic SKU naming, atomic replacement, source hashing, and local composition.
8. Require repeatable regression and ablation evidence before changing production defaults.

## Non-goals

- Do not move Logo or typography rendering into the image model.
- Do not let the image model redraw the authoritative product.
- Do not replace deterministic product placement with model-generated placement.
- Do not replace the fixed local 2D shadow with a generated shadow.
- Do not introduce automatic aesthetic acceptance or automatic visual retries.
- Do not redesign the Classic MD3 direction.
- Do not add M3 Expressive.

---

# Phase 0 — Establish an Images 2.5 baseline

**Status: COMPLETED**  
**Priority: P0**

## Completed evidence

- Existing deterministic workflow self-check: PASS.
- Real production Work run established with:
  - `黑.png` as MASTER source,
  - `橙.png` as SKU A,
  - `白.png` as SKU B,
  - `HUAWEI-LOGO.png`,
  - fixed two-line product title and Russian version text.
- v2.0 MASTER and two SKU outputs were visually reviewed and accepted as the baseline.
- Real delivered files were inspected directly instead of trusting UI-reported logical dimensions.
- Background-mode control was verified in the callable image runtime.
- The project-conversation image surface was proven not equivalent to the production Skill transport contract for exact prompt/reference/edit testing.
- Current callable chat edit probes did not enter verified image-edit semantics; Phase 4 therefore remains runtime-gated.

## Important finding

Work reported `1536 × 2048`, while downloaded production outputs were consistently observed at:

```text
1086 × 1448
```

Both are exact 3:4, but they are different pixel resolutions.

This finding directly changed Phase 1.

---

# Phase 1 — Production raster contract

**Status: COMPLETED**  
**Priority: P0**

The original plan assumed `1536 × 2048` should become the mandatory delivered raster. Real Work evidence disproved that assumption.

## Implemented contract

### Logical layout canvas

Keep:

```text
1536 × 2048
```

as the canonical deterministic layout coordinate system produced by `measure_text.py`.

It defines normalized placement and safe-zone geometry. It is not a promise about the Image Gen delivery raster.

### MASTER delivery raster

A MASTER background may use any exact 3:4 raster accepted by the workflow.

The local composite is created at the actual generated-background raster. Do not automatically upscale a valid MASTER background merely to force `1536 × 2048`.

When the user locks the MASTER, its actual width/height are recorded in `master.json`.

### SKU delivery raster

Every SKU background must match the locked MASTER's actual pixel width and height exactly.

A background that is still 3:4 but has different dimensions fails deterministically with:

```text
SKU_BACKGROUND_RASTER_MISMATCH
```

No automatic image-generation retry is allowed.

### Legacy compatibility

For an older bound `master.json` without a persisted raster field, the workflow derives the raster from the hash-verified `ORIGINAL_MASTER_BACKGROUND.png`. It never guesses another size.

## Production changes

- `scripts/common.py`
  - raster inspection helpers
  - strict 3:4 validation
  - master-raster verification
  - legacy-raster derivation
- `scripts/artifact_flow.py`
  - MASTER preview records actual raster
  - MASTER bind persists raster
  - local master assets are checked against the same raster
  - SKU background must equal MASTER raster
  - SKU output manifest records the raster
- `scripts/test_raster_integration.py`
  - verifies new MASTER raster persistence
  - rejects a different-size 3:4 SKU background
  - verifies failed mismatch does not consume the SKU
  - verifies matching SKU succeeds
  - verifies legacy master compatibility

## Acceptance

- production raster integration self-check: PASS
- existing deterministic workflow self-check: PASS

---

# Phase 2 — Structured master prompt

**Status: COMPLETED / PROMOTED**  
**Priority: P0**

The prose-heavy v2.0 prompt was replaced with the validated structured background artifact specification.

## Default prompt structure

1. `DELIVERABLE`
2. `REFERENCE ROLES`
3. `VISUAL SYSTEM`
4. `PALETTE`
5. `COMPOSITION`
6. `LIGHTING`
7. `EXCLUSIONS`
8. `OUTPUT CONTRACT`

The deterministic `FINAL_INFORMATION_SAFE_ZONE`, accumulated user additions, and canonical product/shadow placement policy continue to be appended by `scene_prompt.py`.

## Required exclusions

The active prompt explicitly prevents:

- product rendering
- product silhouettes / hardware geometry copying
- packaging geometry
- Logo
- text
- watermark
- product shadow
- floor
- table
- display stand
- realistic physical environment

## A/B result

Using the same HUAWEI source set in real Work:

- structured black MASTER: PASS
- structured orange SKU: PASS
- structured white SKU: PASS

The structured version was preferred over v2.0 for:

- quieter reusable background composition,
- safe-zone cleanliness,
- cleaner palette migration,
- SKU composition consistency.

No regression was observed in local deterministic composition.

## Decision

`references/image-gen-prompt.txt` is the default structured prompt.

The v2.0 prompt is preserved at:

```text
references/image-gen-prompt-v2-baseline.txt
```

for regression, ablation, and fallback comparison only.

Detailed evidence is in `docs/phase-2/`.

---

# Phase 3 — Deterministic palette-reference ablation

**Status: IN PROGRESS**  
**Priority: P1**

## Question

Should Image Gen continue receiving the complete product image when the only required transfer is color palette?

The Phase 2 full-product reference remains the production default until this ablation is complete.

## Implemented extractor

```text
scripts/extract_palette.py
```

Current deterministic policy:

- ignore pixels below alpha threshold 32,
- nearest-neighbor source sampling with max edge 512,
- 5-bit/channel RGB histogram,
- fixed maximum of 7 representative colors,
- 4 coverage-oriented dominant slots,
- remaining slots reserve saturation-aware accent colors,
- diversity thresholds are fixed by code,
- after selecting representatives, assign every visible histogram bin to its nearest representative,
- use those full-coverage weights for the color-band widths,
- generate a 1024 × 256 RGB `palette-reference.png` containing color bands only.

No model is used for palette extraction.

## Deterministic verification

Tests verify:

- identical source -> byte-identical palette JSON and reference PNG,
- changing RGB values only in fully transparent pixels does not change the visible palette or reference PNG,
- fully transparent input fails deterministically,
- existing workflow regression remains PASS.

## Real Work ablation

### A — baseline

Phase 2 structured prompt + full product image as palette reference.

Already completed for black / orange / white.

### B — palette-only

Use the same structured prompt and deterministic local product composition, but Image Gen receives only the extracted color-only reference for palette information.

Run in two gates:

1. black MASTER only,
2. only if MASTER passes: orange and white SKU variants.

Evaluate:

- palette harmony
- background quality
- Classic MD3 adherence
- safe-zone cleanliness
- SKU composition consistency
- unwanted product copying
- product-like geometry
- accidental generated text / Logo / label

## Adoption rule

Palette-only becomes default only if it reduces semantic/product-copy risk without materially reducing palette/background quality.

Otherwise retain full-product reference and record Phase 3 as a rejected ablation.

Detailed protocol and current HUAWEI palette fingerprints are in `docs/phase-3/PLAN.md`.

---

# Phase 4 — Constrained SKU background editing

**Status: PLANNED / RUNTIME-GATED**  
**Priority: P0 after Phase 3**

Intended goal: use `ORIGINAL_MASTER_BACKGROUND.png` as the authoritative editable image and change palette only.

## Intended preserve contract

Must preserve:

- composition
- geometry
- panel/card placement
- shape count
- relative size
- negative space
- information safe zone
- lighting direction
- elevation hierarchy
- visual density

Must never copy from SKU reference:

- product geometry
- labels
- icons
- text
- Logo
- product silhouette

## Runtime gate

Current project-conversation probes did not verify real edit semantics. Therefore:

- do not replace the current production SKU path yet,
- do not claim that an edit call is available merely because the public API supports one,
- retain the current locked-master composition-reference generation path as fallback.

Adopt constrained editing only after a real Skill/Work surface proves the edit operation and shows materially lower composition drift.

---

# Phase 5 — Optional layout-control reference

**Status: PLANNED / P2**

Test `layout-guide.png` only if later evidence shows numeric safe-zone instructions remain insufficient.

Rules:

- guidance only, never pixel-accurate guarantee,
- never weaken deterministic local placement,
- do not introduce masks unless actual runtime behavior is verified,
- keep only if safe-zone consistency materially improves without guide artifacts or excessive rigidity.

---

# Phase 6 — Model and quality policy

**Status: PLANNED**  
**Priority: P1**

Public Images 2.5 API capabilities and the actual Skill runtime are not assumed to be identical.

Before changing defaults:

- enumerate controls actually exposed to the production runtime,
- test master and SKU separately,
- compare only settings the runtime can really invoke,
- evaluate instruction following, MD3 quality, palette relevance, safe-zone adherence, object contamination, composition drift, failure rate, and latency where observable.

Use the fastest/lowest-cost option that consistently meets the acceptance criteria. Do not assume the highest quality setting is automatically best.

---

# Phase 7 — Consolidated regression and ablation suite

**Status: PLANNED**  
**Priority: P1**

## Deterministic coverage

Maintain tests for:

- product-directory identity
- source hashes
- layout reuse
- logical 3:4 layout contract
- actual MASTER raster persistence
- SKU/master raster equality
- palette extraction determinism
- safe-zone calculation
- prompt assembly order
- prompt hashing
- master binding
- SKU labels
- SKU redo atomic replacement
- failed redo preserving old final
- reusable asset identity

## Visual matrix

Maintain explicitly scored Work results for:

- background quality
- Classic MD3 adherence
- palette harmony
- safe-zone cleanliness
- unwanted product copying
- SKU composition drift
- accidental generated text / Logo / objects

## Required ablations

1. v2.0 prompt vs structured prompt — **DONE**
2. full product reference vs deterministic palette-only reference — **IN PROGRESS**
3. SKU regeneration vs constrained edit — planned
4. numeric safe zone vs numeric + optional layout guide — optional
5. model/quality configurations actually exposed by runtime — planned

---

# Phase 8 — Public Skill contract, README, and release

**Status: PLANNED**  
**Priority: P1**

Only accepted, tested behavior is documented as production behavior.

Expected final files may include:

- `SKILL.md`
- `README.md`
- `references/image-gen-prompt.txt`
- `references/replace-variant-block.md`
- `scripts/scene_prompt.py`
- raster-contract helpers/tests
- palette extraction code/tests if Phase 3 is accepted
- optional layout-guide code only if accepted

No release is cut from an unresolved ablation state.

---

# Invariants that must survive every phase

1. One exact complete product name maps to one product directory.
2. Reusable assets are identity-checked and never silently replaced.
3. Product artwork remains authoritative local source artwork.
4. Logo remains authoritative local source artwork.
5. Title lines remain exactly user supplied.
6. `TITLE_LINES` is never inferred.
7. Text remains locally rendered using the project font policy.
8. Product placement remains deterministic.
9. Product shadow remains deterministic.
10. The master is not bound until the user explicitly locks it.
11. One user generation instruction permits one image-model operation unless the user explicitly requests another attempt.
12. The Skill does not automatically accept or reject generated visual quality.
13. Deterministic failures do not trigger an automatic image-generation retry.
14. SKU redo preserves the old final until the replacement passes deterministic checks.
15. Final replacement remains atomic.
16. The logical layout canvas and the actual delivery raster are distinct concepts.
17. After MASTER lock, all SKU outputs must match the MASTER actual raster exactly.

---

# Current implementation order

```text
Phase 0  Baseline / capability verification             DONE
   ↓
Phase 1  Master-bound production raster contract        DONE
   ↓
Phase 2  Structured master prompt                       DONE
   ↓
Phase 3  Deterministic palette-reference ablation       IN PROGRESS
   ↓
Phase 4  Constrained SKU edit path                      RUNTIME-GATED
   ↓
Phase 6  Model / quality ablation
   ↓
Phase 5  Optional layout-guide ablation
   ↓
Phase 7  Consolidated regression suite
   ↓
Phase 8  Final Skill / README / release
```

Phase 3 now precedes Phase 4 because the real production structured generation path is already stable, while the edit surface remains unverified. Palette-only reference can therefore be measured independently without conflating it with an unverified edit mechanism.

---

# Definition of done

The Images 2.5 upgrade is complete only when all of the following are true:

- the structured master prompt remains the validated default,
- logical layout and actual delivery raster semantics are correct and documented,
- locked MASTER raster is enforced across SKUs,
- the Phase 3 palette-reference decision is backed by Work A/B evidence,
- SKU edit is either validated and adopted or explicitly rejected with the existing fallback retained,
- no deterministic product/Logo/text/shadow responsibility moves into the image model,
- prompt generation remains reproducible and recorded,
- accepted ablations are documented,
- deterministic regression tests pass,
- `SKILL.md` and `README.md` describe implemented behavior rather than planned behavior.
