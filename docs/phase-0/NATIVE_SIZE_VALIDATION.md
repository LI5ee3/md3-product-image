# Native Size Validation

Status: **API PASS / CURRENT SKILL RUNTIME FAIL FOR EXACT NATIVE SIZE**

Date: 2026-09-09

This Phase 0 check evaluates whether the canonical `1536 × 2048` canvas used by `md3-product-image` is valid for GPT Image 2.5 and whether the current Skill runtime actually returns that exact raster size.

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

This is structurally compatible with the documented GPT Image 2.5 custom-size form:

```text
1536x2048
```

However, schema compatibility is not sufficient for this project. The delivered raster must be inspected because the local deterministic composition pipeline depends on exact pixel dimensions.

## Empirical runtime probe

A disposable image-generation probe was issued through the current ChatGPT image runtime with the target size `1536x2048`.

The delivered PNG was then opened directly with Pillow and inspected from the actual raster file rather than trusting any generated text or visual appearance.

Observed raster properties:

```text
Requested size: 1536 × 2048
Returned size:  1448 × 1086
Returned ratio: 4:3 landscape
Format:         PNG
Color mode:     RGB
Alpha channel:  no
```

Observed result:

- exact width match: **FAIL**
- exact height match: **FAIL**
- requested 3:4 orientation preserved: **FAIL**
- PNG delivery: **PASS**
- opaque RGB raster: **PASS**

The runtime therefore did not deliver the requested canonical canvas size in this test.

Disposable outputs inspected during this runtime check consistently resolved to `1448 × 1086`, which reinforces that the current ChatGPT image runtime should not be treated as a pixel-exact custom-size interface for this Skill.

## Important interpretation

This result does **not** mean GPT Image 2.5 API custom sizes are unsupported.

It means only that the **current Skill/ChatGPT image runtime available in this environment did not honor `1536x2048` as the final delivered raster size**.

The distinction is:

- GPT Image 2.5 API contract accepts `1536x2048`: **verified**.
- Current Skill runtime exposes a `size` field: **verified**.
- Current Skill runtime empirically returns exactly `1536 × 2048`: **failed in this probe**.

## Consequence for Phase 1

Phase 1 must not assume native `1536 × 2048` delivery from the current Skill runtime.

Therefore:

1. do not remove the existing resize/fallback path,
2. add deterministic validation of every returned background raster before composition,
3. retain an explicit conversion path to the canonical `1536 × 2048` canvas when the runtime returns another size,
4. do not silently crop or distort; conversion policy must be defined and tested,
5. keep the native-size path conditional so it can become the preferred path later if the runtime begins returning the exact requested dimensions.

## Decision

**Native custom size is supported by the GPT Image 2.5 API contract but is not reliable as an exact delivered raster in the current Skill runtime.**

For this repository, `1536 × 2048` remains the canonical local composition size, not a guaranteed image-generation output size.
