# Phase 6 — Model and Quality Runtime Policy

Status: **IN PROGRESS / C0 COMPLETE / C1 REFERENCE-ISOLATION NEXT**

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

## C1 — Explicit reference-isolation call

C1 validates the only newly discovered production-relevant control before adoption.

Use a fresh Work conversation with the isolated C1 Skill package and the real HUAWEI `黑.png` source.

The complete `黑.png` remains a recent conversation image and is used locally only to build the deterministic palette reference.

C1 then performs exactly one Image Gen call with:

```text
prompt = exact C1 empty-background prompt
num_last_images_to_include = 0
referenced_image_paths = [deterministic palette-reference.png]
```

The complete `黑.png` must not appear in `referenced_image_paths`.

### C1 acceptance

C1 passes when:

1. the callable Image Gen operation accepts `num_last_images_to_include=0`,
2. the callable operation accepts the explicit local palette path in `referenced_image_paths`,
3. exactly one image-model operation occurs,
4. no fallback or retry occurs,
5. the returned image is an empty background rather than an obvious copied HUAWEI WATCH product scene.

Visual inspection is supporting evidence only; callable argument acceptance is the primary gate.

If the call rejects the explicit controls, stop without retry and report:

```text
REFERENCE_ISOLATION_CALL_REJECTED
```

If the call succeeds, report:

```text
REFERENCE_ISOLATION_CALL_ACCEPTED
```

## Production decision after C1

If C1 passes, production Image Gen calls should explicitly use:

```text
num_last_images_to_include = 0
referenced_image_paths = exact explicit authority list
```

MASTER:

```text
[palette-reference.png]
```

SKU:

```text
[ORIGINAL_MASTER_BACKGROUND.png, current-SKU-palette-reference.png]
```

The complete product/SKU artwork remains local and must not be sent to Image Gen.

If C1 fails, do not assume that zero recent-image inclusion can be enforced by the Skill; retain the current explicit reference-role instructions and record the runtime limitation.

## Model / quality decision

Do not write public API model names or unsupported quality/size/background/output-format/action controls into `SKILL.md`.

Do not run model/quality A/B tests until the Work Skill runtime actually exposes such controls.

Detailed C0 evidence is in `docs/phase-6/RESULTS.md`.
