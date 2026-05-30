# EXE Name Entry Keyboard: Detailed Decode

**Date**: 2026-05-28
**EXE**: `extracted/SLPM_653.78`

---

## 1. Table 2A: Kana Keyboard Grid (0x3C9BF0 - 0x3C9DA0)

38 entries x 12 bytes. Each entry = 6 x uint16 glyph IDs, one per input page/mode.

### Column Ranges

| Column | Range (hex) | Range (dec) | Content |
|--------|-------------|-------------|---------|
| 0 | 0x001A-0x0100 | 26-256 | Hiragana (あ-ん + voiced) + punctuation (entries 30-34) |
| 1 | 0x00A9-0x0139 | 169-313 | Hiragana voiced/semi-voiced (ぢ-ぼ...) |
| 2 | 0x001B-0x0172 | 27-370 | Katakana + punctuation |
| 3 | 0x011B-0x01AB | 283-427 | Katakana voiced/semi-voiced |
| 4 | 0x0019-0x016B | 25-363 | Mixed symbols + kana |
| 5 | 0x00BF-0x01A4 | 191-420 | Mixed kana |

### Full Entry Decode

```
Entry  0: 0070(あ) 00A9(ぢ) 00E2(ア) 011B     0154     018D
Entry  1: 0071(い) 00AA(づ) 00E3(イ) 011C     0155     018E
Entry  2: 0072(う) 00AB(で) 00E4(ウ) 011D     0156     018F
Entry  3: 0073(え) 00AC(ど) 00E5(エ) 011E     0157     0190
Entry  4: 0074(お) 00AD(ば) 00E6(オ) 011F     0158     0191
Entry  5: 0075(か) 00AE(び) 00E7(カ) 0120     0159     0192
Entry  6: 0076(き) 00AF(ぶ) 00E8(キ) 0121     015A     0193
Entry  7: 0000     0000     0000     0000     0000     0000   <-- row separator
Entry  8: 0077(く) 00B0(べ) 00E9(ク) 0122     015B     0194
...
Entry 15: 0000     0000     0000     0000     0000     0000   <-- row separator
Entry 16: 0082(て) 00BB     00F4     012D     0166     019F
...
Entry 22: 0000     0000     0000     0000     0088(の) 00C1   <-- partial row separator
...
Entry 29: 0100(ブ) 0139     0172     01AB     0000     0000
Entry 30: 0000     0000     0000     0000     0019(９) 0000   <-- row separator
Entry 31: 001A(：) 0000     001B     0000     001C     0000   <-- punctuation
Entry 32: 001D     0000     001E     0000     001F(？) 0000
Entry 33: 0020     0000     0021(a)  0000     0022(b)  0000
Entry 34: 0023(c)  0000     0024(d)  0000     0072(う) 0000
Entry 35: 0000     0000     0000     0000     0000     0000   <-- separator
Entry 36: 1900     0000     1901     0000     1902     0000   <-- bitmap tab labels
Entry 37: 1903     0000     1904     0000     FFFF     FFFF   <-- end marker
```

**Key finding**: Entries 30-34 contain punctuation/symbol glyph IDs (25-36) interspersed with zero padding. Entries 36-37 reference bitmap tab labels (glyph IDs 6400-6404).

All glyphs here are **main font (R1272) IDs**, used only for the kana input pages. This table is NOT used for alphanumeric mode.

---

## 2. Alphanumeric Grid (0x3CA690)

Separate from Table 2A. Contains R1189-local indices (NOT main font glyph IDs):

```
Row 0:  0  1  2  3  4   5  6  7  8  9    -> A B C D E a b c d e
Row 1: 10 11 12 13 14  15 16 17 18 19    -> F G H I J f g h i j
Row 2: 20 21 22 23 24  25 26 27 28 29    -> K L M N O k l m n o
Row 3: 30 31 32 33 34  35 36 37 38 39    -> P Q R S T p q r s t
Row 4: 40 41 42 43 44  45 46 47 48 49    -> U V W X Y u v w x y
Row 5: 50 51 52 53 54  55 60 60 60 60    -> Z [ ? . - (space) (pad...)
Row 6: 60 60  6  7  8   9 10 11 12 13    -> (pad) 0 1 2 3 4 5 6 7
Row 7: 14 15 16 17 18  19 20 21 22 23    -> 8 9 ...
Row 8: 24 25 26 27 28  29 30 31 32 33    -> (wraps)
Row 9: 34 35 60 60 60  60 60 60 60 60    -> (pad)
Row10: 60 45 46 47 48  49 50 51 52 53    -> (more wraps)
```

The index 60 is used as filler/blank. Indices 0-55 map to characters baked into R1189's 512x256 PSMT4 texture.

**Already contains A-Z, a-z, 0-9. No changes needed.**

---

## 3. Mode Index Table (0x3CA770)

12 uint16 values mapping tab positions to internal mode IDs:

```
Position:  0     1     2     3     4     5     6     7     8     9    10    11
Mode ID:   0     2     1   FFFF    4   FFFF    5     6     7     8     9    10
Label:   (tab0)(tab1)(tab2) ---  (tab3) --- (OK) (Male)(Fem)(Del)(Clear)(?)
```

- Position 0 = Katakana (mode 0)
- Position 1 = Hiragana (mode 2, despite being tab index 1)
- Position 2 = Alphanumeric (mode 1)
- Position 3 = FFFF (unused/separator)
- Position 4 = Symbols (mode 4)
- Position 5 = FFFF (unused/separator)
- Positions 6-11 = Action buttons (OK, Male Name, Female Name, Delete, Clear, extra)

---

## 4. Keyboard Grid Display Area (0x3C5F00 - 0x3C6700)

This 2048-byte area contains **rendering command sequences** for the keyboard display, organized in 3 blocks:

### Block 1: Hiragana display (0x3C5F00 - 0x3C618A)
- 65 entries, 10 bytes each
- Pattern: `{cmd=0x0B, glyphID, 0x02, 0x08, glyphID}`
- Glyph IDs 0x6A-0xAA (106-170): symbols + hiragana (あ through づ)
- The 0x0B/0x08 values are likely rendering mode flags (normal vs. selected highlight)

### Block 2: Navigation/cursor map (0x3C619E - 0x3C6694)
- 128 entries, 10 bytes each
- Pattern: `{position, cmd=0x0C, next_position, 0x02, 0x04}`
- Sequential positions 0-127, each pointing to the next
- Likely defines cursor navigation (right/down movement) within the kana grid

### Block 3: Additional grid (0x3C669E - 0x3C66F8)
- ~9 entries
- Pattern: `{position, cmd=0x0D, next_position, 0x02, 0x00}`
- Terminated by `{0x0008, 0x000D, 0x0009, 0x0002, 0x0000}`
- Possibly symbol page navigation

**None of these blocks affect alphanumeric mode.** The alphanumeric grid is rendered from R1189's bitmap texture using the index table at 0x3CA690.

---

## 5. Tab Label Bitmap Glyphs (Table 2E, 0x3C9DA0)

Glyph IDs 6400-6412 (0x1900-0x190C) reference bitmap regions baked into R1188's 1024x1024 PSMT4 texture:

| Glyph ID | Label (Japanese) | English replacement needed |
|----------|-----------------|---------------------------|
| 6400 | カナ (Katakana) | "Kana" or "Kata" |
| 6401 | かな (Hiragana) | "Hira" |
| 6402 | 英数 (Alphanumeric) | "ABC" |
| 6403 | 記号 (Symbols) | "Sym" |
| 6404 | (5th tab, unused?) | -- |
| 6405 | 決定 (Confirm) | "OK" |
| 6406 | 男名 (Male Name) | "M.Name" |
| 6407 | 女名 (Female Name) | "F.Name" |
| 6408 | 1文字消す (Delete char) | "Delete" |
| 6409 | 全消去 (Clear all) | "Clear" |
| 6410-6412 | Extra labels | TBD |

These are resolved at runtime by the function at VA 0x494050, which looks up R1188's BSS glyph table at VA 0x4EBBEC. The glyph IDs themselves don't need changing -- only the pixel data in R1188's texture.

---

## 6. Init Function (VA 0x2ED060 / file 0x1ED0E0)

The init function sets up the name entry screen. The default input mode is determined here. To make the keyboard default to alphanumeric (ABC) instead of katakana:

- Find where mode index 0 is stored as the initial selection
- Patch it to mode index 2 (alphanumeric position in the mode table)

The function references the table base address via `lui/addiu` pairs loading 0x00560000 + offset (VA range), followed by loads from the mode table.

---

## 7. Verdict: What Needs Changing for English

### Already works (NO changes needed):
1. **R1189 character grid** -- A-Z, a-z, 0-9 already present as bitmap glyphs
2. **Alphanumeric grid table (0x3CA690)** -- indices correctly map to R1189 characters
3. **Table 2A kana grid** -- can be left as-is (kana tabs still functional)
4. **Keyboard display area (0x3C5F00-0x3C6700)** -- rendering commands for kana pages, irrelevant to alphanumeric mode
5. **Mode index table (0x3CA770)** -- mode mapping is correct
6. **Glyph IDs in Table 2E** -- reference correct bitmap regions, don't need ID changes

### Must change (R1188 texture edit only):
1. **Tab labels in R1188** -- edit the 1024x1024 PSMT4 texture to replace Japanese labels with English (see table in section 5)
2. **Title/instruction text in R1188** -- "新規登録" -> "NEW CHARACTER", instruction text -> English

### Optional EXE patches:
1. **Default tab to ABC** -- patch init at VA 0x2ED060 to start on alphanumeric tab instead of katakana (change mode index from 0 to 2)
2. **Hide kana tabs** -- reduce visible tab count to only show ABC/Sym/OK/buttons (optional cosmetic improvement)

### Bottom line:
The name entry keyboard requires **zero mandatory EXE patches**. All Japanese text visible on the name entry screen is baked into R1188's bitmap texture. Editing R1188 is sufficient for a complete English name entry experience. The optional "default to ABC tab" EXE patch is a quality-of-life improvement but not strictly necessary.
