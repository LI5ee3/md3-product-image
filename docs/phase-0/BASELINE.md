# Phase 0 Baseline

Status: **IN PROGRESS — VISUAL BASELINE BLOCKED BY HARNESS MISMATCH**

Date: 2026-09-09

This document freezes the current `md3-product-image` behavior before any Images 2.5 implementation change lands.

Phase 0 separates four things that must not be conflated:

1. frozen repository behavior,
2. deterministic workflow correctness,
3. GPT Image / ChatGPT Images capabilities,
4. controls and transport actually exposed by the runtime used for a given test.

No production behavior changes during Phase 0.

---

## 1. Frozen repository baseline

Production behavior is compared against:

`128d8b2f1197f1a17aed34a61c82ac5fc6284736`

Relevant frozen blobs:

| File | Git blob SHA |
| --- | --- |
| `SKILL.md` | `0afeb08e0bec2c8ce0313a64b345a13921d2ec23` |
| `references/image-gen-prompt.txt` | `163dc1a43408b97b60653e1d35553dcaa2dac43f` |
| `references/replace-variant-block.md` | `a9eab5f83ae9913e00c18e78c7e7ac1e3ff40908` |
| `scripts/scene_prompt.py` | `dfec120454e3b3af9e313ab94959b6d65efa32fb` |
| `scripts/test_workflow.py` | `567cf81f5f7c933e3f2b6a1d12b6c56220a07ba7` |

### MASTER path

`MEASURE -> BUILD_PROMPT -> IMAGE_GEN_BACKGROUND -> LOCAL_FULL_COMPOSITE -> MASTER_USER_LOCK_OR_REDO`

### SKU path

The frozen SKU path generates a new empty background using:

- bound `ORIGINAL_MASTER_BACKGROUND.png` as composition reference,
- current SKU product image as palette reference.

It is reference-guided regeneration, not an explicit Images API edit endpoint in repository code.

---

## 2. Deterministic workflow baseline

`scripts/test_workflow.py` was executed unchanged through GitHub Actions in the repository environment.

Result:

**PASS**

Recorded evidence:

`docs/phase-0/DETERMINISTIC_BASELINE.md`

The workflow self-check covers source handling, exact title preservation, safe-zone prompt inclusion, attempt state, master binding, sequential SKU naming, SKU redo behavior, atomic replacement, cached product/shadow reuse, and related deterministic invariants.

This remains the hard regression gate for later phases.

---

## 3. Authoritative visual input set

The earlier synthetic fixtures remain available only for deterministic code/regression tests.

All visual evaluation from this point forward uses the project Google Drive folder documented in:

`docs/phase-0/AUTHORITY_INPUTS.md`

Fixed visual sequence:

1. MASTER: `黑.png`
2. SKU A: `橙.png`
3. SKU B: `白.png`
4. Logo: `HUAWEI-LOGO.png`
5. copy: Drive file `信息`

Exact copy:

```text
完整产品名称：HUAWEI WATCH FIT 5 Pro
产品名称显示行数：两行
产品名称第一行：HUAWEI
产品名称第二行：WATCH FIT 5 Pro
版本文字：Глобальная версия
```

These source files, IDs, raster dimensions, and SHA-256 identities are frozen in `AUTHORITY_INPUTS.md`.

---

## 4. Current MASTER prompt baseline

The black MASTER prompt was assembled from the frozen repository behavior and archived at:

`docs/phase-0/huawei-watch-fit-5-pro/master-prompt-black.txt`

Prompt SHA-256:

`12148360c40fe556ee8304c68a3914aa69e380d9fd75863b29809eac6a01a773`

Current measured merged information safe zone:

```text
FINAL_INFORMATION_SAFE_ZONE: x 0.0%-75.0%, y 0.0%-40.8%
```

The archived prompt, not a reconstructed summary, is the authoritative baseline prompt for this real-input case.

---

## 5. GPT Image / runtime capability matrix

| Capability | API / product capability | Current project-conversation surface | Phase 0 status |
| --- | --- | --- | --- |
| GPT Image 2.5 Flare | documented | no model selector exposed | API VERIFIED / RUNTIME UNSELECTABLE |
| GPT Image 2.5 Sunburst | documented | no model selector exposed | API VERIFIED / RUNTIME UNSELECTABLE |
| Image generation | supported | callable | VERIFIED |
| Explicit image edit endpoint | API supports editing; Sunburst is precision-oriented | project probe did not enter demonstrable edit mode | API VERIFIED / CURRENT HARNESS NOT VERIFIED |
| Quality control | API documents quality tiers | not exposed here | API VERIFIED / RUNTIME UNAVAILABLE |
| Custom size | API supports custom resolutions under documented constraints | exact raster control not successfully validated in this harness | API VERIFIED / CURRENT HARNESS UNVERIFIED |
| Transparent background | supported | boolean control exposed and tested | VERIFIED |
| Non-transparent background | supported | boolean false tested | VERIFIED |
| Explicit `background=opaque` enum | API-level option | enum not exposed here | API VERIFIED / RUNTIME NOT EXPOSED DIRECTLY |
| Output format selector | API-level option | not exposed here | RUNTIME UNAVAILABLE |
| Edit mask | API edit capability depends on surface | not exposed here | RUNTIME UNAVAILABLE |
| Verbatim prompt transport | repository requires exact stdout forwarding | current project conversation does not expose equivalent `functions.exec -> generatedImage` bridge | HARNESS MISMATCH |

### Background-mode evidence

`docs/phase-0/BACKGROUND_MODE_VALIDATION.md`

Result:

**PASS**

- transparency enabled -> RGBA PNG with real transparent pixels
- transparency disabled -> RGB PNG with no alpha channel

### Native-size evidence

`docs/phase-0/NATIVE_SIZE_VALIDATION.md`

The API-level legality of `1536x2048` is verified, but exact runtime raster delivery has not been validly demonstrated through the current project-conversation harness.

### Image-edit evidence

`docs/phase-0/IMAGE_EDIT_VALIDATION.md`

The current project probe did not demonstrate true edit-mode entry, so Phase 4 cannot be treated as runtime-verified yet.

---

## 6. Prompt-delivery harness finding

See:

`docs/phase-0/PROMPT_DELIVERY_VALIDATION.md`

The frozen `SKILL.md` requires:

1. `scene_prompt.py build` stdout,
2. captured successfully,
3. forwarded verbatim to Image Gen,
4. through its documented `functions.exec` / `generatedImage(result)` flow.

The image surface callable in the current project conversation is not equivalent to that transport contract. It derives generation intent from conversation context rather than exposing the same explicit stdout-forwarding bridge.

A real-input black MASTER probe therefore generated a complete product advertisement containing product, Logo, copy, and pedestal instead of the required empty background.

That probe is **INVALID AS A PRODUCTION BASELINE SAMPLE**.

It does not prove that the frozen prompt fails under the intended Skill runtime.

Classification:

- prompt source: **VERIFIED**
- prompt deterministic assembly/hash: **VERIFIED**
- verbatim delivery through current project harness: **NOT EQUIVALENT**
- current-project visual MASTER sample: **INVALID**

Do not rewrite the production prompt during Phase 0 merely to compensate for this harness mismatch.

---

## 7. Evaluation table

`docs/phase-0/evaluation-results.csv` now contains the three authoritative HUAWEI cases only:

- black MASTER
- orange SKU
- white SKU

The black row records the frozen prompt SHA and notes the invalid real-input probe.

Generated-background hashes, final-composite hashes, and visual scores remain empty until a valid prompt-delivery runtime produces a faithful sample.

---

## 8. Phase 0 completion checklist

- [x] Pin repository baseline commit and relevant blob identities.
- [x] Freshly execute `scripts/test_workflow.py` in repository CI.
- [x] Verify deterministic workflow baseline passes.
- [x] Verify current OpenAI Images 2.5 model/API capabilities needed for planning.
- [x] Verify transparent and non-transparent background behavior in the callable surface.
- [x] Attempt custom-size validation and correct the record to **runtime unverified** rather than false FAIL.
- [x] Attempt image-edit/reference behavior and record current-harness limitation.
- [x] Replace synthetic visual acceptance set with authoritative Google Drive HUAWEI assets and copy.
- [x] Freeze the real black MASTER prompt and input hashes.
- [x] Test the current project-conversation prompt-delivery path.
- [x] Record the project-harness mismatch without changing production behavior.
- [ ] Produce a valid black MASTER background through a runtime that can demonstrate exact repository prompt delivery.
- [ ] Locally composite and inspect the black MASTER candidate.
- [ ] Explicitly lock a representative MASTER for the baseline.
- [ ] Produce orange and white baseline SKU outputs with the frozen reference-guided workflow.
- [ ] Fill all required visual scores and output hashes.

Phase 0 is not complete until the remaining visual baseline items have valid evidence.

---

## 9. Next valid action

Do **not** spend additional project-conversation image calls trying to tune around the harness mismatch.

The next valid Phase 0 action is to execute the frozen Skill through its actual intended runtime, or create a clearly separated API test harness that passes the exact archived prompt and reference image explicitly.

Only then can the black MASTER visual baseline be accepted.
