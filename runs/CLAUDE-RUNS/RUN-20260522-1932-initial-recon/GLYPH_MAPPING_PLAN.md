# Glyph Mapping Decode Plan
## BUSIN 0: Wizardry Alternative Neo -- Static Analysis Only (No Emulator)

**Created:** 2026-05-22
**Objective:** Determine the mapping from glyph index (0x0000-0x035A, 858 slots) to actual Japanese character for all 836 used glyphs.

---

## Current State of Knowledge

- **858 glyph slots** in a 256x512 PSMT4 font atlas (21 cols x 42 rows, 12x12 cells)
- **836 unique glyphs** actually appear across 47 valid MSG resources (111,749 total tokens)
- **84 ASCII mappings** known from EXE at 0x3C0870 (space through 's', with gaps)
- **Japanese mapping** lives in BSS RAM at 0x5191F0 as 80-byte structs, loaded at runtime from PACKDATA
- **No SJIS sequences** found in EXE or PACKDATA resources -- the mapping is NOT a simple SJIS lookup table
- **Deswizzle incomplete** -- the raw 128px-width render shows recognizable Japanese characters but the full 256x512 PSMT4 deswizzle is still garbled
- **BUSIN 1 MSG files** use the SAME Japanese glyph indices (confirmed identical encoding)
- **BUSIN 1 EXE** has English game data (monster names at 0x4B0960 as raw ASCII, class names, etc.) but uses a different font descriptor format

---

## Approach Ranking (Recommended Attack Order)

| Priority | Approach | Likelihood | Effort | Depends On |
|----------|----------|------------|--------|------------|
| **1** | **C: Known-Text Cross-Reference** | **90%** | Medium | Glossary + MSG parsing |
| **2** | **B: Font Atlas Visual OCR** | **80%** | Medium | Clean deswizzle |
| **3** | **F: Brute Force Resource Search** | **70%** | Low-Medium | PACKDATA extractor |
| **4** | **A: Static EXE Disassembly** | **60%** | High | MIPS analysis skill |
| **5** | **E: BUSIN 1 Comparison** | **50%** | Medium | B1 resource extraction |
| **6** | **D: SJIS Code Point Assumption** | **15%** | Low | Nothing (quick test) |

**Parallelism:** Approaches C, B, and F can all run concurrently. D is a quick sanity check to run first (5 minutes). A and E are fallbacks if C+B+F don't produce a complete mapping.

---

## Approach D: SJIS/JIS Ordering Hypothesis (Quick Sanity Check)

### Likelihood: 15%
Already partially disproven -- no SJIS sequences found in EXE or PACKDATA. But worth a 5-minute test.

### Rationale
Some PS2 games map glyph indices directly to JIS X 0208 character order. If glyph 94 (first non-ASCII glyph) = first hiragana character, and the atlas follows JIS row order (hiragana rows 4-5, katakana rows 5-6, kanji starting row 16), then we can compute the mapping arithmetically.

### Script: `tools/glyph_jis_test.py`

```
1. Build a JIS X 0208 character list in standard row-major order:
   - Row 1: symbols (0x2121-0x217E)
   - Row 4: hiragana (0x2421-0x247E)
   - Row 5: katakana (0x2521-0x257E)
   - Rows 16+: kanji by frequency (0x3021+)

2. Try several base offsets:
   - Hypothesis A: glyph 0 = JIS 0x2121 (first symbol)
   - Hypothesis B: glyph 94 = JIS 0x2421 (first hiragana, after ASCII block)
   - Hypothesis C: glyph 0 = first hiragana

3. For each hypothesis, generate the first 20 predicted characters

4. Cross-reference against known data:
   - Glyph 0x0000 is most frequent (66.55%) -> must be space/null (already known: it's padding)
   - Glyph 0x0001 is second most frequent (1.78%) -> likely a common particle or space
   - Check if the frequency distribution matches expected Japanese character frequencies

5. Quick validation: if hypothesis works, katakana ファイター (FIGHTER) should appear
   as a specific glyph sequence in class-name MSG data
```

### Verdict
If glyph indices follow any standard Japanese encoding order, this test reveals it in minutes. Most likely outcome: they don't (the 84-entry ASCII table has gaps at indices 2-4, 11-12, 31-32, 87-88, suggesting custom ordering).

**Effort:** 30 minutes. **Dependencies:** None.

---

## Approach C: Known-Text Cross-Reference (PRIMARY)

### Likelihood: 90%
This is the highest-confidence approach because we have extensive known content from the English guide.

### Rationale
We know the exact Japanese text for hundreds of game terms: class names (ファイター, シーフ, メイジ...), race names (ヒューマン, エルフ...), spell names (クレタ, ヒール...), monster names, item names. Each katakana/hiragana character must map to a specific glyph index. If we can find these known strings in the MSG data, we can decode the mapping character by character.

### Phase C1: Build Japanese Term Database

**Script: `tools/build_japanese_terms.py`**

```
1. For each glossary entry, add the known Japanese equivalent:

   Classes (from standard Wizardry Japanese):
     FIGHTER    = ファイター (5 katakana)
     THIEF      = シーフ (3 katakana)
     MAGE       = メイジ (3 katakana)
     PRIEST     = プリースト (5 katakana)
     BISHOP     = ビショップ (4 katakana)
     ALCHEMIST  = アルケミスト (6 katakana)
     SAMURAI    = サムライ (4 katakana)
     NINJA      = ニンジャ (4 katakana)
     LORD       = ロード (3 katakana)
     CLERIC     = クレリック (5 katakana)

   Races:
     HUMAN      = ヒューマン (5 katakana)
     ELF        = エルフ (3 katakana)
     GNOME      = ノーム (3 katakana)
     DWARF      = ドワーフ (4 katakana)
     HOBBIT     = ホビット (4 katakana)

   Spell names (romanized Japanese in the game itself):
     KRETA      = クレタ
     HEAL       = ヒール
     etc. (56 spells -- these may appear as-is in katakana or as romanized ASCII)

   Monster names (from BUSIN 1 English data at EXE 0x4B0960):
     BUBBLY SLIME = バブリースライム
     GAS DRAGON   = ガスドラゴン
     etc.

2. Output: JSON mapping { "english": "...", "japanese": "...", "katakana_chars": [...] }
   Include the individual katakana/hiragana characters used across all terms.
```

### Phase C2: Find Term-Containing MSG Resources

**Script: `tools/find_known_terms.py`**

```
1. For each MSG resource (47 valid ones, plus 17 Format A at indices 34-49):
   - Parse all messages as BE uint16 glyph streams
   - Look for messages with length matching known term lengths:
     * Class names: 3-6 glyphs
     * Race names: 3-5 glyphs
     * Spell names: 2-6 glyphs

2. Focus on resources 34-49 (Format A, system/menu text):
   - These likely contain character creation screens (class/race selection)
   - Extract all short messages (1-8 glyphs) -- these are menu labels

3. Look for structural patterns:
   - A block of exactly 5 or 10 consecutive messages with lengths [5,3,3,5,4,6,4,4,3,5]
     would match [FIGHTER,THIEF,MAGE,PRIEST,BISHOP,ALCHEMIST,SAMURAI,NINJA,LORD,CLERIC]
   - A block of 5 messages with lengths [5,3,3,4,4] = race names

4. Look for repeated katakana patterns:
   - ファイター and ファイア (fire) share ファイ = 3 common glyphs
   - If the same 3-glyph prefix appears in both a class name context and a
     spell/element context, those 3 glyphs = ファイ
```

### Phase C3: Constraint-Solving Decoder

**Script: `tools/glyph_constraint_solver.py`**

```
1. Build constraint system:
   For each identified term match:
   - "Message [resource X, msg Y] = ファイター" means:
     glyph[0] = フ, glyph[1] = ァ, glyph[2] = イ, glyph[3] = タ, glyph[4] = ー

2. Cross-validate constraints:
   - If glyph 0x0088 = フ in one context, it must be フ everywhere
   - If two terms disagree on a glyph's identity, the match hypothesis is wrong

3. Propagate:
   - Known katakana assignments let us decode other messages
   - Once we know all katakana (~90 chars), decode katakana-heavy messages
   - Use decoded messages to identify hiragana and common kanji

4. Frequency validation:
   - In Japanese text, common hiragana (の, は, に, を, て, が, で, と) dominate
   - Glyph 0x0001 (1.78% frequency, excluding null) should be one of these
   - の is typically the most frequent character (~4-5% of non-space text)

5. Output: partial glyph_map.json { glyph_index: "character", ... }
```

### Phase C4: Iterative Expansion

```
1. Start with katakana (most constrained -- game terms are almost all katakana)
2. Use decoded katakana to read item/monster names and verify against glossary
3. Decode hiragana from dialogue particle patterns (は、が、の、を、に、etc.)
4. Decode kanji from context + frequency (most frequent kanji in games:
   の、は、に、を、て、が、で、と、た、い、る、し、な、ま、す、れ、か、ら、り、よ)
5. Final validation: decode a full dialogue MSG and check if it reads as coherent Japanese
```

**Effort:** 2-3 days for full pipeline. **Dependencies:** MSG parser (exists), glossary (exists).

---

## Approach B: Font Atlas Visual OCR

### Likelihood: 80% (conditional on clean deswizzle)
The raw 128px-wide render shows recognizable characters. If we can extract clean 12x12 cells, OCR or manual identification can map every glyph.

### Phase B1: Fix PSMT4 Deswizzle

**Script: `tools/psmt4_deswizzle_v3.py`**

```
Current status: The raw 128px-wide render (1272_raw_128w.png) shows clean characters.
The 256x512 deswizzle attempts have block-level artifacts.

The problem: at 128px width, each 128x128 page is rendered linearly (correct within-page).
The issue is page-to-page arrangement for the full 256x512 layout.

Approach:
1. Don't fight the deswizzle. Instead, render at 128px width and re-tile:
   - The atlas is 256x512 = 2 pages wide x 4 pages tall = 8 pages
   - At 128px width, pages stack vertically (128x1024 effectively)
   - Re-arrange: take each 128x128 page and place it in the correct 2x4 grid

2. Or: use the raw 128px render directly for OCR (it shows the characters fine)
   - Just need to know which 128px-wide position maps to which glyph index
   - The glyph index formula uses 21 columns at 256px width
   - At 128px width, the formula changes: need to account for page boundaries

3. Alternative: render the atlas as a series of 128-pixel-wide strips:
   - Page 0 (top-left of 256x512): raw bytes 0-8191, render at 128px wide = 128x128
   - Page 1 (top-right): raw bytes 8192-16383, render at 128px wide = 128x128
   - Place page 0 left, page 1 right -> 256x128 strip
   - Repeat for pages 2-7
   - Stack 4 strips vertically -> 256x512
```

### Phase B2: Extract Individual Glyph Cells

**Script: `tools/extract_glyph_cells.py`**

```
1. From the clean 256x512 atlas (or 128px-wide equivalent with corrected mapping):
   - Extract each 12x12 cell as a separate image
   - Name: glyph_NNNN.png (where NNNN = glyph index 0000-0857)

2. Generate a contact sheet:
   - 4x upscaled (48x48 per cell)
   - Grid with glyph index labels
   - Save as glyph_contact_sheet.png

3. Validate ASCII range:
   - Glyph 1 should visually match space (blank)
   - Glyph 5 should visually match '!' 
   - Glyph 22-30 should match '0'-'8' (with gap at '9'=33)
   - Glyph 41-66 should match 'A'-'Z'
```

### Phase B3: Character Identification

**Method A: Automated OCR (if Tesseract available)**
```
1. pip install pytesseract (or use built-in PIL + template matching)
2. For each glyph cell:
   - Upscale 4x with nearest-neighbor
   - Run Tesseract with Japanese language pack (jpn)
   - Record top candidate and confidence
3. Expected: good for katakana/hiragana (distinctive shapes), poor for kanji at 12px
```

**Method B: Template Matching Against Known Font**
```
1. Render all JIS X 0208 characters at 12x12 using a standard Japanese pixel font
   (e.g., MS Gothic, IPAGothic, or a free bitmap font)
2. For each atlas glyph cell:
   - Compare against all rendered templates using pixel correlation
   - Record best match and similarity score
3. This works even for kanji if the font matches the game's style
```

**Method C: Manual Identification (Fallback)**
```
1. Generate the contact sheet at high magnification
2. Manually identify hiragana (46 chars) and katakana (46 chars) first
   - These have very distinctive shapes even at 12x12
   - Cross-reference with known frequency data
3. Then tackle kanji -- the game uses ~700 kanji
   - Use radical identification + context from decoded messages
   - Prioritize high-frequency kanji first
```

**Effort:** 1-2 days (automated) or 3-5 days (manual). **Dependencies:** Clean deswizzle (Phase B1).

---

## Approach F: Brute Force Resource Search

### Likelihood: 70%
The mapping table MUST exist somewhere in PACKDATA.DIG -- it gets loaded into BSS at runtime. We can search for it systematically.

### What We're Looking For

The BSS table at 0x5191F0 contains 80-byte structs. But the raw PACKDATA resource probably has a more compact format that gets expanded during loading. Possible formats:

1. **Flat character code array:** 858 entries x 2 bytes = 1,716 bytes (uint16 character codes)
2. **Flat with width data:** 858 entries x 4 bytes = 3,432 bytes (code + width)
3. **Variable-length:** compressed or run-length encoded
4. **Embedded in font resource:** part of the font atlas resource (1272) header data

### Script: `tools/search_glyph_mapping.py`

```
Phase F1: Search for the mapping resource

1. Check resource 1272 (font atlas) more carefully:
   - The 192-byte header has fields we haven't fully decoded
   - Check if there's a secondary data section after the pixel data
   - Total resource: 65,792 bytes. Header: 192. Palette: 64. Pixels: 65,536.
     192 + 64 + 65536 = 65,792. No room for extra data in THIS resource.

2. Check adjacent resources (1271, 1273, 1274):
   - Font resources often come in groups (atlas + metrics + mapping)
   - The mapping resource would be type 01 (data) with size ~1700-3500 bytes

3. Scan ALL 2881 resources for character-code-like data:
   - For each resource, read payload as uint16 LE and uint16 BE
   - Score based on:
     a. Contains values in hiragana unicode range (0x3040-0x309F) -> unlikely, PS2 uses SJIS
     b. Contains values in SJIS hiragana range (0x82A0-0x82F1) -> possible
     c. Contains ascending/sequential values with small gaps -> possible ordering table
     d. Contains exactly 858 or 882 entries of consistent pattern -> size match

4. Check for JIS-to-glyph or glyph-to-JIS arrays:
   - A table of 858 ascending JIS code points would have values like:
     0x2121, 0x2122, ..., 0x2421, 0x2422, ... (with gaps for unused chars)
   - Search for any resource containing 10+ consecutive values in JIS range

5. Search for font metric arrays:
   - 858 entries of per-glyph width data (uint8 or uint16)
   - Would appear as a block of 858+ small values (4-16 range for pixel widths)

Phase F2: Check resource 49

Resource 49 is interesting: type 01, 3458 bytes payload.
3458 / 4 = 864.5 (close to 858 + header)
3458 / 2 = 1729 (close to 858*2=1716 + 13-byte header)
Investigate this resource specifically.

Phase F3: Cross-reference with EXE loading code

The EXE must reference a resource ID when loading the mapping.
Search for PACKDATA resource load calls that store results to 0x5191F0.
```

**Effort:** 1 day. **Dependencies:** PACKDATA extractor (exists).

---

## Approach A: Static EXE Disassembly

### Likelihood: 60%
We can find the exact resource that gets loaded into BSS 0x5191F0, but the loading code may transform the data (decompress, reformat), making it harder to use.

### Script: `tools/trace_bss_init.py`

```
Phase A1: Find the initialization function

1. The 20 references to 0x5191F0 cluster at VA 0x178680-0x17C280 (file 0x078700-0x07C280)
   This is a large function (or set of functions) that uses the BSS table.

2. But we need the function that POPULATES the table, not the one that READS it.
   Look for:
   - sw (store word) instructions targeting 0x5191F0 offsets
   - jal (function call) to memcpy-like functions with 0x5191F0 as destination
   - Loops that iterate over resource data and write to 0x5191F0

3. Search for the PACKDATA load API:
   - Find strings like "PACKDATA" or resource-loading function signatures
   - The API likely takes a resource index and returns a data pointer
   - Look for: load resource -> memcpy to 0x5191F0

Phase A2: Trace the resource ID

1. The loading function will have a hardcoded resource index (e.g., `li $a0, 1272`)
   or compute it from a table

2. Common patterns:
   - jal packdata_load; li $a0, RESOURCE_ID (in delay slot)
   - Result in $v0, then: jal memcpy; move $a0, BSS_ADDR; move $a1, $v0; li $a2, SIZE

3. Once we find the resource ID, extract that resource and decode it

Phase A3: Decode the resource format

1. The 80-byte BSS struct contains more than just the character code:
   - It has type bytes (checked against constants 2,5,6,7,8)
   - It has sub-bytes used for hash/encoding
   
2. The source resource may store this in a more compact format
   (e.g., 4 bytes per entry that gets expanded to 80 bytes)

3. Decode the format by analyzing the loading loop
```

### What Makes This Hard
- MIPS disassembly without Ghidra is tedious (need a Python MIPS decoder)
- PS2 function call conventions and register usage need careful tracking
- The BSS init might happen through multiple indirection levels
- We have ~15,000 lines of relevant code to analyze in the 0x078xxx-0x07Cxxx range

**Effort:** 3-5 days. **Dependencies:** MIPS disassembly tools.

---

## Approach E: BUSIN 1 Comparison

### Likelihood: 50%
BUSIN 1 MSG files use the same Japanese glyph indices but BUSIN 1 ALSO has English text in the EXE. If we can find the BUSIN 1 glyph mapping, it applies to BUSIN 0.

### Script: `tools/busin1_glyph_map.py`

```
Phase E1: Extract BUSIN 1 PACKDATA

1. BUSIN 1 has PACKDATA.CIG (not .DIG) at extracted_busin1/PACKDATA.CIG
2. Parse its TOC (may differ from BUSIN 0 format)
3. Find the font atlas resource and mapping data

Phase E2: BUSIN 1 EXE Analysis

1. BUSIN 1 EXE (SLUS_202.59) has:
   - Proportional width table at 0x491B30 (covers 0x000-0x11D+ glyph codes)
   - Character set table at 0x4B4170 (renderable glyph list)
   - English text strings at 0x3B8900+
   
2. The width table at 0x491B30 maps glyph codes to pixel widths.
   If it's indexed by glyph code, the ORDER tells us which glyphs exist.
   But it doesn't tell us which CHARACTER each glyph represents.

3. BUSIN 1 might have its OWN glyph-to-character mapping in a different format.
   Since the English version also renders Japanese text (MSG files are Japanese),
   it must have the Japanese font system intact.

Phase E3: Cross-Game Glyph Comparison

1. If both games use the same glyph indices for the same characters:
   - Find a known text string that appears in both games
   - BUSIN 1 has English equivalents visible in the EXE
   - Match the English text to specific MSG file messages
   - The MSG glyph indices in those messages give us the Japanese characters

2. Example: "BUBBLY SLIME" appears at BUSIN 1 EXE 0x4B0960.
   The corresponding monster entry in BUSIN 1's MSG files uses glyph indices
   that spell バブリースライム. If we can find which MSG resource contains
   monster names and locate BUBBLY SLIME's position, we decode 8 katakana at once.
```

### What Makes This Hard
- BUSIN 1 PACKDATA.CIG may have a different format than BUSIN 0's .DIG
- The game versions may use DIFFERENT glyph orderings (same engine, different builds)
- BUSIN 1's English text is in the EXE, not in MSG files, so correlating them is indirect

**Effort:** 2-3 days. **Dependencies:** BUSIN 1 PACKDATA parser.

---

## Recommended Execution Plan

### Day 1: Quick Wins + Parallel Setup

**Morning (2 hours):**
1. Run Approach D (JIS ordering test) -- 30 minutes, likely negative but eliminates a hypothesis
2. Run Approach F Phase F2 (check resource 49 specifically) -- 30 minutes
3. Start Approach F Phase F1 (brute-force resource scan) -- runs in background

**Afternoon (4 hours):**
4. Start Approach C Phase C1 (build Japanese term database)
5. Start Approach B Phase B1 (fix deswizzle OR work with raw 128px render)

### Day 2: Core Analysis

**Morning:**
6. Complete Approach B Phase B2 (extract glyph cells from 128px render)
   - Even without perfect deswizzle, the 128px render shows clean chars
   - Map the 128px-wide layout back to glyph indices using page math
7. Complete Approach C Phase C2 (find known terms in MSG data)

**Afternoon:**
8. Start Approach C Phase C3 (constraint solver) using any matches from C2
9. Start Approach B Phase B3 (template matching or manual ID of extracted cells)
10. Cross-validate B and C results against each other

### Day 3: Convergence

11. Merge results from all approaches into unified glyph_map.json
12. Run full MSG decode with the mapping
13. Spot-check decoded text against English guide translations
14. If coverage < 100%, use Approach A (EXE disassembly) to fill gaps

### Day 4 (if needed): Mop-Up

15. Approach A or E for any remaining unmapped glyphs
16. Manual identification of rare kanji from atlas images
17. Final validation pass

---

## Key Scripts to Write

| Script | Approach | Priority | Purpose |
|--------|----------|----------|---------|
| `tools/glyph_jis_test.py` | D | P0 (quick) | Test JIS ordering hypothesis |
| `tools/search_glyph_mapping.py` | F | P0 | Scan PACKDATA for mapping resource |
| `tools/build_japanese_terms.py` | C | P1 | Build known JP term database |
| `tools/psmt4_deswizzle_v3.py` | B | P1 | Fix atlas render or re-tile from 128px |
| `tools/find_known_terms.py` | C | P1 | Find known terms in MSG data |
| `tools/extract_glyph_cells.py` | B | P2 | Extract individual 12x12 cells |
| `tools/glyph_constraint_solver.py` | C | P2 | Solve mapping from cross-references |
| `tools/glyph_template_match.py` | B | P2 | Match atlas cells to font templates |
| `tools/trace_bss_init.py` | A | P3 | MIPS disassembly of BSS loading |
| `tools/busin1_glyph_map.py` | E | P3 | Extract BUSIN 1 mapping data |

---

## Critical Insight: The 128px Raw Render IS the Clean Atlas

The file `dumps/font_renders/1272_raw_128w.png` shows perfectly legible Japanese characters when the 65,536-byte pixel data is rendered linearly at 128 pixels wide. This means:

- Within each 128x128 page, the pixel data is stored linearly (no block swizzle within pages)
- The only "swizzle" is the page arrangement (how 8 pages tile to form 256x512)
- For OCR purposes, we can work directly with the 128px render

**Page mapping for the 128px render:**
- The 256x512 atlas = 2 columns x 4 rows of 128x128 pages
- At 128px width, this becomes 8 vertically stacked pages (128x1024)
- Page order in memory: page 0, page 1, page 2, ..., page 7
- Screen layout: pages [0,1] = row 0, [2,3] = row 1, [4,5] = row 2, [6,7] = row 3
- In the 128px render: even pages are left-column strips, odd pages are right-column strips

**Glyph index to 128px-render coordinate:**
```
screen_col = glyph_index % 21        # 0-20
screen_row = glyph_index / 21        # 0-41
screen_x = screen_col * 12           # 0-240 within 256px width
screen_y = screen_row * 12           # 0-492 within 512px height

page_col = screen_x / 128            # 0 or 1 (left or right page column)
page_row = screen_y / 128            # 0-3
page_idx = page_row * 2 + page_col   # 0-7

local_x = screen_x % 128             # 0-127 within page
local_y = screen_y % 128             # 0-127 within page

render128_x = local_x                # same (128px wide)
render128_y = page_idx * 128 + local_y  # stack pages vertically
```

This formula lets us extract every glyph cell from the 128px render and label it with its glyph index. This is the fastest path to visual identification.

---

## Expected Outcome

The combination of Approaches B+C should yield a complete or near-complete mapping:

- **B (Atlas OCR)** gives us the visual identity of every glyph (what character it looks like)
- **C (Cross-Reference)** gives us confirmed assignments (what character it IS, validated by context)
- Together: B provides candidates, C confirms them

For the ~700 kanji in the atlas, OCR will be less reliable than for kana, but:
- Frequency data narrows candidates (common kanji first)
- Context from decoded messages provides validation
- The English guide gives us the expected content of every text resource

Worst case: manual identification of ~200 ambiguous kanji from the atlas images, guided by frequency ranking and contextual clues. This is tedious but tractable (a few hours of expert work).

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Deswizzle remains broken | Blocks Approach B | Use 128px raw render directly (proven working) |
| No matching term patterns in MSG | Degrades Approach C | Use brute-force frequency analysis instead |
| Glyph ordering differs between BUSIN 0 and 1 | Blocks Approach E | Already low-priority; validate before using |
| Mapping resource is compressed/encrypted | Blocks Approach F | Fall back to Approaches A+B+C |
| MIPS disassembly too complex | Blocks Approach A | Already low-priority; only needed if B+C fail |
| Kanji OCR accuracy too low | Partial mapping | Manual identification from zoomed atlas + context |
