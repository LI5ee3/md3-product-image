# Phase 6 — Model and Quality Runtime Policy

Status: **COMPLETED**

Date: 2026-09-10

## Objective

Determine which Images 2.5 generation controls are actually exposed to the real ChatGPT Work + Skill runtime, then test only those controls that the production Skill can genuinely invoke.

Public API capability is not authority for the Work Skill surface.

## C0 transport history

The first attempts in the existing Work conversation were invalid because that conversation continued resolving the older Phase 4 Skill instance even after a renamed Phase 6 package was installed.

Those attempts:

- performed zero image-model operations,
- did not establish the Image Gen callable schema,
- were excluded from Phase 6 evidence.

The valid rerun used a fresh Work conversation and the isolated identity:

```text
name: phase6-runtime-control-probe-r2
PROBE_PACKAGE_ID: PHASE6-C0-R2-20260910
```

## Valid C0 result

The fresh-session R2 probe returned:

```text
RUNTIME_CONTROL_SCHEMA_CONFIRMED
```

with zero image-model operations.

### Not exposed

No directly settable callable parameter exists for:

- model selection,
- quality / effort,
- output size / resolution,
- background mode / transparency,
- output format,
- image action / mode.

Therefore no model/quality/size/background/output-format ablation is valid on the current Work Skill surface.

### Exposed

The callable interface exposes:

```text
prompt: string
num_last_images_to_include: integer | null
referenced_image_paths: array<string> | null
```

## C1 — Combined selectors

C1 used a fresh Work conversation and performed exactly one Image Gen attempt with:

```text
num_last_images_to_include = 0
referenced_image_paths = [deterministic palette-reference.png]
```

The runtime rejected the invocation with:

```text
provide only one of `referenced_image_paths` or `num_last_images_to_include`
```

Result:

```text
REFERENCE_ISOLATION_CALL_REJECTED
```

This is valid runtime evidence. It proves these two controls are mutually exclusive on the tested Work Image Gen callable surface.

No background was generated and no production MASTER/SKU file was created or modified.

### C1 decision

Do **not** set `num_last_images_to_include=0` together with `referenced_image_paths` in production.

The project requires exact local reference files for its deterministic MASTER/SKU reference contract, so `referenced_image_paths` takes precedence.

## C2 — Explicit reference-path mode

C2 then tested the production-relevant alternative:

```text
prompt = exact C2 empty-background prompt
referenced_image_paths = [deterministic palette-reference.png]
```

with `num_last_images_to_include` omitted entirely from the call.

The complete `黑.png` was used locally only to produce the deterministic palette reference and was not passed to Image Gen.

The call succeeded and returned:

```text
EXPLICIT_REFERENCE_PATH_CALL_ACCEPTED
```

with exactly one image-model operation and no retry.

The returned raw background was directly inspected as:

```text
1086 × 1448
RGBA
fully opaque
sha256 d9f5b6fa0389b4a3475352c79509a09ac35e80e725fe5caba7344f697e4a99b9
```

## Accepted production callable contract

Production Image Gen calls use:

```text
prompt = exact deterministic scene prompt
referenced_image_paths = exact explicit authority list
```

and **omit `num_last_images_to_include` entirely**.

MASTER:

```text
referenced_image_paths = [palette-reference.png]
```

SKU:

```text
referenced_image_paths = [ORIGINAL_MASTER_BACKGROUND.png, current-SKU-palette-reference.png]
```

The complete product/SKU artwork remains local and must not be listed in `referenced_image_paths`.

## Unsupported controls

Do not write public API model names or unsupported quality/size/background/output-format/action controls into `SKILL.md`.

Do not run model/quality A/B tests until the Work Skill runtime actually exposes such controls.

## Phase 6 acceptance

Phase 6 is complete because:

1. the real Work callable schema was enumerated in a fresh isolated session,
2. unsupported controls were excluded from the production contract,
3. the mutual-exclusion behavior of the two reference selectors was proven,
4. explicit `referenced_image_paths`-only mode was proven by a real Image Gen call,
5. the accepted mode matches the Phase 3 deterministic palette-only architecture.

Detailed evidence is in `docs/phase-6/RESULTS.md`.
