# Phase 6 — Model and Quality Runtime Policy Results

Status: **C0 COMPLETE / C1 REFERENCE-ISOLATION PENDING**

Date: 2026-09-10

## Valid C0 evidence

The isolated fresh-session Work probe completed with:

```text
probe: phase6-c0-runtime-controls-r2
probe_package_id: PHASE6-C0-R2-20260910
image_model_operations: 0
conclusion: RUNTIME_CONTROL_SCHEMA_CONFIRMED
```

The package identity matched the isolated Phase 6 R2 probe, so this result is valid runtime-interface evidence rather than the earlier Phase 4 Skill-instance collision.

## Controls not exposed to the Skill

The real Work + Skill Image Gen callable interface does **not** expose directly settable parameters for:

| Concept | Parameter | Directly settable |
| --- | --- | --- |
| model selection | none | no |
| quality / effort | none | no |
| output size / resolution | none | no |
| background / transparency | none | no |
| output format | none | no |
| image action / mode | none | no |

No enum values or defaults for those concepts are available to the Skill because no callable parameters are exposed.

This independently aligns with Phase 4: the current Work Skill surface does not expose an explicit edit action/mode selector.

## Controls explicitly exposed

### `prompt`

```text
type: string
required callable argument
directly_settable_by_skill: true
```

### `num_last_images_to_include`

```text
type: integer | null
directly_settable_by_skill: true
tool guidance maximum: 5
```

The callable declaration did not expose a default value or a complete allowed range.

### `referenced_image_paths`

```text
type: array<string> | null
directly_settable_by_skill: true
```

## C0 decision

There is no valid model/quality/size/background/output-format ablation to run on the current Work Skill surface because those variables are not callable controls.

Do not hard-code or document unsupported public-API parameters as production Skill behavior.

No model or quality A/B follows C0.

## C1 requirement

Before adopting explicit conversation-image isolation in production, validate one real call with:

```text
num_last_images_to_include = 0
referenced_image_paths = [deterministic palette-reference.png]
```

using the real HUAWEI black source to construct the palette reference locally.

C1 exists because the C0 callable declaration exposed `integer | null` and a maximum, but did not declare a full allowed range or default. The project will not assume that zero is accepted until the real Work call proves it.

If C1 passes, production MASTER/SKU calls can explicitly use zero recent conversation images and exact `referenced_image_paths`, strengthening the Phase 3 palette-only contract.

If C1 fails, the project records the limitation and does not claim strict recent-image isolation.

## Current decision

```text
Runtime control schema: CONFIRMED
Model selection configurable: NO
Quality configurable: NO
Output size configurable: NO
Background mode configurable: NO
Output format configurable: NO
Explicit edit/action configurable: NO
Prompt configurable: YES
Recent conversation-image inclusion configurable: YES
Explicit reference-image paths configurable: YES
Run model/quality A/B: NO
Adopt num_last_images_to_include=0: PENDING C1
```
