# R1188 Gender Symbol Analysis: 男/女 to ♂/♀

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## 1. Summary

The gender kanji 男 and 女 exist in R1188's atlas pixel data but are NOT individually addressable through R1188's cell data system. The cell data system renders multi-character sprites (like tab labels "男名"/"女名"), not individual kanji. The individual 男/女 characters visible in the atlas are used by the R1272-based MSG rendering system instead.

**Replacing gender display requires patching the R1272 font atlas (already done) and ensuring the correct glyph IDs flow through the R38 MSG pipeline.**

---

## 2. Glyph ID Mapping

| Glyph ID | Original | Replacement | R1188 Cell Data? | R1272 Atlas? |
|----------|----------|-------------|------------------|-------------|
| 518 (0x0206) | 男 | ♂ | YES (page 0x02, index 6, U=0 V=66) -- but this is the "男名" tab label sprite, NOT standalone 男 | YES (tile at row 24, col 14 = 168,288) |
| 349 (0x015D) | 女 | ♀ | NO (page 0x01 only has 3 entries; index 0x5D=93 is out of range) | YES (tile at row 16, col 13 = 156,192) |
| 418 | 女 (alt) | ♀ | Not checked | YES |

---

## 3. R1188 Cell Data: What Glyph 518 Actually Points To

Page 0x02, index 6 cell entry at EXE file offset 0x3D8DC0:
```
U=0, V=66, W=100, flag=0, vram_blk=0xA1E8, gs=0x004F
```

V=66 in TBW=4 space corresponds to the **"Male Name" (男名) tab label row** -- the same row used by page 0x19 entry 6 (glyph 0x1906, the name entry screen's "男名" tab). This is a multi-character pre-composed sprite (~48x20 pixels), NOT the standalone 男 kanji.

Page 0x19 (tab labels) index 6: U=0, V=66, W=100, vram=0xB430 (different CLUT, same UV).

---

## 4. Where 男 and 女 Exist in R1188's Deswizzled Atlas

The R1188 atlas (`build/textures_to_edit/R1188_CORRECT_dbw512.png`, 1024x1024 grayscale) contains these kanji in its proportional-width grid:

### 男 (male)
- **Row 8** (y=192-215): `紹上乗場常情信盛前相他台大段男知置柱調鉄店`
- **Position**: Within the merged blob x=280-349 (contains 大段男). 男 occupies approximately **x=328-349, y=192-215** (22x24 pixels).
- Character index in row: 14 (0-based)

### 女 (female)
- **Row 9** (y=216-239): `頼理立連脇長髪成告落容薬味物美転眺帯先女書`
- **Position**: Standalone blob at **x=449-471, y=216-239** (23x24 pixels).
- Character index in row: 19 (0-based)

These positions are in the DESWIZZLED atlas. They are individual character glyphs used by the R1272 MSG rendering when the game reads R38 glyph streams. The R1188 cell data system does NOT directly reference these positions.

---

## 5. Original R38 Gender Entries

Original R38 from ISO:
```
MSG 25 (offset 0x040E): glyphs = [17]     -> fullwidth "1"
MSG 26 (offset 0x0418): glyphs = [18]     -> fullwidth "2"
```

Orphaned data exists at:
```
0x0450: glyph 518 (男) + FFFE + FFFF
0x0456: glyph 349 (女) + FFFE + FFFF
```
These are NOT referenced by any offset table entry -- they are remnant/unused data between MSG 32 and MSG 33.

Current built R38:
```
MSG 25: glyphs = [44, 86, 17] -> "Lv1"
MSG 26: glyphs = [44, 86, 18] -> "Lv2"
```

The translation chunk specifies:
```json
{"resource": 38, "message": 25, "japanese": "男", "english": "♂ / "}
{"resource": 38, "message": 26, "japanese": "女", "english": "♀ / "}
```
But these translations appear to not have been applied (the built MSG 25/26 contain "Lv1"/"Lv2" instead).

---

## 6. R1272 Atlas: ♂ and ♀ Are Already Present

The English font atlas (`build/english_font_atlas_preview.png`) contains correctly rendered symbols:

### ♂ (Mars, glyph 518)
```
............
.......####.
.........##.
........#.#.
...###.#..#.
..#...#.....
.#.....#....
.#.....#....
.#.....#....
..#...#.....
...###......
............
```
Position: row 24, col 14 (pixel 168, 288), 26 foreground pixels.

### ♀ (Venus, glyph 349)
```
............
....####....
...#....#...
..#......#..
..#......#..
..#......#..
...#....#...
....####....
.....##.....
...######...
.....##.....
.....##.....
```
Position: row 16, col 13 (pixel 156, 192), 30 foreground pixels.

---

## 7. Why Gender May Still Show Japanese

### Most Likely Cause: R38 MSG 25/26 Not Correctly Patched

The built R38 contains "Lv1"/"Lv2" for MSG 25/26, NOT "♂ / "/"♀ / ". The translation chunk exists but appears not applied. This is likely a build pipeline issue.

### The R1188 Atlas Position Is Irrelevant for Gender Display

The standalone 男/女 kanji in the R1188 atlas grid (rows 8-9 of the kanji area) are used by the R1272 MSG rendering system's glyph lookup. When the game renders glyph 518, it looks up tile (168, 288) in the R1272 atlas, NOT in R1188. The R1188 atlas pixels at that position only matter for the keyboard grid display (page 0x0B).

### Rendering Paths

| Context | Rendering Path | Glyph Source |
|---------|---------------|-------------|
| Chargen sidebar gender VALUE (男/女) | R38 MSG system -> R1272 font atlas | Glyph IDs from R38 MSG, rendered via R1272 tiles |
| Name entry "男名"/"女名" tab labels | R1188 cell data (page 0x02/0x19) | Pre-composed sprite at (U=0, V=66)/(U=0, V=67) in TBW=4 PSMT4 space |
| Keyboard grid individual kanji | R1188 cell data (page 0x0B/0x0C) | Individual chars at various (U,V) positions |

---

## 8. Recommended Actions

### Priority 1: Fix R38 MSG 25/26 Build

The translation chunk correctly specifies:
- MSG 25: "♂ / " (glyph IDs: [518, 0, 87, 0])
- MSG 26: "♀ / " (glyph IDs: [349, 0, 87, 0])

But the build pipeline is NOT applying this. Investigate why `chunk_r38_fix.json` entries for messages 25 and 26 are not being encoded into the built R38.

### Priority 2: R1188 Tab Labels "男名"/"女名"

The name entry screen tab labels "男名" and "女名" are rendered as R1188 atomic sprites at:
- V=66: 男名 (Male Name) 
- V=67: 女名 (Female Name)

These should be edited to show "M.Name" and "F.Name" (or similar). This requires:
1. Computing the deswizzled atlas pixel positions for V=66 and V=67 in TBW=4 PSMT4 space
2. Replacing the Japanese text with English at those pixel positions
3. Re-swizzling the atlas

This is already handled by PCSX2 texture replacement (`patch_r1188_direct.py`) but NOT yet by atlas pixel editing.

### Priority 3: Do NOT Edit R1188 Atlas for Gender Symbols

Editing the individual 男/女 kanji in R1188's atlas grid (rows 8-9) would affect the keyboard grid display but would NOT fix the chargen sidebar gender display. The sidebar uses R1272 tiles, not R1188 pixels.

---

## 9. Key File Locations

| File | Purpose |
|------|---------|
| `data/translate_chunks/chunk_r38_fix.json` | Translation overrides for R38 MSG 25/26 (gender) |
| `data/english_glyph_table.json` | Maps ♂->518, ♀->349 |
| `data/msg_glyph_map.json` | Maps 518->男, 349->女 (original JP) |
| `build/english_font_atlas_preview.png` | R1272 atlas with ♂/♀ tiles at positions 518/349 |
| `build/packdata_resources/0038_type01.raw` | Built R38 (currently has wrong content for MSG 25/26) |
| `tools/patch_r1188_direct.py` | PCSX2 texture replacements for R1188 tab labels |
| `extracted/SLPM_653.78` offset 0x3D8DC0 | Page 0x02 cell data entry for glyph 518 (V=66 tab label) |

---

## 10. EXE Cell Data Reference for Gender-Adjacent Entries

### Page 0x02 (glyph 0x0200-0x0218, 25 entries)

| Index | Glyph ID | U | V | Purpose |
|-------|----------|---|---|---------|
| 0 | 0x0200 (512) | 0 | 60 | Same as tab "Kana" |
| 1 | 0x0201 (513) | 0 | 61 | Same as tab "Hira" |
| 2 | 0x0202 (514) | 0 | 62 | Same as tab "ABC" |
| 3 | 0x0203 (515) | 0 | 63 | Same as tab "Sym" |
| 4 | 0x0204 (516) | 0 | 64 | (5th tab) |
| 5 | 0x0205 (517) | 0 | 65 | Same as tab "OK/Confirm" |
| **6** | **0x0206 (518)** | **0** | **66** | **Same as tab "Male Name" (男名)** |
| **7** | **0x0207 (519)** | **0** | **67** | **Same as tab "Female Name" (女名)** |
| 8 | 0x0208 (520) | 0 | 68 | Same as tab "Delete" |
| 9 | 0x0209 (521) | 0 | 69 | Same as tab "Clear" |

Page 0x02 entries mirror the tab label positions from page 0x19 but with different VRAM block addresses (different CLUT palette). Glyph 518 renders the same sprite as the "男名" tab, not the standalone 男 kanji.
