# ROADMAP

## Purpose

This roadmap defines the upgrade path for `md3-product-image` to take advantage of the latest Images 2.5 capabilities without weakening the deterministic parts of the existing workflow.

The project will continue to follow one core architectural rule:

> Generative image models are responsible only for the visual background layer. Product artwork, Logo, title text, version text, placement, fixed 2D shadow, file identity, and final composition remain deterministic and locally controlled.

The upgrade is therefore an evolution of the current workflow, not a rewrite.

---

## Goals

1. Improve master-background quality and instruction following.
2. Improve SKU background consistency relative to the locked master.
3. Reduce unwanted product-like geometry or copied product details in generated backgrounds.
4. Use the native final canvas size whenever supported instead of depending on unnecessary resizing.
5. Make image-generation prompts more explicit, structured, testable, and model-version aware.
6. Preserve the current user-controlled master approval flow.
7. Preserve deterministic SKU file naming, atomic replacement, reusable-asset hashing, and local composition.
8. Add repeatable regression and ablation tests before changing production behavior.

## Non-goals

- Do not move Logo or typography rendering into the image model.
- Do not let the image model redraw the authoritative product image.
- Do not replace deterministic product placement with model-generated placement.
- Do not replace the fixed local 2D shadow with a generated shadow.
- Do not introduce automatic aesthetic acceptance or automatic visual retries.
- Do not redesign the Classic MD3 visual direction.
- Do not add M3 Expressive.

---

# Phase 0 — Establish an Images 2.5 baseline

**Priority: P0**

Before changing implementation behavior, establish a reproducible baseline against the current workflow.

## Tasks

- Record the current master-generation prompt and representative outputs.
- Record representative SKU outputs using the current master-reference workflow.
- Select a small fixed evaluation set covering:
  - light products
  - dark products
  - saturated products
  - low-saturation products
  - wide products
  - tall products
  - products with multiple dominant colors
- Verify the currently available Images 2.5 API/tool capabilities actually exposed to the Skill runtime before coding against them.
- Confirm supported native output dimensions, edit/reference-image behavior, quality controls, and background controls from the actual interface in use.
- Do not hard-code undocumented model names, quality values, or edit parameters until verified.

## Acceptance criteria

- A fixed baseline dataset exists.
- Current behavior can be reproduced.
- Every Images 2.5 capability required by later phases has been verified against the actual callable interface.

---

# Phase 1 — Native 3:4 generation contract

**Priority: P0**

Align generation directly with the deterministic 1536 × 2048 layout used by the local composition pipeline whenever the active Images 2.5 interface supports that size natively.

## Tasks

- Treat `1536 × 2048` as the canonical final canvas.
- Request the canonical size directly from image generation when supported.
- Explicitly request an opaque background when the interface supports background-mode control.
- Preserve PNG as the canonical reusable background format.
- Remove any unnecessary resize path between generated background and local composition.
- Add deterministic dimension validation before composition.

## Acceptance criteria

- Generated background dimensions exactly match the local composition canvas.
- No implicit crop or rescale is required in the normal path.
- Existing layout coordinates remain valid without conversion.
- Wrong-size outputs fail deterministically and do not trigger an automatic generation retry.

---

# Phase 2 — Structured master prompt

**Priority: P0**

Replace the current prose-heavy master prompt with a structured background artifact specification.

## Target prompt structure

1. `DELIVERABLE`
2. `REFERENCE ROLES`
3. `VISUAL SYSTEM`
4. `PALETTE`
5. `COMPOSITION`
6. `INFORMATION SAFE ZONE`
7. `LIGHTING`
8. `EXCLUSIONS`
9. `OUTPUT CONTRACT`

## Requirements

The prompt must explicitly state that the model creates an empty background plate only.

The prompt must explicitly forbid:

- product rendering
- product silhouettes
- copied packaging geometry
- Logo
- text
- watermark
- product shadow
- floor
- table
- display stand
- realistic physical environment

The Classic MD3 direction remains fixed:

- soft neumorphic surfaces
- rounded cards, capsules, discs, and panels
- restrained elevation
- high-key neutral lighting
- low-contrast shadows
- light macaron palette derived from the product palette
- no hard outlines or high-contrast graphic borders

## Safe-zone contract

Continue to derive `FINAL_INFORMATION_SAFE_ZONE` deterministically from the measured Logo/title/version union plus the existing margin policy.

The generated prompt must treat this as the only mandatory empty information area.

## Acceptance criteria

- Prompt assembly remains deterministic.
- The complete generated prompt is still recorded per attempt.
- Existing accumulated user additions remain supported.
- No visual requirement is silently invented by the Skill.

---

# Phase 3 — Deterministic palette extraction

**Priority: P1**

Stop depending on the complete product artwork as the only palette reference when a smaller deterministic palette representation is sufficient.

## New reusable assets

Introduce a deterministic palette extraction step that can produce:

- `reusable/palette.json`
- `reusable/palette-reference.png`

For SKU variants, generate or cache an equivalent SKU palette reference for the active product image.

## Requirements

- Palette extraction must be deterministic for identical source pixels.
- Alpha-transparent regions must not distort color extraction.
- The number of representative colors must be fixed by implementation policy rather than selected by the model.
- The palette reference must contain color information only and no product silhouette, text, Logo, label, or packaging geometry.
- Source-image hashes remain authoritative.

## Evaluation

Run an ablation test:

**A.** complete product image as palette reference  
**B.** deterministic palette reference only

Evaluate:

- palette relevance
- unwanted product copying
- product-like geometry in background
- visual quality
- cross-run stability

## Acceptance criteria

Adopt palette-only reference as the default only if it reduces unwanted copying without materially reducing palette quality.

Otherwise retain the current product-reference path and document the result.

---

# Phase 4 — SKU generation becomes constrained background editing

**Priority: P0**

This is the primary Images 2.5 workflow upgrade.

Instead of asking the model to independently regenerate a new SKU background while using the master as a composition reference, use the locked `ORIGINAL_MASTER_BACKGROUND.png` as the authoritative editable image whenever the active Images 2.5 interface supports sufficiently controlled image editing.

## Intended edit contract

### Authoritative source

`ORIGINAL_MASTER_BACKGROUND.png`

### Allowed change

- palette / color relationships required to harmonize with the current SKU

### Must remain unchanged

- composition
- geometry
- panel placement
- card placement
- shape count
- relative size
- negative space
- information safe zone
- lighting direction
- elevation hierarchy
- visual density

### Must never be copied from the SKU reference

- product geometry
- packaging structure
- labels
- icons
- text
- Logo
- product silhouette

## Prompt direction

The SKU instruction should use an explicit edit contract equivalent to:

```text
TASK
Edit the master background only.

REFERENCE ROLES
MASTER_BACKGROUND: authoritative composition and geometry.
SKU_PALETTE_REFERENCE: color reference only.

CHANGE
Change only the background color palette so it harmonizes with the current SKU palette.

PRESERVE
Preserve composition, geometry, placement, lighting structure, elevation hierarchy, negative space, and the information safe zone.

DO NOT
Do not add, remove, move, resize, or redesign scene elements.
Do not copy product geometry, labels, text, logos, icons, packaging, or silhouettes from the SKU reference.

OUTPUT
Empty background plate only.
```

The exact runtime prompt must be generated by `scene_prompt.py`; the Skill must not reconstruct it independently.

## Fallback

If the active Images 2.5 interface cannot provide sufficiently constrained editing, retain the current master-composition-reference generation path as a documented fallback instead of fabricating an unsupported edit API.

## Acceptance criteria

Compared with the current SKU method, the Images 2.5 edit path must demonstrate measurably lower composition drift across the fixed evaluation set.

No change is accepted solely because one example looks better.

---

# Phase 5 — Optional layout-control reference experiment

**Priority: P2**

Test whether a generated `layout-guide.png` improves safe-zone adherence.

## Proposed asset

`reusable/layout-guide.png`

It may encode only layout-control information such as:

- canvas bounds
- final information safe zone
- broad background-geometry region

It must not become part of the final composite.

## Rules

- Treat the guide as model guidance only, never as a pixel-accurate guarantee.
- Do not weaken local deterministic placement because a guide exists.
- Do not introduce an edit mask unless the actual Images 2.5 interface supports it and its behavior has been verified.

## Evaluation

Compare:

**A.** numeric safe-zone prompt only  
**B.** numeric safe-zone prompt + layout guide

Measure visually significant intrusions into the information safe zone.

## Acceptance criteria

Keep the guide only if it materially improves safe-zone consistency without causing visible guide artifacts or compositional rigidity.

---

# Phase 6 — Model and quality policy

**Priority: P1**

Do not assume that the highest available quality setting is automatically the correct production default.

## Tasks

- Enumerate the actually available Images 2.5 generation/edit choices in the runtime.
- Test master generation separately from SKU editing.
- Compare supported quality levels using the same fixed prompts and source assets.
- Measure:
  - instruction following
  - MD3 style quality
  - palette relevance
  - unwanted object generation
  - safe-zone adherence
  - SKU composition drift
  - failure rate
  - latency where observable

## Decision rule

Use the lowest-cost / fastest configuration that meets the visual and structural acceptance criteria consistently.

A higher quality tier becomes the default only when the regression set demonstrates a meaningful improvement.

## Acceptance criteria

- Master-generation policy is documented.
- SKU-edit policy is documented.
- Chosen settings are backed by repeatable tests rather than a single subjective comparison.

---

# Phase 7 — Regression and ablation test suite

**Priority: P1**

Extend the current deterministic workflow tests with image-generation workflow checks that do not depend on pretending visual generation is deterministic.

## Deterministic tests

Continue or add tests for:

- exact product-directory resolution
- source hash conflicts
- layout reuse
- canonical 3:4 dimensions
- palette extraction determinism
- safe-zone calculation
- prompt assembly order
- prompt hashing
- master binding
- SKU sequential labels
- SKU redo atomic replacement
- failed redo preserving the existing final
- reusable asset identity

## Visual evaluation matrix

Maintain a manual or explicitly scored evaluation table for the fixed reference set covering:

- background quality
- Classic MD3 adherence
- palette harmony
- safe-zone cleanliness
- unwanted product copying
- SKU composition drift
- accidental text / Logo / object generation

## Required ablations

At minimum compare:

1. current prompt vs structured prompt
2. full product palette reference vs deterministic palette reference
3. SKU regeneration vs SKU edit
4. numeric safe zone vs numeric safe zone + layout guide
5. candidate model/quality configurations actually available in the runtime

## Acceptance criteria

No major workflow replacement lands without regression results showing that it is at least equivalent on deterministic requirements and materially better on the targeted visual metric.

---

# Phase 8 — Skill contract and documentation update

**Priority: P1**

Only after implementation behavior is validated, update the public Skill contract.

## Files expected to change

- `SKILL.md`
- `README.md`
- `references/image-gen-prompt.txt`
- `references/replace-variant-block.md`
- `scripts/scene_prompt.py`
- relevant composition / workflow scripts if native-size handling changes
- `scripts/test_workflow.py`
- new palette-extraction code and tests if Phase 3 is accepted
- optional layout-guide code if Phase 5 is accepted

## SKILL.md requirements

The final Skill instructions must clearly distinguish:

### Master

`MEASURE -> PALETTE -> BUILD_PROMPT -> IMAGE_GENERATE -> LOCAL_FULL_COMPOSITE -> USER_LOCK_OR_REDO`

### SKU

Preferred path after validation:

`SKU_PALETTE -> BUILD_EDIT_PROMPT -> EDIT_MASTER_BACKGROUND -> LOCAL_FULL_COMPOSITE -> FINALIZE`

Fallback path, only if required by the runtime:

`SKU_PALETTE -> BUILD_PROMPT -> IMAGE_GENERATE_WITH_MASTER_REFERENCE -> LOCAL_FULL_COMPOSITE -> FINALIZE`

The Skill must use only interfaces that have actually been verified.

---

# Invariants that must survive every phase

The following are architectural constraints, not optimization targets:

1. One exact complete product name maps to one product directory.
2. Reusable assets are identity-checked and never silently replaced.
3. Product artwork remains authoritative local source artwork.
4. Logo remains authoritative local source artwork.
5. Title lines remain exactly user supplied.
6. `TITLE_LINES` is never inferred.
7. Text remains locally rendered using the project-defined font policy.
8. Product placement remains deterministic.
9. Product shadow remains deterministic.
10. The master is not bound until the user explicitly locks it.
11. One user generation instruction permits one image-model operation unless the user explicitly requests another attempt.
12. The Skill does not automatically accept or reject generated visual quality.
13. Deterministic failures do not trigger an automatic image-generation retry.
14. SKU redo preserves the old final until the replacement passes deterministic checks.
15. Final file replacement remains atomic.

---

# Recommended implementation order

```text
Phase 0  Baseline and capability verification
   ↓
Phase 1  Native 1536×2048 contract
   ↓
Phase 2  Structured master prompt
   ↓
Phase 4  Constrained SKU edit path
   ↓
Phase 3  Deterministic palette-reference ablation
   ↓
Phase 6  Model / quality ablation
   ↓
Phase 5  Optional layout-guide ablation
   ↓
Phase 7  Consolidated regression suite
   ↓
Phase 8  Final Skill and README contract update
```

Phase 4 is deliberately implemented before making palette-only references mandatory: first isolate the benefit of constrained editing, then separately measure the palette-reference change.

---

# Definition of done

The Images 2.5 upgrade is complete only when all of the following are true:

- master backgrounds use the validated Images 2.5 path
- SKU backgrounds use the validated constrained-edit path, or a documented fallback if the runtime cannot support it
- the canonical canvas is generated natively when supported
- no deterministic product/Logo/text/shadow responsibility has moved into the image model
- prompt generation remains reproducible and recorded
- the fixed regression set shows improved SKU consistency and no regression in deterministic behavior
- all accepted ablation decisions are documented
- tests pass
- `SKILL.md` and `README.md` describe the implemented behavior rather than planned behavior
