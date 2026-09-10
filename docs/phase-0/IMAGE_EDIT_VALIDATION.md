# Image Edit / Reference Image Validation

Status: **CURRENT SKILL CALLABLE RUNTIME EDIT MODE NOT VERIFIED / PROBE DID NOT ENTER EDIT MODE**

Date: 2026-09-09

This Phase 0 validation checks whether the image-generation interface currently callable by this Skill can perform a true reference-image edit rather than generating a new image, and whether multiple reference images can be assigned distinct roles reliably enough for the planned SKU constrained-edit workflow.

No production Skill behavior was changed by this validation.

---

## Target behavior

The intended SKU workflow requires an operation equivalent to:

```text
MASTER_BACKGROUND = authoritative editable image
SKU_REFERENCE      = palette reference only

CHANGE
Change only the palette of MASTER_BACKGROUND.

PRESERVE
Composition, geometry, panel placement, relative sizes, negative space,
lighting direction, elevation hierarchy, and information safe zone.
```

For this to be considered available in the current Skill runtime, the probe must demonstrate that the runtime actually enters image-edit mode and binds the supplied source image as the editable image.

---

## Probe design

A clean blue abstract background already present in the conversation was selected as the intended source image.

The edit instruction was deliberately narrow:

- change only the overall blue palette to warm beige / apricot,
- preserve all discs, arches, platforms, spheres, positions, counts, sizes, lighting direction, and negative space,
- add no text and no new elements.

A second attempt explicitly bound the existing image reference while keeping the same edit-only instruction.

A prior general Image Edit / Reference Image probe was also excluded because it produced a newly generated validation poster instead of editing an existing source image.

---

## Observed behavior

All probe attempts produced new infographic / validation-poster images rather than a recolored version of the selected source background.

The returned generation metadata reported:

```text
edit_op: null
```

for the attempted edit calls.

The intended source geometry was not preserved because the source image was not actually edited. The outputs were unrelated newly generated compositions describing the validation task itself.

Therefore these outputs cannot be scored for edit fidelity, palette-only change fidelity, composition drift, or multi-reference role separation.

---

## Result

### True edit semantics

**NOT VERIFIED / PROBE DID NOT ENTER EDIT MODE**

The current callable image runtime used by this Skill did not demonstrate a true image-edit operation in this environment.

### Single-reference source binding

**NOT VERIFIED**

Explicitly identifying an existing conversation image did not result in a source-bound edit during this probe.

### Multi-reference role separation

**NOT TESTABLE IN THIS RUNTIME PATH**

Because the runtime did not first establish a valid editable source image, there is no valid basis for testing:

- image 1 as authoritative composition,
- image 2 as palette-only reference,
- product / palette role separation,
- prevention of product-geometry leakage.

Any generated image that merely depicts multiple reference examples is not evidence of multi-reference role control.

---

## Important interpretation

This result must not be generalized to every GPT Image 2.5 API surface.

It establishes only that the **currently callable ChatGPT / Skill image-generation path available in this validation did not expose or execute a verifiable source-bound edit operation**.

Therefore the repository must distinguish:

- GPT Image 2.5 image-edit capability in supported API surfaces: separate capability question,
- current Skill callable runtime entering edit mode: **not verified here**,
- current Skill callable runtime supporting role-separated multi-reference editing: **not verified here**.

---

## Consequence for Phase 4

Phase 4 must not replace the existing SKU reference-guided generation flow with a mandatory constrained-edit path yet.

Until the Skill runtime exposes a verifiable edit interface:

1. keep the existing SKU generation path as the production fallback,
2. do not write instructions that imply `ORIGINAL_MASTER_BACKGROUND.png` is being edited when it is only being supplied as a reference,
3. keep the constrained-edit prompt contract documented as a future preferred path,
4. gate activation of that path on a successful runtime probe whose metadata and raster behavior prove that an edit actually occurred,
5. do not score newly generated comparison posters or generated text as evidence of reference-image editing.

---

## Valid future probe requirements

A future Image Edit probe counts only if all of the following are true:

1. an existing source raster is explicitly bound as the editable image,
2. the runtime reports or otherwise proves an actual edit operation,
3. the output visibly derives from the same source composition,
4. the returned raster is compared directly with the source rather than judged from generated labels,
5. a palette-only edit is attempted before testing multi-reference role separation,
6. no automatic retry is used,
7. only after single-source edit semantics pass may a second reference be introduced as palette-only guidance.

---

## Decision

**The current Skill callable runtime cannot yet be treated as a verified Image Edit / role-separated Reference Image interface.**

For the Images 2.5 upgrade, constrained SKU editing remains a conditional future path, while the current master-reference SKU generation path remains the verified fallback.
