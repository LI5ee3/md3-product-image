# Phase 4 — Constrained SKU Background Edit Results

Status: **COMPLETED / NOT ADOPTED**

Date: 2026-09-09

## C0 runtime gate

The Phase 4 C0 Work probe was executed against the real ChatGPT Work + Skill runtime.

Returned result:

```text
IMAGE_EDIT_INTERFACE_UNAVAILABLE
```

Observed runtime condition:

- the callable Image Gen surface exposed normal generation capability,
- no explicit existing-image `edit` operation or equivalent edit selector was exposed,
- the Skill therefore could not prove that `ORIGINAL_MASTER_BACKGROUND.png` would be edited rather than used as a reference for a new generation.

Per the C0 contract, the run stopped immediately.

## Safety / production effect

The C0 probe correctly performed **no image-model call** after the edit-interface gate failed.

It also:

- did not generate a candidate edited background,
- did not create a production SKU,
- did not replace an existing SKU,
- did not modify the locked MASTER,
- did not fall back to ordinary generation while presenting it as an edit.

This is the required fail-closed behavior.

## C1 / C2

C1 orange edit and C2 white edit were **not executed** because C0 did not prove genuine edit semantics.

Running visual edit ablations without a verified edit operation would confound normal regeneration with editing and therefore would not produce valid evidence.

## Decision

```text
C0 edit interface proof: FAIL / INTERFACE UNAVAILABLE
C1 orange edit: NOT RUN
C2 white edit: NOT RUN
Adopt constrained SKU edit: NO
Retain Phase 3 SKU regeneration path: YES
```

The accepted production SKU path remains:

```text
ORIGINAL_MASTER_BACKGROUND.png     composition reference
SKU palette-reference.png         color-only reference
        ↓
Image Gen background regeneration
        ↓
deterministic local composition
        ↓
final SKU
```

The authoritative product artwork remains local and is not sent to Image Gen for palette transfer.

## Interpretation

This result does not mean Images 2.5 lacks image-edit capability in general. It means the currently tested Work + Skill runtime does not expose a verifiable edit operation that this Skill can explicitly invoke.

The project must not infer parity with public API controls.

Phase 4 may be reopened in the future if the Work/Skill runtime exposes an explicit edit operation or equivalent verifiable edit semantics.

## Acceptance

Phase 4 is complete because its runtime gate produced a decisive result and the fallback path is already validated by Phase 3.

No production code change is required from Phase 4.
