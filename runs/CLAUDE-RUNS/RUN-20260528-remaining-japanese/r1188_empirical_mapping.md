# R1188 Empirical Glyph ID to Atlas Cell Mapping

**Date**: 2026-05-28
**Source atlas**: `build/textures_to_edit/R1188_CORRECT_dbw512.png` (1024x1024, grayscale)
**Source EXE**: `extracted/SLPM_653.78`
**Source R1188**: `extracted/packdata_raw/1188_type01.raw` (528,384 bytes)

---

## 1. Atlas Grid Structure (Left Half: x=0-495)

The deswizzled atlas (TBW=16, DBW=512) contains a character grid in its left half with
21 columns and 42 rows. Cell boundaries were determined empirically by analyzing
horizontal and vertical brightness gaps.

### Column x-positions (21 columns)

| Col | x-start | Width | Notes |
|-----|---------|-------|-------|
| 0   | 0       | 15px  | Narrow first column |
| 1   | 17      | 22px  | Standard width |
| 2   | 41      | 22px  | |
| 3   | 65      | 22px  | |
| 4   | 89      | 22px  | |
| 5   | 113     | 22px  | |
| 6   | 137     | 22px  | |
| 7   | 161     | 22px  | |
| 8   | 185     | 22px  | |
| 9   | 209     | 22px  | |
| 10  | 233     | 22px  | |
| 11  | 257     | 22px  | |
| 12  | 281     | 22px  | |
| 13  | 305     | 22px  | |
| 14  | 329     | 22px  | |
| 15  | 353     | 22px  | |
| 16  | 377     | 22px  | |
| 17  | 401     | 22px  | |
| 18  | 425     | 22px  | |
| 19  | 449     | 22px  | |
| 20  | 473     | 22px  | |

### Row y-positions (42 rows)

| Row | y-start | Height | Content |
|-----|---------|--------|---------|
| 0   | 5       | 16px   | ASCII: 5-9, punctuation, A-I |
| 1   | 29      | 18px   | ASCII: (c), a-s |
| 2   | 51      | 18px   | Symbols + hiragana start |
| 3   | 74      | 19px   | Hiragana continued |
| 4   | 99      | 17px   | Hiragana voiced tail + katakana start |
| 5   | 122     | 18px   | Katakana continued |
| 6-41| 146-986 | 24px each | Kanji (36 rows x 21 cols = 756 kanji) |

---

## 2. Character Inventory by Row

### Row 0 (y=5): ASCII Upper
```
Col: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
     5  6  7  8  9  :  ;  <  =  >  ?  SP A  B  C  D  E  F  G  H  I
```
20 occupied cells (col 11 = space/blank).

### Row 1 (y=29): ASCII Lower
```
Col: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
     .  (c) a  b  c  d  e  f  g  h  i  j  k  l  m  n  o  p  q  r  s
```
Col 0 is nearly empty (stray pixels). 20 occupied cells.

### Row 2 (y=51): Symbols + Hiragana Start
```
Col: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
     ×  ○  ×  ←  →  ＿  SP あ い う え お か き く け こ さ し す せ
```
Cols 0-2: button icons (X, circle, X). Cols 3-4: arrows. Col 5: underscore.
Col 6: empty. Cols 7-20: hiragana あ through せ (14 chars). Visually confirmed.

**MISSING HIRAGANA**: Between せ (row 2 col 20) and や (row 3 col 0), the standard
hiragana sequence そ た ち つ て と な に ぬ ね の は ひ ふ へ ほ ま み む め
(20 characters) is NOT in the left-half grid.

### Row 3 (y=74): Hiragana Continued
```
Col: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
     や ゆ よ ら り る れ ろ わ を ん が ぎ ぐ げ ご ざ じ ず ぜ ぞ
```
21 characters: hiragana や through ん (11), then voiced が through ぞ (10). Confirmed.

### Row 4 (y=99): Hiragana Voiced Tail + Katakana Start
```
Col: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
     ?  ?  ?  ?  ア イ ウ エ オ カ キ  ク ケ コ サ シ  ス セ ソ タ チ
```
Cols 0-3: hiragana voiced characters (partially illegible at low resolution,
likely ぱ ぴ ぷ ぺ or similar handakuten characters completing the hiragana set).
Cols 4-20: katakana ア through チ (17 characters). Visually confirmed from strip image.

### Row 5 (y=122): Katakana Continued + Voiced Katakana
```
Col: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
     ラ リ ル レ ロ ワ ヲ ン ガ ギ グ  ゲ ゴ ザ ジ ズ  ゼ ゾ ダ ヂ ヅ
```
Katakana ラ through ン (8 chars), then voiced katakana ガ through ヅ (13 chars).
Visually confirmed from strip image.

**MISSING KATAKANA**: The standard katakana sequence between チ (row 4 col 20)
and ラ (row 5 col 0) is: ツ テ ト ナ ニ ヌ ネ ノ ハ ヒ フ ヘ ホ マ ミ ム メ モ ヤ ユ ヨ
(21 characters). These are NOT present in the left-half grid rows 0-5. They must be:
- In the right half of the atlas (x=512-1023), which contains a smaller-scale
  rendering of the same character set in an irregular dense layout
- Or in a different atlas resource (R1189 for the keyboard character grid)
- The right half appears to contain all characters at ~16x16 size but lacks
  clear column/row boundaries for precise mapping

### Rows 6-41 (y=146-986): Kanji Grid

Each row has 21 kanji. Total: 756 kanji across 36 rows.
Full transcription available in `r1188_label_coordinates.md`.

Key kanji locations for tab labels:

| Kanji | Row | Col | Atlas Position (x, y) | Used In |
|-------|-----|-----|----------------------|---------|
| 記    | 10  | 6   | (137, 242)           | 記号 (Sym tab) |
| 力    | 10  | 12  | (281, 242)           | 力 (STR stat) |
| 性    | 19  | 20  | (473, 456)           | 性別 (Gender), 属性 (Align) |
| 決    | 20  | 8   | (185, 482)           | 決定 (Confirm) |
| 号    | 21  | 19  | (449, 506)           | 記号 (Sym tab) |
| 職    | 15  | 9   | (209, 362)           | 職業 (Class) |
| 種    | 18  | 10  | (233, 434)           | 種族 (Race) |
| 族    | 18  | 11  | (257, 434)           | 種族 (Race) |
| 属    | 37  | 1   | (17, 890)            | 属性 (Align) |
| 敏    | 36  | 20  | (473, 866)           | 敏捷度 (AGI) |
| カ    | 4   | 15  | (353, 99)            | カナ (Kana tab) |
| ナ    | 5   | 9   | (209, 122)           | カナ (Kana tab) |

---

## 3. Glyph ID System for R1188

### ID Encoding

```
glyph_id = (group << 8) | index
group = glyph_id >> 8
index = glyph_id & 0xFF
```

### Groups Found in EXE

Four groups reference R1188 bitmap sprites:

| Group | Base ID | EXE Table Offset | Purpose |
|-------|---------|-------------------|---------|
| 0x19 (25) | 6400  | 0x3C9DA0          | Tab labels, buttons (primary state) |
| 0x1A (26) | 6656  | 0x3C9E50          | Same labels (highlighted/selected state?) |
| 0x1B (27) | 6912  | 0x3C9F00          | Same labels (another visual state?) |
| 0x1C (28) | 7168  | 0x3C9FB0          | Same labels (yet another state?) |

Each group contains 13 glyph IDs (indices 0-12) in the same layout positions,
corresponding to the same UI elements rendered with different CLUTs for visual states
(normal, hover, selected, disabled).

### Group 0x19 (6400-6412): Tab Labels and Buttons

| Glyph ID | Hex    | Index | Japanese Label | English | PCSX2 Hash | Sprite Size |
|----------|--------|-------|----------------|---------|------------|-------------|
| 6400     | 0x1900 | 0     | カナ           | Kana    | 1f839869   | 48x20       |
| 6401     | 0x1901 | 1     | かな           | Hira    | 9677cb23   | 48x20       |
| 6402     | 0x1902 | 2     | 英数           | ABC     | 6f1fb24f   | 48x20       |
| 6403     | 0x1903 | 3     | 記号           | Sym     | 19a39fbc   | 48x20       |
| 6404     | 0x1904 | 4     | (5th tab)      | --      | --         | 48x20?      |
| 6405     | 0x1905 | 5     | 決定           | OK      | d09a04bd   | 40x24       |
| 6406     | 0x1906 | 6     | 男名           | M.Name  | --         | 48x20?      |
| 6407     | 0x1907 | 7     | 女名           | F.Name  | --         | 48x20?      |
| 6408     | 0x1908 | 8     | 1文字消す      | Delete  | --         | wider       |
| 6409     | 0x1909 | 9     | 全消去         | Clear   | --         | wider       |
| 6410     | 0x190A | 10    | Extra 1        | --      | --         | --          |
| 6411     | 0x190B | 11    | Extra 2        | --      | --         | --          |
| 6412     | 0x190C | 12    | Extra 3        | --      | --         | --          |

### Chargen Sidebar Labels (from PCSX2 dumps, same CLUT)

| PCSX2 Hash       | Japanese | English | Size  | Group | Notes |
|------------------|----------|---------|-------|-------|-------|
| 16625baf9feaeafb | 性別     | Gender  | 48x20 | 0x19  | Sidebar label |
| 88ff8b577084a2a8 | 職業     | Class   | 48x20 | 0x19  | Sidebar label |
| 9bec87b4031a7172 | 種族     | Race    | 48x20 | 0x19  | Sidebar label |
| c89b469f7a152a6  | 属性     | Align   | 48x20 | 0x19  | Sidebar label |

### Stat Labels (from PCSX2 dumps, same CLUT)

| PCSX2 Hash       | Japanese | English | Size  | Notes |
|------------------|----------|---------|-------|-------|
| f2013a64642252e3 | 力       | STR     | 64x16 | Single kanji |
| bb20512b10c3128b | 知恵     | IQ      | 64x16 | 2 kanji |
| aa43f966ad69195e | 信仰心   | PIE     | 64x16 | 3 kanji |
| 5d0c6327e20384e7 | 生命力   | VIT     | 64x16 | 3 kanji |
| 4841ef9a2dc4981  | 敏捷度   | AGI     | 64x16 | 3 kanji |
| 280ea82c1c476a98 | 幸運度   | LCK     | 64x16 | 3 kanji |
| d455234204274c43 | HP/MAX   | HP/MAX  | 64x16 | Already Latin |

---

## 4. Runtime Resolution: VRAM Sub-Atlas Mapping

### The TBW Problem

R1188's pixel data is uploaded to GS VRAM as PSMCT32 with DBW=512 (buffer width 512
32-bit words = 2048 bytes per row). It is then read as PSMT4 with TBW=16, producing
a coherent 1024x1024 character grid.

However, when rendering tab labels and stats, the game reconfigures TEX0:
- TBW=4 (256 pixels per row in PSMT4 terms)
- TW=8, TH=8 (256x256 texture window)
- TBP0 = base + page_offset (selects a 256x256 sub-region)

This means glyph UV coordinates (U, V) are relative to a 256x256 window, not the
full 1024x1024 atlas. The mapping between 256x256 windows and 1024x1024 pixel
positions is NOT a simple spatial subdivision -- PSMT4 block/column swizzle tables
produce complex reordering within each 128x128 page when TBW changes.

### Per-Glyph UV Resolution

The EXE function at VA 0x4943D0 (file offset 0x3943D0) resolves glyph IDs:

```c
void render_bitmap_glyph(uint16 glyph_id) {
    uint8 group = glyph_id >> 8;     // e.g., 0x19 for tab labels
    uint8 index = glyph_id & 0xFF;   // e.g., 0x00 for "カナ"
    
    // BSS table at VA 0x4EB104: stride 8 per group
    // Populated at runtime from R1188 header metadata
    uint32 texpage = *(uint32*)(0x4EB100 + group*8);
    uint32 uv_base = *(uint32*)(0x4EB104 + group*8);
    
    uint8* glyph_data = uv_base + index * 8;
    uint8 U = glyph_data[0];   // U within 256x256 window (0-255)
    uint8 V = glyph_data[1];   // V within 256x256 window (0-255)
    uint8 flags = glyph_data[2];
    
    gs_draw_sprite(U | (V << 8) | (texpage << 16), flags);
}
```

### BSS Table Population

The BSS table at VA 0x4EB100 is populated at runtime when R1188 loads.
The source data is in R1188's header at file offset 0xA60-0xBFF (416 bytes).

This data region uses a **game-specific packed encoding** that could not be decoded
through brute-force byte interpretation. Tested interpretations include:
- 4-byte UVWH tuples: values too large and irregular
- 2-byte LE pairs: no sensible coordinate pattern
- GS UV 10.4 fixed point: many values exceed 1024x1024
- GIF tags: NLOOP values unreasonably large
- Nibble-packed data: no clear structure

The data consists of 9 non-zero groups separated by zero padding (704 bytes of data
total, 256 bytes of zeros), matching the 9 groups of sprite metadata in the header.

---

## 5. Empirical Pixel Mapping: Glyph IDs to PCSX2-Captured Positions

Since runtime UV data cannot be decoded from the R1188 header, the definitive
mapping comes from PCSX2 texture dumps which capture exactly what the GS renders.

### PCSX2 Texture Replacement Filenames

Format: `{content_hash}-{clut_hash}-r{W}x{H}-{gs_page}.png`

All R1188 sprites share:
- CLUT hash: `3cb39bf7659ef15f`
- GS page: `00002214`

### Confirmed Glyph ID to Content Hash Mapping

| Glyph ID | Content Hash      | Label    | Replace With | Size  |
|----------|-------------------|----------|--------------|-------|
| 6400     | 1f839869fab251d   | カナ     | Kana         | 48x20 |
| 6401     | 9677cb23da53ff88  | かな     | Hira         | 48x20 |
| 6402     | 6f1fb24fad5cd1a   | 英数     | ABC          | 48x20 |
| 6403     | 19a39fbc8a08d7ec  | 記号     | Sym          | 48x20 |
| 6405     | d09a04bdfaf715bc  | 決定     | OK           | 40x24 |

Additional sidebar/chargen labels (glyph IDs uncertain, may be in groups 0x1A-0x1C):

| Content Hash      | Label    | Replace With | Size  |
|-------------------|----------|--------------|-------|
| 16625baf9feaeafb  | 性別     | Gender       | 48x20 |
| 88ff8b577084a2a8  | 職業     | Class        | 48x20 |
| 9bec87b4031a7172  | 種族     | Race         | 48x20 |
| c89b469f7a152a6   | 属性     | Align        | 48x20 |

Stat labels (glyph IDs likely in a different group, possibly from R38 system):

| Content Hash      | Label    | Replace With | Size  |
|-------------------|----------|--------------|-------|
| f2013a64642252e3  | 力       | STR          | 64x16 |
| bb20512b10c3128b  | 知恵     | IQ           | 64x16 |
| aa43f966ad69195e  | 信仰心   | PIE          | 64x16 |
| 5d0c6327e20384e7  | 生命力   | VIT          | 64x16 |
| 4841ef9a2dc4981   | 敏捷度   | AGI          | 64x16 |
| 280ea82c1c476a98  | 幸運度   | LCK          | 64x16 |

---

## 6. Missing Kana Analysis

The left-half grid contains only ~59 of ~160 kana characters. The missing characters
(approximately 100 kana) must reside in the right half (x=512-1023) or in R1189.

### Left-Half Kana Inventory

| Section | Characters Present | Count | Missing Range | Missing Count |
|---------|-------------------|-------|---------------|---------------|
| Hiragana basic | あ-せ | 14 | そ-め | 20 |
| Hiragana ya-row | や-ん | 11 | -- | 0 |
| Hiragana voiced | が-ぞ (row 3) | 10 | -- | 0 |
| Hiragana voiced | row 4 cols 0-3 (4 chars) | 4 | remaining voiced | ~6 |
| Katakana basic | ア-チ | 17 | ツ-ヨ | 21 |
| Katakana ra-n | ラ-ン | 8 | -- | 0 |
| Katakana voiced | ガ-ヅ | 13 | デ-ヴ | ~8 |
| **Total** | | **~77** | | **~55** |

### Implications for Tab Labels

The tab label "カナ" requires both カ and ナ:
- **カ is present** at row 4 col 9, atlas position (209, 99)
- **ナ is NOT present** in the left-half grid (it belongs to the ツ-ヨ gap)

The tab label "かな" requires both か and な:
- **か is present** at row 2 col 12, atlas position (281, 51)
- **な is NOT present** in the left-half grid (it belongs to the そ-め gap)

Since glyph IDs 6400+ reference PRE-RENDERED BITMAP SPRITES (not individual chars),
the game reads these labels from specific UV regions within R1188's VRAM layout.
These sprites are NOT visible in the deswizzled left-half grid -- they exist either
as composed multi-character regions in a TBW=4 sub-atlas view, or in the right half.

---

## 7. Atlas Character Grid: Complete Cell Index

Each cell in the 21-column, 42-row grid has a linear index:
```
cell_index = row * 21 + col
```

The atlas contains approximately 878 occupied cells:
- Rows 0-1: 40 ASCII characters (digits, punctuation, letters)
- Row 2: 14 hiragana + 7 symbols = 21 cells (1 empty)
- Row 3: 21 hiragana
- Row 4: 10 hiragana voiced + 11 katakana = 21
- Row 5: 21 katakana
- Rows 6-41: 756 kanji (36 rows x 21 cols)
- Total: ~878 occupied cells

### Kana Character Positions (Key Characters for Tab Labels)

| Character | Meaning | Row | Col | Cell Index | Atlas (x, y) |
|-----------|---------|-----|-----|------------|--------------|
| カ        | ka (katakana) | 4   | 9   | 93         | (209, 99)    |
| ナ        | na (katakana) | --  | --  | --         | **NOT IN LEFT HALF** |
| か        | ka (hiragana) | 2   | 12  | 54         | (281, 51)    |
| な        | na (hiragana) | --  | --  | --         | **NOT IN LEFT HALF** |
| あ        | a             | 2   | 7   | 49         | (161, 51)    |
| い        | i             | 2   | 8   | 50         | (185, 51)    |
| う        | u             | 2   | 9   | 51         | (209, 51)    |
| え        | e             | 2   | 10  | 52         | (233, 51)    |
| お        | o             | 2   | 11  | 53         | (257, 51)    |
| ア        | A (katakana)  | 4   | 4   | 88         | (89, 99)     |
| イ        | I (katakana)  | 4   | 5   | 89         | (113, 99)    |
| ウ        | U (katakana)  | 4   | 6   | 90         | (137, 99)    |
| エ        | E (katakana)  | 4   | 7   | 91         | (161, 99)    |
| オ        | O (katakana)  | 4   | 8   | 92         | (185, 99)    |
| キ        | KI (katakana) | 4   | 10  | 94         | (233, 99)    |
| ク        | KU (katakana) | 4   | 11  | 95         | (257, 99)    |
| ラ        | RA (katakana) | 5   | 0   | 105        | (0, 122)     |
| ン        | N (katakana)  | 5   | 7   | 112        | (161, 122)   |
| ガ        | GA (katakana) | 5   | 8   | 113        | (185, 122)   |
| ギ        | GI (katakana) | 5   | 9   | 114        | (209, 122)   |

**CRITICAL: Characters ナ and な are NOT in the left-half grid.**
- Katakana ナ is part of the missing sequence ツ-ヨ (21 chars between チ and ラ)
- Hiragana な is part of the missing sequence そ-め (between せ and や)
- Row 2 cols 7-20 contain あいうえおかきくけこさしすせ (14 chars ending at せ)
- Row 3 starts with やゆよ (skipping そたちつてとなにぬねのはひふへほまみむめ)
- These missing kana must exist in the RIGHT HALF (x=512-1023) or in R1189

---

## 8. Critical Finding: Deswizzled Atlas vs Runtime VRAM

The deswizzled atlas (`R1188_CORRECT_dbw512.png`) shows the data as if read with
TBW=16 (1024-pixel-wide rows). But the game renders tab labels using TBW=4
(256-pixel-wide rows) with a different TBP0 page offset.

**The pixel positions in the deswizzled atlas do NOT directly correspond to the U,V
coordinates used by the glyph rendering code.** The PSMT4 swizzle tables produce a
different pixel arrangement when the buffer width changes.

This means:
1. You CANNOT simply read pixel coordinates from the deswizzled atlas and use them
   as UV values in the glyph rendering system
2. To find where glyph ID 6400 (カナ) appears in VRAM, you would need to simulate
   the GS VRAM page/block/column layout with TBW=4 and the specific TBP0 offset
3. The PCSX2 texture replacement approach (matching by content hash) completely
   bypasses this problem -- no UV knowledge needed

---

## 9. Translation Approaches (Ranked by Feasibility)

### A. PCSX2 Texture Replacement (ALREADY IMPLEMENTED)
- Replace PCSX2 dump PNGs by content hash
- Tool: `tools/patch_r1188_tabs.py`
- Status: Working for tab labels (48x20), stat labels (64x16), confirm button (40x24)
- Limitation: Only works with PCSX2 (not real hardware or other emulators)

### B. Direct R1188 Pixel Edit at Original Positions
- Requires knowing the exact TBW=4 VRAM positions of each label sprite
- Then converting those positions to TBW=16 deswizzled atlas coordinates
- Then editing the deswizzled atlas and re-swizzling
- Blocked by: cannot decode the UV metadata at 0xA60-0xBFF

### C. EXE Code Patch: Replace Bitmap Glyph IDs with Main Font Strings
- Patch the render function at VA 0x2FB0B0 to intercept glyph IDs 6400+
- When detected, render English text using the main text engine (R1272 font)
- Most flexible but requires finding free EXE code space for the hook

### D. Redirect UV Coordinates via EXE/R1188 Header Patch
- Render English labels in unused atlas area (e.g., bottom strip y=1008-1023)
- Patch R1188 header metadata (0xA60-0xBFF) to point UV data to new positions
- Requires understanding the packed UV encoding (currently blocked)

---

## 10. Key Files Reference

| Item | Path |
|------|------|
| R1188 raw | `extracted/packdata_raw/1188_type01.raw` |
| Deswizzled atlas | `build/textures_to_edit/R1188_CORRECT_dbw512.png` |
| PCSX2 tab dumps | `build/pcsx2_dumps/*3cb39bf7659ef15f*r48x20*` |
| PCSX2 stat dumps | `build/pcsx2_dumps/*3cb39bf7659ef15f*r64x16*` |
| Tab label patcher | `tools/patch_r1188_tabs.py` |
| R1188 parser | `tools/parse_r1188.py` |
| EXE glyph table 0x19 | EXE file 0x3C9DA0 (13 glyph IDs: 6400-6412) |
| EXE glyph table 0x1A | EXE file 0x3C9E50 (13 glyph IDs: 6656-6668) |
| EXE glyph table 0x1B | EXE file 0x3C9F00 (13 glyph IDs: 6912-6924) |
| EXE glyph table 0x1C | EXE file 0x3C9FB0 (13 glyph IDs: 7168-7178?) |
| Glyph resolver func | EXE VA 0x4943D0 (file 0x3943D0) |
| GS draw sprite func | EXE VA 0x474D30 |
| BSS glyph UV table | VA 0x4EB100 (runtime, stride 8 per group) |
| R1188 UV metadata | R1188 file 0xA60-0xBFF (416 bytes, packed encoding) |
