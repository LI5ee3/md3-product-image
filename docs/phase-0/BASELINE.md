# Phase 0 Baseline

Status: **IN PROGRESS**

Date: 2026-09-09

This document freezes the current `md3-product-image` behavior before any Images 2.5 implementation change lands.

The purpose of Phase 0 is to separate three things that must not be conflated:

1. the current repository behavior,
2. capabilities documented for GPT Image 2.5 in the OpenAI API,
3. controls actually exposed by the image-generation runtime available to this Skill.

No production behavior should change during Phase 0.

---

## 1. Frozen repository baseline

The baseline starts from branch commit:

`128d8b2f1197f1a17aed34a61c82ac5fc6284736`

Relevant files at that baseline:

| File | Git blob SHA |
| --- | --- |
| `SKILL.md` | `0afeb08e0bec2c8ce0313a64b345a13921d2ec23` |
| `references/image-gen-prompt.txt` | `163dc1a43408b97b60653e1d35553dcaa2dac43f` |
| `references/replace-variant-block.md` | `a9eab5f83ae9913e00c18e78c7e7ac1e3ff40908` |
| `scripts/scene_prompt.py` | `dfec120454e3b3af9e313ab94959b6d65efa32fb` |
| `scripts/test_workflow.py` | `567cf81f5f7c933e3f2b6a1d12b6c56220a07ba7` |

These hashes are the authoritative Phase 0 comparison point. Later prompt or workflow changes must be evaluated against this exact baseline rather than against memory or a reconstructed prompt.

### Current master behavior

The baseline master path is:

`MEASURE -> BUILD_PROMPT -> IMAGE_GEN_BACKGROUND -> LOCAL_FULL_COMPOSITE -> MASTER_USER_LOCK_OR_REDO`

Image generation creates an empty background plate. Product artwork, product placement, fixed 2D shadow, Logo, title, version text, and final composition remain local and deterministic.

### Current SKU behavior

The baseline SKU path generates a new empty background using:

- `ORIGINAL_MASTER_BACKGROUND.png` as composition reference,
- the current SKU product image as palette reference.

The prompt asks the model to keep composition unchanged and adapt only colors. This is reference-guided regeneration, not an explicit image-edit contract in repository code.

---

## 2. Existing deterministic self-check

`scripts/test_workflow.py` is retained as the deterministic workflow baseline.

It currently checks, among other things:

- PNG / WEBP source handling,
- exact title-line preservation,
- safe-zone prompt inclusion,
- prompt recording,
- one active user-decision gate,
- cached master product and shadow reuse,
- prompt-addition accumulation,
- explicit master binding,
- final master filename,
- automatic SKU label assignment,
- SKU redo without consuming a new label,
- failed SKU redo preserving the existing final,
- successful atomic replacement,
- cached SKU product and shadow reuse,
- absence of thumbnails.

The existing self-check uses one simple synthetic red master product and one blue SKU product. It remains useful for deterministic workflow regression, but it is not sufficient as the Images 2.5 visual evaluation set.

### Execution note

A direct clone-and-run attempt from the current assistant container was blocked because that container cannot resolve `github.com`. This is an environment network limitation, not a repository test failure.

The test source itself was read successfully through the connected GitHub interface. Phase 0 should not mark the deterministic self-check as freshly executed until it is run in a repository-capable runtime or CI environment.

---

## 3. Fixed visual evaluation inputs

Phase 0 introduces:

`scripts/generate_phase0_fixtures.py`

It deterministically generates seven transparent PNG product references plus a common source Logo and a hash-bearing `manifest.json`.

The fixed coverage set is:

1. `light-product`
2. `dark-product`
3. `saturated-product`
4. `low-saturation-product`
5. `wide-product`
6. `tall-product`
7. `multi-dominant-color`

Each fixture uses the same 768 × 1024 source canvas and fixed pixels. The generated `manifest.json` records SHA-256 identities so later ablations can verify that identical source inputs were used.

Generate the set with:

```text
python scripts/generate_phase0_fixtures.py --output-dir <phase-0-fixture-directory>
```

The generator was locally self-checked before being committed:

- exactly seven fixtures were produced,
- all seven required coverage categories were present,
- every product fixture was 768 × 1024 RGBA,
- the manifest parsed successfully.

These synthetic inputs are intentionally simple. They isolate palette and geometry classes without introducing changing third-party product photography. Real-product spot checks may be added later, but they must not replace this fixed set for cross-phase comparisons.

---

## 4. Current prompt baseline

The baseline master prompt is the exact contents of:

`references/image-gen-prompt.txt`

at Git blob:

`163dc1a43408b97b60653e1d35553dcaa2dac43f`

The baseline SKU-specific block is the exact contents of:

`references/replace-variant-block.md`

at Git blob:

`a9eab5f83ae9913e00c18e78c7e7ac1e3ff40908`

Do not duplicate or rewrite those files for the baseline. The pinned blob identities are the record. This avoids creating two authoritative copies of the same prompt.

For every visual baseline run, archive the complete prompt emitted by `scene_prompt.py`; that emitted prompt remains the authoritative per-attempt record because it also contains the measured safe zone and any accumulated user additions.

---

## 5. GPT Image 2.5 capability verification

The following matrix distinguishes OpenAI API support from the Skill runtime surface visible in this session.

| Capability | OpenAI API documentation | Current Skill runtime surface | Phase 0 status |
| --- | --- | --- | --- |
| GPT Image 2.5 Flare | Model exists | No model selector exposed | API VERIFIED / RUNTIME UNSELECTABLE |
| GPT Image 2.5 Sunburst | Model exists | No model selector exposed | API VERIFIED / RUNTIME UNSELECTABLE |
| Dated model snapshot | `gpt-image-2.5-*-2026-09-08` documented | No model selector exposed | API VERIFIED / RUNTIME UNAVAILABLE |
| Image generation | Supported | Image-generation operation available | VERIFIED |
| Explicit image edit endpoint | Sunburst documents `/v1/images/edits` | Editing existing conversation images is supported semantically, but no endpoint selector is exposed | API VERIFIED / RUNTIME PARTIAL |
| Reference image input | Image input supported | Existing images in the conversation can be used for edits/references | VERIFIED AT HIGH LEVEL |
| Quality control | `low`, `medium`, `high`, `xhigh`, `max`, `auto` documented for Flare and Sunburst | No quality parameter exposed | API VERIFIED / RUNTIME UNAVAILABLE |
| Size control | GPT Image API supports size controls; exact 2.5 runtime behavior must be trialed | Runtime exposes a `size` string | PARAMETER EXPOSED / 1536×2048 NOT YET TRIALED |
| Transparent background control | Model/API family supports background controls | Runtime exposes `transparent_background: bool` | PARAMETER EXPOSED |
| Explicit `background=opaque` enum | Documented in the GPT Image 2.5 API rollout | Runtime does not expose an `opaque` enum; only the transparency boolean | API VERIFIED / RUNTIME NOT EXPOSED DIRECTLY |
| Output format selector | Available in API-level image workflows | No output-format parameter exposed in the current Skill image tool | RUNTIME UNAVAILABLE |
| Edit mask | API edit workflows may expose masks depending on interface | No mask parameter exposed in the current Skill image tool | RUNTIME UNAVAILABLE |
| Explicit input-fidelity control | API-level feature may vary by image interface/model | No input-fidelity parameter exposed in the current Skill image tool | RUNTIME UNAVAILABLE |

### Important consequence

The repository must not hard-code the following based only on API documentation:

- `gpt-image-2.5-sunburst`,
- `gpt-image-2.5-flare`,
- a `quality` value,
- a mask argument,
- an explicit `background=opaque` argument,
- a specific edit endpoint.

Those are safe to use only if the actual Skill execution interface exposes them.

The current runtime can still benefit from Images 2.5 behavior when the platform routes image operations to it, but the Skill cannot claim deterministic control over a parameter it cannot set.

---

## 6. Official sources checked

OpenAI sources checked on 2026-09-09:

- `https://openai.com/index/introducing-chatgpt-images-2-5/`
- `https://developers.openai.com/api/docs/models/gpt-image-2.5-flare`
- `https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst`

Verified from those sources:

- ChatGPT Images 2.5 launched on 2026-09-08.
- API models are GPT Image 2.5 Flare and GPT Image 2.5 Sunburst.
- Sunburst is the precision-oriented generation/editing model.
- Flare is the faster default-oriented model.
- Both model pages document `low`, `medium`, `high`, `xhigh`, `max`, and `auto` quality choices.
- Sunburst explicitly lists the Image Edit endpoint.
- dated 2026-09-08 model snapshots are documented.

---

## 7. Visual baseline run protocol

Each of the seven fixtures must receive one baseline master run using the frozen repository behavior.

For each fixture:

1. generate the fixture set and verify its manifest SHA-256 values,
2. run the existing `measure_text.py` path,
3. build the master prompt with the frozen prompt implementation,
4. perform exactly one image-model operation,
5. create exactly one full local composite,
6. do not auto-retry based on aesthetics,
7. record the generated-background identity and final-composite identity,
8. record the actual resolved image dimensions if observable,
9. score the output using `docs/phase-0/evaluation-results.csv`.

After a representative master is explicitly bound, create at least one baseline SKU for that fixture using the existing reference-guided regeneration path and record the same information.

Do not introduce the structured prompt, palette-only reference, constrained edit path, layout guide, or new quality policy during these baseline runs.

---

## 8. Scoring contract

Use integer scores from 1 to 5 for subjective metrics:

- `background_quality`
- `classic_md3_adherence`
- `palette_harmony`
- `safe_zone_cleanliness`
- `sku_composition_consistency`

Use binary `0/1` fields for undesirable events:

- `unwanted_product_copying`
- `product_like_geometry`
- `accidental_text_or_logo`
- `unexpected_physical_environment`

Do not average away failures. Keep the raw per-fixture records available for every later ablation.

---

## 9. Phase 0 completion checklist

- [x] Pin the repository baseline by commit and relevant blob identities.
- [x] Document the existing deterministic workflow test coverage.
- [x] Define a fixed seven-category visual evaluation set.
- [x] Add a deterministic generator for that evaluation set.
- [x] Self-check the fixture generator.
- [x] Verify GPT Image 2.5 model names and API-level quality/edit capabilities from current OpenAI documentation.
- [x] Record which controls are and are not exposed by the current Skill image runtime.
- [ ] Freshly execute `scripts/test_workflow.py` in a repository-capable runtime or CI.
- [ ] Trial an actual runtime image operation at exact `1536x2048` and record the resolved dimensions.
- [ ] Trial runtime opaque/non-transparent output behavior and record the resolved result.
- [ ] Produce and archive baseline master outputs for the fixed evaluation set.
- [ ] Produce and archive representative baseline SKU outputs using the current reference-guided regeneration path.
- [ ] Fill the Phase 0 evaluation-results table.

Phase 0 is not complete until every unchecked item above has evidence recorded.
