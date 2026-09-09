# Phase 6 — Model and Quality Runtime Policy Results

Status: **COMPLETED / RUNTIME CONTROLS ENUMERATED**

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

This confirms the Phase 4 finding from another angle: the current Work Skill surface does not expose an explicit edit action/mode selector.

## Controls explicitly exposed

The callable interface exposes only these relevant controls:

### `prompt`

```text
type: string
required callable argument
directly_settable_by_skill: true
```

The production Skill already constructs the complete prompt deterministically and passes it verbatim.

### `num_last_images_to_include`

```text
type: integer | null
directly_settable_by_skill: true
tool guidance maximum: 5
```

The callable declaration did not expose a default value or a complete allowed range.

For deterministic reference isolation, production calls should explicitly use:

```text
num_last_images_to_include = 0
```

rather than allowing recent conversation images to be included implicitly.

### `referenced_image_paths`

```text
type: array<string> | null
directly_settable_by_skill: true
```

Production must use explicit local reference paths only:

MASTER:

```text
[palette-reference.png]
```

SKU:

```text
[ORIGINAL_MASTER_BACKGROUND.png, current-SKU-palette-reference.png]
```

The complete product/SKU artwork remains local and must not be listed in `referenced_image_paths`.

## Production decision

There is no valid model/quality/size/background/output-format ablation to run on the current Work Skill surface because those variables are not callable controls.

Do not hard-code or document unsupported public-API parameters as production Skill behavior.

The only Phase 6 production change is reference-context isolation:

```text
prompt = deterministic scene prompt
num_last_images_to_include = 0
referenced_image_paths = exact explicit authority list
```

This strengthens the Phase 3 palette-only contract by preventing recent conversation images from being implicitly included in the Image Gen call.

## No visual A/B required

No model or quality A/B follows C0 because there is no model or quality control to vary.

The reference-context change does not alter the accepted structured prompt, palette extraction, local composition, raster contract, or master/SKU reference roles. It makes the intended reference set explicit at the callable boundary.

A final end-to-end production smoke test belongs in Phase 7 after all accepted deterministic changes are consolidated.

## Final decision

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
Adopt explicit reference-context isolation: YES
```
