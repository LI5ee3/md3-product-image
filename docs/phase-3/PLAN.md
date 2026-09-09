# Phase 3 — Deterministic Palette Reference Ablation

Status: **IN PROGRESS / READY FOR WORK A/B**

Date: 2026-09-09

## Objective

Determine whether Images 2.5 should continue receiving the complete product artwork as the palette reference, or whether a deterministic color-only reference can preserve palette quality while reducing semantic/product-geometry leakage risk.

The production default is **not** changed by this phase until the visual ablation passes.

## Fixed authority inputs

Use only the project Google Drive source set:

- MASTER product: `黑.png`
- SKU A: `橙.png`
- SKU B: `白.png`
- Logo: `HUAWEI-LOGO.png`
- complete product name: `HUAWEI WATCH FIT 5 Pro`
- title line 1: `HUAWEI`
- title line 2: `WATCH FIT 5 Pro`
- version: `Глобальная версия`

The Phase 2 structured-prompt outputs are the A baseline.

## Extraction implementation

`src` equivalent:

```text
scripts/extract_palette.py
```

Current policy:

- 7 representative colors
- source downsample: nearest-neighbor, maximum edge 512
- alpha threshold: 32
- RGB histogram: 5 bits per channel
- 4 dominant-color slots with minimum RGB-distance diversity
- remaining slots reserve saturation-aware accent candidates
- transparent pixels do not contribute to color selection
- after representatives are selected, every visible histogram bin is assigned to its nearest selected color
- `reference_weight` is the full visible-pixel coverage assigned to that representative
- output reference is a 1024 × 256 RGB PNG made only of vertical color bands
- no text, Logo, product silhouette, label, icon, or packaging geometry is present
- identical source pixels and policy produce identical outputs

## Why nearest-color reassignment is required

The first implementation weighted the reference bands only by the individual selected histogram bins. Real HUAWEI testing showed that this could over-emphasize a single dark screen bin in the orange SKU even though orange/cream colors occupy more of the visible product.

That weighting was rejected before visual ablation.

The corrected implementation assigns all visible bins to the nearest representative and therefore makes the reference-band widths describe the whole visible product color distribution.

## Real HUAWEI palette references

### Black MASTER source

Source SHA-256:

```text
b0739efd15f379ea5654fdaedf11bacd36590817a17006f7027d7f1a2ae40fe8
```

Corrected palette JSON SHA-256:

```text
e9f410166556c3e4d80cb8a9647962b557d8b6b37021c709a1c52eacf99f53d6
```

Corrected palette-reference PNG SHA-256:

```text
6aadbbb4341490bd95c7a2bd6ef36c52911d1bf00c581f1b4919c17b902c1f4a
```

Representative colors / full-reference weights:

| Rank | Color | Reference weight |
| ---: | --- | ---: |
| 1 | `#2A2C2D` | 36.60% |
| 2 | `#424445` | 18.76% |
| 3 | `#141719` | 11.50% |
| 4 | `#A4BBD4` | 10.37% |
| 5 | `#3A4C64` | 10.27% |
| 6 | `#4D627C` | 9.62% |
| 7 | `#010101` | 2.87% |

### Orange SKU source

Source SHA-256:

```text
decffdcf0aaaa4f38346c7bb33e5621a6780a35d3feb487ebe151b19530e6e76
```

Corrected palette JSON SHA-256:

```text
2d97130cd290005a586ef2992965052720d79dad3837a7ca5e3ef106dbc87c9d
```

Corrected palette-reference PNG SHA-256:

```text
17d212e5199f2b569162ae92fc1ee52c01341b068d91999cf4d9191d59fb7003
```

Representative colors / full-reference weights:

| Rank | Color | Reference weight |
| ---: | --- | ---: |
| 1 | `#F9E3B4` | 23.92% |
| 2 | `#F97D33` | 22.43% |
| 3 | `#CB3404` | 18.98% |
| 4 | `#F56514` | 16.81% |
| 5 | `#A41C03` | 8.50% |
| 6 | `#7B0C01` | 6.36% |
| 7 | `#010101` | 3.01% |

### White SKU source

Source SHA-256:

```text
43b4f6658956cfcf97fda96f0df8862df5d811c791dc24bc48373edad41a46b4
```

Corrected palette JSON SHA-256:

```text
a5e20946ced24f051430aa373a44dfc9b700107fe19363899cd912d0f13554f6
```

Corrected palette-reference PNG SHA-256:

```text
82a5e0b982ed55952fe47b54cf033c80c900b1b9f2a4b0f82fe634867fa2866c
```

Representative colors / full-reference weights:

| Rank | Color | Reference weight |
| ---: | --- | ---: |
| 1 | `#DCDCDC` | 42.61% |
| 2 | `#F2F2F2` | 18.54% |
| 3 | `#C4C4C4` | 16.35% |
| 4 | `#4394C4` | 10.07% |
| 5 | `#235B94` | 6.22% |
| 6 | `#132C6B` | 3.79% |
| 7 | `#010101` | 2.42% |

## Ablation groups

### A — Phase 2 baseline

Image Gen receives the complete authoritative product image as the palette reference.

Already completed:

- black structured MASTER: PASS
- orange structured SKU: PASS
- white structured SKU: PASS

### B — Palette-only reference

Image Gen receives only `palette-reference.png` for palette information.

The authoritative product image remains available only to the deterministic local product composite; it must not be sent to Image Gen as a palette/semantic reference in B.

## Execution order

Run the ablation in two gates so that one variable can be isolated cleanly.

### Gate B1 — MASTER

1. Fresh Work conversation.
2. Same Phase 2 structured prompt.
3. Same `黑.png` is still used for deterministic local product composition.
4. Send only the black `palette-reference.png` to Image Gen as palette reference.
5. One MASTER generation call only.
6. No automatic retry and no corrective prompt.
7. Lock the first candidate only for raster/final comparison after it has been visually reviewed.

If B1 materially reduces palette quality, stop Phase 3 and retain full-product reference.

### Gate B2 — SKU

Only if B1 passes:

1. Use the palette-only locked MASTER.
2. Orange SKU Image Gen input: locked master background + orange palette-reference only.
3. White SKU Image Gen input: locked master background + white palette-reference only.
4. Original orange/white product images remain local-composition inputs only.
5. One image-model operation per SKU.

## Evaluation metrics

Compare A and B on:

- background quality
- Classic MD3 adherence
- palette harmony
- safe-zone cleanliness
- SKU composition consistency
- unwanted product copying
- product-like geometry
- accidental text / Logo / labels
- unexpected physical environment

## Adoption rule

Palette-only becomes the default only if:

1. palette harmony does not materially regress,
2. background quality does not materially regress,
3. deterministic local composition remains unchanged,
4. product-copying / product-like geometry risk is no worse and preferably lower,
5. both orange and white SKU behavior remain acceptable after the MASTER gate passes.

Otherwise keep the Phase 2 full-product palette reference as the production default and document Phase 3 as a rejected ablation.

## Current deterministic verification

The Phase 3 unit workflow verifies:

- same source -> identical JSON and PNG
- transparent RGB changes do not alter extracted visible colors
- transparent RGB changes do not alter the palette-reference PNG
- fully transparent source -> deterministic failure
- existing workflow regression remains PASS

The visual decision remains a Work-based manual A/B using the authoritative HUAWEI materials above.
