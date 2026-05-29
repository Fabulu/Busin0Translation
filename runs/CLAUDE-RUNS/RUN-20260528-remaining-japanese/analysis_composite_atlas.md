# Composite Glyph Atlas Analysis

**Date**: 2026-05-28
**Question**: Which font atlas texture holds "composite glyphs" (IDs 480+)?

---

## CRITICAL CORRECTION: No Composite Glyphs Exist

The premise of this investigation was based on a misunderstanding. **Glyph IDs 480+ are NOT composite glyphs representing entire pre-rendered words.** They are individual kanji characters, exactly like all other glyph IDs.

### Evidence
- `msg_glyph_map.json` has 1,100 entries mapping glyph IDs 0-1747 to individual characters
- ID 480 = "回", ID 500 = "召", ID 501 = "喚" -- each is a single character
- Menu labels like "召喚" (Summon) are formed by rendering glyph 500 + glyph 501 **side by side** as two separate characters, not as one composite tile
- The EXE menu label structs (56-byte records at 0x3C3000-0x3C5300) store 2-3 individual glyph IDs per menu option, rendered individually

### Correction to FINDINGS_LEDGER
The earlier finding that "each glyph ID 480+ represents an entire pre-rendered Japanese word as a single font tile" was **WRONG**. Menu translation does NOT require replacing font texture tiles. It requires changing the glyph ID references in the EXE structs.

---

## R1272 Atlas: Confirmed Properties

| Property | Value |
|----------|-------|
| Resource | R1272 (PACKDATA index 1272, type01) |
| Format | PSMT4 (4-bit indexed, 16-color palette) |
| Dimensions | 256 x 512 pixels |
| TEX0 | TBP0=0, TBW=4, PSM=20, TW=8(256), TH=9(512) |
| Cell size | 12 x 12 pixels |
| Grid | 21 columns x 42 rows = **882 cells** (IDs 0-881) |
| File sizes | .raw = 67,584 bytes (2048 header + 65,536 pixels) |
|            | .bin = 65,792 bytes (192 GS header + 65,536 pixels + 64 palette) |

### Cell layout formula
```
col = glyph_id % 21
row = glyph_id // 21
pixel_x = col * 12
pixel_y = row * 12
```
Confirmed by EXE disassembly: multiple `addiu rX, r0, 21` + `div` + `mfhi` sequences found at VAs 0x2C22C4, 0x2FA2EC, 0x2FA364, and many others.

---

## Glyph ID Ranges in the Game

### Menu label structs (EXE 0x3C3000-0x3C5300)
- **331 unique glyph IDs**, range 475-862
- **ALL fit within the 882-cell atlas** (max ID 862 < 882)
- Zero IDs exceed 881

### Kana keyboard (EXE 0x3C83C0-0x3C93A0)
- **351 unique glyph IDs**, range varies
- Max ID: 474
- ALL fit within the atlas

### MSG dialogue text (type02 resources)
- Glyph IDs up to **~1800** appear in dialogue text
- **298 mapped glyph IDs** in msg_glyph_map.json exceed 881
- These map to individual kanji characters used in dialogue

### Special ranges
| Range | Use | Atlas |
|-------|-----|-------|
| 0-881 | Main font (kana, kanji, Latin, symbols) | R1272 |
| 2036-2047 | Equipment type labels | Separate texture (per FINDINGS_LEDGER) |
| 6400+ | Name entry tab labels | R1189 bitmap font |

---

## The ID > 881 Mystery

### The Problem
- The atlas has 882 cells (IDs 0-881)
- MSG dialogue uses IDs up to ~1800
- ID 882 would map to row 42, y=504 (atlas ends at 512)
- IDs > ~903 would wrap past the bottom of the 512px atlas

### What Doesn't Work
1. **Simple wrapping**: ID 883 wraps to position 1 (which is space " "), but the character at ID 883 is "教" -- they don't match
2. **R1270/R1271/R1273 as secondary atlases**: These are 133,120 bytes = PSMT8 256x512 textures (not PSMT4 font). Visual inspection of R1270 rendered as PSMT4 shows garbled data, not font glyphs
3. **No subtraction constant**: No `addiu rX, rY, -882` instruction found in the EXE

### Most Likely Explanation: Duplicate Glyphs + GS VRAM Tricks

**78 characters appear at BOTH low and high IDs** in msg_glyph_map.json. For example:
- "教" appears at IDs 11, 336, 396, 733, 883, 1037
- "戦" appears at IDs 286, 923, 1017, 1190
- "動" appears at IDs 290, 594, 1081, 1104

This duplication means: **the same kanji is rendered at multiple atlas positions**. The game likely uses a runtime mechanism to handle IDs > 881:

**Theory A: PS2 GS TBW allows larger VRAM texture**
- TBW=4 for PSMT4 means 512px buffer width in VRAM
- The game may upload font data to a VRAM area larger than 256x512
- By modifying TEX0 at runtime (TW=9, TH=10 for 512x1024), the game could address ~1800 cells
- The extra pixel data may come from loading multiple resources sequentially into VRAM

**Theory B: Glyph ID remapping table**
- A lookup table in VRAM or in code could remap high IDs to low positions
- No clear candidate found in the EXE data section, but the table could be generated at runtime

**Theory C (least likely): VRAM wrapping with pre-arranged duplicates**
- The developers may have arranged the atlas so that wrapped positions happen to contain the correct characters
- This would explain the many duplicate characters in the glyph map
- But the math doesn't work out (ID 883 wraps to position 1, not to a "教" cell)

---

## Impact on Translation Strategy

### Menu Translation: SOLVED
- Menu labels (EXE structs) use glyph IDs 475-862, all within the atlas
- Translation approach: **Replace glyph ID references in EXE structs** with English letter glyph IDs
- No texture tile replacement needed
- The English font atlas (build/english_font_atlas.bin) already has all needed Latin characters at IDs 0-94

### Dialogue Translation: ALREADY WORKING
- The build pipeline (build_full_english_v2.py) encodes English text using glyph IDs 0-94
- All English glyphs fit in the first 95 cells of the atlas
- The 12,725+ translated messages already use this approach successfully
- High glyph IDs (>881) are only in UNTRANSLATED Japanese messages

### Remaining Work for Menus
1. Map the **94 unmapped glyph IDs** (IDs 480-930 range) in the menu structs
2. Create an EXE patching tool to replace glyph IDs in the 56-byte structs
3. Design short English labels (1-3 chars each) for each menu option
4. Patch the EXE data section at offsets 0x3C3000-0x3C5300

### No Need to Solve the ID > 881 Mystery
Since English text only uses IDs 0-94 (all within the atlas), the high-ID glyph rendering mechanism is irrelevant for translation. The mystery of how the game renders IDs > 881 is academically interesting but not a blocker.

---

## Files Referenced
- Font atlas resource: `extracted/packdata_raw/1272_type01.raw` (67,584 bytes)
- English font atlas: `build/english_font_atlas.bin` (65,792 bytes)
- Glyph map: `data/msg_glyph_map.json` (1,100 entries, IDs 0-1747)
- English glyph table: `data/english_glyph_table.json` (95 entries, IDs 0-94)
- Atlas generator: `tools/generate_font_atlas.py`
- EXE: `extracted/SLPM_653.78`
- Menu structs: EXE offsets 0x3C3000-0x3C5300 (106 x 56-byte records)
