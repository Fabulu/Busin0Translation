# BUSIN 1 (English) vs BUSIN 0 (Japanese) Font System Cross-Reference

## Executive Summary

**BUSIN 1 (SLUS_202.59) retains the same Japanese glyph encoding as BUSIN 0 (SLPM_653.78).** The MSG files in BUSIN 1 use BE uint16 glyph indices from the same Japanese character set. The English version did NOT remap glyphs to ASCII -- it uses the original Japanese glyph index space with the font texture swapped to render English-appearing characters. However, the EXE contains separate embedded text strings (battle messages, menus) that use LE uint16 with ASCII-like glyph codes.

## 1. BUSIN 0 Font System Reference

### Font Descriptors (0x3C0700)
- **12 entries**, each 28 bytes (7 x uint32 LE)
- Entry format: `[packed_width_format] [packed_height_pos] [0] [0x80808080] [0x01000100] [0] [0]`
- Field 0: `(glyph_width << 16) | 0x0002` -- widths range 0x20-0x2C (32-44 pixels)
- Field 1: `(row << 16) | column` -- rows 0x10-0x40, cols 0x10/0x38/0x50/0x60
- Field 3: Color/alpha = 0x80808080 (constant)
- Field 4: Scale = 0x01000100 (constant)
- Entry 12 is terminator: `[0000FFFF] [0] [0] [80808080] [01000100] [0] [0]`

### Glyph Table (0x3C0870)
- **84 entries** of uint16 LE, mapping sequential index to glyph code
- Range: 0x0001 to 0x005D
- Entries 0-24: Control codes (0x01, 0x05-0x0A, 0x0D-0x1E)
- Entries 25-83: ASCII characters ! through ] (0x21-0x5D)
- Notable gap: no lowercase letters (a-z), no 0x57/0x58 (W/X skipped differently)
- After glyph table: 4 zero bytes, then 32-bit pointers (0x004Exxxx) to font texture data

## 2. BUSIN 1 Font System

### BUSIN 1 does NOT have B0-style font descriptors
- No 0x80808080 color fields in descriptor-like structures (the only 0x80808080 block is a 123-byte fill at 0x449B30)
- The 0xFFFF+0x80808080 terminator pattern from B0 is absent
- **BUSIN 1 uses a completely different font descriptor format**

### Glyph Input Tables Found at 0x4A2800
Two identical character input mapping tables (keyboard layout for name entry):
```
0x4A2808: !"#$%&'()*+,-./0123456789:  (0x21-0x3A)
          [4 padding slots = FFF9]
          ABCDEFGHIJKLMNOPQRSTUVWXYZ  (0x41-0x5A)
          [4 padding slots = FFF9]
          [control codes 0x10-0x19]
```
Second table at 0x4A28DC adds: `_[\` and additional control codes (0x01-0x1D).

These confirm the glyph codes for ASCII characters match their ASCII values.

### Proportional Width Table at 0x491B30
A large ascending glyph-to-width mapping table starting around 0x491B30:
- Maps glyph codes 0x000 through 0x11D+ to proportional widths
- Entries cover the full range of Japanese characters used in MSG files
- This is the font metrics table -- each entry defines the pixel width for rendering

### Glyph Rendering Table at 0x4B4170
A character set table listing valid renderable glyph codes:
```
0x4B4178: $0123 5:;<=>?@ABCDEFGHIJKLMNO UVWXY
0x4B41C8: ijklmnoqrstuvwxyz{|}~[7F]
```
Note the gaps -- some ASCII codes are missing (P-T, Z, a-h, p), replaced by Japanese chars at those indices.

## 3. UEDA.MSG Glyph Analysis (BUSIN 1 English)

### File: `extracted_busin1/IMAGE/EVENT/UEDA.MSG` (16,768 bytes)
- 8,384 total uint16 values (BE)
- 272 FFFF codes (line breaks)
- 343 FFFE codes (message separators)
- 7,467 non-control glyph indices
- 382 unique glyph codes used

### Frequency Distribution -- NOT English, STILL Japanese
The frequency distribution conclusively shows **Japanese text encoding**:

| Rank | Glyph | Hex    | Count | Pct   | Notes |
|------|-------|--------|-------|-------|-------|
| 1    | 64    | 0x0040 | 248   | 3.32% | '@' in ASCII = Japanese particle |
| 2    | 87    | 0x0057 | 220   | 2.95% | 'W' in ASCII = Japanese char |
| 3    | 78    | 0x004E | 201   | 2.69% | 'N' in ASCII = Japanese char |
| 4    | 618   | 0x026A | 199   | 2.67% | Beyond ASCII = Japanese kanji |
| 5    | 88    | 0x0058 | 178   | 2.38% | 'X' in ASCII = Japanese char |
| 6    | 83    | 0x0053 | 171   | 2.29% | 'S' in ASCII = Japanese char |
| 7    | 328   | 0x0148 | 168   | 2.25% | Beyond ASCII = Japanese char |
| 8    | 329   | 0x0149 | 168   | 2.25% | Beyond ASCII = Japanese char |
| 9    | 84    | 0x0054 | 165   | 2.21% | 'T' in ASCII = Japanese char |
| 10   | 107   | 0x006B | 161   | 2.16% | 'k' in ASCII = Japanese char |

**Evidence this is Japanese, not English:**
1. Top glyph frequency is only 3.32% (English space would be ~18%)
2. The distribution is flat (Japanese uses many characters at similar frequency)
3. 243 of 382 unique codes are >= 0x100 (well beyond ASCII)
4. The top-20 codes span 0x0040-0x026E -- far too wide for English

### Glyph Index Range Distribution
| Range | Unique | Occurrences | % of total |
|-------|--------|-------------|------------|
| 0x00-0x7F (ASCII) | 65 | 4,078 | 54.6% |
| 0x80-0xFF (extended) | 74 | 1,177 | 15.8% |
| 0x100-0x1FF | 142 | 1,379 | 18.5% |
| 0x200-0x3FF | 101 | 833 | 11.2% |

## 4. Embedded English Text in BUSIN 1 EXE

Separately from the MSG files, BUSIN 1's EXE contains English text as LE uint16 at 0x3B8900+:
```
"SOUL SMASH"
"SEALING VOICE"
"SPIRIT HEALING"
"DECEPTIVE SLIP"
"INDIVIDUAL ACTION"
"THE MONSTERS HAVE ATTACKED FROM BEHIND"
"SURPRISE ATTACK"
"MAKE A DECISION"
"THESE MONSTERS ARE FRIENDLY"
"FIGHT"
"LEAVE"
"SELECT THE CHARACTER'S ACTION"
"START BATTLE"
"DO YOU WISH TO START BATTLE?"
```

These use ASCII codes directly (0x0041='A', space=0x0000, 0x001D=prefix marker).

## 5. Cross-Reference: B0 vs B1 Glyph Table Overlap

Of B0's 84 glyph table entries (codes 0x0001-0x005D):
- **29 codes** also appear in B1's UEDA.MSG
- These are: `?`, `@`, `A-O`, `P-V`, `Y-Z`, `[`, `\`, `]`
- **353 codes** used by B1 MSG are NOT in B0's 84-entry table

This means B1 uses an expanded superset of glyph codes. The B0 glyph table at 0x3C0870 is only a partial view -- B0 likely has additional glyph mappings loaded from elsewhere (the font texture data pointed to by 0x004Exxxx addresses).

## 6. Key Conclusions for Fan Translation

1. **MSG format is identical**: Both games use BE uint16 glyph indices with FFFF/FFFE control codes.

2. **Glyph encoding is Japanese**: The BUSIN 1 MSG files (EVENT/*.MSG) still use Japanese glyph indices. The English translation text is stored separately in the EXE, not in the MSG files.

3. **The MSG files in BUSIN 1 contain the ORIGINAL JAPANESE TEXT**, not English translations. The English version apparently loads translated text from the EXE's embedded strings instead of (or in addition to) the MSG files.

4. **For a BUSIN 0 translation**: You would need to either:
   - (a) Modify the MSG files to use the existing glyph codes (mapping Japanese chars to English via font texture swap), OR
   - (b) Add a separate English string table in the EXE (like BUSIN 1 did), OR
   - (c) Remap the glyph table to include ASCII lowercase and modify the MSG files

5. **Font descriptor format differs**: B0 uses 28-byte descriptors with 0x80808080 color at offset+12. B1 does not have this pattern -- it uses a different structure entirely.

6. **B1's font system components**:
   - Glyph input layout tables: 0x4A2800 (character entry screen mapping)
   - Proportional width table: ~0x491B30 (glyph width metrics)
   - Character set definition: ~0x4B4170 (renderable glyph list)
   - Embedded English strings: 0x3B8900+ (battle/menu text as LE uint16)

## 7. Top 50 Glyph Comparison Table

| Rank | B1 Code | B1 Hex | B1 Count | B1 % | In B0 Table? |
|------|---------|--------|----------|------|-------------|
| 1 | 64 | 0x0040 | 248 | 3.32% | Yes (pos 56) |
| 2 | 87 | 0x0057 | 220 | 2.95% | No |
| 3 | 78 | 0x004E | 201 | 2.69% | Yes (pos 70) |
| 4 | 618 | 0x026A | 199 | 2.67% | No |
| 5 | 88 | 0x0058 | 178 | 2.38% | No |
| 6 | 83 | 0x0053 | 171 | 2.29% | Yes (pos 75) |
| 7 | 328 | 0x0148 | 168 | 2.25% | No |
| 8 | 329 | 0x0149 | 168 | 2.25% | No |
| 9 | 84 | 0x0054 | 165 | 2.21% | Yes (pos 76) |
| 10 | 107 | 0x006B | 161 | 2.16% | No |
| 11 | 103 | 0x0067 | 144 | 1.93% | No |
| 12 | 109 | 0x006D | 143 | 1.92% | No |
| 13 | 68 | 0x0044 | 140 | 1.87% | Yes (pos 60) |
| 14 | 65 | 0x0041 | 130 | 1.74% | Yes (pos 57) |
| 15 | 74 | 0x004A | 128 | 1.71% | Yes (pos 66) |
| 16 | 142 | 0x008E | 127 | 1.70% | No |
| 17 | 622 | 0x026E | 124 | 1.66% | No |
| 18 | 82 | 0x0052 | 117 | 1.57% | Yes (pos 74) |
| 19 | 81 | 0x0051 | 114 | 1.53% | Yes (pos 73) |
| 20 | 101 | 0x0065 | 109 | 1.46% | No |
| 21 | 77 | 0x004D | 88 | 1.18% | Yes (pos 69) |
| 22 | 119 | 0x0077 | 85 | 1.14% | No |
| 23 | 144 | 0x0090 | 85 | 1.14% | No |
| 24 | 204 | 0x00CC | 83 | 1.11% | No |
| 25 | 97 | 0x0061 | 79 | 1.06% | No |
| 26 | 70 | 0x0046 | 78 | 1.04% | Yes (pos 62) |
| 27 | 185 | 0x00B9 | 76 | 1.02% | No |
| 28 | 93 | 0x005D | 75 | 1.00% | Yes (pos 83) |
| 29 | 122 | 0x007A | 67 | 0.90% | No |
| 30 | 69 | 0x0045 | 66 | 0.88% | Yes (pos 61) |
| 31 | 75 | 0x004B | 66 | 0.88% | Yes (pos 67) |
| 32 | 190 | 0x00BE | 66 | 0.88% | No |
| 33 | 227 | 0x00E3 | 66 | 0.88% | No |
| 34 | 583 | 0x0247 | 65 | 0.87% | No |
| 35 | 104 | 0x0068 | 65 | 0.87% | No |
| 36 | 220 | 0x00DC | 63 | 0.84% | No |
| 37 | 231 | 0x00E7 | 63 | 0.84% | No |
| 38 | 100 | 0x0064 | 62 | 0.83% | No |
| 39 | 102 | 0x0066 | 61 | 0.82% | No |
| 40 | 72 | 0x0048 | 59 | 0.79% | Yes (pos 64) |
| 41 | 325 | 0x0145 | 58 | 0.78% | No |
| 42 | 184 | 0x00B8 | 58 | 0.78% | No |
| 43 | 108 | 0x006C | 57 | 0.76% | No |
| 44 | 80 | 0x0050 | 57 | 0.76% | Yes (pos 72) |
| 45 | 63 | 0x003F | 55 | 0.74% | Yes (pos 55) |
| 46 | 73 | 0x0049 | 55 | 0.74% | Yes (pos 65) |
| 47 | 172 | 0x00AC | 53 | 0.71% | No |
| 48 | 225 | 0x00E1 | 51 | 0.68% | No |
| 49 | 71 | 0x0047 | 50 | 0.67% | Yes (pos 63) |
| 50 | 106 | 0x006A | 47 | 0.63% | No |

Of the top 50 B1 glyphs, **21 exist in B0's 84-entry table** (all in the 0x003F-0x005D ASCII range) and **29 do not** (codes 0x0057+, 0x0065+, 0x008E+, 0x0100+, 0x0200+).
