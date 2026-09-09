# Prompt Delivery Validation

Status: **HARNESS MISMATCH CONFIRMED**

Date: 2026-09-09

This Phase 0 check determines whether the image-generation surface used in the current project conversation is equivalent to the execution path required by the repository `SKILL.md`.

No production Skill behavior is changed by this validation.

---

## 1. Repository execution contract

The frozen `SKILL.md` requires the following sequence:

1. `scripts/scene_prompt.py build` writes the complete Image Gen prompt to stdout.
2. The successful stdout is captured.
3. That stdout is passed **verbatim** to Image Gen in the same tool flow.
4. The product image is supplied only as a palette reference for MASTER.
5. Image Gen must return an empty background plate only.
6. The generated background is then passed to the local deterministic composition pipeline.

The frozen Skill additionally documents an execution bridge using `functions.exec` and `generatedImage(result)`.

This means a faithful baseline run requires a runtime in which the exact prompt emitted by `scene_prompt.py` can be forwarded as the actual image-generation instruction.

---

## 2. Current project-conversation image surface

The image-generation surface callable in the current project conversation is not equivalent to that repository contract.

Observed properties in this harness:

- the image operation derives its effective generation instruction from conversation context;
- the repository's documented `functions.exec -> generatedImage(result)` bridge is not exposed as the callable path used here;
- therefore the Phase 0 prompt text cannot be proven to have been forwarded verbatim as the effective image-model instruction through this harness.

This distinction is important: an image generated in this conversation can test broad ChatGPT Images behavior, but it cannot automatically be treated as evidence that the frozen Skill's stdout-forwarding path behaved the same way.

---

## 3. Real-input probe evidence

Authoritative inputs were successfully materialized from the project Google Drive folder:

- MASTER product: `黑.png`
- SKU A: `橙.png`
- SKU B: `白.png`
- Logo: `HUAWEI-LOGO.png`
- copy: `信息`

The frozen MASTER prompt for the black product was built and archived at:

`docs/phase-0/huawei-watch-fit-5-pro/master-prompt-black.txt`

Prompt SHA-256:

`12148360c40fe556ee8304c68a3914aa69e380d9fd75863b29809eac6a01a773`

The prompt contract explicitly requires an empty background and forbids product, Logo, text, product shadow, floor, table, and display stand.

One project-conversation image probe was then attempted with the authoritative product available in context.

The returned image contained:

- a rendered smartwatch,
- HUAWEI branding,
- product-name text,
- version text,
- a physical pedestal/display surface.

This output violates the frozen background-only contract and therefore was **not accepted as a MASTER baseline sample**.

---

## 4. Interpretation

The invalid probe must not be used to conclude that `references/image-gen-prompt.txt` itself fails under the repository's intended Skill runtime.

The result demonstrates only that the current project-conversation image harness did not provide evidence of the repository's required verbatim prompt-delivery path.

Accordingly, classify this as:

**PROMPT SOURCE: VERIFIED**  
**PROMPT HASHING/ASSEMBLY: VERIFIED DETERMINISTICALLY**  
**VERBATIM DELIVERY THROUGH CURRENT PROJECT HARNESS: NOT AVAILABLE / NOT EQUIVALENT**  
**REAL MASTER VISUAL BASELINE THROUGH THIS HARNESS: INVALID**

Do not rewrite the production prompt merely to compensate for this harness mismatch during Phase 0.

---

## 5. Official product/API context

OpenAI's current ChatGPT Images documentation confirms that ChatGPT accepts natural-language image creation and editing requests in conversation, while the Images API exposes a separate programmable image-generation surface.

Those public docs do not establish that the current project-conversation image call is the same execution bridge as the repository-specific `functions.exec -> generatedImage(result)` contract.

Therefore API/ChatGPT capability and repository Skill transport must continue to be tracked separately.

---

## 6. Phase 0 consequence

The authoritative HUAWEI source set remains the visual acceptance set.

However, the current project-conversation harness must not be used to populate `generated_background_sha256`, final-composite hashes, or visual scores for a frozen production baseline unless the exact repository prompt-delivery contract can be demonstrated.

The next valid visual baseline must run in one of the following:

1. the actual Skill runtime that exposes the repository's `functions.exec` image bridge; or
2. another runtime/API harness explicitly wired to pass the exact archived prompt and exact reference image as model inputs, with that difference documented as a test harness rather than production behavior.

Until then, the correct status is **visual baseline blocked by prompt-delivery harness mismatch**, not **prompt failed**.
