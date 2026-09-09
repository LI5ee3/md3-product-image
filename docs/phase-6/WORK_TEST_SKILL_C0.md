---
name: md3-product-image
description: "Phase 6 C0 runtime-control probe for md3-product-image. Inspect the real Work Image Gen callable interface and report only explicitly exposed production controls. This probe must not perform any image-model operation."
---

# MD3 Product Image — Phase 6 C0 Runtime Control Probe

This package is only for Phase 6 C0 capability enumeration.

It must perform **zero image-model operations**.

Do not create, replace, redo, or renumber MASTER or SKU outputs.

## Objective

Answer one question only:

> Which Image Gen generation controls can this real ChatGPT Work + Skill runtime explicitly set from the installed Skill?

## Evidence authority

Use only the actual callable Image Gen interface/tool declaration exposed in this Work session.

Do not use:

- public OpenAI API documentation,
- prior chat claims,
- model knowledge,
- prompt wording,
- observed image behavior,
- guessed parameter names or values.

If the callable interface cannot be inspected precisely enough to ground the inventory, return:

```text
IMAGE_RUNTIME_CONTROL_SCHEMA_UNAVAILABLE
```

and stop.

## Controls to inspect

Inspect the callable interface for controls corresponding to these concepts, without assuming exact names:

1. model selection
2. quality / effort level
3. output size / resolution
4. background mode / transparency
5. output format
6. image operation action/mode
7. other explicitly exposed generation controls that can materially affect output

For each discovered control, record only information explicitly declared by the callable interface:

- `concept`
- `parameter_name`
- `type`
- `allowed_values` or range, if declared
- `default`, if declared
- `directly_settable_by_skill`: true/false
- `notes`

For a concept with no explicit parameter, record:

```json
{
  "parameter_name": null,
  "directly_settable_by_skill": false
}
```

Do not invent allowed values for unavailable controls.

## Required output

Return one JSON object in this shape:

```json
{
  "probe": "phase6-c0-runtime-controls",
  "image_model_operations": 0,
  "controls": [
    {
      "concept": "model selection",
      "parameter_name": null,
      "type": null,
      "allowed_values": null,
      "default": null,
      "directly_settable_by_skill": false,
      "notes": ""
    }
  ],
  "other_exposed_controls": [],
  "conclusion": "RUNTIME_CONTROL_SCHEMA_CONFIRMED"
}
```

Use:

```text
RUNTIME_CONTROL_SCHEMA_CONFIRMED
```

only if the inventory is grounded in the actual callable interface.

Otherwise use:

```text
IMAGE_RUNTIME_CONTROL_SCHEMA_UNAVAILABLE
```

## Prohibitions

- Do not invoke Image Gen.
- Do not generate a test image to infer hidden defaults.
- Do not install or call another API client.
- Do not infer public API parity.
- Do not modify production files.
- Do not change `SKILL.md` production behavior.

## Stop after C0

Do not design or run quality/model A/B tests inside this package.

Later Phase 6 ablations are defined only after the C0 runtime inventory is reviewed outside Work.
