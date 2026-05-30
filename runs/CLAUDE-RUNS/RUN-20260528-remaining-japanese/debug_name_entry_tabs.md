# Debug: Name Entry Tabs Still Japanese in v17

**Date**: 2026-05-28
**Status**: ROOT CAUSE IDENTIFIED

---

## Root Cause: TWO INDEPENDENT FAILURES

### Failure 1: R1188 pixel edits go to wrong location (rows 1009-1020 are unused space)

`tools/patch_r1188_direct.py` renders English labels into rows y=1009-1020 of the
1024x1024 PSMT4 atlas. But **nothing redirects the game to read from those rows**.
The game's glyph resolver (VA 0x494050) uses BSS tables populated at runtime from
R1188's header metadata to find UV coordinates for glyph IDs 6400+. The original
UV coordinates still point to the original Japanese label positions in the atlas.

The English pixels are sitting in unused atlas space that nothing ever reads.

### Failure 2: build_full_english_v2.py never calls the R1188 patcher

The current build pipeline (`build/build_full_english_v2.py`) has NO R1188 patching
step. It only does:
1. Load translations
2. Encode translations
3. Inject font atlas (R1272)
4. Inject MSG translations into resources
5. Rebuild PACKDATA.DIG
6. Build ISO

The old `build_v9.py` had "Step 3.6: R1188 tab labels" which called
`tools/patch_r1188_direct.py`, but this step was dropped when the pipeline was
rewritten as `build_full_english_v2.py`.

Even if the step were included, Failure 1 means it still would not work.

---

## How Glyph IDs 6400+ Are Resolved

### Data flow (traced from disassembly):

```
EXE Table 2E (file 0x3C9DA0, VA 0x4C9D20)
  Contains: [0x1900, 0x1901, 0x1902, 0x1903, 0x1904, ...]
            = glyph IDs [6400, 6401, 6402, 6403, 6404, ...]

    |
    v

Code at VA 0x2FB094: loads glyph ID from table
    r4 = glyph_id (e.g., 0x1900)
    jal 0x494350      (render_bitmap_glyph)

    |
    v

VA 0x494350: render_bitmap_glyph(glyph_id)
    calls 0x494300 to validate glyph is loaded
    group = glyph_id >> 8       (0x19 = 25)
    index = glyph_id & 0xFF     (0x00 = 0)

    |
    v

VA 0x494300: check_glyph_loaded(glyph_id)
    group = glyph_id >> 8
    looks up BSS table at 0x4EB100 + group*8
    checks table at 0x575C10 + (group_info)*32
    returns 1 if loaded, 0 if not

    |
    v (if loaded)

VA 0x494350 continues:
    loads base_ptr from BSS 0x4EB104 + group*8
    loads base_ptr2 from BSS 0x4EB100 + group*8
    reads 3 bytes at base_ptr + index*8: (u, v, flags)
    composes texture coordinates:
      r4 = u | (v << 8) | (base_ptr2 << 16)
    jal 0x474D30     (GS draw sprite)
```

### Key insight: UV coordinates come from R1188's header

The BSS tables at 0x4EB100/0x4EB104 are populated when R1188 is loaded into VRAM.
R1188's header (0x560-0x6B3) contains 17 sprite metadata entries that define the
UV rectangles for each bitmap glyph group. The glyph resolver reads these at
runtime to find where each tab label lives in the 1024x1024 texture.

The UV coordinates are NOT in the EXE -- they are embedded in R1188's binary header.

---

## What the Tabs Actually Reference

Glyph IDs 6400+ (group 0x19) map to bitmap sprites in R1188's 1024x1024 PSMT4 atlas.
They are NOT R1272 main font glyphs. The rendering path is completely separate from
the main text renderer.

| Glyph ID | Group:Index | Japanese Label | Purpose |
|----------|-------------|----------------|---------|
| 6400     | 0x19:0x00   | katakana       | Tab: katakana input mode |
| 6401     | 0x19:0x01   | hiragana       | Tab: hiragana input mode |
| 6402     | 0x19:0x02   | eisu           | Tab: alphanumeric mode |
| 6403     | 0x19:0x03   | kigou          | Tab: symbol mode |
| 6404     | 0x19:0x04   | (unused?)      | Tab: 5th slot |
| 6405     | 0x19:0x05   | kettei         | Button: Confirm/OK |
| 6406     | 0x19:0x06   | otokona        | Button: Male Name |
| 6407     | 0x19:0x07   | onnana         | Button: Female Name |
| 6408     | 0x19:0x08   | 1moji kesu     | Button: Delete char |
| 6409     | 0x19:0x09   | zensakujo      | Button: Clear all |

---

## The Fix: THREE options (ranked by difficulty)

### Option A: Edit R1188 pixel data AT THE CORRECT UV positions (HARD)

1. Fully deswizzle R1188's 1024x1024 PSMT4 (dbw_ct32=512 confirmed)
2. Parse R1188's sprite metadata (0x560-0x6B3) to find exact UV rects for each
   glyph index in group 0x19
3. Render English labels at those exact pixel positions, overwriting the Japanese
4. Re-swizzle and inject back

**Problem**: The sprite metadata format is not fully decoded. The 17 entries at
0x560 have format `{marker(4B), 0xFFFFFFFF(4B), entry_id(u16), flags(u16), pad(4B),
w(u16), h(u16)}` but these are atlas-level dimensions (1024x1024), not per-glyph
UV rects. The actual per-glyph UV data might be in the 16-byte records at 0x6B4
or in the GS register blocks.

### Option B: Replace glyph IDs in EXE table with main font composition (MEDIUM)

Instead of bitmap glyph IDs 6400+, replace them with sequences of R1272 main font
ASCII glyph IDs that spell out the English labels.

**Problem**: The table at 0x3C9DA0 stores one glyph ID per tab. The renderer draws
ONE bitmap sprite per tab label. You cannot replace a single bitmap glyph ID with
multiple ASCII character IDs -- the rendering code expects exactly one sprite per
table entry, not a string.

This would require significant code patching to loop through characters and render
them individually.

### Option C: PCSX2 texture replacement (EASIEST -- already implemented!)

The PCSX2 texture replacement PNGs are already generated by `patch_r1188_direct.py`.
They work by matching the content hash + CLUT hash of each texture as PCSX2 loads
it from VRAM.

**This approach ONLY works in PCSX2 with texture replacement enabled.** It does NOT
affect the ISO itself. For a distributable fan translation, this is insufficient.

### Option D: Edit R1188 header UV data to point to new pixel positions (BEST)

1. Render English labels into the unused bottom rows of R1188 (already done by
   patch_r1188_direct.py at y=1009-1020)
2. Parse and modify R1188's sprite metadata / UV table to redirect glyph group
   0x19's UV coordinates from the original Japanese positions to y=1009-1020
3. This avoids needing to find and overwrite the exact Japanese pixel positions

**Requirements**:
- Decode the sprite metadata format at R1188 offsets 0x560-0x7C3
- Identify which metadata fields control the per-glyph UV coordinates
- Patch those fields to point to the new English label positions

---

## Immediate Next Steps

1. **Decode R1188 sprite metadata format**: The 17 entries at 0x560 and 17 records
   at 0x6B4 need full structural analysis. Cross-reference with PCSX2 texture dumps
   (48x20, 40x24 sizes) to determine which fields are UV coordinates.

2. **Add R1188 patching back to build pipeline**: Even before fixing the UV issue,
   `build_full_english_v2.py` needs to call the R1188 patcher.

3. **Consider the hybrid approach**: Edit pixels at original Japanese UV positions
   (Option A) if the UV metadata proves too complex to patch.

---

## File References

| Item | Path |
|------|------|
| R1188 patcher (direct) | `tools/patch_r1188_direct.py` |
| R1188 patcher (PCSX2 only) | `tools/patch_r1188_tabs.py` |
| Current build pipeline | `build/build_full_english_v2.py` |
| Old build pipeline (had R1188 step) | `build/build_v9.py` |
| R1188 raw resource | `extracted/packdata_raw/1188_type01.raw` |
| R1188 patched output | `build/packdata_resources/1188_type01.raw` |
| PCSX2 replacement PNGs | `build/pcsx2_texture_replacements/` |
| EXE glyph table (Table 2E) | EXE file offset 0x3C9DA0 |
| Glyph resolver function | EXE VA 0x494050 (file 0x3940D0) |
| Bitmap glyph renderer | EXE VA 0x494350 (file 0x3943D0) |
| Group validator | EXE VA 0x494300 (file 0x394380) |
| BSS glyph group table | VA 0x4EB100 (runtime, populated from R1188 header) |
| Name entry tab caller | EXE VA 0x2FB094 (file 0x1FB114) |
| R1188 sprite metadata | R1188 file offsets 0x560-0x6B3 (17 entries x 20 bytes) |
| R1188 UV/rect records | R1188 file offsets 0x6B4-0x7C3 (17 entries x 16 bytes) |
