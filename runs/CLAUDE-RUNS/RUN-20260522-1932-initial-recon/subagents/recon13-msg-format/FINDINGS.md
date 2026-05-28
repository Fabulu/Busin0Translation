# Recon 13: MSG (Message/Dialogue) File Format Analysis

**Date:** 2026-05-22
**Source:** BUSIN 1 / Wizardry: Tale of the Forsaken Land (English PS2 release, SLUS_202.59)
**Files analyzed:**
- `extracted_busin1/IMAGE/EVENT/UEDA.MSG` (16,768 bytes)
- `extracted_busin1/IMAGE/EVENT/KYOUGOKU.MSG` (16,768 bytes)
- `extracted_busin1/IMAGE/EVENT/FUKAUMI.MSG` (11,520 bytes)

---

## 1. Critical Finding: No English ASCII Text

**Despite being from the "English" PS2 release, these MSG files contain NO ASCII English text.**
The data is encoded as a stream of **16-bit glyph indices** (big-endian uint16), where each
value maps to a glyph in a font texture atlas. The font atlas itself (not present in these
files) would contain the actual rendered characters -- whether Japanese, English, or symbols.

This means:
- The same MSG format is used for both JP and EN versions
- Localization is achieved by changing the **font texture atlas** (mapping glyph index to character image), not by changing the encoding
- OR: The English text for this game is stored elsewhere (e.g., inside PACKDATA.CIG or the executable), and these MSG files contain Japanese event script data that was carried over unchanged into the English release

---

## 2. File Identity

**UEDA.MSG and KYOUGOKU.MSG are byte-for-byte identical** (both 16,768 bytes).
FUKAUMI.MSG (11,520 bytes) is a different, shorter file with different content.

The filenames correspond to Japanese developer names (Ueda, Kyougoku, Fukaumi) -- these
are likely the event script authors' working copies.

---

## 3. MSG File Format Specification

### 3.1 Overall Structure

```
[Message 0 tokens] FFFF [Message 1 tokens] FFFF [Message 2 tokens] FFFF ... [Zero padding]
```

- **No header.** The file is a flat stream of big-endian uint16 values.
- Messages are separated by the delimiter `0xFFFF`.
- The file ends with zero-padding (`0x0000` words) to fill the remaining space.

### 3.2 Encoding

| Property | Value |
|----------|-------|
| Word size | 16 bits (2 bytes) |
| Byte order | **Big-endian** |
| Glyph index range | 0x0000 -- 0x035A (~858 possible glyphs) |
| Control code range | 0xFFC0 -- 0xFFFF |
| Total unique values used | ~397 (in UEDA.MSG) |

### 3.3 File Statistics

| File | Size | Total uint16 | Messages (FFFF) | Line breaks (FFFE) | Data bytes | Trailing zeros |
|------|------|-------------|-----------------|--------------------|-----------:|---------------:|
| UEDA.MSG | 16,768 | 8,384 | 272 | 343 | 16,724 | 22 words (44 B) |
| KYOUGOKU.MSG | 16,768 | 8,384 | 272 | 343 | 16,724 | 22 words (44 B) |
| FUKAUMI.MSG | 11,520 | 5,760 | 193 | 225 | 11,406 | 57 words (114 B) |

---

## 4. Control Codes

All control codes are in the range 0xFFC0--0xFFFF (negative values if interpreted as signed int16).

| Code | Count (UEDA) | Meaning | Context |
|------|-------------|---------|---------|
| `0xFFFF` | 272 | **Message separator** | Ends each message; next message starts immediately after |
| `0xFFFE` | 343 | **Line break** | Within a message, starts a new display line |
| `0xFFF9` | 19 | **Line break variant** | Always follows FFFE; possibly "wait for input then newline" |
| `0xFFD2` | 80 | **Page break / clear box** | Always follows FFFE; likely clears text box before continuing |
| `0xFFD3` | 99 | **Page break variant** | Always follows FFFE; alternate page break behavior |
| `0xFFD4` | 41 | **Page break variant** | Always follows FFFE; third page break type |
| `0xFFE0` | 20 | **Inline formatting** | Appears paired with FFE1; possibly color/style toggle off |
| `0xFFE1` | 23 | **Inline formatting** | Often follows FFFE+FFD2; possibly color/style toggle on |
| `0xFFE2` | 2 | Rare formatting code | |
| `0xFFE3` | 7 | Formatting code | |
| `0xFFE7` | 2 | Rare formatting code | |
| `0xFFC0` | 2 | Rare control code | |
| `0xFFC1` | 2 | Rare control code | |
| `0xFFD0` | 2 | Rare control code | |
| `0xFFD1` | 3 | Rare control code | |

### Control Code Patterns

```
FFFE             = simple line break (stay in same text box)
FFFE FFD2        = page break (clear text box, wait for input)
FFFE FFD3        = page break variant (different animation/behavior)
FFFE FFD4        = page break variant
FFFE FFF9        = line break with wait-for-input
FFFE FFD2 FFE1 ... FFE0 = highlighted/colored text section
```

---

## 5. Message Internal Structure

### 5.1 Common Message Prefixes

Messages (segments between FFFF delimiters) show recurring header patterns:

**Pattern A: Speaker-tagged messages (34 occurrences)**
```
011e 0247 [0148] [glyph tokens...] [0149] FFFF
```
- `011e 0247` = "Set speaker / show name banner" control sequence
- Followed by either `0148` or text tokens for the speaker name
- `0148` = open quote / begin dialogue text
- `0149` = close quote / end dialogue text (168 occurrences, matches 0148 count)

**Pattern B: Continuation messages (common)**
```
0145 0146 0147 0148 [glyph tokens...] [0149] FFFF
```
- `0145 0146 0147` = "Continue with same speaker" or "narrative text"
- `0148` / `0149` brackets still used

**Pattern C: Special messages**
Various other starting sequences, e.g.:
- `0111 0112 ... 0113 0114 ...` (first message in UEDA.MSG, likely scene setup)
- `004d ...` (direct text without headers)
- `007b ...` (direct text without headers)

### 5.2 Glyph Value Ranges

| Range | Unique Values | Likely Content |
|-------|--------------|----------------|
| 0x0000--0x00FF | ~162 | Primary glyphs: hiragana, katakana, ASCII-range characters, common kanji |
| 0x0100--0x01FF | 142 | Extended glyphs: kanji, special characters, possibly some control tokens |
| 0x0200--0x02FF | 78 | Extended glyphs: more kanji, punctuation (0x026A and 0x026E are very common -- likely period/comma equivalents) |
| 0x0300--0x035A | ~20 | Rare/extended glyphs |

### 5.3 High-Frequency Glyph Values

| Value | Count | Likely Glyph |
|-------|-------|-------------|
| 0x0040 | 248 | Very common character (possibly Japanese particle like "no" or space) |
| 0x0057 | 220 | Very common character |
| 0x004E | 201 | Very common character |
| 0x026A | 199 | Very common -- likely sentence-ending punctuation (period/"。") |
| 0x0058 | 178 | Very common character |
| 0x026E | 124 | Common -- likely another punctuation mark |

---

## 6. Paired EVE + MSG File System

Each MSG file has a corresponding `.EVE` (event) file:

| File | MSG Size | EVE Size | EVE Records (16B) |
|------|----------|----------|-------------------|
| UEDA | 16,768 | 5,888 | 368 |
| KYOUGOKU | 16,768 | (not checked, likely different from UEDA) |
| FUKAUMI | 11,520 | (not checked) |

The EVE file appears to be an event script / bytecode that references messages in the MSG
file by index or byte offset. EVE records are 16 bytes each (big-endian) with fields
including what appear to be byte offsets (0x0150, 0x0348, 0x04A8...) that may point into
the MSG file.

---

## 7. Implications for BUSIN 0 Translation

### For MSG file translation:
1. **The encoding is glyph-index-based**, not character-based. To translate text, you need:
   - The font texture atlas (glyph images)
   - The glyph-to-index mapping table
   - To either remap existing indices to English glyphs, or create a new font atlas

2. **The format is simple**: flat uint16 stream with FFFF separators. No compression, no pointers, no complex headers. Easy to parse and rebuild.

3. **Control codes are well-defined**: FFFE=newline, FFFF=end, FFDx=page breaks. These should be preserved during translation.

4. **Message boundaries are clear**: Split on FFFF to get individual messages. Each message may have a header (011e 0247 or 0145-0147) followed by body text bracketed by 0148/0149.

### Key unknowns:
- The glyph-to-character mapping table location (likely in the font texture or executable)
- Whether 0x0100-0x02FF values are all glyphs or some are inline control codes
- The exact semantics of `011e 0247` vs `0145 0146 0147` message headers
- How the EVE file references specific messages (by index count or byte offset)

---

## 8. Format Summary Diagram

```
MSG File Layout:
+------------------------------------------------------------------+
| [msg0 tokens] FFFF [msg1 tokens] FFFF ... [msgN tokens] FFFF     |
| [zero padding to file end]                                        |
+------------------------------------------------------------------+

Single Message:
+------------------------------------------------------------------+
| [optional header: 011e 0247 or 0145 0146 0147]                   |
| [0148 = begin text]                                               |
| [glyph indices: uint16 BE, range 0x0000-0x035A]                  |
| [FFFE = line break] [optional FFDx = page break modifier]         |
| [more glyph indices...]                                           |
| [0149 = end text]                                                 |
+------------------------------------------------------------------+

Token Types (uint16 BE):
  0x0000 - 0x035A  = Glyph index (maps to font atlas tile)
  0xFFC0 - 0xFFD4  = Formatting/page break control codes
  0xFFE0 - 0xFFE7  = Inline formatting (color/style)
  0xFFF9           = Wait-for-input line break
  0xFFFE           = Line break (newline)
  0xFFFF           = Message separator (end of message)
```
