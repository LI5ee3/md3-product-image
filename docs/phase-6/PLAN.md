# Phase 6 — Model and Quality Runtime Policy

Status: **IN PROGRESS / C0 R2 FRESH-SESSION PROBE NEXT**

Date: 2026-09-10

## Objective

Determine which Images 2.5 generation controls are actually exposed to the real ChatGPT Work + Skill runtime, then test only those controls that the production Skill can genuinely invoke.

Public API capability is evidence of what the platform can support in some surfaces. It is not authority for the Work Skill surface.

No production model, quality, size, output-format, or background-mode setting changes during C0.

## C0 — Runtime control enumeration

C0 performs **zero image-model operations**.

Its only purpose is to inspect the callable Image Gen interface available to the installed Skill and report the controls that are explicitly exposed.

### C0 attempt-1 transport finding

The first Work attempts were **not valid runtime-control evidence**.

The Work conversation had previously loaded the Phase 4 C0 probe under the production-like `md3-product-image` Skill identity. Even after installing a Phase 6 package with a changed internal name, the same Work conversation continued resolving the callable Skill state to the older Phase 4 instructions.

Observed response referenced:

```text
md3-product-image
Phase 4 C0 Edit Probe
```

instead of the Phase 6 instructions.

Therefore:

- this result is not `IMAGE_RUNTIME_CONTROL_SCHEMA_UNAVAILABLE`,
- it says nothing about the actual Image Gen control schema,
- no image-model operation was performed,
- C0 must be rerun in a **fresh Work conversation** with only the isolated Phase 6 probe loaded.

The isolated rerun package uses:

```text
name: phase6-runtime-control-probe-r2
PROBE_PACKAGE_ID: PHASE6-C0-R2-20260910
```

If the active Skill does not expose both identifiers, the probe must stop with:

```text
PHASE6_C0_WRONG_SKILL_INSTANCE
```

### Controls of interest

Check whether the runtime exposes an explicit callable control corresponding to each of the following concepts:

- model selection
- quality / effort level
- output size or resolution
- background mode / transparency
- output format
- image operation action/mode
- any other generation parameter that materially changes production output

Do not assume these exact parameter names are used by Work.

For every control, report:

1. callable parameter name, if exposed,
2. declared type,
3. allowed enum values or documented range, only if present in the callable interface,
4. default value, only if explicitly exposed,
5. whether the Skill can set the value directly.

If the callable interface cannot be inspected with enough certainty to identify controls, stop with:

```text
IMAGE_RUNTIME_CONTROL_SCHEMA_UNAVAILABLE
```

Do not infer controls from OpenAI public API documentation, model knowledge, prior chat, prompt wording, or observed output.

## C0 acceptance

C0 passes when Work can produce a concrete runtime-control inventory grounded only in its callable Image Gen interface.

Expected conclusion:

```text
RUNTIME_CONTROL_SCHEMA_CONFIRMED
```

or:

```text
IMAGE_RUNTIME_CONTROL_SCHEMA_UNAVAILABLE
```

No image is generated in either case.

## C1+ — Ablation design

Only after C0 is reviewed should later tests be defined.

For each exposed control:

- vary one control at a time,
- keep the accepted Phase 3 palette-only reference path fixed,
- keep the structured prompt fixed,
- keep deterministic local composition fixed,
- use one image-model operation per user instruction,
- compare MASTER and SKU behavior separately when relevant.

### Evaluation dimensions

- instruction following
- Classic MD3 adherence
- background quality
- palette harmony
- safe-zone cleanliness
- accidental object/text/Logo contamination
- SKU composition consistency
- actual delivered raster
- latency, when observable

## Adoption rule

Use the fastest/lowest-cost runtime configuration that consistently satisfies the accepted visual and deterministic contract.

Do not assume a highest quality setting is automatically best.

Do not write an API model name or parameter into `SKILL.md` unless the real Work/Skill callable interface proves that the Skill can set it.
