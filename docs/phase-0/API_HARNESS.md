# Phase 0 Exact-Prompt API Harness

Status: **HARNESS VALIDATED / LIVE CALL PENDING API CREDENTIAL**

Date: 2026-09-09

This document defines the fallback Phase 0 test harness used when the current ChatGPT project-conversation image surface cannot reproduce the repository Skill's exact prompt-delivery transport.

It does **not** redefine production Skill behavior.

## Why this harness exists

The frozen Skill contract requires the exact stdout emitted by `scene_prompt.py` to become the image-generation instruction.

The current project-conversation image surface derives image intent from conversation context and therefore cannot prove verbatim prompt transport.

The Responses API provides a suitable test-only alternative because it supports:

- explicit text input,
- explicit image input in the same request,
- the GPT Image 2.5 image-generation tool,
- `action: generate` to force creation of a new image while keeping the source product as a reference image rather than the editable canvas.

The implementation is:

`scripts/phase0_responses_image_harness.py`

## Safety / reproducibility properties

The harness:

1. reads the archived prompt bytes directly from disk;
2. verifies the prompt SHA-256 before any API call;
3. reads the exact reference-image bytes directly from disk;
4. verifies the reference-image SHA-256 before any API call;
5. sends the exact prompt text and image reference in one Responses API input message;
6. configures one image-generation tool call with `action: generate`;
7. performs at most one Responses API call per invocation;
8. never retries automatically;
9. refuses to overwrite an existing output or metadata record;
10. saves the returned image unchanged;
11. records response ID, image-call ID, revised prompt when available, output SHA-256, format, mode, and dimensions;
12. never writes or logs the API key or image Base64 input.

## Official API selection

Current documented test defaults:

- Responses main model: `gpt-6-astra`
- image tool model: `gpt-image-2.5-sunburst`
- image action: `generate`
- size: `auto`
- quality: `auto`
- background: `auto`

`size`, `quality`, and `background` remain `auto` for the frozen visual baseline so the API harness does not introduce a new production choice before the relevant Phase 0/Phase 1 ablations.

The harness supports explicit overrides later for dedicated capability tests.

## Authoritative black MASTER call

Inputs:

- prompt: `docs/phase-0/huawei-watch-fit-5-pro/master-prompt-black.txt`
- prompt SHA-256: `12148360c40fe556ee8304c68a3914aa69e380d9fd75863b29809eac6a01a773`
- reference product: Google Drive `黑.png`
- reference SHA-256: `b0739efd15f379ea5654fdaedf11bacd36590817a17006f7027d7f1a2ae40fe8`

When the Drive file has been materialized locally as `黑.png` and `OPENAI_API_KEY` is available, the single-call command is:

```text
python scripts/phase0_responses_image_harness.py \
  --prompt docs/phase-0/huawei-watch-fit-5-pro/master-prompt-black.txt \
  --reference-image /path/to/黑.png \
  --expected-prompt-sha256 12148360c40fe556ee8304c68a3914aa69e380d9fd75863b29809eac6a01a773 \
  --expected-reference-sha256 b0739efd15f379ea5654fdaedf11bacd36590817a17006f7027d7f1a2ae40fe8 \
  --output phase0-black-master-background.png \
  --metadata phase0-black-master-response.json
```

Do not add `--size`, `--quality`, or `--background` to this frozen-baseline call.

## Validation evidence

GitHub Actions workflow:

`.github/workflows/phase0-responses-harness-check.yml`

Run ID:

`34333433792`

Validated successfully:

- Python compilation;
- frozen prompt SHA verification;
- dry-run request construction;
- failure before network access when `OPENAI_API_KEY` is absent.

The authoritative black product was also materialized in the current project environment and independently re-hashed as:

`b0739efd15f379ea5654fdaedf11bacd36590817a17006f7027d7f1a2ae40fe8`

which matches `AUTHORITY_INPUTS.md`.

## Current blocker

The current assistant execution container does not expose `OPENAI_API_KEY`.

Therefore the live Responses API image operation has not been executed from this harness yet.

This is a credential/runtime blocker, not a prompt failure and not a harness failure.

No visual baseline output or score may be recorded until a live call returns exactly one image-generation result and that result is inspected against the background-only contract.
