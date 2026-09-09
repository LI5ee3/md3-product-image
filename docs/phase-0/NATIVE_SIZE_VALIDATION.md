# Native Size Validation

Status: **PARTIAL PASS — API CONTRACT VERIFIED; SKILL RUNTIME PIXEL OUTPUT NOT YET EMPIRICALLY VERIFIED**

Date: 2026-09-09

This Phase 0 check evaluates whether the canonical `1536 × 2048` canvas used by `md3-product-image` is valid for GPT Image 2.5 and whether the current Skill runtime exposes a compatible size control.

No production code or Skill behavior is changed by this validation.

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

Documented constraints:

- width and height must both be multiples of 16,
- aspect ratio must be between `1:3` and `3:1`,
- neither edge may exceed `3840` pixels,
- total pixel count must be between `655,360` and `8,294,400` pixels,
- resolutions above `2560 × 1440` are experimental.

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

Because the portrait height is 2048, this resolution is not above the documentation's `2560 × 1440` experimental boundary by total long-edge comparison in the same orientation-independent sense normally intended for that note; nevertheless the Skill must rely on actual output validation rather than assuming exact raster delivery from documentation alone.

## Current Skill runtime contract

The image-generation tool exposed to the current Skill runtime includes a `size` argument represented as a string.

This is structurally compatible with the documented GPT Image 2.5 custom-size form:

```text
1536x2048
```

However, the runtime tool schema does not enumerate accepted size values and does not itself guarantee that the returned raster will be exactly the requested dimensions.

Therefore the following distinction is mandatory:

- **API validity:** verified.
- **Current runtime exposes a size field:** verified.
- **Current runtime empirically returns exactly 1536 × 2048 pixels:** not yet verified.

## ChatGPT product-level evidence

Current ChatGPT Images documentation states that ChatGPT Images 2.5 can generate images in any aspect ratio and supports choosing or requesting a desired aspect ratio.

This supports use of a 3:4 request at the product level, but does not replace pixel-dimension verification for the Skill workflow.

## Required empirical probe

The remaining runtime test is deliberately narrow:

1. invoke the current Skill image-generation runtime once with `size="1536x2048"`,
2. use a trivial disposable prompt unrelated to production visual quality,
3. inspect the delivered raster dimensions,
4. record the exact returned width and height,
5. mark PASS only if the raster is exactly `1536 × 2048`,
6. do not retry automatically if the request fails or returns another size.

The probe must not be used to judge style, palette, composition, or quality. Those are separate Phase 0 visual-baseline tasks.

## Decision

At this point it is safe to state that `1536 × 2048` is a documented GPT Image 2.5-compatible size and that the current Skill runtime has a compatible size parameter.

It is **not yet safe** to remove any resize/fallback path or to declare native-size delivery complete until one actual Skill-runtime raster has been inspected and confirmed to be exactly `1536 × 2048`.
