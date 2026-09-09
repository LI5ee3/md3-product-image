# Phase 6 — Model and Quality Runtime Policy Results

Status: **C0 COMPLETE / C1 VALID FAILURE / C2 PENDING**

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

## C2 requirement

C2 must validate one real call with:

```text
referenced_image_paths = [deterministic palette-reference.png]
```

while omitting `num_last_images_to_include` entirely from the invocation.

Do not pass zero or null.

If accepted, this becomes the callable-boundary production reference contract for MASTER and SKU operations.

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
Recent conversation-image selector configurable: YES
Explicit reference-image paths configurable: YES
Both selectors may be combined: NO
Run model/quality A/B: NO
Adopt num_last_images_to_include=0: NO
C2 explicit referenced_image_paths-only validation: PENDING
```
