# EXE Patching Requirements for Busin 0 English Translation

**Date:** 2026-05-22
**EXE:** `extracted/SLPM_653.78` (4,185,776 bytes, MIPS ELF)
**Reference EXE:** `extracted_busin1/SLUS_202.59` (5,038,496 bytes, Busin 1 English)

---

## Executive Summary

**Yes, the EXE must be modified.** While the bulk of translatable text lives in PACKDATA.DIG MSG resources (which use glyph-index encoding), the EXE contains critical font rendering infrastructure, hardcoded text strings, name entry tables, and the text rendering loop -- all of which need patching for a proper English translation. The five specific questions are answered below with detailed technical analysis.

---

## Question 1: Can We Avoid EXE Modifications Entirely?

**Answer: No.** Even if the MSG resources are re-encoded with English glyph indices and the font atlas is replaced, the EXE still needs modifications for the following reasons:

### 1a. The ASCII Glyph Table Is Incomplete

The EXE contains an 84-entry ASCII glyph lookup table at file offset 0x3C0870 (RAM 0x4C07F0). This table maps ASCII characters 0x20-0x73 (space through 's') to glyph indices 1-93. **Coverage stops at 's'** -- characters t-z and symbols like `{`, `|`, `}`, `~` are missing. For a full English translation, this table must be extended to cover the complete ASCII printable range (0x20-0x7E, 95 characters).

Additionally, there are 9 gaps in the existing mapping (glyph indices 2, 3, 4, 11, 12, 31, 32, 87, 88 are skipped), and the table currently uses a linear search algorithm (function at RAM 0x1A4B90). The table itself is only 168 bytes and could be expanded in-place or relocated.

### 1b. Font Descriptor Structs May Need Updates

12 active font descriptor structs at 0x3C0700 (28 bytes each) define 4 font size groups x 3 sub-variants each. These reference 256x256 texture pages via GS VRAM parameters (`tex_param_a`, `tex_param_b`). If the replacement font atlas uses a different page layout, texture format, or dimensions, these descriptors need updating.

### 1c. The Name Entry System Uses Hardcoded Tables

The name entry screen uses multiple EXE-resident tables:
- Katakana grid: 0x4C9AB0-0x4C9CCF (45 basic characters, 6 size variants each)
- Hiragana grid: 0x4C99B8-0x4C9AA7
- Special characters: 0x4C9CE0-0x4CA607 (dakuten, small kana, kanji)
- Kanji reverse-lookup: 0x4C9D20 (159 entries, SJIS-to-internal-ID)
- European/alphanumeric grid: 0x4CA608-0x4CA6EF

For an English translation, the name entry system must be converted from katakana/hiragana/kanji tabs to a Latin alphabet layout. This requires rewriting the grid tables and potentially patching the tab-switching code.

### 1d. Glyph Property Structs Control Rendering

133 per-glyph property structs at 0x3C0E78 (28 bytes each) contain float scale values, metric bytes, and atlas row/column coordinates. These structs are accessed by the rendering code at RAM 0x1F7770. If glyph positions change in the new atlas, these structs need updating. If not all 133 entries are needed (English needs far fewer than 858 glyphs), unused entries can be zeroed.

---

## Question 2: Variable Width Font (VWF) -- Is EXE Patching Required?

**Answer: Almost certainly yes.** The current rendering is fixed-width 12x12 pixel cells, and English text will look poor without VWF.

### Current Fixed-Width System

The text rendering code uses a `div-by-21` pattern to compute atlas UV coordinates from glyph indices:

```
col = glyph_index % 21    // 21 columns in 256-pixel atlas
row = glyph_index / 21    // row position
x_pixel = col * 12        // fixed 12px cell width
y_pixel = row * 12        // fixed 12px cell height
```

This pattern appears at 40+ locations in the EXE (clusters at file offsets 0x1E4xxx, 0x1EAxxx, 0x322xxx, 0x345xxx), indicating it is deeply embedded in the rendering system.

### What VWF Patching Requires

1. **Width table injection:** Add a byte array (one entry per glyph, ~128-858 entries depending on character count) with the pixel advance width of each glyph. This can be placed in unused EXE data space or in a modified PACKDATA resource.

2. **X-advance patch:** Find the instruction(s) that advance the cursor X-position by a fixed 12 pixels after each glyph. Replace the constant with a table lookup:
   ```mips
   # Before (fixed width):
   addiu $cursor_x, $cursor_x, 12
   
   # After (VWF):
   lbu   $t0, width_table($glyph_index)
   addu  $cursor_x, $cursor_x, $t0
   ```

3. **UV coordinate adjustment:** The source rectangle for each glyph can remain 12x12 (the full cell is blitted), or the U2 coordinate can be adjusted to clip unused pixels. The simpler approach is to keep the 12x12 source rect and only change the advance width.

4. **Line-wrap recalculation:** If the game has hardcoded line length limits (e.g., 20 characters per line at 12px = 240px), these must be changed to pixel-width-based wrapping rather than character-count-based.

### VWF Difficulty Assessment

**MODERATE-HIGH.** The div-by-21 pattern is used for atlas UV lookup, not for cursor advance. The cursor advance is likely a separate instruction. The approach is:

1. Use PCSX2 debugger to set a breakpoint on the text rendering function
2. Identify the exact instruction that adds the fixed advance width to the X cursor
3. Inject a hook at that point to read from a width table instead
4. Use **Armips** assembler to write the MIPS patch

### Can We Skip VWF?

Technically yes, but the result would be ugly. Fixed-width Latin text means 'i' and 'W' occupy the same 12px cell width. At 12px cells, a line can hold ~21 characters -- far too few for English dialogue. VWF could roughly double the characters per line (from ~21 to ~35-40), which is critical for fitting English translations.

### No VWF Table in the EXE

A scan of the EXE data section found **no existing glyph width tables** (confirmed by recon26). The 4 identical 256-byte tables at 0x3DDC40 that were initially suspected are actually `floor(log2(n))` lookup tables from the Metrowerks C runtime library. The adjacent data at 0x3DE040 is a standard ctype classification table. **VWF is not implemented in the original game** and must be added from scratch.

---

## Question 3: Hardcoded Text Strings in the EXE

**Answer: Yes, there are 464 Shift-JIS strings that need review, plus several specific categories that need translation.**

### Categories of EXE Strings

| Category | Count | File Offset Range | Translation Required? |
|----------|-------|-------------------|----------------------|
| Debug logging (developer-only) | ~300 | 0x3EC910-0x3F8000 | No -- not player-visible |
| Battle debug messages | ~50 | 0x3F0B00-0x3F3000 | No -- debug build only |
| Save slot labels | 3-5 | 0x3F9370+ | **YES** |
| Error/system messages | ~20 | scattered | **YES** (if player-visible) |
| Format strings with `%d`/`%s` | ~30 | scattered | **YES** (careful: preserve format specifiers) |
| Debug menu label | 1 | near 0x3F0000 | Optional |

### Specific Strings Requiring Translation

1. **Save slot names:** Full-width Japanese strings like "BUSIN 0 data 1/2/3" (at 0x3F9370+). The Busin 1 English EXE uses `WIZ-GBUSIN0/1/2` and `WIZ-STOPPAGE` instead.

2. **"Msg No Over!!" and similar system messages:** These appear when the message system encounters errors. Should be translated for debugging purposes.

3. **FCD_ resource name references:** Busin 0 has 32 FCD_ resource references (e.g., `FCD_battle_font`, `FCD_event_font`). These are **functional strings** used by the resource loader to find data, NOT debug-only. **Do NOT translate these** -- they must match the resource names in PACKDATA.DIG. (Note: Busin 1's release build stripped these, suggesting they may be loaded differently in a clean build.)

4. **Memory card identifier:** String like `BASLPS-25249WIZTFL` -- this is the save file directory name on the memory card. **Do NOT change** unless you want to break compatibility with existing Japanese saves. (To match Busin 1 convention, it could be changed to `BASLPM-65378WIZTFL`.)

### String Patching Constraints

- Each EXE string occupies a fixed number of bytes at a known offset
- English replacement must be <= original byte length (cannot expand EXE strings without code relocation)
- Pad with null bytes after English text
- Shift-JIS characters are 2 bytes; ASCII characters are 1 byte. A 10-character Japanese string (20 bytes) can hold up to 19 ASCII characters + null terminator
- Verify modified offsets are in .data/.rodata sections, NOT .text (code) sections
- VA-to-file calculation: `file_offset = VA - 0x00100000 + 0x80`

---

## Question 4: Atlas Grid Change and the div-21 Pattern

**Answer: If you change the atlas grid layout, you MUST patch the div-21 instructions. But you probably should NOT change the grid.**

### Current Atlas Layout

- Texture: 256x512 pixels, PSMT4 (4bpp indexed, 16 colors)
- Grid: 21 columns x 42 rows = 882 slots (858 used)
- Cell size: 12x12 pixels (252 of 256 horizontal pixels used, 504 of 512 vertical)
- Glyph position: `x = (index % 21) * 12`, `y = (index / 21) * 12`

### Why NOT to Change the Grid

The div-21 pattern appears at **40+ locations** across multiple EXE code clusters. Patching all of them is error-prone and risky. Instead, the recommended approach is:

1. **Keep the 21x42 grid and 12x12 cell size**
2. Place English glyphs in the first ~96 grid positions (A-Z, a-z, 0-9, punctuation)
3. Leave remaining grid positions empty or available for special characters
4. The VWF system handles the visual width; the atlas cell size stays 12x12

### If You MUST Change the Grid

If a different grid layout is absolutely needed (e.g., larger cells for better readability):

- **16x16 cells:** 16 columns x 32 rows = 512 slots. Change all `li $r, 21; div` to `li $r, 16; div` (or better: replace with `srl $r, 4` for a power-of-2 divide).
- **Every instance** of the constant 21 used in glyph coordinate math must be found and patched.
- The font descriptor structs, glyph property structs, and any float-based UV calculations must also be updated.
- This is a HIGH-RISK modification with many potential failure points.

### If You Change the Texture Dimensions

The TEX0 GS register value at font resource header offset 0x50 encodes the texture dimensions (currently TW=8 meaning 2^8=256 width, TH=9 meaning 2^9=512 height). If you change texture dimensions, update this register value AND any EXE code that references the texture size.

---

## Question 5: Save Data Format and English Character Names

**Answer: Yes, this is a real concern. The name entry system uses a custom encoding that must be adapted.**

### Current Name Storage

Character names in save data are stored as arrays of **8 x uint16 LE** values, with unused slots filled with 0xFFFF. The encoding is NOT SJIS, NOT Unicode, NOT raw glyph indices. It uses an internal "name value" system tied to the name entry grid position:

- Basic katakana: `name_value = grid_position + 193`
- Glyph conversion: `glyph_index = name_value - 95` (for katakana, equals `grid_position + 98`)
- Extended characters (dakuten, small kana): different mappings
- Chouon (long vowel mark): `name_value = 93` (special case)
- Max name length: 8 characters (16 bytes)

### RAM Locations

- Guild roster names: base 0x55DD22, stride 992 bytes per character
- Active party names: base 0x5601F2, stride 496 bytes per character
- Level field: offset +0xBA from name start

### What Must Change for English Names

1. **Name entry grid tables (EXE):** Replace katakana/hiragana/kanji grids (at 0x4C99B8-0x4CA607) with a Latin alphabet grid. Each grid cell needs 6 glyph-index variants (one per font size) or the size-variant system needs simplification.

2. **Name encoding logic (EXE code):** The conversion from name_value to glyph_index (at code region 0x2F5410-0x2F6554) must handle the new Latin character set. The simplest approach: define name_value = ASCII code for Latin characters, and add a new conversion path in the renderer.

3. **Name length:** 8 characters at uint16 per char = 16 bytes. This is sufficient for English names (8 characters max). If longer names are needed, the save struct must be expanded, which affects all save/load code.

4. **Save compatibility:** Existing Japanese saves will have name_values that map to katakana. If the font atlas is replaced with Latin characters, loading an old save will display garbage names. Options:
   - Accept incompatibility (typical for fan translations)
   - Add a name_value translation layer that converts old katakana name_values to equivalent romaji
   - Change the memory card directory identifier to a new value so old saves are invisible

5. **Memory card identifier:** Currently `BASLPS-25249WIZTFL` or similar. Consider NOT changing this (the game still needs to access the same save format). The Busin 1 English release uses `BASLUS-20259WIZTFL` -- a different serial.

### NPC Names

NPC/character names that appear in dialogue (Vera, Erika, Konde, etc.) are stored as glyph-index sequences in MSG resources, NOT as save data. These translate by changing the MSG data. However, when party members are referenced by name in events, the name rendering may pull from the save data name field -- verify by testing in PCSX2.

---

## Complete EXE Patch Checklist

| Priority | Patch Target | EXE File Offset | Difficulty | Required? |
|----------|-------------|-----------------|------------|-----------|
| CRITICAL | Font atlas resource in PACKDATA (not EXE) | n/a | Medium | YES |
| CRITICAL | VWF: X-advance width table + cursor patch | TBD (find in debugger) | High | YES for quality |
| HIGH | ASCII glyph table: extend to full A-Z, a-z, 0-9, punct | 0x3C0870 | Low | YES |
| HIGH | Name entry grid tables: Latin alphabet | 0x3C99B8-0x3CA607 (file) | Medium | YES |
| HIGH | Per-glyph property structs: update for new glyph positions | 0x3C0E78 | Low-Med | Likely |
| MEDIUM | Save slot label strings: translate SJIS | 0x3F9370+ | Low | YES |
| MEDIUM | Player-visible error/system messages | scattered | Low | YES |
| MEDIUM | Name encoding logic: support Latin chars | code at 0x2F5410+ | Medium-High | YES |
| LOW | Font descriptor structs: GS params | 0x3C0700 | Low | Maybe |
| LOW | Debug strings (developer-only) | 0x3EC910-0x3F8000 | Low | No |
| DO NOT | FCD_ resource name strings | scattered | n/a | NO - functional |
| DO NOT | Memory card directory identifier | varies | n/a | Avoid |

---

## Recommended Approach

### Phase 1: Minimal Viable Patch (No VWF)

1. Replace font atlas texture (PACKDATA resource 1272) with English glyphs in the existing 21x42 grid
2. Extend ASCII glyph table at 0x3C0870 to cover full printable ASCII
3. Update per-glyph property structs at 0x3C0E78 for new glyph positions
4. Re-encode all MSG resources with English glyph indices
5. Translate save slot labels and visible system strings in EXE
6. **Result:** English text renders, but fixed-width (ugly but functional)

### Phase 2: VWF Enhancement

1. Use PCSX2 debugger to trace the text rendering loop from the div-21 glyph lookup
2. Identify the cursor X-advance instruction
3. Inject a width table lookup using Armips (MIPS assembler for ELF patching)
4. Store the width table in unused EXE data section space (~128 bytes for ASCII widths)
5. Test line wrapping and text box overflow

### Phase 3: Name Entry System

1. Replace katakana/hiragana/kanji grid tables with Latin alphabet grid
2. Patch name encoding to use ASCII-compatible name_values
3. Test name entry, save, load, and in-dialogue name display

### Phase 4: Polish

1. Translate remaining EXE strings
2. Adjust text box dimensions if needed (search for hardcoded pixel widths in UI layout code)
3. Handle edge cases (text overflow, special characters, format strings)

---

## Key Code Locations for Debugger Work

| Function | RAM VA | File Offset | Purpose |
|----------|--------|-------------|---------|
| Glyph lookup (linear search) | 0x1A4B90 | 0x0A4C10 | Searches 84-entry ASCII table |
| Glyph property access | 0x1F7770 | 0x0F77F0 | Reads metric byte from 28B struct |
| Atlas UV calc (div-21) | 0x2E4230 | 0x1E42B0 | Computes column = index % 21 |
| Atlas UV calc (second) | 0x2E4284 | 0x1E4304 | Second div-21 for row calc |
| Atlas UV with offset | 0x2EA540 | 0x1EA5C0 | col+80 offset variant |
| Name entry renderer | 0x2F5410-0x2F6554 | 0x1F5490+ | Name grid rendering code |
| BSS char table ref | 0x183500 | 0x08351C | References font pointer table |

---

## Reference: Busin 1 (English) vs Busin 0 (Japanese) EXE Differences

| Feature | Busin 0 (JP) | Busin 1 (EN) |
|---------|-------------|-------------|
| EXE size | 4.1 MB | 4.8 MB |
| FCD_ debug strings | 32 references | 0 (stripped) |
| TextEvent debug | 20+ strings | 0 (stripped) |
| Monster name table | Not in EXE | 108 entries at 0x4B0960 |
| Class/race names | Not in EXE | In EXE (FIGHTER, THIEF, etc.) |
| Item category labels | Not in EXE | In EXE (FLAIL, STAFF, etc.) |
| Source code paths | Not present | 87 paths (source/game/...) |
| Save ID | SLPS-25249 | SLUS-20259 |
| VWF implementation | None found | Unknown (needs investigation) |

**Important:** Busin 1 is a "release build" with debug strings stripped, while Busin 0 is closer to a "debug build." The underlying font rendering code is likely very similar between the two, making Busin 1's EXE a useful reference for understanding how the English localization team handled VWF (if they did).

---

## Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| VWF patching breaks text rendering | HIGH | MEDIUM | Test incrementally; keep backup of original EXE |
| Missed div-21 instances cause partial rendering bugs | HIGH | MEDIUM | Keep the 21-column grid; don't change it |
| Name entry patch corrupts save data | MEDIUM | LOW | Change MC directory ID to isolate from JP saves |
| Format strings with %d/%s cause crashes if patched wrong | HIGH | LOW | Preserve all format specifiers exactly |
| FCD_ resource names accidentally modified | HIGH | LOW | Mark these strings as DO NOT TRANSLATE |
| EXE string patch overwrites adjacent code | HIGH | LOW | Verify each patch offset is in .data, not .text |
