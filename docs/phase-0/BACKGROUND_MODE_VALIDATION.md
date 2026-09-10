# Background Mode Validation

Status: **PASS**

Date: 2026-09-09

This Phase 0 check validates the behavior of the current Skill image-generation runtime when the `transparent_background` control is explicitly set.

No production Skill code or prompt was changed.

## Scope

This validation covers background/alpha behavior only. It does not validate visual quality, native custom-size delivery, model selection, quality tiers, or edit/reference fidelity.

Two explicit runtime probes were used:

1. `transparent_background=true`
2. `transparent_background=false`

The returned PNG files were inspected directly with Pillow. Generated text or visual claims inside the images were not treated as evidence.

## Probe A — transparent background

Runtime control:

```text
transparent_background=true
```

Observed raster properties:

```text
Format:      PNG
Size:        1688 × 932
Color mode:  RGBA
Alpha range: 0–255
```

Direct pixel inspection found fully transparent pixels (`alpha = 0`) as well as partially/fully opaque pixels.

Measured values:

- total pixels: `1,573,216`
- fully transparent pixels (`alpha = 0`): `138,542`
- alpha minimum: `0`
- alpha maximum: `255`
- SHA-256: `7241900219b497e17ba3cd2582275342aa5e5de7f6a3a795e4e5781748e07e31`

Result: **PASS**

The current runtime can return a PNG with a real alpha channel when `transparent_background=true` is explicitly applied.

## Probe B — opaque background

Runtime control:

```text
transparent_background=false
```

Observed raster properties:

```text
Format:      PNG
Size:        1448 × 1086
Color mode:  RGB
Alpha:       none
```

Measured values:

- no Alpha channel is present
- SHA-256: `b3227ed92f07d74798360304cc1427445eaafdfc4d071c53410b538766a357a7`

Result: **PASS**

The current runtime returns an opaque RGB PNG when `transparent_background=false` is explicitly applied.

## Interpretation

The `transparent_background` control is empirically exposed and functional in the current Skill runtime:

| Runtime control | Returned mode | Transparent pixels observed | Result |
| --- | --- | --- | --- |
| `true` | RGBA | yes | PASS |
| `false` | RGB | no | PASS |

The raster sizes differed between the two disposable probes because size was not part of this validation. These dimensions must not be used as evidence for or against exact custom-size behavior.

## Consequence for the project

For `md3-product-image`, production background plates should remain explicitly opaque unless a later workflow intentionally requires transparency.

A future implementation may safely request opaque background behavior explicitly when the runtime exposes this control, but local composition must still validate the returned raster mode and dimensions before use.

## Decision

**Background-mode control is verified in the current Skill runtime.**

`transparent_background=true` produces a real alpha-bearing RGBA PNG, while `transparent_background=false` produces an opaque RGB PNG.
