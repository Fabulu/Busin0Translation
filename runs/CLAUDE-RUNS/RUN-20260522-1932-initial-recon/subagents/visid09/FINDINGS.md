# Visual Identification: Sheets 02-03 (Glyphs 200-399) -- Kana Verification Attempt

**Date:** 2026-05-22
**Status:** INCONCLUSIVE -- key findings contradict the premise
**Input:** `dumps/glyph_sheets/sheet_02_glyphs_0200-0299.png`, `dumps/glyph_sheets/sheet_03_glyphs_0300-0399.png`

---

## Executive Summary

**Glyphs 200-399 are NOT the hiragana and katakana ranges.** Multiple independent lines of evidence demonstrate that the most-used kana characters occupy LOW glyph indices (0x00-0xFF), while glyphs 200-399 are moderately-used characters that are more likely a mix of less-common kana, symbols, and the beginning of the kanji range. The glyph sheet images cannot be used for reliable individual character identification at this resolution.

---

## Evidence Against 200-399 Being the Kana Range

### 1. Frequency Analysis Contradiction

In standard Japanese text, hiragana particles (no, ha, ni, wo, te, de, ga, to) dominate frequency. The top-frequency glyphs in the MSG data are:

| Rank | Glyph Index | Count | % of tokens |
|------|-------------|-------|-------------|
| 2 | 1 | 1,988 | 1.78% |
| 3 | 255 | 1,075 | 0.96% |
| 4 | 3 | 901 | 0.81% |
| 5 | 113 | 675 | 0.60% |
| 6 | 136 | 665 | 0.60% |
| 7 | 158 | 493 | 0.44% |
| 8 | 152 | 491 | 0.44% |
| 9 | 93 | 489 | 0.44% |
| 10 | 130 | 480 | 0.43% |

The top 25 non-null glyphs are ALL below index 200. If hiragana started at 200, we would expect indices 200-280 to dominate the frequency chart. Instead, the 0x200-0x23F range accounts for only 966 total tokens vs. 83,898 for 0x0000-0x003F.

### 2. Range Density Analysis

Fine-grained density (msg_frequency_analysis.txt) shows:

| Block | Total Tokens | Unique Glyphs |
|-------|-------------|---------------|
| 0x0000-0x003F | 83,898 | 64 |
| 0x0070-0x007F | 4,224 | 16 |
| 0x0080-0x008F | 3,639 | 16 |
| 0x0090-0x009F | 3,167 | 16 |
| 0x00F0-0x00FF | 1,648 | 16 |
| **0x0200-0x020F** | **477** | **16** |
| **0x0300-0x030F** | **262** | **16** |

The 0x0070-0x009F range (112-159) has the highest density after the first block -- consistent with being the kana region. Glyphs 200-399 have moderate density, consistent with less-frequent kanji or rare kana.

### 3. Individual Glyph Extraction Shows Blank

The `glyphs_v3/` directory (882 individual 48x48 PNGs) shows glyphs 200-383 as nearly blank -- only 1-3 lit pixels per glyph. This was also reported by the template matcher (impl14), which mapped these as spaces or backticks. The glyph sheets show more content due to a different deswizzle approach, but the discrepancy means the atlas region containing these glyphs has not been properly extracted.

### 4. Deswizzle Discrepancy

The glyph sheet images were rendered from the raw PSMT4 atlas data using a block-level deswizzle (atlas_final_render.py). The individual glyph extraction likely used a different column interleaving. Each cell in the glyph sheets shows TWO rows (top = correct rendering), but even the "correct" row shows characters at extremely low resolution (roughly 8-10 visible pixels per character), making individual kana identification unreliable.

### 5. Glyph Property Table Scope

The EXE's 133-entry per-glyph property table at 0x3C0E78 covers only glyph indices relevant to the ASCII subset and font rendering coordinates. It does NOT contain character identity information for the Japanese glyphs. The actual Japanese glyph-to-character mapping resides in BSS RAM at 0x5191F0, loaded from PACKDATA at runtime (recon20).

---

## What the Glyph Sheets Actually Show

### Sheet 02 (Glyphs 200-299)

- **200-214**: Very sparse patterns (1-4 lit pixels). These appear to be tile top-fragments of characters whose main body is rendered in adjacent tiles.
- **215-240**: Moderate-density patterns with horizontal bars and some structure. Could be simple kana (e.g., horizontal-stroke characters like て, こ, に, ー) or JIS punctuation/symbols.
- **240-260**: Medium complexity, some recognizable stroke patterns but too small for confident identification.
- **260-270**: Medium-complex characters with distinctive shapes.
- **270-299**: Dense, multi-stroke characters. The density increase suggests a transition from kana-class characters to kanji-class characters around glyph 270-280.

### Sheet 03 (Glyphs 300-399)

- **300-369**: Very dense, complex multi-stroke characters. These are consistent with kanji, NOT katakana. Katakana characters are typically simpler (2-4 strokes) and would not produce the pixel density seen here.
- **370-399**: Abrupt simplification -- characters become horizontal bars and simple shapes. This matches the pattern seen in sheet_04 (400+) where tile fragments dominate, suggesting the main character set ends around glyph 370 and tile fragment data begins.

---

## Where Kana Actually Are (Hypothesis)

Based on the frequency evidence and the ASCII mapping (glyphs 0-93 = ASCII), the most likely kana arrangement is:

| Glyph Range | Likely Content | Evidence |
|-------------|---------------|----------|
| 0-93 | ASCII (confirmed) | EXE glyph table at 0x3C0870 |
| 94-~176 | JIS symbols/punctuation | First post-ASCII characters |
| ~177-~259 | Hiragana (83 chars) | High frequency in 0x70-0xFF |
| ~260-~345 | Katakana (86 chars) | Moderate frequency in 0x100-0x150 |
| ~346-~857 | Kanji (~512 chars) | Lower frequency, high complexity |

Note: These ranges are APPROXIMATE. The exact offsets cannot be determined without:
1. Successfully deswizzling the full font atlas and performing OCR
2. Cross-referencing known game text (class names like "Fighter" = katakana sequence) against MSG glyph data
3. Finding and parsing the BSS RAM character struct table from the PACKDATA resource that loads it

---

## Answers to Specific Questions

### 1. Does the sequence start at glyph 200?

**No.** Kana do NOT start at glyph 200. The highest-frequency Japanese characters (which must be hiragana particles) are at indices below 200. The kana sequence likely starts in the 94-180 range. Glyph 200 is somewhere in the middle of the kana-to-kanji transition.

### 2. Are they in standard order or custom order?

**Cannot determine from visual inspection.** The glyph sheet images are too low-resolution (roughly 8-10 visible pixels per character at the rendered scale) for reliable identification of individual kana. However, the game's use of a custom glyph index table (with gaps at 2-4, 11-12, 31-32, 87-88 in the ASCII range) suggests a custom ordering rather than strict JIS X 0208.

### 3. Where does hiragana end and katakana begin?

**Cannot determine from these sheets.** The transition point is likely between glyph 259 and glyph 345 (roughly), based on the hypothesis above. But this needs confirmation from cross-reference analysis or successful font OCR.

### 4. Are there gaps (blank slots) between hiragana and katakana?

**Likely no.** The glyph range density shows all 16-glyph blocks in the 0x80-0x160 range having exactly 15-16 unique glyphs used, suggesting continuous allocation with no gaps.

---

## Recommendations

1. **Do NOT assume glyphs 200-399 are kana.** The frequency data strongly contradicts this.
2. **Priority: Cross-reference approach.** Match known game strings (class names, spell names) against MSG glyph sequences to establish concrete glyph-to-character mappings. This is the GLYPH_MAPPING_PLAN's "Approach C" and remains the highest-confidence path.
3. **Fix the deswizzle.** The individual glyph extraction (glyphs_v3) produces blank images for indices 200-383, while the glyph sheet renderer shows content. Reconciling these will enable proper template matching.
4. **Visual ID of kana should target sheets 00-01**, not sheets 02-03. The kana characters are most likely in the 94-250 glyph range.
