# Phase 0 Authority Inputs

Status: **ACTIVE AUTHORITY SET**

Date: 2026-09-09

All visual tests from this point forward use the assets and copy in the project Google Drive folder `md3-product-image` as the authoritative input set.

The earlier synthetic fixtures under `docs/phase-0/fixtures/` are retained only for deterministic script/regression testing. They are not part of the visual acceptance set unless this document is explicitly changed later.

## Google Drive source folder

Folder ID:

`1GhPhrjxLA4vLUI9FXXafe3gMLBsnR5Yj`

## Product and Logo assets

| Role | Drive title | Drive file ID | Raster | Mode | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| MASTER product | `黑` | `1_NT5nVYL6T_v-g_XnHzESSCx_hI3MkDy` | 3000×4000 | RGBA | `b0739efd15f379ea5654fdaedf11bacd36590817a17006f7027d7f1a2ae40fe8` |
| SKU product A | `橙` | `1l_08hprGvn-Gc0EQdFVACCIjGPTuLo_-` | 3000×4000 | RGBA | `decffdcf0aaaa4f38346c7bb33e5621a6780a35d3feb487ebe151b19530e6e76` |
| SKU product B | `白` | `1auFnwwbQbk1aXePBOgpG4R_yEKvosZJe` | 3000×4000 | RGBA | `43b4f6658956cfcf97fda96f0df8862df5d811c791dc24bc48373edad41a46b4` |
| Logo | `HUAWEI-LOGO` | `1x9tiPyVsTwq66q1_9KiP43J2KNFTit67` | 2500×1887 | RGBA | `9d71ef4893d1858d0f2f42d7570e53375329eac4f7132614df99d356d9a3eae0` |

The order above is the fixed Phase 0 visual sequence:

1. `黑` establishes the MASTER.
2. `橙` is the first SKU variant.
3. `白` is the second SKU variant.

## Authoritative copy

Source file title: `信息`

Drive file ID:

`1aV3UKiiv6MkSWdaZOiRb4FIzr4nFpzAI`

Exact content:

```text
完整产品名称：HUAWEI WATCH FIT 5 Pro
产品名称显示行数：两行
产品名称第一行：HUAWEI
产品名称第二行：WATCH FIT 5 Pro
版本文字：Глобальная версия
```

Mapped Skill inputs:

- complete product name: `HUAWEI WATCH FIT 5 Pro`
- `TITLE_LINES`: `2`
- title line 1: `HUAWEI`
- title line 2: `WATCH FIT 5 Pro`
- version: `Глобальная версия`

These values must not be inferred, rewritten, translated, normalized, or substituted during the test series.

## Current MASTER safe-zone measurement

Using the current layout policy on the canonical 1536×2048 logical canvas, the authoritative copy and HUAWEI Logo resolve to the merged prompt safe zone:

```text
FINAL_INFORMATION_SAFE_ZONE: x 0.0%-75.0%, y 0.0%-40.8%
```

This measurement belongs to the current baseline layout contract and should be recalculated by the repository implementation whenever the layout implementation changes.

## Change-control rule

If any Drive source file or `信息` content changes, its current bytes/content must be re-read and the corresponding baseline hashes/metadata updated before another visual comparison is accepted.
