# xref52-party: Party Member Names in EE RAM

**Date:** 2026-05-22
**Save State:** normaldungeonscreen.p2s
**Output:** data/xref_party.json

---

## Executive Summary

Party member names were found stored as uint16 LE arrays in EE RAM character structs. The name encoding uses an internal grid-position numbering system, NOT glyph indices directly. For basic katakana (46 chars), the formula `glyph_size0 = name_value - 95` converts name values to glyph indices. For extended characters (dakuten, small kana, chouon, vu), the glyph indices could NOT be determined from RAM alone -- they require font atlas visual identification.

---

## Key Findings

### 1. Name Storage Format

Character names are stored as arrays of 8 x uint16 (little-endian), with unused slots filled with 0xFFFF. Names are NOT stored as SJIS, Unicode, EUC-JP, or raw glyph indices. They use an internal "name value" encoding tied to the name entry grid position.

### 2. Memory Locations

**Guild Roster (all created characters):**
- Base address: 0x55DD22 (name of first character)
- Struct stride: 0x3E0 (992 bytes)
- Level field offset from name: 0xBA (186 bytes after name start)

**Active Party / NPC Array:**
- Example base: 0x5601F2
- Struct stride: 0x1F0 (496 bytes)
- Level field offset: 0xBA (same as guild roster)

### 3. Name Encoding System

For basic katakana (46 characters, grid positions 0-45):
- `name_value = grid_position + 193`
- `glyph_index_size0 = name_value - 95` (equivalent to grid_position + 98)
- Exception: katakana N (grid position 45, name_value 238) maps to glyph 97

For extended characters (dakuten, handakuten, small kana):
- `name_value = grid_position + 193` still applies
- But glyph indices are NOT a simple offset; they map to different regions of the font atlas

For the chouon (long vowel mark):
- name_value = 93 (does NOT follow the grid_position + 193 formula)
- This character appears to be on a separate page in the name entry system

### 4. Decoded Party Members

| # | Name | Values | Known Glyphs | Class | Lv |
|---|------|--------|--------------|-------|-----|
| 1 | ia | [194, 193] | [99, 98] -- all known | FIG | 21 |
| 2 | ve-ra | [273, 270, 93, 231] | [?vu, ?small_e, ?chouon, 136] | KNI | 27 |
| 3 | konde | [202, 238, 252] | [107, 97, ?de] | MAG | 14 |
| 4 | basuko- | [254, 205, 202, 93] | [?ba, 110, 107, ?chouon] | FIG | 21 |
| 5 | e-rika | [196, 93, 232, 198] | [101, ?chouon, 137, 103] | PRI | 15 |
| 6 | furi-jia | [220, 232, 93, 245, 193] | [125, 137, ?chouon, ?ji, 98] | PRI | 16 |

### 5. Unknown Glyph Indices (6 characters)

| Character | Name Value | Grid Pos | Base Char |
|-----------|-----------|----------|-----------|
| chouon (long vowel mark) | 93 | special | n/a |
| ba (dakuten ha) | 254 | 61 | ha (glyph 123) |
| ji (dakuten shi) | 245 | 52 | shi (glyph 109) |
| de (dakuten te) | 252 | 59 | te (glyph 116) |
| small e | 270 | 77 | e (glyph 101) |
| vu (dakuten u) | 273 | 80 | u (glyph 100) |

These 6 glyphs exist somewhere in the font atlas (indices 0-857) but their specific indices cannot be determined from RAM data alone. They are NOT in the documented glyph_map_partial.json range.

### 6. What Was NOT Found

- Party names are NOT stored as SJIS (confirmed zero hits for all 6 names)
- Party names are NOT stored as Unicode (confirmed zero hits)
- Party names are NOT stored as glyph indices in any standard uint16/uint32 format
- The name entry table at 0x4C99B0-0x4C9CE0 only contains basic katakana and hiragana glyph tuples, NOT dakuten/extended characters

---

## Method

1. Extracted EE RAM (32 MB) from the PCSX2 save state (ZIP format, eeMemory.bin)
2. Searched for all possible encodings of party names (SJIS, Unicode, glyph indices as uint16 LE/BE, uint32, byte sequences)
3. Discovered that comparing fight1.p2s and normaldungeonscreen.p2s reveals character level fields (level 24 vs 27 for vera)
4. Found the level pattern [27, 27, 27] at 0x5602AC, traced back to name field at offset -0xB8
5. Decoded the name encoding by cross-referencing known characters across multiple party members
6. Verified the grid_position + 193 formula against all known basic katakana characters

---

## Implications

1. **To find the 6 unknown glyph indices:** Need to either (a) trace the game's name rendering code in the EXE disassembly, or (b) visually identify the dakuten/special characters in the font atlas PNG renders
2. **The name encoding system is a complete closed system:** The game stores names using internal IDs, converts them to glyph indices for rendering, and the conversion logic is in the EXE code
3. **For translation:** Character names will need to be re-encoded using the same name_value system, with appropriate glyph indices for the replacement font atlas
