# WAVE 9 FIX PLAN - Consolidated from 10 Recon Reports

**Date**: 2026-05-28
**Build**: v17 (identical to current v9 ISO on disk)
**Reports analyzed**: 10 Wave 9 recon agent outputs

---

## Priority Summary

| Fix | Difficulty | Risk | Impact | Description |
|-----|-----------|------|--------|-------------|
| FIX-1 | EASY | LOW | 2,394 msgs | Remove double word-wrapping in Step 4 |
| FIX-2 | EASY | LOW | 4 labels | Fix R38 gender/alignment index errors in JSON |
| FIX-3 | EASY | LOW | 3 prompts | Shorten R37 chargen prompts to fit 3-line box |
| FIX-4 | HARD | MED | 10 labels | R1188 tab/stat bitmap sprite replacement |
| FIX-5 | HARD | MED | 5 labels | EXE sidebar labels + title banner composite glyphs |

---

## FIX-1: Remove double word-wrapping (Step 4)

**Priority**: CRITICAL - fixes 2,394 broken type-2 dialogue messages (17.9% of corpus)

**Root cause**: `build_v9.py` line 202 calls `word_wrap(en_text)` on translations that ALREADY contain intentional ` / ` line breaks placed at ~18 char boundaries. The `word_wrap()` function then splits on ` / `, finds segments > 18 chars, and inserts ADDITIONAL ` / ` breaks. This doubles the line count, creating unwanted page breaks (FFD2) in mid-sentence.

**Example**:
```
Input:  "The medal earned from / defeating the floor / master was offered."
After word_wrap: "The medal earned / from / defeating the / floor / master was / offered."
Result: 6 lines instead of 3, with a page break splitting the thought
```

**File**: `C:/Programmieren/wizardrytranslation/build/build_v9.py`
**Line**: 202

**Fix** (Option B from report - recommended):
```python
# BEFORE (line 202):
        en_text = word_wrap(en_text)

# AFTER - REMOVE the line entirely, or comment out:
        # en_text = word_wrap(en_text)  # REMOVED: translations already have line breaks
```

Additionally, fix the trailing empty segment FFD2 interaction (lines 203-217). After removing word_wrap, also strip trailing empty segments before FFD2 counting:

```python
    for mi, en_text in msg_trans.items():
        # word_wrap REMOVED - translations already have ' / ' breaks
        glyphs = []
        parts = en_text.split(' / ')
        # Strip trailing empty segments (from trailing ' / ')
        while parts and parts[-1].strip() == '':
            parts.pop()
        line_count = 0
        for pi, part in enumerate(parts):
            if pi > 0:
                line_count += 1
                if line_count >= 3:
                    glyphs.append(0xFFD2)
                    line_count = 0
                else:
                    glyphs.append(0xFFFE)
            for ch in part:
                glyphs.append(enc(ch))
        # Restore trailing FFFE to match original binary format
        glyphs.append(0xFFFE)
        encoded_trans[mi] = glyphs
```

**Risk**: LOW. The translations were written with ` / ` breaks at appropriate positions. Removing `word_wrap()` preserves the translator's intended layout. The only risk is translations with single long lines (no ` / ` breaks) exceeding 18 chars, but these are rare in the type-2 corpus.

**Validation**: After build, count messages with > 3 consecutive non-FFD2 lines. Should be near zero.

---

## FIX-2: Fix R38 message index mapping errors

**Priority**: HIGH - gender shows "lv.6"/"lv.7", alignment shows triple "good"

### FIX-2a: Gender label indices (MSG 25-28)

**Root cause**: `chunk_r38_fix.json` has entries at wrong indices:
- MSG 25 = "lv.6" (WRONG - MSG 25 is spell level Lv7 in the original)
- MSG 26 = "lv.7" (WRONG - MSG 26 is the male kanji in the original)
- MSG 27 = "male" (WRONG - MSG 27 is the female kanji in the original)
- MSG 28 = "female" (WRONG - MSG 28 is "Io" world name in the original)

**What the game expects** (from v3 original binary analysis):
- MSG 25 = Lv7 (spell level) -- already correct from lv1-lv7 translations, do NOT overwrite
- MSG 26 = male (was Japanese kanji 518)
- MSG 27 = female (was Japanese kanji 349)
- MSG 28 = Io (world name, leave as-is or translate)
- MSG 29 = Europa (world name, leave as-is or translate)

**File**: `C:/Programmieren/wizardrytranslation/data/translate_chunks/chunk_r38_fix.json`

**Fix**: Edit the JSON entries (near lines 1052-1075):
```json
  // DELETE these two entries entirely - MSG 25 is already lv7 from earlier translations:
  // {"resource": 38, "message": 25, "japanese": "", "english": "lv.6 / "}
  // {"resource": 38, "message": 26, "japanese": "", "english": "lv.7 / "}

  // CHANGE MSG 27 -> MSG 26:
  {"resource": 38, "message": 26, "japanese": "", "english": "male / "},

  // CHANGE MSG 28 -> MSG 27:
  {"resource": 38, "message": 27, "japanese": "", "english": "female / "}

  // MSG 28 and 29 (Io, Europa) should NOT be overwritten - remove any entries for them
```

### FIX-2b: Alignment label data error (MSG 148-158)

**Root cause**: TWO bugs:
1. **Data error**: MSG 149 in chunk_r38_fix.json says `"english": "good \"g\" / "` but the Japanese source `"中立「n」 / "` means "neutral". This is a copy-paste error from MSG 148.
2. **The new injection entries (MSG 150-158) are correct** -- the issue is MSG 149 alone.

**Current state in chunk_r38_fix.json**:
- MSG 148: `good "g"` -- CORRECT
- MSG 149: `good "g"` -- WRONG (should be `neutral "n"`)
- MSG 150: `good "g"` -- from new injection block, should be `evil "e"`
- MSG 151: `neutral "n"` -- from new injection block, CORRECT for position 151
- MSG 152: `evil "e"` -- from new injection block, CORRECT for position 152

Wait -- cross-referencing the v17_vs_v9_comparison report more carefully:

**Original R38 layout (from v3 binary)**:
| MSG | Original Content | Should be |
|-----|-----------------|-----------|
| 148 | Good "G" (JP: 善「g」) | good "g" |
| 149 | Neutral "N" (JP: 中立「n」) | neutral "n" |
| 150 | Evil "E" (JP: 悪「e」) | evil "e" |
| 151 | Good (JP kanji) | good |
| 152 | Neutral (JP) | neutral |
| 153 | Evil (JP) | evil |
| 154 | G | g |
| 155 | N | n |
| 156 | E | e |

**Fix in chunk_r38_fix.json**: Change MSG 149's english value:
```json
  // BEFORE:
  {"resource": 38, "message": 149, "japanese": "中立「n」 / ", "english": "good \"g\" / "}
  // AFTER:
  {"resource": 38, "message": 149, "japanese": "中立「n」 / ", "english": "neutral \"n\" / "}
```

And verify the new injection entries (MSG 150-158) have the correct mapping:
```json
  {"resource": 38, "message": 150, "japanese": "", "english": "evil \"e\" / "},
  {"resource": 38, "message": 151, "japanese": "", "english": "good / "},
  {"resource": 38, "message": 152, "japanese": "", "english": "neutral / "},
  {"resource": 38, "message": 153, "japanese": "", "english": "evil / "},
  {"resource": 38, "message": 154, "japanese": "", "english": "g / "},
  {"resource": 38, "message": 155, "japanese": "", "english": "n / "},
  {"resource": 38, "message": 156, "japanese": "", "english": "e / "}
```

NOTE: The current JSON has MSG 150="good g", 151="neutral n", 152="evil e" -- these are shifted by +1. The correct values based on the original binary are shown above.

**Risk**: LOW. These are simple JSON value edits.

**Validation**: After build, dump R38 MSG 26-29 and MSG 148-158. Verify:
- MSG 26 = "male", MSG 27 = "female"
- MSG 148 = "good g", MSG 149 = "neutral n", MSG 150 = "evil e"
- MSG 151 = "good", MSG 152 = "neutral", MSG 153 = "evil"
- MSG 154 = "g", MSG 155 = "n", MSG 156 = "e"

---

## FIX-3: Fix R37 chargen prompt overflow

**Priority**: MEDIUM - top textbox shows 4 lines instead of 3

**Root cause**: R37 messages 1, 2, and 124 produce 5 display lines after encoding (max is 3 for the chargen top textbox). Each content line must be <= 18 chars, and total visible lines (including trailing FFFE blank) must be <= 3. Effectively: **2 content lines maximum**.

### FIX-3a: MSG 1 (name entry prompt)

**File**: `C:/Programmieren/wizardrytranslation/data/translate_chunks/chunk_01_translated.json`
**Line**: ~528

```json
// BEFORE:
"english": "Enter your name. [M / name/F name: Auto- / fill] /"

// AFTER (2 content lines, fits in 3-line box):
"english": "Enter your name. / "
```

The "[M name/F name: Auto-fill]" instruction is redundant -- the UI buttons already show these options.

### FIX-3b: MSG 2 (name entry prompt, override)

**File**: `C:/Programmieren/wizardrytranslation/data/translate_chunks/chunk_r37_r48_r49_translated.json`
**Line**: ~6

```json
// BEFORE:
"english": "enter a name. m / name, f name: auto- / fill /"

// AFTER:
"english": "Enter your name. / "
```

### FIX-3c: MSG 124 (confirmation prompt)

**File**: `C:/Programmieren/wizardrytranslation/data/translate_chunks/chunk_r37_extra.json`
**Line**: ~657

```json
// BEFORE:
"english": "Press O or X button / to confirm your / choices. /"

// AFTER (fits in 18 chars x 2 lines):
"english": "Confirm with O/X. / "
```

Alternative: `"Press O/X to / confirm. / "`

**Risk**: LOW. Purely text shortening.

**Validation**: After build, check R37 MSG 1-8 glyph streams. Each should have at most 2 FFFE tokens (= 3 lines max).

---

## FIX-4: R1188 tab/stat bitmap labels (HARD)

**Priority**: MEDIUM-HIGH - affects all chargen screens

**What's still Japanese** (all from R1188 bitmap atlas, NOT R38):
- Tab labels: katakana, hiragana, alphanumeric, symbol (glyph IDs 6400-6403)
- Buttons: Confirm/OK, Male Name, Female Name, Delete, Clear (glyph IDs 6405-6409)
- Stat labels: STR, INT, FTH, VIT, AGI, LCK (from R1188 atlas, rendered as bitmap sprites)

**Current state**:
- `tools/patch_r1188_direct.py` renders English labels into R1188 atlas rows y=1009-1020
- BUT nothing redirects the game to read from those rows (the UV coordinates still point to original Japanese positions)
- `build_full_english_v2.py` does NOT call the R1188 patcher (step was dropped from pipeline rewrite)
- `build_v9.py` Step 3.6 DOES call it, but the pixel edits go to unused space

**Options** (ranked by feasibility):

### Option A: Edit pixels at original UV positions (overwrite Japanese in-place)
1. Parse R1188 sprite metadata at file offsets 0x560-0x6B3 (17 entries x 20 bytes) to find UV rects for glyph group 0x19
2. Parse per-glyph UV records at 0x6B4-0x7C3 (17 entries x 16 bytes)
3. Cross-reference with PCSX2 texture dumps (48x20, 40x24 pixel sizes) to identify exact pixel positions
4. Render English labels at those exact pixel positions, overwriting the Japanese
5. Re-swizzle PSMT4 and inject back

**Requires**: Full decode of R1188 sprite metadata format (not yet done).

### Option D: Patch R1188 header UV data to redirect to new pixel positions
1. Keep English labels at y=1009-1020 (already rendered by patch_r1188_direct.py)
2. Parse and modify R1188 UV metadata to redirect glyph group 0x19 UV coordinates from original positions to y=1009-1020
3. Re-inject R1188

**Requires**: Same metadata decode as Option A, but modifies metadata instead of pixels.

### Option C: PCSX2 texture replacement (SHORT-TERM WORKAROUND)
Already implemented. Users enable PCSX2 texture replacement feature.
PNGs are at `build/pcsx2_texture_replacements/`.

**Immediate action**: Document PCSX2 texture replacement as interim solution. Schedule R1188 sprite metadata decode as a separate research task.

**Files involved**:
- `tools/patch_r1188_direct.py` -- current patcher (writes to wrong location)
- `build/build_v9.py` line 146 -- Step 3.6 call (works but patcher target is wrong)
- `extracted/packdata_raw/1188_type01.raw` -- original R1188
- R1188 sprite metadata: file offsets 0x560-0x7C3
- EXE glyph table (Table 2E): file offset 0x3C9DA0 (VA 0x4C9D20)
- BSS glyph group table: VA 0x4EB100 (runtime, populated from R1188 header)

**Risk**: MEDIUM. Requires reverse-engineering of sprite metadata format.

---

## FIX-5: EXE sidebar labels + title banner

**Priority**: MEDIUM - cosmetic but prominent on all chargen screens

**What's still Japanese**:
- Sidebar field labels: 性別 (gender), 種族 (race), 属性 (alignment), 職業 (class)
- Title banner: 新規登録 (New Character Registration)

**Root cause**: These are rendered using composite glyph IDs (480+) from the EXE's hardcoded data section. The rendering code at VA 0x2FB094 loads a single glyph ID from Table 2E and calls `render_bitmap_glyph()` (VA 0x494350). Each glyph ID maps to a pre-baked bitmap sprite in R1188's atlas.

**Options**:

### Option A: Replace font texture tiles for composite glyphs
- Find the composite glyph bitmap positions in R1188
- Overwrite those pixel regions with English text
- Same challenge as FIX-4 (need R1188 sprite metadata decode)

### Option B: Patch EXE glyph ID sequences
- Replace the composite glyph IDs in the EXE data section with sequences of individual Latin glyph IDs
- **Problem**: The renderer expects ONE bitmap sprite per label, not a multi-character string. Would require code patches to the rendering loop.

### Option C: PCSX2 texture replacement (SHORT-TERM WORKAROUND)
- PCSX2 replacement PNG for title banner exists (`a2d3fce36c8c719d-...120x24...png`)
- Sidebar labels would need additional PCSX2 replacement PNGs

**Immediate action**: Same as FIX-4 -- this is fundamentally the same R1188 sprite system. Solving FIX-4's metadata decode would also solve FIX-5.

**Files involved**:
- EXE data section containing composite glyph ID tables
- R1188 atlas (same as FIX-4)
- `build/patch_exe.py` -- current EXE patcher

**Risk**: MEDIUM-HIGH. EXE code patching carries higher risk of crashes.

---

## Build Pipeline Issue: R38 Double-Processing

**Not a user-visible bug currently, but a latent risk.**

The v2 pipeline (Step 1) writes R38 with variable-size injection and offset table rebuild. Then Step 2 of `build_v9.py` USED to overwrite R38 with fixed-size injection (pad/truncate). However, `build_v9.py` line 79 currently only lists `[35, 2654]` for Step 2, so R38 is NOT being double-processed.

**The v17 R38 is 100% English** (confirmed by full decode -- all 188 text messages, 0 Japanese glyphs). The v2 pipeline handles R38 correctly.

**Action**: No fix needed. Just noting that R38 should never be added back to Step 2's resource list.

---

## Execution Order

1. **FIX-1** (remove word_wrap from Step 4) -- 1 line change, biggest impact
2. **FIX-2** (R38 JSON fixes) -- JSON edits, fixes gender/alignment display
3. **FIX-3** (R37 prompt shortening) -- JSON edits, fixes textbox overflow
4. Build v18 and test
5. **FIX-4** (R1188 sprite metadata research) -- separate research task
6. **FIX-5** (EXE composite glyphs) -- depends on FIX-4 findings

---

## Quick Reference: What Each Fix Addresses

| User-Reported Issue | Fix |
|---|---|
| 1. Name entry tabs still Japanese | FIX-4 (R1188 sprites) |
| 2. Top textbox shows 4 lines | FIX-1 (double wrapping) + FIX-3 (shorten prompts) |
| 3. Some things got worse (double word-wrapping) | FIX-1 |
| 4. Attributes/stats still Japanese on CHARGEN | FIX-4 (R1188 sprites) |
| 5. Spurious text appearing (auto-name from button labels) | FIX-3 (shorten MSG 1/2) |
| 6. Sidebar labels still Japanese | FIX-5 (EXE composite glyphs) |
| 7. "New Registration" title still Japanese | FIX-5 (EXE composite glyphs) |
| 8. Gender shows "lv.6"/"lv.7" | FIX-2a (JSON index fix) |
| 9. Alignment all shows "good" | FIX-2b (JSON data fix) |
