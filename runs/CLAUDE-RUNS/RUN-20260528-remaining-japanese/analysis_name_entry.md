# Name Entry Screen Analysis for English Translation

**Date**: 2026-05-28
**Resources**: R1188 (type-01, 527KB), R1189 (type-02, 65KB)
**EXE**: `extracted/SLPM_653.78`

---

## 1. R1188 Header Structure (0x000-0xBFF)

R1188 is a self-contained PS2 GS upload packet, not a sprite atlas with a separate UV table.

| Offset Range | Size | Content |
|-------------|------|---------|
| 0x000-0x00F | 16B | File header: `{0, 527360, 16, 0}` (pad, total_size, sub_count, pad) |
| 0x010-0x55F | 0x550 | 17 identical GS A+D blocks (0x50 bytes each): GIFtag + TEX0/TEX1/MIPTBP1/CLAMP registers. TEX0 configures 1024x1024 PSMT4. |
| 0x560-0x6B3 | 0x154 | 18 sprite metadata entries (20 bytes each). Fields: `{marker(4B), 0xFFFFFFFF(4B), entry_id(u16), flags=0x0101(u16), pad(4B), w(u16)=1024, h(u16)=1024}`. Entry IDs 1-16 plus duplicate ID 9. |
| 0x6B4-0x7C3 | 0x110 | Index/offset table (18 x 16-byte records). Record 0 is header: total_hdr_size=332, atlas_dims=512x256, data_offset=2048. Records 1-16: each points to one of the 17 GS blocks at stride-48 offsets (316,364,...,1036). The 8x2 values are GS register field sizes, not pixel dimensions. |
| 0x7C4-0x83F | 0x7C | Zero padding |
| 0x840-0xBFF | 0x3C0 | PSMT4 CLUT palette data and GS rendering state blocks (16-color CLUT tables for different UI element color schemes) |
| 0xC00-end | 524,288B | 1024x1024 PSMT4 pixel data (the actual texture atlas) |

**Key finding**: There are no explicit UV coordinate tables in R1188's header. The tab label positions within the 1024x1024 texture are determined by the game's runtime code, not by embedded sprite rect definitions. The 17 GS blocks configure the same texture but may represent different rendering states (normal/highlighted/selected for each tab).

---

## 2. Table 2E: Bitmap Tab Label Glyph IDs (EXE offset 0x3C9DA0)

Table 2E contains glyph IDs in range 0x1900-0x190C (6400-6412), stored as LE uint32, organized in 3 groups separated by 0xFFFFFFFF padding:

| File Offset | Glyph ID | Hex | Group:Index | Tab/Button Label |
|-------------|----------|-----|-------------|-----------------|
| 0x3C9DA0 | 6400 | 0x1900 | 25:0 | **カナ** (Katakana) |
| 0x3C9DA4 | 6401 | 0x1901 | 25:1 | **かな** (Hiragana) |
| 0x3C9DA8 | 6402 | 0x1902 | 25:2 | **英数** (Alphanumeric) |
| 0x3C9DAC | 6403 | 0x1903 | 25:3 | **記号** (Symbols) |
| 0x3C9DB0 | 6404 | 0x1904 | 25:4 | (5th tab slot, unused?) |
| --- | FFFF x26 | padding | --- | 26 dwords of 0xFFFFFFFF |
| 0x3C9DEC | 6405 | 0x1905 | 25:5 | **決定** (Confirm/OK) |
| 0x3C9DF0 | 6406 | 0x1906 | 25:6 | **男名** (Male Name) |
| 0x3C9DF4 | 6407 | 0x1907 | 25:7 | **女名** (Female Name) |
| 0x3C9DF8 | 6408 | 0x1908 | 25:8 | 1文字消す (Delete char) |
| 0x3C9DFC | 6409 | 0x1909 | 25:9 | 全消去 (Clear all) |
| --- | FFFF x7 | padding | --- | |
| 0x3C9E20 | 6410 | 0x190A | 25:10 | Extra label 1 |
| 0x3C9E24 | 6411 | 0x190B | 25:11 | Extra label 2 |
| 0x3C9E28 | 6412 | 0x190C | 25:12 | Extra label 3 |

**Group encoding**: `group = id >> 8 = 0x19 = 25`, `index = id & 0xFF = 0..12`

The function at VA 0x494050 resolves 6400+ glyph IDs via a BSS lookup table at VA 0x4EBBEC. At runtime, the game loads R1188/R1189 resources and populates this BSS table with texture page/offset info for each bitmap glyph. The 7 MIPS code blocks at VA 0x2FB094-0x2FB4C4 use this lookup:
```mips
lui   r3, 0x004D          ; upper bits
addiu r3, r3, -0x4414     ; = 0x4CBBEC -> BSS glyph table  
sll   r4, r4, 4           ; index * 16 stride
addu  r3, r3, r4          ; &table[index]
lw    r4, 0(r3)           ; load texture page/offset
```

---

## 3. Table 2A: Name Entry Keyboard Grid (EXE offset 0x3C9BF0)

38 entries x 12 bytes. Each entry: `{u16 primary, u16 alt1, u16 alt2, u16 alt3, u16 alt4, u16 alt5}`.

The 6 columns correspond to 6 keyboard modes/pages. From the glyph map:

| Column | Content | Glyph ID Range | Source |
|--------|---------|---------------|--------|
| 0 (primary) | Hiragana (あ-ん + voiced) | 112-256 | Main font R1272 |
| 1 (alt1) | More hiragana (small/voiced) | 169-313 | Main font R1272 |
| 2 (alt2) | Katakana (メ-ン + voiced) | 226-370 | Main font R1272 |
| 3 (alt3) | Kanji group 1 | 283-427 | Main font R1272 |
| 4 (alt4) | Kanji group 2 | 340-425 | Main font R1272 |
| 5 (alt5) | Kanji group 3 | 397-427+ | Main font R1272 |

Entries [7], [15], [22], [30], [35] are null spacers (grid row separators).
Entries [31-34] contain low-ID control/punctuation characters (IDs 25-36).
Entries [36-37] contain bitmap glyph IDs 6400-6404 (tab label references).

**The kana/kanji grid uses main font (R1272) glyph IDs.**

---

## 4. Alphanumeric Grid (EXE offset 0x3CA690)

The "英数" (alphanumeric) mode uses a **separate grid table** at 0x3CA690, NOT table 2A. This table stores sequential indices 0-55 (+ filler value 60):

```
Row 0:  0  1  2  3  4  5  6  7  8  9     -> A B C D E a b c d e
Row 1: 10 11 12 13 14 15 16 17 18 19     -> F G H I J f g h i j
Row 2: 20 21 22 23 24 25 26 27 28 29     -> K L M N O k l m n o
Row 3: 30 31 32 33 34 35 36 37 38 39     -> P Q R S T p q r s t
Row 4: 40 41 42 43 44 45 46 47 48 49     -> U V W X Y u v w x y
Row 5: 50 51 52 53 54 55 60 60 60 60     -> Z (blank) (blank) ... 
Row 6: 60 60  6  7  8  9 10 11 12 13     -> (blanks) then 1234567890...
Row 7: 14 15 16 17 18 19 20 21 22 23     -> ... (wraps to digits/symbols)
```

**These indices (0-55) are NOT main font glyph IDs.** They are indices into R1189's own bitmap character grid (512x256 PSMT4). R1189 is a self-contained character set with its own layout: indices 0-25 = A-Z uppercase, 5-30? = a-z lowercase (interleaved with uppercase in the grid display).

**This means the alphanumeric mode already has A-Z, a-z, 0-9 available.** The letters visible in the "英数" screenshot are rendered from R1189, not the main font.

---

## 5. Does the Character Grid Use R1272 (Main Font)?

**No, for alphanumeric mode.** The character grid in "英数" mode renders from **R1189** (512x256 PSMT4 texture), using its own sequential index system (0-55). This is confirmed by:
- The grid table at 0x3CA690 stores raw indices 0-55, not MSG glyph IDs
- The screenshots show the alphanumeric characters are rendered in a different style than the main game font
- R1189 has its own CLUT palette (16 colors with pinkish/bluish tones)

**Yes, for kana modes.** The hiragana/katakana grids in table 2A use main font glyph IDs (112-256), which are R1272 glyphs.

**The latin characters (A-Z, a-z, 0-9) in R1189 already work for English name entry.** The character grid does not need modification.

---

## 6. Minimum Changes for English Name Entry

### What Already Works
- **A-Z, a-z, 0-9 character grid**: Already present in R1189 and the "英数" mode table
- **Character selection and input flow**: The d-pad navigation and button confirm logic works regardless of language
- **Name length**: Character names already accept Latin characters

### What Needs Changing

#### Priority 1: Tab Labels (R1188 texture edit)
The 4 right-side tab labels and 3 bottom buttons show Japanese text baked into R1188's 1024x1024 texture:

| Current Japanese | English Replacement | Glyph ID |
|-----------------|-------------------|----------|
| カナ (Katakana) | Kana | 6400 |
| かな (Hiragana) | Hira | 6401 |
| 英数 (Alphanumeric) | ABC | 6402 |
| 記号 (Symbols) | Sym | 6403 |
| 決定 (Confirm) | OK | 6405 |
| 男名 (Male Name) | M. Name | 6406 |
| 女名 (Female Name) | F. Name | 6407 |

**Method**: Edit R1188's PSMT4 pixel data directly. This requires:
1. Full PSMT4 deswizzle of R1188's 1024x1024 texture
2. Locate tab label pixel regions (currently unknown -- need PCSX2 texture dump of the name entry screen)
3. Render English labels matching the game's visual style
4. Re-swizzle and inject back into PACKDATA.DIG

#### Priority 2: Title Bar and Instructions (R1188 texture edit)
The title "新規登録" (New Registration) and the instruction text "名前を入力してください。(男名・女名＝名前を自動で入力)" are also baked into R1188. These should become:
- Title: "NEW CHARACTER" or "REGISTER"
- Instructions: "Enter a name. (M.Name / F.Name = auto name)"

**Same method as Priority 1** -- edit R1188 texture.

#### Priority 3: Default Tab Selection (EXE patch, optional)
Currently the name entry defaults to katakana (カナ) mode. For English, it should default to alphanumeric (英数) mode.

**Patch**: Find the initialization code that sets the default tab index and change it from 0 (katakana) to 2 (alphanumeric). The mode index table at 0x3CA770 maps tab positions to mode IDs: `{0, 2, 1, FFFF, 4, FFFF, 5, 6, 7, 8, 9, 10}`.

The init function at VA 0x2ED060 (file 0x1ED0E0) likely sets the default mode.

#### Priority 4: Hide Unnecessary Tabs (EXE patch, optional)
Katakana, hiragana, and symbol tabs are unnecessary for English. Options:
- **Simple**: Leave them visible (players can still use alphanumeric)
- **Cleaner**: Patch the tab count or mode table to only show "ABC" + "OK" + "M.Name" + "F.Name"
- **Easiest**: Just change all tab labels to English and let players ignore the kana tabs

### What Does NOT Need Changing
- **R1189 character grid texture**: Already contains A-Z, a-z, 0-9
- **Alphanumeric grid table (0x3CA690)**: Already has correct indices
- **Table 2A kana grid**: Can be left as-is (kana tabs still functional for Japanese name aesthetic)
- **Table 2D kana mapping**: Only needed if restructuring the input flow
- **Glyph IDs in Table 2E**: The bitmap glyph IDs (6400-6412) correctly reference the tab label regions in R1188. Changing the texture content is sufficient; the IDs don't need patching.

---

## 7. Implementation Plan

### Step 1: Capture Name Entry Texture (Prerequisite)
Run PCSX2 with texture dumping enabled, navigate to the name entry screen, and capture R1188's deswizzled 1024x1024 texture. This reveals exact pixel positions of each tab label.

### Step 2: Edit R1188 Texture
Using the captured texture as reference:
1. Open the deswizzled 1024x1024 image
2. Locate and overwrite each tab label region with English text
3. Match font color/style to surrounding UI elements
4. Re-swizzle to PSMT4 format
5. Inject at offset 0xC00 in R1188's raw data
6. Rebuild PACKDATA.DIG with modified R1188

### Step 3: EXE Default Mode Patch (Optional)
Patch the name entry init function to default to alphanumeric (英数) mode instead of katakana.

### Step 4: Test
Verify in PCSX2:
- Tab labels display correctly in English
- Alphanumeric input works (A-Z, a-z, 0-9)
- Name is saved and displayed correctly in-game
- "M.Name" and "F.Name" auto-name buttons still function

---

## 8. File Reference

| Item | Path/Offset |
|------|-------------|
| R1188 raw | `extracted/packdata_raw/1188_type01.raw` |
| R1189 raw | `extracted/packdata_raw/1189_type02.raw` |
| R1188 pixel data start | File offset 0xC00 |
| Tab glyph IDs (Table 2E) | EXE offset 0x3C9DA0-0x3C9E28 |
| Keyboard grid (Table 2A) | EXE offset 0x3C9BF0-0x3C9DA0 |
| Alphanumeric grid | EXE offset 0x3CA690-0x3CA770 |
| Mode index table | EXE offset 0x3CA770-0x3CA788 |
| Init function | VA 0x2ED060 (file 0x1ED0E0) |
| Glyph resolver | VA 0x494050 (file 0x3940D0) |
| BSS glyph table | VA 0x4EBBEC (runtime only) |
| Name entry screenshots | `NameEntryHiraganamode.png`, `NameEntryEuropean.png` |
| R1188 texture dumps | `dumps/name_entry_font/r1188_*.png` |
| R1189 texture dumps | `dumps/name_entry_font/r1189_*.png` |
