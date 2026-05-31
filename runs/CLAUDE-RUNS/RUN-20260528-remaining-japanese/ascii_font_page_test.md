# ASCII Font Page Test: Do Glyph IDs 33-90 Render from R1272 or R1304+?

**Date:** 2026-05-28
**Verdict:** R1272. English translations in R38 SHOULD display correctly.

---

## 1. Font Page Table at EXE 0x3CA968 (VA 0x4CA8E8)

The table contains 64 entries (32 unique, each doubled), structured as uint16 pairs
(0x0000 padding + resource ID). It maps font page indices to PACKDATA resource IDs:

| Entry | Resource | Entry | Resource |
|-------|----------|-------|----------|
| 0-1   | R1304    | 16-17 | R1278    |
| 2-3   | R1305    | 18-19 | R1279    |
| 4-5   | R1306    | 20-21 | R1280    |
| 6-7   | R1307    | 22-23 | R1281    |
| 8-9   | R1308    | 24-25 | R1282    |
| 10-11 | R1309    | 26-27 | R1284    |
| 12-13 | R1310    | 28-29 | R1285    |
| 14-15 | R1311    | ...   | ...R1303 |

**R1272 (0x04F8) does NOT appear in this table.**

## 2. R1272 vs R1304+ Format Differences

| Property | R1272 | R1304+ |
|----------|-------|--------|
| TEX0 TW  | 8 (256px) | 9 (512px) |
| TEX0 TH  | 9 (512px) | 9 (512px) |
| PSM      | PSMT4 (0x14, 4bpp) | PSMT8 (0x13, 8bpp) |
| File size | 65,792 bytes | 263,360 bytes |
| Glyph grid | 21 cols x 42 rows = 882 slots | Different (512px wide) |

R1272 is the **primary/base** font atlas (halfwidth, 4bpp).
R1304+ are **kanji overflow pages** (fullwidth, 8bpp, different format entirely).

## 3. R1272 Is Loaded Separately, Not via the Page Table

At VA 0x30B370 (EXE file 0x20B3F0), the code loads R1272 directly:

```
  0x30B370: lui   $r4, 0x04F8      ; R1272 resource key upper bits
  0x30B374: jal   0x004924A0       ; resource load function
```

This appears 5 times in the renderer region (VA 0x30B370, 0x30B3A4, 0x30B3AC,
0x30B53C, 0x30B64C), confirming R1272 is a dedicated resource loaded by the
text renderer independently of the kanji page table.

## 4. Original R1272 Content Confirms Usage

The original (unmodified) R1272 atlas has character bitmaps at positions that
match the original `glyph_map_partial.json`:

- Glyph 41 = 'A' (original mapping)
- Glyph 51 = 'K'
- Glyph 73 = 'a'
- Glyph 86 = hiragana 'a'

All positions 0-90+ contain visible character bitmaps in the original R1272.
The game renders these characters on screen from R1272, confirming it is the
active font atlas for low glyph IDs.

## 5. Glyph ID Range Analysis

- **R1272** handles glyph IDs **0 through 881** (21 cols x 42 rows)
- **Font page table** (R1304+) handles glyph IDs **882+** (kanji overflow)
- All English glyph IDs used by our translation are **0 to 90** (well within R1272)

English glyph table assignments:
- Space = 0, ! = 1, digits 0-9 = 16-25
- A-Z = 33-58, a-z = 65-90
- Punctuation scattered in 1-15 and 91-94

## 6. Self-Consistency of the Translation Pipeline

The pipeline is self-consistent:

1. `generate_font_atlas.py` renders English bitmaps at positions matching `english_glyph_table.json`
2. `encode_english_text.py` encodes text using the same glyph table (e.g., 'S' = 51)
3. The game renderer looks up glyph 51 in R1272 and finds the 'S' bitmap
4. R1304+ kanji pages are never consulted for glyph IDs below 882

**Note:** The english_glyph_table uses different position assignments than the
original Japanese glyph_map_partial (shifted by ~8 positions). This is intentional
-- the R1272 atlas is completely rebuilt with new content at new positions, and the
MSG data is re-encoded to match.

## 7. Conclusion

**ASCII glyphs (IDs 0-94) always render from R1272.**
R1304-R1311 kanji font pages are irrelevant for English text rendering.
R38 English translations (e.g., MSG 2 = "STR" using glyphs 51, 52, 50)
will display correctly from the modified R1272 atlas.

No action needed to put English bitmaps in R1304+.
