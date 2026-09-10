# Native Size Validation

Status: **REAL WORK OUTPUT STABLE AT 1086 × 1448 ACROSS MASTER + 2 SKU / UI REPORTS 1536 × 2048**

Date: 2026-09-09

This Phase 0 check separates the repository's logical layout canvas from the raster actually delivered by the real ChatGPT Work Skill runtime.

No production behavior was changed during this validation.

## 1. Logical layout canvas

The existing repository measures text and information placement on a logical canvas of:

```text
1536 × 2048
```

This is exactly 3:4. The layout rectangles are stored as normalized coordinates, so later local composition can scale them to another exact 3:4 raster.

## 2. GPT Image 2.5 API contract

`1536x2048` is valid under the documented GPT Image 2.5 custom-size constraints. API support alone does not prove that the ChatGPT Work Skill bridge requests or returns that exact raster.

## 3. Real production Skill evidence

The authoritative HUAWEI WATCH FIT 5 Pro baseline was generated with `md3-product-image v2.0` in ChatGPT Work.

Work reported `1536×2048 (3:4)` for the generated outputs. The actual downloaded PNG files were inspected directly.

| Output | Actual raster | Mode | Alpha | SHA-256 |
| --- | --- | --- | --- | --- |
| locked black MASTER | `1086×1448` | RGBA | fully opaque | `083d625d2a039ca565fbaf548c55e58714c6770601b1fcb1141f5360201f286f` |
| orange `SKU_VARIANT-A` | `1086×1448` | RGBA | fully opaque | `9f8be325c1d6ac486024393629ebd18650c684d9af936b9f01ec600a599d42ff` |
| white `SKU_VARIANT-B` | `1086×1448` | RGBA | fully opaque | `22f16d60736c81a6738a987b4f1d4d5ff29460f4a16a3c0ed284f1f3643ed66b` |

All three real production outputs therefore resolve to the same exact 3:4 raster:

```text
1086 × 1448
```

This satisfies the previously requested three-output stability check using real Skill production artifacts rather than conversational probes.

## 4. Why the current pipeline still works

The repository currently has two different size concepts:

1. `measure_text.py` creates a `1536×2048` logical layout and stores normalized element rectangles.
2. `compose_scene.py` uses the generated background's actual raster as the local composition canvas and only requires exact 3:4.
3. `compose_image.py` scales the normalized Logo/text rectangles to that actual scene raster.

Therefore a `1086×1448` generated background naturally produces a `1086×1448` final composite without any required resize back to `1536×2048`.

The Work message reporting `1536×2048` should not be treated as proof of the downloadable raster size.

## 5. Invalidated earlier probes

Earlier project-conversation attempts to test explicit `1536x2048` or `1086x1448` requests remain excluded. Those calls did not demonstrably carry the intended explicit size argument and were not equivalent to the real Skill production path.

## 6. Phase 1 decision

Phase 1 must not force `1536×2048` merely because it is the logical measurement canvas.

Instead:

- keep `1536×2048` as the deterministic logical layout canvas;
- accept the locked MASTER background's actual exact-3:4 raster as the product's delivery raster contract;
- require every later SKU generated background to match the locked MASTER background width and height exactly;
- reject a same-ratio but different-size SKU background deterministically;
- never trigger an automatic image-generation retry after a raster mismatch;
- continue recording the actual delivered raster rather than trusting UI text.

This preserves current working output while preventing mixed-resolution MASTER/SKU sets.

## 7. Current conclusion

**The real v2.0 Work path is stable at 1086×1448 across one MASTER and two SKU outputs. The repository's 1536×2048 value is a logical layout canvas, not the verified downloadable raster. Phase 1 should lock SKU raster dimensions to the actual bound MASTER rather than force an unsupported 1536×2048 delivery size.**
