# Phase 6 — Model and Quality Runtime Policy

Status: **COMPLETED / NO MODEL-QUALITY CONTROLS EXPOSED**

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

## Production policy

The accepted production call boundary is now explicit:

```text
prompt = deterministic scene prompt
num_last_images_to_include = 0
referenced_image_paths = exact explicit authority list
```

MASTER references:

```text
[palette-reference.png]
```

SKU references:

```text
[ORIGINAL_MASTER_BACKGROUND.png, current-SKU-palette-reference.png]
```

The complete product/SKU artwork remains local and must not be sent to Image Gen.

This prevents recent conversation images from being implicitly added to the model context and strengthens the Phase 3 palette-only isolation contract.

## Decision

Do not write public API model names or unsupported quality/size/background/output-format/action controls into `SKILL.md`.

Do not run model/quality A/B tests until the Work Skill runtime actually exposes such controls.

Phase 6 is complete. Detailed evidence is in `docs/phase-6/RESULTS.md`.
