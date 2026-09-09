# Native Size Validation

Status: **REAL PRODUCTION OUTPUT OBSERVED AT 1086 × 1448 / 1536 × 2048 UI REPORT MISMATCH**

Date: 2026-09-09

This Phase 0 check evaluates whether the canonical `1536 × 2048` canvas used by `md3-product-image` is valid for GPT Image 2.5 and what raster size is actually delivered by the real Skill runtime.

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

## Invalidated conversational probes

Earlier project-conversation probes intended to test `1536 × 2048` and `1086 × 1448` are excluded from evidence because the callable chat image surface did not demonstrably carry the requested explicit size parameter. Those probes remain invalid and are not retroactively scored.

## Real production Skill evidence

A real `md3-product-image v2.0` run was executed in ChatGPT Work using the authoritative HUAWEI source set.

The Skill reported the logical/final master size in its UI as:

```text
1536 × 2048 (3:4)
```

The user then downloaded/supplied the locked `ORIGINAL_MASTER_FINAL.png` result for direct raster inspection.

The delivered PNG is:

```text
width: 1086
height: 1448
aspect ratio: 3:4
format: PNG
mode: RGBA
alpha extrema: 255..255
SHA-256: 083d625d2a039ca565fbaf548c55e58714c6770601b1fcb1141f5360201f286f
```

This is a real production Skill output and therefore materially stronger evidence than the earlier conversational probes.

## Interpretation

The current evidence demonstrates a mismatch between the Work/Skill-reported logical canvas and the raster delivered back to the user:

```text
reported logical/final canvas: 1536 × 2048
actual delivered PNG raster:   1086 × 1448
```

Both are exact 3:4 canvases, but they are not pixel-identical resolutions.

This means Phase 1 must not assume that a `1536 × 2048` logical composition canvas guarantees a `1536 × 2048` user-visible PNG.

The observation also provides the first valid real-runtime evidence that `1086 × 1448` is an actual production output size in the current Work/Skill path.

It does **not** yet establish that explicitly requesting `1086x1448` will always return that size, nor that every run is stable at this resolution. Stability still requires repeated real production outputs.

## Consequence for Phase 1

1. Keep `1536 × 2048` as the canonical deterministic logical composition canvas unless later evidence supports changing it.
2. Add final-raster dimension inspection as a required validation step.
3. Do not claim native exact `1536 × 2048` delivery in the current Work runtime.
4. Preserve resize/output-normalization logic until the source of the `1536×2048 -> 1086×1448` conversion is identified.
5. Treat `1086 × 1448` as an observed production delivery size, not yet a guaranteed requested-size contract.
6. Repeat the same inspection for the orange and white SKU outputs to determine whether the delivered raster size is stable across variants.

## Decision

**GPT Image 2.5 API accepts the canonical custom size, but the real ChatGPT Work Skill run reported 1536×2048 while delivering a 1086×1448 PNG. Phase 1 must explicitly account for this runtime/output normalization behavior.**
