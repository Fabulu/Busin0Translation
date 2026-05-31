# Phase 1: Save State 27-1 Analysis (Name Entry Screen)

Save state: `RAMdumps/27-1.p2s`
Screenshot: `RAMdumps/v27_screenshots/27-1_Screenshot.png`
EXE base in RAM: file_offset + 0x0FFF80 (text section at file offset 0x80 loaded to VA 0x100000)

---

## Summary of Findings

The v27 save state has the **patched EXE** (all glyph ID changes confirmed in RAM) but
the **original R1272 font atlas** loaded in GS VRAM. This means the ISO used for this
save state either did not include the rebuilt PACKDATA.DIG, or the font atlas resource
was not correctly integrated. Translated MSG resources (e.g., "Enter Your Name.") ARE
present, confirming PACKDATA was at least partially patched for text.

---

## Japanese Element #1: Banner "新規登録" (upper-left red box)

**What we see:** Four large kanji characters in a red banner at top-left.

**EXE patch status: APPLIED**

| Record     | EXE offset  | RAM address  | Original glyphs | Patched glyphs | Status   |
|------------|-------------|--------------|-----------------|----------------|----------|
| 新 (shin)  | 0x3C33F0    | 0x004C3370   | 719, 720        | 46 (N), 69 (e) | Patched  |
| 規 (ki)    | 0x3C3428    | 0x004C33A8   | 721, 722        | 87 (w), 0 (sp) | Patched  |
| 登 (tou)   | 0x3C3268    | 0x004C31E8   | 705, 706        | 50 (R), 69 (e) | Patched  |
| 録 (roku)  | 0x3C32A0    | 0x004C3220   | 707, 708        | 71 (g), 14 (.) | Patched  |

**Font atlas status: ORIGINAL (not patched)**

- Original R1272 raw data confirmed at RAM `0x004AF678` (exact byte match)
- English atlas raw data NOT found anywhere in RAM
- Original R1272 pixel data confirmed in GS VRAM at offset `0x284FA8`
- English atlas NOT found in GS VRAM

**Root cause (TWO problems):**

1. **R1272 font atlas not loaded from patched PACKDATA.** The original R1272 is in
   RAM/VRAM. Even though the EXE struct glyph IDs are patched to ASCII positions
   (46='N', 69='e' etc.), the font atlas at those positions contains the original
   12x12 ASCII glyphs (tiny letters), not the large banner-style tiles the rendering
   expects. The menu_labels.csv has `strategy=skip` for these banner entries, so
   `render_menu_tiles.py` never rendered English tiles at the new glyph positions.

2. **EXE patch changes the wrong fields.** Even if the font atlas were loaded, the
   banner rendering likely uses `field[0] high_u16` (record IDs 618-625) rather than
   the glyph ID fields at offsets +26/+28. These record IDs were NOT changed by the
   patch. The record IDs index into a sprite/tile table that maps directly to the
   pre-rendered kanji bitmaps.

**Recommended fix:** Abandon the glyph-ID approach for the banner. Instead:
- Render English text ("New Reg." or "Register") directly into R1272 font atlas tiles
  at the ORIGINAL glyph positions (705-708, 719-722), OR
- Identify the rendering code and override the tile lookup.

---

## Japanese Element #2: Tabs -- カナ, かな, 英数, 記号

**What we see:** Four tab labels in Japanese on the right side of the character grid.

**Mechanism:** R1188 font atlas (528,384-byte type01 texture resource).

**Patch status: FAILED**

All entries in `data/r1188_label_map.json` show:
```
"atlas_match": "FAILED - deswizzle incorrect (see r1188_template_match.md)"
```

Labels affected:
| Japanese | Intended English | Category | GS page |
|----------|-----------------|----------|---------|
| カナ     | Kana            | tab      | 0x2214  |
| かな     | Hira            | tab      | 0x2214  |
| 英数     | ABC             | tab      | 0x2214  |
| 記号     | Sym             | tab      | 0x2214  |

The `build/packdata_resources/1188_type01.raw` has 1,068 differing bytes from the
original, suggesting some partial patching was attempted but incorrectly positioned
due to the PSMT4 deswizzle failure.

**Root cause:** The PS2 PSMT4 (4-bit indexed, swizzled) texture format used by R1188
was not correctly deswizzled/reswizzled. Template matching to find the correct pixel
positions for each label failed because the deswizzle algorithm produces incorrect
output for R1188's specific texture dimensions.

**Recommended fix:** Fix the PSMT4 deswizzle for R1188's texture dimensions (likely
1024-wide or 512-wide with different block parameters than R1272). Alternatively,
directly patch the GS VRAM upload data in the resource at known byte offsets determined
through emulator VRAM dumping.

---

## Japanese Element #3: 決定 (confirm button, bottom-right area)

**What we see:** Two kanji characters forming the "confirm/OK" button.

**EXE struct at 0x3C35E8 (RAM 0x004C3568):**
- Glyph IDs: 737, 738 (unchanged -- these use `strategy=abbrev` with English text "ok")
- `render_menu_tiles.py` WOULD render "ok" at glyph positions 737/738 in the font atlas

**Root cause:** Same as #1 -- the English R1272 font atlas is not loaded. The patched
atlas would have "ok" rendered at glyph positions 737/738, but the original atlas has
the Japanese kanji 決定 at those positions.

**Fix:** Loading the correct patched R1272 atlas will fix this automatically. The
`menu_labels.csv` entry and `render_menu_tiles.py` already handle this case correctly.

---

## Japanese Element #4: "Laur" and "M name" at bottom (NOT actually broken)

**What we see:** Text "Laur" and "M name" at the bottom of the name entry panel.

**Analysis:** These are WORKING correctly. Decoded from RAM at `0x012B1738`:

| Slot | Content       | Meaning                           |
|------|---------------|-----------------------------------|
| 1    | Laura         | Pre-filled default character name  |
| 2    | M name        | Male name placeholder              |
| 3    | F name        | Female name placeholder            |
| 4    | Press O or X to confirm. | Instruction text         |
| 5    | Male          | Gender label                       |
| 6    | Female        | Gender label                       |

These use glyph IDs encoded as high-byte-first u16 values (e.g., L=0x2C00, a=0x4100).
The text IS English. The visual "oddity" is caused by wide character cell spacing.

---

## Japanese Element #5: Wide character spacing (24px per glyph)

**What we see:** Letters in the name grid (a-z) and bottom area are widely spaced.

**Root cause:** The name entry grid uses 12x12 pixel character cells with 24px horizontal
spacing (designed for fullwidth Japanese characters where each kanji occupies a full
12x12 cell). English halfwidth letters occupy ~6-8px of the 12px cell, leaving large
gaps between characters.

**Recommended fix:** Either:
1. Implement VWF (variable-width font) rendering for the name entry screen
2. Halve the cell spacing constant in the EXE (find the 24px stride and change to 12px)
3. Accept the spacing as-is for the initial release

---

## Working Elements

| Element                | Status  | Source                                    |
|------------------------|---------|-------------------------------------------|
| "Enter Your Name."     | Working | Translated MSG resource (glyph IDs in RAM at 0x012B0F53) |
| Character grid (a-z)   | Working | Name entry character set (glyph-based)    |
| "Level 1"              | Working | Translated MSG resource                   |
| "Name" (decorative)    | Working | Pre-rendered texture or MSG               |
| NPC names (Emilia/Lute)| Working | EXE Patch 3 confirmed at RAM 0x004C9330   |

---

## Build Pipeline Issue

The build PACKDATA.DIG (`build/PACKDATA.DIG`, 839,854,080 bytes) DOES contain the
English R1272 atlas at LBA 211367 (41 sectors, payload 82,176 bytes). However, the
save state loads the original R1272 (33 sectors, payload 65,792 bytes).

**Possible causes:**
1. The ISO was built with an older PACKDATA.DIG that predates the R1272 fix
2. The build script (`build_full_english_v2.py`) was not run to completion, or its
   output ISO was not the one used to create this save state
3. A partial build ran `patch_exe.py` into an existing ISO but did not replace PACKDATA

**Action item:** Rebuild the ISO using the current `build/PACKDATA.DIG` and verify that
R1272 loads correctly. The font atlas, NPC name patches, and most menu labels (those
with `strategy != skip`) should then work.

---

## Root Cause Summary

| Issue                      | Root Cause                                      | Fix Difficulty |
|----------------------------|--------------------------------------------------|----------------|
| Banner 新規登録            | R1272 atlas not loaded + wrong EXE patch approach | Medium         |
| Tabs カナ/かな/英数/記号   | R1188 PSMT4 deswizzle broken                     | Hard           |
| Confirm 決定               | R1272 atlas not loaded (will auto-fix)            | Easy           |
| Wide spacing               | Fullwidth cell grid in EXE                        | Medium         |
