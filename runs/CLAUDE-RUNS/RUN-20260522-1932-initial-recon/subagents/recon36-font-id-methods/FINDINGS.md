# Font Atlas Character Identification Methods -- Research Findings

## Context
- PS2 game font atlas containing 858 Japanese characters at 12x12 pixels each
- Standard OCR fails at this resolution
- Game compiled with Metrowerks CodeWarrior for PS2

---

## 1. How Romhackers Identify Characters in Game Font Atlases

### Table File (.tbl) Approach
The romhacking community uses **table files** (.tbl) -- simple text files mapping hex values to characters:
```
00=（space）
01=あ
02=い
41=A
8140=　
```

The standard workflow:
1. **Visual inspection** -- Open the font atlas in a tile editor or image viewer and visually identify recognizable characters (hiragana/katakana are easiest since there are only ~150)
2. **Relative search** -- Once a few characters are known, search the ROM for known text strings. If "ATTACK" appears on screen, search for the byte pattern that would spell it given the partial table
3. **Pattern deduction** -- If the font follows a known encoding (Shift-JIS, JIS), the ordering of characters in the atlas directly reveals the mapping
4. **Hex editor correlation** -- Open the ROM with the partial table in a hex editor (like Hexposure, WindHex, or Crystal Tile 2) to see readable text appear, confirming and extending the table

### Key Insight for Our Case
For Japanese PS2 games, **most use Shift-JIS encoding natively**. If the font atlas arranges glyphs in Shift-JIS order, then glyph position N maps directly to Shift-JIS code point N -- no OCR needed at all. We just need to confirm the ordering.

### Sources
- [Romhacking.net - Getting Started](https://www.romhacking.net/start/)
- [Romhacking.net - RomHacking 102 - Font & Sprites](https://www.romhacking.net/documents/872/)
- [Table File Format specification by Nightcrawler](https://transcorp.romhacking.net/scratchpad/Table%20File%20Format.txt)
- [Romhacking.net - Shift-JIS Table](https://www.romhacking.net/documents/179/)
- [GBAtemp - How to make a table file](https://gbatemp.net/threads/how-to-make-a-table-file-for-a-rom-gba-nds.327308/)

---

## 2. JIS X 0208 Standard Ordering

JIS X 0208 is organized as a **94-row x 94-column grid** (ku-ten / row-cell system). The character layout:

| Rows | Content | Character Count |
|------|---------|----------------|
| 1-2 | Punctuation and symbols | ~147 |
| 3 | Latin letters, digits | ~63 |
| 4 | **Hiragana** | 83 |
| 5 | **Katakana** | 86 |
| 6 | Greek alphabet (upper+lower) | 48 |
| 7 | Cyrillic alphabet (upper+lower) | 66 |
| 8 | Line-drawing characters | 32 |
| 9-15 | Reserved / unused | 0 |
| 16-47 | **Level 1 Kanji** | 2,965 |
| 48-84 | **Level 2 Kanji** | 3,390 |
| **Total** | | **~6,879** |

### Level 1 Kanji Ordering
Level 1 kanji (rows 16-47) are sorted by:
1. **Primary:** Representative on'yomi/kun'yomi reading (phonetic order)
2. **Secondary:** On'yomi alone to break ties
3. **Tertiary:** Kun'yomi

This means Level 1 kanji start with characters read as "a" (e.g., 亜) and proceed through the Japanese syllabary.

### Level 2 Kanji Ordering
Level 2 kanji (rows 48-84) follow **radical-stroke order** (the 214 Kangxi radicals, then stroke count within each radical).

### Shift-JIS Encoding of JIS Rows
Shift-JIS encodes the JIS rows into byte pairs:
- **0x8140-0x84BE**: Rows 1-8 (symbols, hiragana, katakana, Greek, Cyrillic)
  - 0x8240-0x829A: Digits and Latin letters
  - 0x829F-0x82F1: **Hiragana** (あ through ん)
  - 0x8340-0x8396: **Katakana** (ア through ヶ)
- **0x889F-0x9FFC**: Rows 16-47 (**Level 1 Kanji**)
- **0xE040-0xEAA4**: Rows 48-84 (**Level 2 Kanji**)

### Mapping to Our 858 Characters
858 characters is a **subset** of JIS X 0208. Likely composition:
- ~147 symbols + punctuation
- 83 hiragana
- 86 katakana
- ~48 Greek (maybe omitted)
- ~66 Cyrillic (maybe omitted)
- ~500-540 most-used kanji (subset of Level 1)
- Total: ~858

A game would only include the characters it actually uses in dialogue/menus. The font atlas likely stores them in Shift-JIS code point order, including only the subset needed.

### Sources
- [JIS X 0208 - Wikipedia](https://en.wikipedia.org/wiki/JIS_X_0208)
- [Shift JIS - Wikipedia](https://en.wikipedia.org/wiki/Shift_JIS)
- [JIS Character Sets Explained](https://harjit.moe/jischarsets.html)
- [Shift JIS Kanji Code Table](http://www.rikai.com/library/kanjitables/kanji_codes.sjis.shtml)
- [JIS X0208 Character Set](https://www.herongyang.com/Unicode/JIS-X0208-Character-Set-for-Japanese-Character.html)

---

## 3. PS2 Game Font Atlas Typical Ordering

### Common Patterns
Based on forum discussions and localization project code:

1. **Shift-JIS order (most common)**: Characters stored in ascending Shift-JIS code point order. The game engine looks up a character's Shift-JIS code and computes the glyph index from it.

2. **Sequential index from font texture**: "Character values are based in the actual font, so it starts with the first font texture having the space as the first character" (GBAtemp forum). The game stores a lookup table or uses a formula to convert Shift-JIS codes to glyph indices.

3. **Custom order with mapping table**: Some games use arbitrary ordering with a separate mapping table stored in the ROM/ISO.

### PS2-Specific Resources
- The **PS2 SJIS Character Table** (documented at ps2-home.com) maps the PS2's specific Shift-JIS implementation, including BIOS-revision-specific variations.
- A **Google Sheets spreadsheet** exists with the complete PS2 Shift-JIS mapping: [PS2 SJIS Table](https://docs.google.com/spreadsheets/d/1Ca4DRn5iYzHlblOjn5m8IQ2GLmxvGm1VB8S5hfuleZI/edit)

### Reference Implementation
The `font_tool.py` from the **Nebula: Echo Night** PS2 localization project demonstrates how PS2 font atlases are handled programmatically:
- [font_tool.py](https://github.com/wmltogether/Project-Console-Game-Localization/blob/master/PS2/Nebula_Echo_Night/tools/Font/font_tool.py)
- This tool generates font atlas textures from character lists, confirming that PS2 games typically use ordered character tables

### Verification Strategy
To determine our game's ordering:
1. Visually identify the first ~10 glyphs in the atlas (space, punctuation, digits, A-Z are easy)
2. Check if they match Shift-JIS order (0x8140 = ideographic space, 0x8141 = 、, 0x8142 = 。, etc.)
3. Find where hiragana starts -- if at the expected Shift-JIS offset, the atlas follows Shift-JIS order
4. Cross-reference with the game's text data to confirm the mapping

### Sources
- [GBAtemp - Extract text from Japanese PS2 game](https://gbatemp.net/threads/how-to-extract-text-and-reimport-japanese-ps2-game.658272/)
- [PS2-HOME SJIS Tutorial](https://www.ps2-home.com/forum/viewtopic.php?t=8914)
- [PS2 SJIS Google Sheet](https://docs.google.com/spreadsheets/d/1Ca4DRn5iYzHlblOjn5m8IQ2GLmxvGm1VB8S5hfuleZI/edit)
- [Nebula Echo Night font_tool.py](https://github.com/wmltogether/Project-Console-Game-Localization/blob/master/PS2/Nebula_Echo_Night/tools/Font/font_tool.py)
- [PS2 fontengine library](https://github.com/F0bes/fontengine)

---

## 4. Template Matching with Known Font Bitmaps

### Candidate Fonts for Matching

**Shinonome Font** (most promising for 12x12):
- Open-source (public domain) Japanese bitmap font available in **12, 14, and 16 pixel** sizes
- Covers JIS X 0201 and JIS X 0208 character sets
- Available in **BDF format** (Bitmap Distribution Format -- easily parseable)
- Download: [efont project](http://openlab.ring.gr.jp/efont/japanese/index.html.en)
- Also available via package managers: `ja-shinonome` on NetBSD/FreeBSD

**MS Gothic**:
- Originally a Ricoh bitmap font, later vectorized for Windows 3.1+
- At 12px rendering, it would produce 12x12 bitmaps for CJK characters
- Available on any Windows system, can be rendered to bitmaps via script
- The precursor bitmap version may match game fonts closely

**DotGothic16**:
- Open-source pixel/dot-matrix style Japanese font on Google Fonts
- Designed to look like 16-dot bitmap fonts
- [Google Fonts - DotGothic16](https://fonts.google.com/specimen/DotGothic16)

### Template Matching Approach with OpenCV
```python
import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image

# 1. Render each JIS X 0208 character using candidate font at 12x12
font = ImageFont.truetype("msgothic.ttc", 12)
for codepoint in jis_codepoints:
    char = chr(codepoint)
    img = Image.new('L', (12, 12), 0)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), char, font=font, fill=255)
    template = np.array(img)
    
    # 2. Compare against each glyph in the atlas
    for glyph in atlas_glyphs:
        # Use normalized cross-correlation or simple XOR
        result = cv2.matchTemplate(glyph, template, cv2.TM_CCOEFF_NORMED)
        # Or: diff = np.count_nonzero(glyph ^ template)
```

**Key considerations:**
- For binary (1-bit) fonts, **XOR comparison** is fastest and most accurate -- count differing pixels
- Need to account for slight positioning differences (the glyph may be offset by 1 pixel)
- If the game uses a custom font rather than a system font, template matching will fail
- Try multiple candidate fonts and pick the one with highest overall match rate

### Metrowerks CodeWarrior PS2 Default Font
No specific information found about a default font bundled with CodeWarrior for PS2. The game likely uses its own custom font or a licensed font baked into the game assets. However, many PS2 JRPGs used fonts visually similar to MS Gothic or Shinonome at small sizes.

### Sources
- [MS Gothic - MyFonts](https://www.myfonts.com/collections/ms-gothic-font-microsoft-corporation)
- [MS Gothic - Microsoft Learn](https://learn.microsoft.com/en-us/typography/font-list/ms-gothic)
- [Shinonome font - NetBSD](https://iso.us.netbsd.org/pub/pkgsrc/current/pkgsrc/fonts/ja-shinonome/index.html)
- [efont Japanese bitmap fonts](http://openlab.ring.gr.jp/efont/japanese/index.html.en)
- [DotGothic16 - Google Fonts](https://fonts.google.com/specimen/DotGothic16)
- [OpenCV Template Matching](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html)

---

## 5. Claude/LLM-Based Character Recognition

### Feasibility Assessment

**The challenge:** 12x12 pixel glyphs are extremely small. Research shows that multimodal LLMs' OCR accuracy **drops significantly below 150 PPI**, and 12x12 pixels is well below that threshold.

**GPT-4o specific issues with Japanese:** Research found 19 kanji characters consistently misrecognized across all resolutions, including simple characters like "一" (misread as hyphen) and "丼" (misread as "井"). At 12x12, this problem would be far worse.

### Practical Approach -- Batched Glyph Sheets
Rather than sending individual 12x12 images (too small for the model to process reliably):

1. **Upscale each glyph** to 48x48 or 96x96 using nearest-neighbor interpolation (preserves pixel art)
2. **Arrange in grids** -- place 20-30 upscaled glyphs on a single image with labels/numbers
3. **Send to Claude** with a prompt like: "Each numbered cell contains a single Japanese character rendered at low resolution. Identify each character."
4. **Focus on subsets**: Hiragana and katakana are easiest (only ~170 characters, very distinctive shapes even at 12px). Kanji will be much harder.

### Expected Accuracy
- **Hiragana/Katakana:** ~90-95% accuracy with upscaling (distinctive shapes)
- **Common kanji (JLPT N5-N3):** ~60-80% accuracy (recognizable at low res)
- **Rare/complex kanji:** ~20-40% accuracy (too many similar-looking characters at 12px)
- **Symbols/punctuation:** ~85-95% (distinctive shapes)

### Hybrid Strategy (Recommended)
1. Use **Claude vision** for initial identification of easy characters (kana, digits, punctuation, common kanji)
2. Use **JIS ordering analysis** to fill in gaps (if ordering is confirmed as Shift-JIS, all characters are known immediately)
3. Use **template matching** against Shinonome 12px BDF font as verification
4. Manual review of remaining ambiguous characters

### Sources
- [Context-Independent OCR with Multimodal LLMs (arXiv)](https://arxiv.org/html/2503.23667v1)
- [Claude Vision for Document Analysis](https://getstream.io/blog/anthropic-claude-visual-reasoning/)
- [Claude Vision Features and Limitations](https://www.datastudios.org/post/can-claude-analyze-images-and-screenshots-vision-features-and-limitations)
- [Next-Gen OCR with Vision LLMs](https://medium.com/@pvsravanth/next-gen-ocr-with-vision-llms-a-guide-to-using-phi-3-claude-and-gpt-4o-4c6fbabe92c8)

---

## Recommended Strategy (Priority Order)

### Priority 1: Confirm Shift-JIS Ordering (Effort: Low, Impact: Complete Solution)
If the font atlas follows Shift-JIS order, every character is immediately known -- no OCR needed.

**Steps:**
1. Extract the first ~20 glyphs from the atlas
2. Visually identify them (space, Japanese punctuation 、。, brackets, etc.)
3. Compare against Shift-JIS code table starting at 0x8140
4. If they match, generate the complete mapping programmatically

**Why this is most likely:** The game uses Shift-JIS text encoding (standard for PS2 JRPGs). The simplest implementation stores glyphs in Shift-JIS order and computes the atlas index from the character code.

### Priority 2: Template Matching with Shinonome 12px (Effort: Medium, Impact: ~80-95%)
If the ordering is not standard, or as verification:

**Steps:**
1. Download Shinonome 12px BDF font
2. Render each JIS X 0208 character to a 12x12 bitmap
3. Compare each atlas glyph against all rendered characters using pixel XOR
4. Best match (lowest XOR count) identifies the character

### Priority 3: Claude Vision for Remaining Characters (Effort: Medium, Impact: Fills Gaps)
For any glyphs not matched by template matching:

**Steps:**
1. Upscale unmatched glyphs to 96x96 (8x nearest-neighbor)
2. Arrange in labeled grids of 20-30
3. Send to Claude with identification prompt
4. Cross-reference results with game context (menu text, dialogue)

### Priority 4: Game Binary Analysis (Effort: High, Impact: Definitive)
Search the game's executable/data files for the character mapping table:

**Steps:**
1. Search for Shift-JIS byte sequences in the ISO
2. Find the font rendering code -- it will contain the mapping logic
3. The mapping table (if any) will be near the font data

---

## Quick Reference: Shift-JIS Character Ranges

| Range | Content |
|-------|---------|
| 0x20-0x7E | ASCII printable characters |
| 0xA1-0xDF | Half-width katakana |
| 0x8140-0x817E | JIS symbols row 1 (first half) |
| 0x8180-0x81AC | JIS symbols row 1 (second half) |
| 0x81B8-0x81BF | Mathematical symbols |
| 0x81C8-0x81CE | More symbols |
| 0x81DA-0x81E8 | More symbols |
| 0x81F0-0x81F7 | More symbols |
| 0x81FC | Circle |
| 0x824F-0x8258 | Full-width digits 0-9 |
| 0x8260-0x8279 | Full-width uppercase A-Z |
| 0x8281-0x829A | Full-width lowercase a-z |
| **0x829F-0x82F1** | **Hiragana (ぁ-ん)** |
| **0x8340-0x8396** | **Katakana (ァ-ヶ)** |
| 0x839F-0x83B6 | Greek uppercase |
| 0x83BF-0x83D6 | Greek lowercase |
| 0x8440-0x8460 | Cyrillic uppercase |
| 0x8470-0x8491 | Cyrillic lowercase |
| **0x889F-0x9FFC** | **Level 1 Kanji (2,965 chars)** |
| **0xE040-0xEAA4** | **Level 2 Kanji (3,390 chars)** |
