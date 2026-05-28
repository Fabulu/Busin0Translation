# MSG Reinsertion Format Research -- FINDINGS

**Date:** 2026-05-22
**Scope:** Determine whether we can encode English text as glyph index streams and write them back into PACKDATA.DIG MSG resources.

---

## 1. Latin Character Coverage in Glyph Map

**Source:** `data/msg_glyph_map.json` (759 mappings total)

### Lowercase a-z: 26/26 PRESENT (ALL)

Glyph indices 33-58 map to lowercase a-z in exact ASCII order:

| Glyph | Char | Glyph | Char | Glyph | Char |
|-------|------|-------|------|-------|------|
| 33 | a | 42 | j | 51 | s |
| 34 | b | 43 | k | 52 | t |
| 35 | c | 44 | l | 53 | u |
| 36 | d | 45 | m | 54 | v |
| 37 | e | 46 | n | 55 | w |
| 38 | f | 47 | o | 56 | x |
| 39 | g | 48 | p | 57 | y |
| 40 | h | 49 | q | 58 | z |
| 41 | i | 50 | r | | |

### Uppercase A-Z: 0/26 -- NONE PRESENT

**CRITICAL GAP.** The glyph map has NO uppercase Latin letters. The game's font atlas only includes lowercase a-z for Latin characters. This means:

- **We must add uppercase glyphs to the font atlas** (Phase 7 font modification).
- We can repurpose Japanese glyph slots (e.g., hiragana slots 112-191, indices 112-191) for uppercase A-Z.
- Alternatively, the game might have uppercase somewhere that the OCR/mapping process missed -- but this is unlikely since there are no gaps in the 33-58 range that would correspond to uppercase.

### Digits: FULLWIDTH ONLY

The map has fullwidth digits only (indices 16-25):

| Glyph | Char |
|-------|------|
| 16 | 0 (fullwidth) |
| 17 | 1 (fullwidth) |
| ... | ... |
| 25 | 9 (fullwidth) |

No halfwidth 0-9 digits are present. For encoding, we can map ASCII '0'-'9' to glyph indices 16-25 (the fullwidth digits) which will render as visually acceptable digits.

### Space: PRESENT

| Glyph | Char |
|-------|------|
| 0 | space |
| 1 | space |

Two glyph slots map to space. Use glyph 0 as the canonical space.

### Punctuation: PARTIAL

Present (as fullwidth or Japanese equivalents):
- Glyph 31: ? (fullwidth)
- Glyph 92: ! (fullwidth)
- Glyph 62: , (Japanese comma)
- Glyph 63: . (Japanese period)
- Glyph 26: : (fullwidth colon)
- Glyph 15: / (fullwidth slash)
- Glyph 13: - (fullwidth minus/dash)
- Glyph 109: % (fullwidth)
- Glyph 91: middle dot
- Glyph 93: long dash (cho-on)
- Glyph 94: tilde
- Glyph 95: heart symbol

**MISSING standard English punctuation:**
- Apostrophe/single quote (')
- Double quote (")
- Semicolon (;)
- Parentheses ( )
- Hyphen-minus (-)  -- we have fullwidth minus at 13, may work
- Underscore (_)
- At sign (@), hash (#), dollar ($), ampersand (&), asterisk (*), plus (+), equals (=)
- Square/curly brackets

For missing punctuation, we will need to either:
1. Repurpose unused Japanese glyph slots and add the glyphs to the font atlas
2. Use available substitutes (fullwidth ! for !, fullwidth ? for ?, etc.)

### Summary of Character Coverage

| Category | Available | Needed | Gap |
|----------|-----------|--------|-----|
| Lowercase a-z | 26/26 | 26 | NONE |
| Uppercase A-Z | 0/26 | 26 | **26 slots needed** |
| Digits 0-9 | 10/10 (fullwidth) | 10 | Can reuse fullwidth |
| Space | 2/1 | 1 | NONE |
| Basic punct (.,:;!?-'") | 5/9 | 9 | **4 slots needed** |
| **TOTAL NEW SLOTS NEEDED** | | | **~30 slots** |

We have 80 hiragana slots (112-191) and 80+ katakana slots (193-272) available for repurposing. Only ~30 are needed for full English coverage. **This is very feasible.**

---

## 2. Reverse Mapping (Character -> Glyph Index)

### Building the Reverse Map

The current map is glyph_index -> character. For encoding, we need character -> glyph_index.

### Ambiguity Analysis

**Multiple glyphs mapping to the same character is VERY COMMON for kanji.** Examples:

| Character | Glyph Indices |
|-----------|---------------|
| 魔 (magic) | 293, 302 |
| 大 (big) | 295, 441, 554 |
| 王 (king) | 296, 475 |
| 法 (law) | 292, 326, 870 |
| 復 (restore) | 413, 428 |
| 上 (up) | 328, 429 |
| 対 (versus) | 374, 479 |
| 不 (not) | 341, 459 |
| 武 (martial) | 316, 450 |
| ... | (many more) |

This is expected because the game's font atlas has multiple pages/contexts (battle font, event font, menu font), with the same kanji appearing in different atlas positions.

**For Latin characters: NO AMBIGUITY.** Each lowercase letter maps to exactly one glyph index (33-58). The only duplication is:
- Space: glyphs 0 and 1 (use 0 as canonical)
- "v": glyphs 54 (Latin v) and 86 (fullwidth v) -- use 54

### Proposed English Glyph Table (character -> glyph index)

```python
ENGLISH_GLYPH_TABLE = {
    # Existing mappings (already in font atlas)
    ' ': 0,      # space
    'a': 33, 'b': 34, 'c': 35, 'd': 36, 'e': 37, 'f': 38,
    'g': 39, 'h': 40, 'i': 41, 'j': 42, 'k': 43, 'l': 44,
    'm': 45, 'n': 46, 'o': 47, 'p': 48, 'q': 49, 'r': 50,
    's': 51, 't': 52, 'u': 53, 'v': 54, 'w': 55, 'x': 56,
    'y': 57, 'z': 58,
    '0': 16, '1': 17, '2': 18, '3': 19, '4': 20,
    '5': 21, '6': 22, '7': 23, '8': 24, '9': 25,
    '?': 31, '!': 92, ',': 62, '.': 63, ':': 26,
    '/': 15, '-': 13, '%': 109, '~': 94,
    
    # NEW mappings (require font atlas modification)
    # Repurpose hiragana slots 112-137 for uppercase A-Z
    'A': 112, 'B': 113, 'C': 114, 'D': 115, 'E': 116,
    'F': 117, 'G': 118, 'H': 119, 'I': 120, 'J': 121,
    'K': 122, 'L': 123, 'M': 124, 'N': 125, 'O': 126,
    'P': 127, 'Q': 128, 'R': 129, 'S': 130, 'T': 131,
    'U': 132, 'V': 133, 'W': 134, 'X': 135, 'Y': 136,
    'Z': 137,
    
    # Additional punctuation (repurpose more hiragana/katakana slots)
    "'": 138,    # apostrophe (was ひ)
    '"': 139,    # double quote (was ふ)  
    '(': 140,    # open paren (was へ)
    ')': 141,    # close paren (was ほ)
    ';': 142,    # semicolon (was ま)
    '+': 143,    # plus (was み)
    '=': 144,    # equals (was む)
    '#': 145,    # hash (was め)
}
```

**Decision point:** The exact slot assignments for uppercase and punctuation depend on which Japanese characters we can safely remove. Since this is a full English patch, ALL hiragana and katakana slots can be repurposed.

---

## 3. Maximum Message Length Analysis

### MSG Resource Sizes (from msg_header_analysis.json)

| Resource | Type | File Size | Messages | Avg Bytes/Msg |
|----------|------|-----------|----------|---------------|
| 1187 | type02 | 332,320 B | 14,310 | 23.2 |
| 704 | type02 | 151,248 B | varies | - |
| 706 | type02 | 151,248 B | varies | - |
| 708 | type02 | 152,288 B | varies | - |
| 1186 | type20 | 500,328 B | 6 | 83,388 |
| 742 | type01 | 122,592 B | varies | - |
| 38 | type01 | 7,512 B | 189 | 35.7 |

### Sector Padding Analysis

Each resource in PACKDATA.DIG is sector-aligned (2048 bytes). The allocated space = sector_count * 2048 - 16 (sub-header). Examples:

| Resource | Payload Size | Sectors | Allocated | Padding Available |
|----------|-------------|---------|-----------|-------------------|
| 34 | 972 B | 34 | 69,616 B | **68,644 B (98.6% free!)** |
| 36 | 3,390 B | 2 | 4,080 B | 690 B (20.3%) |
| 690 | 72,384 B | 47 | 96,240 B | 23,856 B (32.9%) |
| 704 | 151,248 B | 83 | 170,032 B | 18,784 B (12.4%) |
| 1187 | 332,320 B | 196 | 401,392 B | **69,072 B (20.7%)** |

**KEY FINDING:** Most MSG resources have 12-33% sector padding available. This means:

- English text that is up to ~15-20% longer than Japanese will fit WITHOUT any changes to sector allocation.
- Japanese text uses 2 bytes per character (one uint16 glyph index). English text also uses 2 bytes per character (one uint16 glyph index). So character count is the relevant metric, not byte count.
- Japanese messages average ~10-15 characters per message. English equivalents will be ~15-25 characters.
- This ~50-100% increase in characters translates to ~50-100% increase in bytes.

**CRITICAL CONCERN:** The 12-20% padding is NOT enough for 50-100% text expansion. Many resources WILL overflow their sector allocation.

### Mitigation Strategies

1. **Rebuild PACKDATA.DIG:** The architecture plan already calls for a full rebuild (Phase 8). When rebuilding, each resource gets new sector allocations. Resources that grow simply get more sectors. Since the DIG file has no hardcoded internal offsets beyond the TOC, this is safe.

2. **Abbreviate aggressively:** Use short English where possible. The guide already uses abbreviations.

3. **Per-message analysis needed:** Some messages (item names, spell names) are very short in both languages. Long dialogue passages are the concern.

4. **Format A resources (with offset table):** The header contains byte offsets to each message. These offsets MUST be recalculated when message lengths change. Only 17 of 296 MSG resources use this format.

5. **Format B resources (without offset table):** 279 resources have no internal offset table. Messages are simply separated by 0xFFFF. These are easier to resize -- just rewrite the entire glyph stream and update the resource size in the TOC.

---

## 4. Architecture Plan Review

The architecture plan (`ARCHITECTURE_PLAN.md`) is thorough and already addresses reinsertion in Phase 6 and rebuilding in Phase 8. Key points relevant to reinsertion:

### Encoding Strategy (from plan)
- **Approach A (recommended):** Reuse existing glyph slots for Latin characters
- Map English letters to indices previously held by Japanese characters
- Modify font atlas to place Latin glyphs at those positions
- This is exactly what we should do, using indices 33-58 (already Latin) plus repurposed hiragana/katakana slots

### MSG Control Codes to Preserve
```
0xFFFF  - Message separator (end of message)
0xFFFE  - Line break
0xFFF9  - Wait + line break  
0xFFD2  - Page break variant 1
0xFFD3  - Page break variant 2
0xFFD4  - Page break variant 3
0xFFE0  - Format off
0xFFE1  - Format on
```

These control codes (range 0xFFC0-0xFFFF) must be preserved exactly. The encoder must:
1. Copy all control code tokens from the original message
2. Replace only glyph tokens with English glyph indices
3. Adjust line breaks (0xFFFE) for English line lengths

### Resource Sub-Header Update
When a resource changes size, the sub-header's payload_size field (LE uint32 at byte offset +4 in the sub-header) must be updated to match the new payload length.

---

## 5. Padding Space in PACKDATA.DIG Resources

### Intra-Resource Padding
As analyzed in section 3, sector-aligned padding provides 12-33% extra space within each resource's current allocation. This is insufficient for full text expansion but provides a buffer for moderate growth.

### Resource 34 Anomaly
Resource 34 (type20, font-related) has extraordinary padding: 972 bytes of payload in 34 sectors (69,632 bytes allocated). That is 98.6% free space. This suggests the resource was deliberately allocated extra space, or the sector_count includes companion data that the extractor did not capture as part of this resource's payload.

### Zero-Fill After Text
MSG resources end their glyph stream with trailing zero bytes (0x0000 pairs) that pad to the end of the payload. This zero-fill is NOT functional data -- it is padding. The game's MSG parser stops when it encounters:
1. A stream of zero bytes (0x0000), or
2. The end of the declared payload_size

This means we can freely overwrite zero padding with additional text data, as long as we update the payload_size and maintain proper message delimiters (0xFFFF).

### PACKDATA.DIG Rebuild Strategy
Since a full rebuild is planned (Phase 8), the definitive solution is:
1. Encode all translated text into new resource payloads
2. Rebuild the entire PACKDATA.DIG with new sector allocations
3. Update the TOC with new sector offsets and counts
4. The game reads resources by TOC lookup, so changed offsets are transparent

The key constraint is the sub-header's payload_size field, which tells the game how many bytes to read. This must match the actual data.

---

## 6. Reinsertion Implementation Plan

### Step 1: Build English Glyph Table
```
File: data/english_glyph_table.json
Format: { "A": 112, "B": 113, ... "a": 33, "b": 34, ... "0": 16, ... }
```

### Step 2: Modify Font Atlas (Phase 7 prerequisite)
- Replace hiragana bitmaps at indices 112-137 with uppercase A-Z glyphs
- Replace hiragana bitmaps at indices 138-145 with punctuation glyphs
- The existing lowercase a-z at indices 33-58 are already correct
- The existing digit bitmaps at indices 16-25 may need halfwidth versions

### Step 3: Encode Messages (tools/encode_msg.py)
For each MSG resource:
1. Load original resource data
2. Parse messages (split on 0xFFFF)
3. For each message, look up its translation
4. Encode translation as BE uint16 glyph index stream
5. Preserve all control codes (0xFFC0-0xFFFF range)
6. Concatenate all encoded messages with 0xFFFF separators
7. For Format A resources: rebuild the offset table header
8. Pad with zeros to fill remaining space

### Step 4: Rebuild Resources
For each modified resource:
1. Reconstruct: sequential_table + header/config + encoded_glyph_stream
2. Calculate new payload_size
3. Write to build/packdata_resources/

### Step 5: Rebuild PACKDATA.DIG (Phase 8)
- New TOC with updated sector offsets/counts
- Preserve header region (sectors 0x00-0x7C)
- Write all resources with proper sub-headers and sector alignment

---

## 7. Risks and Open Questions

### RISK: Uppercase Letters Not in Font Atlas
**Severity: HIGH, Likelihood: CERTAIN**
The font atlas must be modified before any uppercase English text can display. This is a hard blocker for reinsertion.

### RISK: Format A Offset Table Rebuild
**Severity: MEDIUM, Likelihood: CERTAIN (for 17 resources)**
Resources with BE uint16 offset tables in their headers need those tables recalculated when message sizes change. The offset table format is: `[msg_count, 0, offset_to_msg1, 0, offset_to_msg2, 0, ...]` where offsets are relative to the glyph stream start (table_end for seq-table resources, absolute for flat resources).

### RISK: Sequential Table Fields
**Severity: MEDIUM, Likelihood: UNKNOWN**
The sequential table entries contain a `field1` value that appears to be a byte size (e.g., entry [1, 5948, 560, 0] where 5948 might be the original sub-resource size). If this is a size field, it must be updated when the glyph stream in that sub-resource grows.

### RISK: Line Width Constraints
**Severity: MEDIUM, Likelihood: HIGH**
The game's text renderer has a maximum line width (likely tied to the text box width). English text must be manually line-broken (0xFFFE) to fit. The Japanese text typically has ~20 characters per line at 16px wide = 320px. English VWF could fit ~30-40 characters per line.

### OPEN QUESTION: Variable-Width Font Support
Does the game already support variable-width rendering? If it uses fixed-width (all glyphs 16px), English text will look very spaced out. The BUSIN 1 English release likely has VWF support -- compare its EXE for the text renderer code.

### OPEN QUESTION: Text Box Overflow
What happens if a message has more lines than the text box can display? The game likely uses page breaks (0xFFD2-0xFFD4) to paginate. We need to insert additional page breaks for longer English messages.
