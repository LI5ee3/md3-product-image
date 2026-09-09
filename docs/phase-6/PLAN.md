# Phase 6 — Model and Quality Runtime Policy

Status: **IN PROGRESS / C0 COMPLETE / C1 REJECTED / C2 EXPLICIT-PATHS NEXT**

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

The callable declaration did not expose defaults for these controls except that `prompt` is required; Work guidance reported a maximum of 5 for `num_last_images_to_include`.

## C1 — Combined recent-image and explicit-path isolation

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

C2 validates the production-relevant alternative selected after C1.

Use a fresh Work conversation with the isolated C2 Skill package and the real HUAWEI `黑.png` source.

The complete `黑.png` is used locally only to produce the deterministic `palette-reference.png` and must not be passed to Image Gen.

Perform exactly one Image Gen call with:

```text
prompt = exact C2 empty-background prompt
referenced_image_paths = [deterministic palette-reference.png]
```

Critically:

```text
num_last_images_to_include
```

must be **omitted entirely** from the callable invocation. Do not pass `0`, `null`, or any other value.

The complete `黑.png` must not appear in `referenced_image_paths`.

### C2 acceptance

C2 passes when:

1. the callable accepts explicit `referenced_image_paths` with `num_last_images_to_include` omitted,
2. exactly one image-model operation occurs,
3. no fallback or retry occurs,
4. an accessible generated background is returned,
5. the complete HUAWEI product source was not explicitly passed to Image Gen.

If the call fails, stop without retry and report:

```text
EXPLICIT_REFERENCE_PATH_CALL_REJECTED
```

If the call succeeds, report:

```text
EXPLICIT_REFERENCE_PATH_CALL_ACCEPTED
```

## Production decision after C2

If C2 passes, the production callable contract becomes:

```text
prompt = deterministic scene prompt
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

The complete product/SKU artwork remains local and must not be listed in `referenced_image_paths`.

If C2 fails, record the limitation and do not claim explicit-path production control is valid.

## Model / quality decision

Do not write public API model names or unsupported quality/size/background/output-format/action controls into `SKILL.md`.

Do not run model/quality A/B tests until the Work Skill runtime actually exposes such controls.

Detailed evidence is in `docs/phase-6/RESULTS.md`.
