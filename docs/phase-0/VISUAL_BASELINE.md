# Phase 0 Visual Baseline

Status: **AUTHORITY INPUT SET FROZEN / VALID VISUAL BASELINE PENDING**

Date: 2026-09-09

This document defines the fixed visual baseline used to compare the existing `md3-product-image` workflow with later Images 2.5 changes.

The visual authority set is now the real HUAWEI WATCH FIT 5 Pro material stored in the project Google Drive folder. Synthetic fixtures remain available only for deterministic script/regression checks and are not used for visual acceptance.

---

## 1. Frozen production baseline

Production behavior is compared against:

`128d8b2f1197f1a17aed34a61c82ac5fc6284736`

That commit is the Phase 0 frozen behavior point established before Images 2.5 implementation changes.

---

## 2. Authoritative visual input set

The authoritative source definition is:

`docs/phase-0/AUTHORITY_INPUTS.md`

The fixed Phase 0 sequence is:

1. MASTER: Google Drive asset `黑`
2. SKU A: Google Drive asset `橙`
3. SKU B: Google Drive asset `白`

All three use the same authoritative source Logo:

`HUAWEI-LOGO`

All three use the exact copy from the Drive file `信息`:

```text
完整产品名称：HUAWEI WATCH FIT 5 Pro
产品名称显示行数：两行
产品名称第一行：HUAWEI
产品名称第二行：WATCH FIT 5 Pro
版本文字：Глобальная версия
```

No synthetic product is allowed to replace these files in a visual ablation or acceptance run.

---

## 3. Current layout contract

The canonical local composition canvas remains:

```text
1536 × 2048
```

Using the current baseline layout policy, authoritative Logo and text resolve to:

```text
FINAL_INFORMATION_SAFE_ZONE: x 0.0%-75.0%, y 0.0%-40.8%
```

This value is part of the current baseline only. Future implementation changes must regenerate it rather than hard-code it as a permanent product constant.

---

## 4. Evaluation rows

`docs/phase-0/evaluation-results.csv` contains three visual baseline rows:

- one MASTER row for `黑`
- one SKU row for `橙`
- one SKU row for `白`

Every row is bound to:

- its role,
- the frozen production baseline commit,
- the exact product SHA-256.

Generated-background hashes, final-composite hashes and visual scores are recorded only after a valid run satisfies the repository workflow contract.

---

## 5. Valid MASTER baseline run

The MASTER run is valid only if all of the following are true:

1. the exact Drive `黑` PNG is supplied as the product palette reference;
2. the exact Drive `HUAWEI-LOGO` PNG is used for local deterministic composition;
3. the exact authoritative copy is used;
4. the existing `references/image-gen-prompt.txt` is used without Images 2.5 prompt restructuring;
5. `scene_prompt.py` semantics are preserved, including the measured information safe zone and current product-area policy;
6. one image-model operation is used for the attempt;
7. the image model returns an empty background plate only;
8. no product, Logo, text, product shadow, floor, table or display stand is generated into the background;
9. the returned background is saved unchanged before local composition;
10. the normal local product / fixed shadow / Logo / text composition path creates the final candidate;
11. there is no automatic aesthetic retry;
12. prompt, source, background and final-composite hashes are recorded.

A result that violates the empty-background contract is an invalid delivery, not a low-scoring baseline image.

---

## 6. Valid SKU baseline runs

A SKU run is valid only after the `黑` MASTER has been generated and explicitly locked.

The current baseline SKU behavior must remain unchanged:

- locked `ORIGINAL_MASTER_BACKGROUND.png` is the composition reference;
- `橙` or `白` is the current SKU product/palette reference;
- `references/replace-variant-block.md` remains the baseline SKU instruction;
- the model generates a new empty SKU background using the current master-reference workflow;
- no future constrained-edit or palette-only implementation is substituted into the baseline;
- local deterministic composition creates the final SKU image;
- hashes and scores are recorded.

---

## 7. Visual scoring

Use an integer `1–5` scale where applicable:

- `1` = materially poor / clear failure
- `2` = weak
- `3` = acceptable baseline
- `4` = good
- `5` = very strong

Positive metrics:

- `background_quality`
- `classic_md3_adherence`
- `palette_harmony`
- `safe_zone_cleanliness`
- `sku_composition_consistency`

Negative metrics:

- `unwanted_product_copying`
- `product_like_geometry`
- `accidental_text_or_logo`
- `unexpected_physical_environment`

For negative metrics:

- `1` = none observed
- `2` = minor
- `3` = noticeable
- `4` = significant
- `5` = severe

Invalid deliveries that break the background-only contract are not assigned normal visual scores; they are recorded separately as invalid probes.

---

## 8. First real-input probe

The Drive assets were successfully materialized into the active runtime, which confirms that the real product and Logo files can be bound as runtime inputs.

A first MASTER probe was then attempted with `黑` as the intended palette reference and the current baseline prompt contract.

Observed output:

```text
returned raster: 1086 × 1448
mode: RGB
```

The image contained:

- a generated watch,
- generated HUAWEI Logo,
- generated product-name text,
- generated version text,
- a physical display pedestal.

This violates the current background-only contract and therefore cannot be accepted as a MASTER baseline result.

The returned image SHA-256 was:

`c6892f807f39087b441633a47dc7146e66b4aeedbb73225972d6c3413b1879e6`

This hash is retained only as evidence of an invalid runtime probe.

---

## 9. Current execution state

- real Drive product references: **READY**
- real Drive Logo: **READY**
- authoritative copy: **READY**
- source SHA binding: **READY**
- deterministic workflow baseline: **PASS**
- current baseline MASTER prompt definition: **READY**
- valid empty-background MASTER delivery: **PENDING**
- locked MASTER: **PENDING**
- `橙` SKU baseline: **BLOCKED BY MASTER**
- `白` SKU baseline: **BLOCKED BY MASTER**

The blocker is no longer source-image availability. The blocker is reliable execution of the repository's complete background-only prompt contract through the currently callable image runtime.

---

## 10. Completion condition

The visual baseline is complete only when the three CSV rows contain valid accepted deliveries with:

- attempt id,
- prompt SHA-256,
- generated-background SHA-256,
- final-composite SHA-256,
- resolved output dimensions,
- required visual scores,
- notes for any observable failure.

Until then, Phase 0 is **authority-input complete but visual-baseline incomplete**.
