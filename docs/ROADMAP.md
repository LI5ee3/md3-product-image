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
| Phase 2 — Structured prompt | **COMPLETED** | Structured prompt promoted; v2.0 prompt retained as baseline/fallback |
| Phase 3 — Deterministic palette reference | **COMPLETED** | Palette-only reference promoted to default after MASTER + orange/white SKU Work A/B |
| Phase 4 — Constrained SKU image edit | **COMPLETED / NOT ADOPTED** | Work exposes no verifiable edit operation; Phase 3 SKU regeneration remains authoritative |
| Phase 5 — Optional layout guide | **SKIPPED / NOT NEEDED** | Accepted Work results kept the numeric safe zone clean; no guide ablation is justified |
| Phase 6 — Runtime/model/quality policy | **COMPLETED** | Runtime schema enumerated; explicit reference-path mode adopted; model/quality controls are not exposed |
| Phase 7 — Consolidated regression suite | **COMPLETED** | Unified deterministic gate and final MASTER → orange SKU → white SKU Work smoke all passed |
| Phase 8 — Public contract / README / release | **NEXT** | Reconcile public docs, validate release package, and prepare the next release |

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

# Phase 0 — Baseline and runtime verification

**Status: COMPLETED**

Authority set:

- `黑.png` MASTER source
- `橙.png` SKU A
- `白.png` SKU B
- `HUAWEI-LOGO.png`
- fixed two-line HUAWEI WATCH FIT 5 Pro title and Russian version text

Key finding: Work reported `1536 × 2048`, while downloaded production outputs were consistently `1086 × 1448`. Both are exact 3:4. This finding changed Phase 1.

---

# Phase 1 — Production raster contract

**Status: COMPLETED**

`1536 × 2048` remains the logical layout coordinate system only.

A MASTER may use any exact 3:4 raster accepted by the workflow. When the user locks it, the actual width/height are persisted in `master.json`.

Every SKU background must match the locked MASTER raster exactly. Same-ratio/different-size backgrounds fail deterministically with:

```text
SKU_BACKGROUND_RASTER_MISMATCH
```

Legacy bound masters without a raster field derive it from the hash-verified `ORIGINAL_MASTER_BACKGROUND.png`; the workflow never guesses another size.

---

# Phase 2 — Structured prompt

**Status: COMPLETED / PROMOTED**

The active prompt uses ordered sections:

1. `DELIVERABLE`
2. `REFERENCE ROLES`
3. `VISUAL SYSTEM`
4. `PALETTE`
5. `COMPOSITION`
6. `LIGHTING`
7. `EXCLUSIONS`
8. `OUTPUT CONTRACT`

Real Work A/B:

- structured black MASTER: PASS
- structured orange SKU: PASS
- structured white SKU: PASS

The structured prompt is the default. The v2.0 prose prompt remains at `references/image-gen-prompt-v2-baseline.txt` for regression/ablation/fallback only.

---

# Phase 3 — Deterministic palette reference

**Status: COMPLETED / PROMOTED**

Image Gen no longer receives complete product artwork merely to learn colors.

Production uses deterministic local palette extraction via:

```text
scripts/extract_palette.py
scripts/palette_cache.py
```

MASTER Image Gen reference:

```text
palette-reference.png
```

SKU Image Gen references:

```text
ORIGINAL_MASTER_BACKGROUND.png
current-SKU-palette-reference.png
```

The complete product/SKU artwork remains local for deterministic composition.

Real Work palette-only MASTER + orange SKU + white SKU all passed with no material regression in palette harmony, background quality, safe-zone behavior, or SKU composition consistency.

---

# Phase 4 — Constrained SKU edit

**Status: COMPLETED / NOT ADOPTED**

A dedicated Work C0 probe returned:

```text
IMAGE_EDIT_INTERFACE_UNAVAILABLE
```

The callable surface exposed normal generation but no explicit existing-image edit operation or equivalent verifiable edit selector. The probe failed closed before any image-model call.

C1/C2 edit ablations were not run because they would not be valid without proven edit semantics.

Production therefore retains the Phase 3 SKU regeneration path.

---

# Phase 5 — Optional layout guide

**Status: SKIPPED / NOT NEEDED**

The conditional gate for `layout-guide.png` was not met. Accepted Phase 2, Phase 3, and final Phase 7 Work results kept the information safe zone clean without an auxiliary layout image.

Adding another model reference would increase complexity without evidence of a current failure. Reopen Phase 5 only if a future production regression shows numeric safe-zone instructions are insufficient.

---

# Phase 6 — Runtime/model/quality policy

**Status: COMPLETED**

A fresh isolated Work C0 probe enumerated the actual Image Gen callable surface.

Directly settable:

```text
prompt
num_last_images_to_include
referenced_image_paths
```

Not directly exposed:

- model selection
- quality / effort
- output size / resolution
- background / transparency
- output format
- image action / mode

Therefore no model/quality/size/background/output-format A/B is valid on the current Work Skill surface.

C1 proved `num_last_images_to_include` and `referenced_image_paths` are mutually exclusive.

C2 proved the accepted production callable mode:

```text
prompt = exact deterministic scene prompt
referenced_image_paths = exact explicit authority list
num_last_images_to_include = OMITTED
```

C2 returned an accessible `1086 × 1448` RGBA background with SHA-256:

```text
d9f5b6fa0389b4a3475352c79509a09ac35e80e725fe5caba7344f697e4a99b9
```

The production `SKILL.md` requires explicit `referenced_image_paths`, omits `num_last_images_to_include`, and forbids inferring unsupported public-API controls.

---

# Phase 7 — Consolidated regression suite

**Status: COMPLETED / PASS**

## Consolidated deterministic gate

GitHub Actions workflow `Phase 7 consolidated regression`, run `34379183114`, passed all steps:

- original workflow regression
- raster contract regression
- raster production integration regression
- structured prompt regression
- palette extraction regression
- palette cache regression
- Work runtime reference contract regression

## Required ablations status

1. v2.0 prompt vs structured prompt — **DONE**
2. full product reference vs deterministic palette-only reference — **DONE**
3. SKU regeneration vs constrained edit — **DONE / NOT ADOPTED**
4. numeric safe zone vs optional layout guide — **SKIPPED / NOT NEEDED**
5. model/quality configurations — **DONE / NOT APPLICABLE: controls not exposed**

## Final production-like Work smoke

The final accepted production candidate was tested in a fresh Work conversation using the authoritative HUAWEI source set:

```text
black MASTER
→ explicit user lock
→ orange SKU_VARIANT-A
→ white SKU_VARIANT-B
```

All three outputs were `1086 × 1448` RGBA with fully opaque alpha and passed visual review.

Final hashes:

```text
MASTER black
5b2d32959cb1aa50c0d754058858f3292c8844091621b1021244a3ac1d90df58

SKU_VARIANT-A orange
76d1eb8540e3d8fba3a7ca5da024ce3c511c014c75fc1d8cea7578021086ba66

SKU_VARIANT-B white
658b65dadfefd8adef6ee3671cf2a064ca3d184c01207e953f11bf7552bfa9ec
```

Observed final behavior:

- structured prompt: PASS
- palette-only references: PASS
- safe-zone cleanliness: PASS
- MASTER/SKU raster equality: PASS
- SKU composition consistency: PASS
- accidental generated product/text/Logo contamination: none observed
- user-controlled MASTER lock flow: PASS

Detailed evidence is in `docs/phase-7/RESULTS.md`.

---

# Phase 8 — Public Skill contract, README, and release

**Status: NEXT**

Only accepted, tested behavior is documented as production behavior.

Required final work:

- reconcile `SKILL.md` and `README.md`
- remove test-only packaging and probe files from release artifacts
- keep only accepted production scripts, references, assets, and required metadata
- validate the final release ZIP from a clean package build
- verify public documentation matches the implemented runtime/reference/raster contracts
- prepare the next release only after final package validation passes

---

# Invariants

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
16. The logical layout canvas and actual delivery raster are distinct concepts.
17. After MASTER lock, all SKU outputs match the MASTER actual raster exactly.
18. Image Gen receives palette-only references by default; authoritative product artwork remains local.
19. Unsupported runtime controls are never inferred from public API capability alone.
20. Image Gen calls use explicit `referenced_image_paths`; `num_last_images_to_include` is omitted because the selectors are mutually exclusive on the validated Work runtime.

---

# Current implementation order

```text
Phase 0  Baseline / capability verification             DONE
   ↓
Phase 1  Master-bound production raster contract        DONE
   ↓
Phase 2  Structured master prompt                       DONE
   ↓
Phase 3  Deterministic palette reference                DONE
   ↓
Phase 4  Constrained SKU edit path                      DONE / NOT ADOPTED
   ↓
Phase 6  Runtime capability / reference-path contract   DONE
   ↓
Phase 5  Optional layout-guide ablation                 SKIPPED / NOT NEEDED
   ↓
Phase 7  Consolidated regression + production smoke     DONE
   ↓
Phase 8  Final Skill / README / release                 NEXT
```

---

# Definition of done

The Images 2.5 behavior upgrade has passed its implementation and production-smoke gates. The project is release-ready only when Phase 8 also completes:

- `SKILL.md` and `README.md` describe only implemented behavior,
- the release artifact excludes test-only probes and CI-only packaging,
- the final clean package validation passes,
- the release notes accurately summarize the accepted behavior changes.
