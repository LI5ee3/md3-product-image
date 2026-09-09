---
name: md3-product-image
description: "Create portrait 3:4 Google Classic MD3 e-commerce product images with Image Gen backgrounds and locally composited product images, fixed 2D shadows, Logo, and Rubik Variable text. Use for product main images, user-locked masters, or automatic locked-layout SKU variants and SKU redos."
---

# MD3 Product Image

## Resolve inputs once

Reuse only inputs from the current task and files in the exact same complete-product-name directory. For the first master request, require:

- authoritative product PNG or WEBP with assumed Alpha channel
- original Logo PNG or WEBP with assumed Alpha channel
- complete product name, exact title line text, and optional version
- `TITLE_LINES`: `1` or `2`

Never infer `TITLE_LINES`. Render each user-supplied title line exactly as written. Do not derive or validate title text from the complete product name.

## Keep one product in one directory

Use `<output root>/<exact complete product name>` as `PRODUCT_DIRECTORY`. Keep all reusable files in `PRODUCT_DIRECTORY/reusable`:

- `layout.json`, `prompt-additions.json`, cropped Logo, and text masks
- cached placed product layers and fixed 2D shadows
- bound master background, product, shadow, scene, and `master.json`

Keep only `output/ORIGINAL_MASTER_FINAL.png` and confirmed sequential `output/SKU_VARIANT-*.png` files in `output`. Keep prompts, run state, full-size previews, manifests, and other attempt records in `PRODUCT_DIRECTORY`. Never create thumbnails.

## Run one user-controlled attempt

Use:

`MEASURE -> BUILD_PROMPT -> IMAGE_GEN_BACKGROUND -> LOCAL_FULL_COMPOSITE -> MASTER_USER_LOCK_OR_REDO`

Each user generation instruction permits exactly one Image Gen call and one full-size composite. Never inspect a generated background separately, decide visual success, or retry automatically. Deterministic failures such as an unreadable file, wrong ratio, hash mismatch, or missing raster stop the run and are reported to the user without another Image Gen call. Assume uploaded product and Logo files are PNG or WEBP with Alpha; do not preflight their format or transparency. If Alpha is unavailable or fully opaque, continue using the full image bounds.

### 1. Measure or reuse

For the first master, run `scripts/measure_text.py` with the authoritative product, Logo, complete product name, `--title-lines`, `--title-line-1`, optional `--title-line-2` and `--version`, and `--output-root`. Always use bundled `assets/Rubik[wght].ttf` with `--font-weight 700`.

The script creates `PRODUCT_DIRECTORY/reusable/layout.json`, the cropped Logo, and title/version masks. If the layout already exists, reuse it. Stop if the source identity conflicts with its recorded hashes; never silently replace reusable assets.

### 2. Build one prompt

For a master:

```text
python scripts/scene_prompt.py build --mode MASTER --layout <reusable/layout.json> --target <candidate-id>
```

For an SKU:

```text
python scripts/scene_prompt.py build --mode SKU --layout <reusable/layout.json> --master <reusable/master.json>
```

`scene_prompt.py build` writes the complete Image Gen prompt to stdout. Capture that successful stdout and pass it verbatim to Image Gen in the same tool flow. Never infer, reconstruct, search for, or read a `scene-prompt-*.txt` filename; those files are records only. Stop before Image Gen if the command fails or stdout is empty.

The prompt order is:

1. current `references/image-gen-prompt.txt`
2. `references/replace-variant-block.md` for SKU only
3. merged information safe-zone block
4. every user-supplied accumulated addition from `reusable/prompt-additions.json`
5. canonical product and shadow placement policy

The merged safe rectangle contains the measured Logo, every title line, and optional version rectangle, expands the union by 5% of the canvas on every side, and clips it to the canvas. It is the only mandatory empty zone.

Prompt additions persist by exact complete product name and accumulate chronologically across the master and all SKUs. Add text only when the user supplies it with a redo instruction. If no addition has ever been supplied, rebuild from the original prompt plus the required SKU, safe-zone, and canonical blocks. Never invent a correction.

For a master, send only the authoritative product image as a palette reference. For an SKU, send exactly `reusable/ORIGINAL_MASTER_BACKGROUND.png` as composition reference and the current SKU product image as palette reference. Image Gen creates only the empty background; never send Logo, text, masks, final composites, or another SKU.

When calling Image Gen through `functions.exec`, forward its return value with `generatedImage(result)`. If no accessible raster is delivered, run `record-delivery-failure`, report it, and stop.

### 3. Composite and show one master preview

Run:

```text
python scripts/artifact_flow.py preview --generated-background <background> --product <product.png> --product-dir <PRODUCT_DIRECTORY> --candidate-id <id>
```

The command immediately creates one full-size composite containing the exact cached or newly prepared product layer, its fixed shadow, cached Logo, and cached text. Reuse an existing product layer and shadow for the same candidate; a redo changes only the background, scene, and final preview. Show the full-size preview and stop.

Do not use visual heuristics to accept, reject, or regenerate. The user owns the visual decision.

### 4. Lock or redo the master

Only after the explicit instruction `锁定母版`, run:

```text
python scripts/artifact_flow.py bind --product-dir <PRODUCT_DIRECTORY> --candidate-id <id>
```

This promotes the exact inspected pixels and creates the bound reusable master files plus `output/ORIGINAL_MASTER_FINAL.png`.

Only after `重做母版`, run:

```text
python scripts/artifact_flow.py discard-preview --product-dir <PRODUCT_DIRECTORY> --candidate-id <id>
python scripts/scene_prompt.py reject --layout <reusable/layout.json> --mode MASTER --target <id> [--additional-prompt <user text>]
```

Then build, generate, composite, show exactly one new preview, and stop. The optional addition is stored and automatically included in this and all later prompts for the product.

### 5. Create or redo one SKU

After the master is bound, build and generate one SKU background, then run:

```text
python scripts/artifact_flow.py sku --generated-background <background> --product <current-SKU.png-or-webp> --product-dir <PRODUCT_DIRECTORY>
```

The script writes the completed image directly to its automatically assigned sequential `output/SKU_VARIANT-*.png`, closes the SKU run, and returns the final image. Treat a successful deterministic composite as accepted; do not ask for confirmation.

Only after an explicit SKU redo request, build with the existing label:

```text
python scripts/scene_prompt.py build --mode SKU --layout <reusable/layout.json> --master <reusable/master.json> --redo [--target <SKU_VARIANT-X>] [--additional-prompt <user text>]
```

Omit `--target` to redo the most recently completed SKU. Reuse the cached product layer and shadow for that label. Generate one replacement background, then run the same `artifact_flow.py sku` command. Keep the existing output unchanged until the replacement composite passes deterministic checks, then atomically replace it without changing the filename. A failed redo must preserve the existing final. A redo does not consume a new sequential label.

For a new SKU after any redo, omit `--redo`; assign the next unused label normally.

## Preserve local composition

Add the exact source Logo, user-supplied title lines, and optional version in that order. Preserve their artwork, characters, spacing, proportions, and alpha. Use only proportional Logo scaling and Rubik Variable text. Keep the manually selected line count and title text unchanged.

Use visible product height 54% and right margin 12%. For aspect ratio `>= 1.35`, use maximum width 68% and bottom margin 18%. For aspect ratio `< 0.90`, use maximum width 52% and bottom margin 12%. Otherwise use maximum width 52% and bottom margin 18%. Use shadow angle 50°, offset 16% of product height, blur radius 0.7% of canvas height, and opacity 28%.

Keep the Logo and text on the visible Logo left edge. Keep the title-to-version gap at 2.5% of canvas height. Always render the product name as `#2C2C2C` and version text as `#5A5A5A`; never adapt or override these colors. Report any visual concern with the full preview, but wait for the user's decision.
