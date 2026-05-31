# Atlas Swizzle Format Fix -- Investigation & Status

## Date: 2026-05-28

## Finding: Fix Already Applied

The atlas swizzle fix was **already implemented** in `generate_font_atlas.py`.
The script correctly applies PSMT4 swizzle before writing the .bin file.

## Root Cause (confirmed)

The PS2 GS uploads PSMT4 texture data to VRAM using **PSMCT32 IMAGE transfers**.
The on-disc pixel data must be in **PSMCT32 upload format** (swizzled), NOT linear.

Evidence from definitive round-trip test:
- `swizzle_psmt4(deswizzle(original_raw_pixels)) == original_raw_pixels` --> **PASS**
- Linear page-layout packing vs original: **25,553 mismatches out of 65,536 bytes**

## Current State of generate_font_atlas.py

The script at `tools/generate_font_atlas.py` already:

1. Imports `swizzle_psmt4` from `psmt4_deswizzle.py` (line 5)
2. Builds a linear pixel array (1 byte per pixel, values 0-15) at page-aligned dimensions (256x640)
3. Calls `swizzle_psmt4(linear_pixels, 256, 640, bw_psmt4=256, dbw_ct32=256)` to produce PSMCT32 upload format
4. Writes `header (192 bytes) + swizzled_pixels (81920 bytes) + palette (64 bytes)` = 82,176 bytes

## Rebuild Performed

Re-ran both build steps to ensure the current .bin and PACKDATA.DIG are up to date:

```
python3 tools/generate_font_atlas.py
  -> Swizzled 256x640 pixels, output: 82,176 bytes
  -> Round-trip test: PASS

python3 build/full_patch_pipeline.py  
  -> Font atlas injected as 1272_type01.raw (83,968 bytes, sector-padded)
  -> PACKDATA.DIG rebuilt: 839,794,688 bytes
```

## Verification

- Round-trip test on patched 256x512 region: **PASS**
- 7,663 non-transparent pixels visible in deswizzled output (glyphs present)

## File Layout Summary

| Format | Layout |
|--------|--------|
| Original .raw pixel data | PSMCT32 upload format (swizzled) |
| Our atlas after `swizzle_psmt4()` | PSMCT32 upload format (swizzled) -- matches |
| Linear page layout (old, broken) | 128x128 pages, 2 cols -- does NOT match |

## No Code Changes Needed

The fix was already in place. The atlas binary and PACKDATA.DIG have been rebuilt
to confirm the current pipeline produces correct output.
