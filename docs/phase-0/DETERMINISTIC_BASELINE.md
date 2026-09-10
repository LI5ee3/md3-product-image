# Deterministic Workflow Baseline

Status: **PASS**

Date: 2026-09-09

This record captures the Phase 0 execution of the existing deterministic workflow self-check without modifying `scripts/test_workflow.py`.

## Repository state

- Branch: `images-2.5-roadmap`
- Tested commit: `df4d590350eb0623528e6cf836476c1b6e7b55d0`
- Baseline test script: `scripts/test_workflow.py`
- Test script blob SHA remains: `567cf81f5f7c933e3f2b6a1d12b6c56220a07ba7`

The tested commit adds only the Phase 0 CI wrapper needed to execute the existing test in the repository environment. The deterministic test implementation itself was not changed.

## Execution environment

GitHub Actions workflow:

- Workflow: `Phase 0 deterministic baseline`
- Workflow file: `.github/workflows/phase0-deterministic-baseline.yml`
- Run ID: `34326130255`
- Job ID: `102383700748`
- Runner: Ubuntu 24.04
- Python: CPython 3.12.14
- Pillow: 12.3.0

Command executed:

```text
python scripts/test_workflow.py
```

## Result

Workflow conclusion: **success**

Test output:

```text
md3-product-image workflow self-check passed
```

Every workflow step completed successfully, including checkout, Python setup, dependency installation, and the existing deterministic workflow self-check.

## Behaviors covered by the existing self-check

The passing result establishes the current deterministic baseline for the behaviors already asserted by `scripts/test_workflow.py`, including:

- PNG / WEBP input handling used by the test fixture
- exact user-supplied title-line preservation
- information safe-zone inclusion in the generated prompt
- exact prompt recording per attempt
- blocking a second generation attempt while user decision is pending
- master product-layer and shadow caching across redo
- prompt-addition persistence and accumulation
- explicit master binding
- `ORIGINAL_MASTER_FINAL.png` creation
- automatic sequential SKU labels
- SKU redo reusing the existing label
- failed SKU redo preserving the previous final image
- successful SKU redo replacing the existing final only after deterministic composition succeeds
- cached SKU product-layer and shadow reuse
- continued sequential SKU allocation after a redo
- no thumbnail generation

## Interpretation

This is a deterministic workflow baseline only. It does not validate Images 2.5 visual quality, model behavior, reference fidelity, native output dimensions, image-edit fidelity, opaque-background behavior, or model/quality controls.

Future implementation phases must keep this test passing unless a change is deliberately accompanied by an equivalent or stronger deterministic assertion.
