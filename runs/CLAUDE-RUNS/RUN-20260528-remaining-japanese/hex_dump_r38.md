# R38 Raw Byte Verification: Original JP vs v29 EN

**Date:** 2026-05-28

## Summary

| ISO | English msgs | Japanese msgs | Other/empty |
|-----|-------------|--------------|-------------|
| Original JP | 47/189 | 133/189 | 9 |
| v29 Patched | **184/189** | **2/189** | 3 |

**VERDICT: R38 in v29 ISO contains English glyphs, NOT Japanese.**

The v29 patched ISO has successfully replaced 131 Japanese messages with English.
Only 2 messages (msg[25] and msg[26]) remain as Japanese glyph indices.

### Notes on glyph display
- The glyph indices are BE 16-bit. Values 0x0021-0x007E map to the ASCII portion
  of the game's font texture (but shifted -- e.g. 0x21='A' not '!', 0x33='S' not '3').
- So `3ORCERY` actually renders as "Sorcery", `$IVINE` as "Divine", `.AME` as "Name", etc.
- Values >= 0x0100 are Japanese kanji/kana in the original font table.

---

```
# Raw hex dump data
# Glyph indices are BIG-ENDIAN 16-bit values
# ASCII-range (0x0021-0x007E) = English glyphs
# High range (>=0x0100) = Japanese glyphs

======================================================================
  ORIGINAL ISO (Japanese)
======================================================================
PACKDATA.DIG LBA: 16029
R38 sector offset: 1965, size: 4 sectors (8192 bytes)
R38 data: 8192 bytes total

--- First 208 bytes ---
  0000: 00 00 00 00 58 1D 00 00 10 00 00 00 00 00 00 00  |....X...........|
  0010: 00 BC 00 00 02 F4 00 00 02 FC 00 00 03 0C 00 00  |................|
  0020: 03 12 00 00 03 1A 00 00 03 24 00 00 03 2E 00 00  |.........$......|
  0030: 03 38 00 00 03 42 00 00 03 4A 00 00 03 54 00 00  |.8...B...J...T..|
  0040: 03 5C 00 00 03 64 00 00 03 6C 00 00 03 74 00 00  |.\...d...l...t..|
  0050: 03 7C 00 00 03 8A 00 00 03 96 00 00 03 A0 00 00  |.|..............|
  0060: 03 AA 00 00 03 B4 00 00 03 BE 00 00 03 C8 00 00  |................|
  0070: 03 D2 00 00 03 DC 00 00 03 E6 00 00 03 EC 00 00  |................|
  0080: 03 F2 00 00 03 FA 00 00 04 06 00 00 04 0E 00 00  |................|
  0090: 04 18 00 00 04 22 00 00 04 2E 00 00 04 3A 00 00  |.....".......:..|
  00A0: 04 4A 00 00 04 50 00 00 04 56 00 00 04 5E 00 00  |.J...P...V...^..|
  00B0: 04 66 00 00 04 70 00 00 04 78 00 00 04 80 00 00  |.f...p...x......|
  00C0: 04 86 00 00 04 8E 00 00 04 96 00 00 04 A2 00 00  |................|

First FFFF at offset 0x302 (770)
Pre-FFFF region = 770 bytes = offset/header table

--- Message content (BE 16-bit glyph indices) ---
--- First 30 messages ---
  msg[0] [EN] = (0\n
  msg[1] [EN] = (0{000F}-(0\n
  msg[2] [JP] = {015A}\n
  msg[3] [JP] = {0217}{02CD}\n
  msg[4] [JP] = {0134}{0162}{0140}\n
  msg[5] [JP] = {02CE}{02B8}{015A}\n
  msg[6] [JP] = {0246}{02CF}{024E}\n
  msg[7] [JP] = {02D0}{02D1}{024E}\n
  msg[8] [JP] = {013A}{01FE}\n
  msg[9] [JP] = {00EA}{0101}{00E9}\n
  msg[10] [JP] = {0201}{0202}\n
  msg[11] [JP] = {01FF}{0200}\n
  msg[12] [JP] = {0203}{01FF}\n
  msg[13] [JP] = {01F8}{0205}\n
  msg[14] [JP] = {01FF}{0204}\n
  msg[15] [JP] = {0118}{0156}{0157}{0118}{0146}\n
  msg[16] [JP] = {02D6}{02D7}{0118}{0146}\n
  msg[17] [JP] = {02BC}{015A}{02C7}\n
  msg[18] [EN] = ,V{0011}\n
  msg[19] [EN] = ,V{0012}\n
  msg[20] [EN] = ,V{0013}\n
  msg[21] [EN] = ,V{0014}\n
  msg[22] [EN] = ,V{0015}\n
  msg[23] [EN] = ,V{0016}\n
  msg[24] [EN] = ,V{0017}\n
  msg[25] [JP] = {0206}\n
  msg[26] [JP] = {015D}\n
  msg[27] [??] = {00C2}{00C5}\n
  msg[28] [JP] = {00C4}{00C3}{00EB}{0103}\n
  msg[29] [JP] = {013F}{0207}\n

--- Full file statistics ---
  Total messages: 189
  English: 47
  Japanese: 133
  Other/empty: 9


======================================================================
  v29 PATCHED ISO (English)
======================================================================
PACKDATA.DIG LBA: 16029
R38 sector offset: 1971, size: 5 sectors (10240 bytes)
R38 data: 10240 bytes total

--- First 208 bytes ---
  0000: 00 00 00 00 24 1E 00 00 10 00 00 00 00 00 00 00  |....$...........|
  0010: 00 BC 00 00 02 F4 00 00 02 FA 00 00 03 08 00 00  |................|
  0020: 03 10 00 00 03 18 00 00 03 20 00 00 03 28 00 00  |......... ...(..|
  0030: 03 30 00 00 03 38 00 00 03 42 00 00 03 4E 00 00  |.0...8...B...N..|
  0040: 03 58 00 00 03 66 00 00 03 72 00 00 03 7E 00 00  |.X...f...r...~..|
  0050: 03 8C 00 00 03 9C 00 00 03 AA 00 00 03 B6 00 00  |................|
  0060: 03 BE 00 00 03 C6 00 00 03 CE 00 00 03 D6 00 00  |................|
  0070: 03 DE 00 00 03 E6 00 00 03 EE 00 00 03 F2 00 00  |................|
  0080: 03 F6 00 00 03 FC 00 00 04 0A 00 00 04 16 00 00  |................|
  0090: 04 1E 00 00 04 2A 00 00 04 36 00 00 04 44 00 00  |.....*...6...D..|
  00A0: 04 52 00 00 04 58 00 00 04 5E 00 00 04 6E 00 00  |.R...X...^...n..|
  00B0: 04 7A 00 00 04 84 00 00 04 92 00 00 04 9E 00 00  |.z..............|
  00C0: 04 AE 00 00 04 BC 00 00 04 CC 00 00 04 DA 00 00  |................|

First FFFF at offset 0x302 (770)
Pre-FFFF region = 770 bytes = offset/header table

--- Message content (BE 16-bit glyph indices) ---
--- First 30 messages ---
  msg[0] [EN] = (0
  msg[1] [EN] = (0{000F}-(0
  msg[2] [EN] = 342
  msg[3] [EN] = ).4
  msg[4] [EN] = &4(
  msg[5] [EN] = 6)4
  msg[6] [EN] = !')
  msg[7] [EN] = ,#+
  msg[8] [EN] = .AME
  msg[9] [EN] = ,EVEL
  msg[10] [EN] = 2ACE
  msg[11] [EN] = 'ENDER
  msg[12] [EN] = !LIGN
  msg[13] [EN] = #LASS
  msg[14] [EN] = 'ENDER
  msg[15] [EN] = 3ORCERY
  msg[16] [EN] = $IVINE
  msg[17] [EN] = 3TATS
  msg[18] [EN] = ,V{0011}
  msg[19] [EN] = ,V{0012}
  msg[20] [EN] = ,V{0013}
  msg[21] [EN] = ,V{0014}
  msg[22] [EN] = ,V{0015}
  msg[23] [EN] = ,V{0016}
  msg[24] [EN] = ,V{0017}
  msg[25] [JP] = {0206}
  msg[26] [JP] = {015D}
  msg[27] [EN] = )O
  msg[28] [EN] = %UROPA
  msg[29] [EN] = (UMAN

--- Full file statistics ---
  Total messages: 189
  English: 184
  Japanese: 2
  Other/empty: 3
```
