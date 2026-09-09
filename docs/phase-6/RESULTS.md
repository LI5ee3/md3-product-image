# Phase 6 — Model and Quality Runtime Policy Results

Status: **COMPLETED / EXPLICIT REFERENCE PATH MODE ADOPTED**

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

## C1 result — valid failure

The isolated C1 probe executed exactly one Image Gen attempt with:

```text
num_last_images_to_include = 0
referenced_image_paths = [<TEMP_DIR>/palette-reference.png]
```

The complete HUAWEI `黑.png` source was used only for local deterministic palette extraction and was not listed in `referenced_image_paths`.

The runtime rejected the invocation with:

```text
provide only one of `referenced_image_paths` or `num_last_images_to_include`
```

Returned conclusion:

```text
REFERENCE_ISOLATION_CALL_REJECTED
```

Observed effects:

- `image_model_operations: 1` attempted call,
- no generated background returned,
- no fallback or retry,
- no production MASTER/SKU file created or modified.

### C1 interpretation

The tested Work callable surface treats `referenced_image_paths` and `num_last_images_to_include` as mutually exclusive arguments.

Therefore the previously proposed production contract:

```text
num_last_images_to_include = 0
referenced_image_paths = exact authority list
```

is invalid and must not be adopted.

Because this project requires deterministic, exact local reference files, the production-preferred selector is `referenced_image_paths`.

## C2 result — accepted

The isolated C2 probe executed exactly one Image Gen call with:

```text
referenced_image_paths = [<TEMP_DIR>/palette-reference.png]
num_last_images_to_include = OMITTED
```

The complete HUAWEI `黑.png` source was used only for local deterministic palette extraction and was not included in `referenced_image_paths`.

The callable accepted the invocation and returned an accessible empty background.

Returned conclusion:

```text
EXPLICIT_REFERENCE_PATH_CALL_ACCEPTED
```

Observed evidence:

```text
PROBE_PACKAGE_ID: PHASE6-C2-EXPLICIT-REFERENCE-PATH-20260910
image_model_operations: 1
palette color count: 7
```

The returned raw background was inspected directly:

```text
width: 1086
height: 1448
mode: RGBA
alpha extrema: 255..255
sha256: d9f5b6fa0389b4a3475352c79509a09ac35e80e725fe5caba7344f697e4a99b9
```

No MASTER or SKU file was created or modified by the probe.

## Production callable contract

Phase 6 establishes this production Image Gen boundary:

```text
prompt = exact deterministic scene prompt
referenced_image_paths = exact explicit authority list
num_last_images_to_include = OMITTED
```

MASTER:

```text
referenced_image_paths = [palette-reference.png]
```

SKU:

```text
referenced_image_paths = [ORIGINAL_MASTER_BACKGROUND.png, current-SKU-palette-reference.png]
```

The complete product/SKU artwork remains local and must not appear in `referenced_image_paths`.

Do not pass `num_last_images_to_include=0` or `null` together with explicit paths. Omit the parameter entirely.

## Unsupported runtime controls

Do not set or document production values for:

- model selection,
- quality / effort,
- output size / resolution,
- background / transparency,
- output format,
- image action / mode.

Those controls are not directly exposed by the tested Work + Skill callable interface.

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
Recent conversation-image selector configurable: YES
Explicit reference-image paths configurable: YES
Both selectors may be combined: NO
Run model/quality A/B: NO
Adopt num_last_images_to_include=0: NO
Adopt explicit referenced_image_paths-only mode: YES
Phase 6: COMPLETED
```
