# Native Size Validation

Status: **API PASS / CURRENT SKILL RUNTIME EXACT-SIZE OUTPUT UNVERIFIED**

Date: 2026-09-09

This Phase 0 check evaluates whether the canonical `1536 × 2048` canvas used by `md3-product-image` is valid for GPT Image 2.5 and whether the current Skill runtime actually returns an exact requested raster size.

No production code or Skill behavior was changed by this validation.

## Canonical project size

The existing project layout uses a canonical portrait canvas of:

```text
1536 × 2048
```

This is exactly 3:4.

Pixel count:

```text
1536 × 2048 = 3,145,728 pixels
```

## OpenAI API contract

The current OpenAI image-generation documentation states that GPT Image 2.5 models support custom dimensions expressed as `WIDTHxHEIGHT` strings.

Documented constraints include:

- width and height must both be multiples of 16,
- aspect ratio must be between `1:3` and `3:1`,
- neither edge may exceed `3840` pixels,
- total pixel count must be between `655,360` and `8,294,400` pixels.

`1536 × 2048` satisfies every hard constraint:

| Constraint | Requirement | 1536 × 2048 | Result |
| --- | --- | --- | --- |
| Width multiple | multiple of 16 | 1536 / 16 = 96 | PASS |
| Height multiple | multiple of 16 | 2048 / 16 = 128 | PASS |
| Aspect ratio | between 1:3 and 3:1 | 3:4 | PASS |
| Maximum edge | <= 3840 | 2048 | PASS |
| Minimum pixels | >= 655,360 | 3,145,728 | PASS |
| Maximum pixels | <= 8,294,400 | 3,145,728 | PASS |

Therefore `1536x2048` is a valid GPT Image 2.5 custom-size request under the documented API contract.

## Current Skill runtime contract

The image-generation tool exposed to the current Skill runtime includes a `size` argument represented as a string.

This is structurally compatible with the documented GPT Image 2.5 custom-size form.

Schema compatibility alone is not sufficient for this project. The delivered raster must be inspected because the local deterministic composition pipeline depends on exact pixel dimensions.

## Invalidated probe record

An earlier Phase 0 note incorrectly marked the current Skill runtime as failing exact `1536 × 2048` output.

That conclusion is withdrawn.

The generated raster that was inspected was real, but the image-generation call used for that probe did **not** actually carry the intended explicit `size="1536x2048"` argument. Therefore the observed `1448 × 1086` output cannot be used as evidence that the runtime rejected or ignored `1536 × 2048`.

The same issue affected a later sequence intended to test `1086 × 1448`: the generated images were influenced by the conversation context and did not constitute valid explicit-size probes.

Those outputs are excluded from the Phase 0 evidence set and must not be scored as PASS or FAIL.

## Current verified state

The distinction is now:

- GPT Image 2.5 API contract accepts `1536x2048`: **verified**.
- `1536 × 2048` satisfies the documented custom-size constraints: **verified**.
- Current Skill runtime exposes a `size` field: **verified**.
- Current Skill runtime empirically returns exactly `1536 × 2048` when that explicit argument is applied: **not yet verified**.
- Current Skill runtime empirically returns exactly `1086 × 1448` when that explicit argument is applied: **not yet verified**.

## Required valid probe

A valid runtime probe must satisfy all of the following:

1. the tool call must explicitly carry the target `size` argument,
2. the generated content must be disposable and unrelated to the evaluation result,
3. the returned file must be inspected directly with Pillow or an equivalent raster reader,
4. generated text claiming a dimension must never be treated as evidence,
5. no automatic retry is allowed,
6. each result must record requested size, actual width, actual height, format, and alpha mode.

For the proposed fallback-sized experiment, run three independent calls with:

```text
size="1086x1448"
```

and mark that candidate stable only if all three returned files are exactly `1086 × 1448`.

## Consequence for Phase 1

Until a valid explicit-size probe is completed:

1. do not remove the existing resize/fallback path,
2. add deterministic validation of every returned background raster before composition,
3. keep `1536 × 2048` as the canonical local composition canvas,
4. do not assume either `1536 × 2048` or `1086 × 1448` is a guaranteed generation raster,
5. keep native-size behavior conditional on empirical runtime evidence.

## Decision

**The GPT Image 2.5 API contract supports the canonical custom size, but exact custom-size delivery by the current Skill runtime remains unverified.**

No Phase 1 implementation decision should rely on the invalidated probes.
