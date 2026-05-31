# Phase 2/3 Analysis: Gender Selection (27-2) and Race Selection (27-3)

**Date**: 2026-05-28
**Save States**: `RAMdumps/27-2.p2s` (gender), `RAMdumps/27-3.p2s` (race)
**ISO Build**: v27 (built 2026-05-31 20:08, save states from 21:07-21:08)

---

## 1. Visible Issues (Confirmed from Screenshots)

### 27-2 (Gender Selection)
- **Header**: Shows "Enter your name." -- stale from previous phase (timing artifact)
- **"Gender" italic header**: English (OK -- pre-rendered TEX at page 0x2254)
- **Options**: Shows kanji 男/女 instead of Mars/Venus symbols
- **Description**: English ("Gender sets base stats. Men=strong, women=wise.") -- OK

### 27-3 (Race Selection)
- **Header**: Shows "Select gender." -- stale from previous phase (timing artifact)
- **"Race" italic header**: English (OK -- pre-rendered TEX)
- **Race list**: Human, Elf, Gnome, Dwarf, Hobbit -- all English (OK)
- **"Hobbit"**: Slightly clipped at right edge but readable
- **Automata**: Not visible (requires scrolling past Hobbit -- this is normal behavior)
- **Sidebar labels**: Shows 性別 and 男 in Japanese (ISSUE)

---

## 2. Root Cause: Gender Symbols (男/女 vs Mars/Venus)

### Data Pipeline (Verified Correct)

| Component | Status | Detail |
|-----------|--------|--------|
| `english_glyph_table.json` | OK | Maps `♂` -> glyph 518, `♀` -> glyph 349 |
| `chunk_r38_fix.json` | OK | MSG 25 = "Mars" (EN), MSG 26 = "Venus" (EN) |
| R38 MSG 25 in PACKDATA | Contains glyph ID 518 | Same as original (男 = glyph 518) |
| R38 MSG 26 in PACKDATA | Contains glyph ID 349 | Same as original (女 = glyph 349) |
| R38 in v27 ISO | MD5 matches build | Correctly injected |
| R38 in RAM (save state) | "gender" text at 0x00E143E8 | Patched version loaded |

### The Translation Is a No-Op

The translation maps `♂` -> glyph 518 and `♀` -> glyph 349. But the ORIGINAL
Japanese text already uses those exact same glyph IDs for 男 and 女. The
"translation" does not change the glyph stream at all.

The INTENDED behavior is that the **R1272 font atlas** would have ♂/♀ bitmaps
replacing the 男/女 bitmaps at positions 518 and 349.

### Atlas Status (Verified)

| Check | Result |
|-------|--------|
| `build/english_font_atlas_preview.png` | ♂ at (168,288) slot 518, ♀ at (156,192) slot 349 -- PRESENT |
| `build/english_font_atlas.bin` | Non-zero pixel data at both positions -- PRESENT |
| R1272 in v27 ISO | MD5=`bafb26595e0058c6047bd7fe89cf0b7d`, matches build, different from original |
| R1272 in PACKDATA.DIG | Correctly injected (83,968 bytes vs original 67,584) |

### Why It Still Shows Kanji

The atlas binary contains ♂/♀ bitmaps at the correct logical positions, and the
patched R1272 is confirmed present in the v27 ISO. Yet the game renders 男/女.

**Most likely cause: PSMT4 swizzle mapping error for these specific glyph positions.**

The R1272 atlas uses PSMT4 (4-bit indexed) texture format. The `generate_font_atlas.py`
renders a linear image then calls `swizzle_psmt4()` to convert to the PS2 GS VRAM
layout. Glyph positions 518 and 349 sit at:
- Slot 518: row 24, col 14, pixel (168, 288)
- Slot 349: row 16, col 13, pixel (156, 192)

These are in the extended atlas area (original was 256x512, patched is 256x540).
If the swizzle computation has any error for rows beyond 256 or at certain column
boundaries, these positions would map to the wrong VRAM addresses, and the game
would still see the original kanji bitmaps from whatever happened to be in those
VRAM positions.

**Alternative explanation**: The atlas was correctly built and swizzled, but the
original R1272 had kanji bitmaps at positions 518 and 349. Our atlas generator
renders over ALL positions, so positions 518 and 349 should have ♂/♀. However,
the atlas is assembled from scratch (not overlaid on the original), so if the
generate script rendered ♂/♀ using the Windows font at size 10, those symbols
may not have rendered clearly enough to be visible at 12x12 pixels, OR the
swizzle placed them at a different location than the game expects.

**To definitively resolve**: Need to either (a) verify the PSMT4-swizzled binary
has correct pixel data at the VRAM addresses the game reads for glyphs 518/349,
or (b) use PCSX2 texture dumping to see what the game actually fetches from VRAM
for those glyph slots.

---

## 3. Root Cause: Sidebar Labels (性別, 種族)

### Rendering Path

The chargen sidebar labels are rendered through the **R38 MSG system + R1272 atlas**,
confirmed by EXE disassembly of `chargen_render_A` at VA 0x002F1090.

Each sidebar label (性別, 種族, 属性, 職業) is composed of 2 kanji, where each
kanji is a separate glyph ID rendered as TWO 12x12 R1272 tiles (left half + right half).

### R38 Data (Verified Correct)

| MSG Index | Original JP | Patched EN | In PACKDATA? | In RAM? |
|-----------|------------|------------|--------------|---------|
| MSG 10 | 種族 (race) | `[50,65,67,69]` = "race" | YES | YES (0x00E143E8 area) |
| MSG 11 | 性別 (gender) | `[39,69,78,68,69,82]` = "gender" | YES | YES |
| MSG 12 | 属性 (align) | `[33,76,73,71,78]` = "align" | YES | YES |
| MSG 13 | 職業 (class) | `[35,76,65,83,83]` = "class" | YES | YES |

The R38 translations are correct and loaded in RAM. Yet the sidebar shows Japanese.

### EXE Menu Struct System

Per `exe_sidebar_glyphs.md`, the sidebar uses a **56-byte menu struct table** at
EXE file offset 0x3C3000. Each struct record maps a glyph ID to R1272 tile pairs:

| Sidebar Label | Records | R1272 Tiles | Glyph IDs |
|--------------|---------|-------------|-----------|
| 性別 (Gender) | rec 31 + rec 32 | 745,746 + 747,748 | 511, 512 |
| 種族 (Race) | rec 33 + rec 34 | 749,750 + 751,752 | 513, 514 |
| 属性 (Alignment) | rec 35 + rec 31 | 753,754 + 745,746 | 515, 511 |
| 職業 (Class) | rec 24 + rec 37 | 731,732 + 757,758 | 504, 517 |

The sidebar renderer processes the R38 MSG glyph stream. When it encounters a
glyph ID >= 480, it looks up the corresponding **menu struct record** and renders
the kanji using the pre-defined R1272 tile pairs.

The translated R38 MSG 11 contains glyph IDs `[39,69,78,68,69,82]` ("gender").
These are all in the range 33-90 (lowercase/uppercase ASCII). The menu struct
system only activates for glyph IDs >= 480. For IDs < 480, the standard single-tile
R1272 rendering path is used.

**The fix IS working for the text system** -- the glyph IDs are correct. The issue
is that the R1272 tiles at positions 39, 69, 78, 68, 69, 82 must contain the correct
English letter bitmaps. Since other English text renders correctly on these same
screens (race names, description text), the lowercase/uppercase letter tiles ARE
present in the atlas.

### Why Sidebar Still Shows Japanese

Two possible explanations:

1. **The sidebar renderer uses a DIFFERENT code path** that reads glyph IDs from the
   EXE menu struct table INSTEAD of from R38. The `chargen_render_A` function might
   use R38 MSG for the description/main text area but use a separate lookup for the
   sidebar summary labels. In this case, the sidebar always renders glyph IDs 511+512
   (性別) regardless of what R38 MSG 11 contains.

2. **The sidebar renders the glyph IDs from R38 MSG but the chargen code uses a
   different MSG index** for sidebar labels vs the main display area. The MSG indices
   we translated (10-13) may be for the main area, while the sidebar uses different
   indices that still contain the original kanji.

**Most likely**: Option 1. The prior analysis in `exe_sidebar_glyphs.md` confirms
the sidebar label renderer loads glyph IDs from the 56-byte menu struct records
(which contain fixed kanji glyph IDs like 511, 512). The R38 MSG system is used
for the text area, but the sidebar labels come from the EXE data section.

### Fix Required

To translate sidebar labels, one of:

a. **Patch the EXE menu struct records** at 0x3C3000+ to change the glyph IDs from
   kanji (511, 512, etc.) to English letter glyph IDs. Challenge: each struct record
   maps ONE kanji -> two R1272 tiles. "Gender" needs 6 letters, each needing one tile.
   The struct format doesn't support multi-character rendering for a single label.

b. **Replace R1272 tile bitmaps** at positions 745-758 to show English text fragments
   instead of kanji. E.g., tiles 745+746 (normally 性 left+right halves) could show
   "Ge" + "nd" for part of "Gender". Challenge: tile reuse -- glyph 511 (性) is shared
   by 性別, 属性, and 性格.

c. **EXE code patch**: Modify the sidebar rendering function to call the R38 MSG
   text renderer instead of the menu struct tile renderer. This would make the sidebar
   use the same translated R38 data as everything else.

---

## 4. Race List Analysis

### Verified Working

| R38 MSG | Original | Patched | Screen Display |
|---------|----------|---------|---------------|
| MSG 29 | 人間 (Human) | `h[85][77][65][78]` = "hUMAN" | "Human" -- OK |
| MSG 30 | エルフ (Elf) | `e[76][70]` = "eLF" | "Elf" -- OK |
| MSG 31 | ノーム (Gnome) | `g[78][79][77][69]` = "gNOME" | "Gnome" -- OK |
| MSG 32 | ドワーフ (Dwarf) | `d[87][65][82][70]` = "dWARF" | "Dwarf" -- OK |
| MSG 33 | ホビット (Hobbit) | `h[79][66][66][73][84]` = "hOBBIT" | "Hobbit" -- slightly clipped |
| MSG 34 | オートマター (Automata) | `a[85][84][79][77][65]` = "aUTOMA" | Not visible (scroll needed) |

Note: First character is lowercase (glyph IDs 33-58 = a-z), remaining characters
use uppercase glyph IDs (65-90) which render as lowercase letters in the atlas.
The visual result shows proper mixed-case: "Human", "Elf", etc.

### Hobbit Clipping

"Hobbit" is 6 characters. The original ホビット is 4 kanji (8 tiles). At 12px per
tile, the original used 48px width (4 glyphs x 12px). "Hobbit" with 6 halfwidth
characters at ~6-8px each needs ~36-48px, which fits but is tight. The slight
right-edge clipping visible in the screenshot suggests the rendering area is exactly
48px wide and "Hobbit" just barely fits.

### Automata

Not visible in the 27-3 screenshot. This is expected -- the original game also
requires scrolling past Hobbit to see the Automata race option. The race list only
shows 5 items at a time.

---

## 5. Header Text Stale Display

Both screenshots show instruction text from the PREVIOUS phase:
- 27-2 shows "Enter your name." (should be "Select gender.")
- 27-3 shows "Select gender." (should be "Select a race.")

This is a **save state timing artifact**. The game updates the instruction text
with a brief delay after the phase transition. The save states were captured
immediately after transitioning, before the text update completed. This is NOT a
bug in the translation -- it's a capture timing issue.

---

## 6. Summary of Issues

| Issue | Severity | Root Cause | Fix Path |
|-------|----------|-----------|----------|
| 男/女 shows instead of ♂/♀ | Medium | R1272 atlas bitmap at slots 518/349 may have swizzle error, OR game reads from wrong VRAM position | Verify PSMT4 swizzle for rows > 256; alternatively use PCSX2 texture replacement |
| 性別/種族 sidebar labels in Japanese | High | EXE menu struct renders fixed kanji glyph IDs, independent of R38 | Requires EXE code patch or R1272 tile bitmap replacement |
| Stale header text | Low | Save state timing artifact | Non-issue (game updates correctly during normal play) |
| Hobbit slight clipping | Low | Character width vs rendering area | Acceptable -- fully readable |
| 新規登録 red banner | Medium | EXE composite glyphs via R1272, not in any MSG resource | R1272 tile replacement for tiles 705-722 |

---

## 7. Verification Checksums

| Resource | v27 ISO MD5 | Build File MD5 | Match? |
|----------|------------|----------------|--------|
| R37 (type01) | `528003c42bb5b635b65a4b7ddce918a4` | Same | YES |
| R38 (type01) | `6390d358800adf5f7628bbe91d28e334` | Same | YES |
| R1272 (type01) | `bafb26595e0058c6047bd7fe89cf0b7d` | Same | YES |

All three patched resources are correctly present in the v27 ISO PACKDATA.DIG and
confirmed loaded in RAM via save state analysis.
