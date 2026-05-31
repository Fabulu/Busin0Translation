# Phase 6-7: Status Screen (27-6) and Confirmation (27-7) Analysis

**Date**: 2026-05-28
**Save states**: 27-6.p2s (status screen), 27-7.p2s (confirmation popup)
**ISO**: BUSIN0_EN_v27.iso (built 2026-05-31 20:08, save states captured ~21:08)

---

## Screenshot Observations

### 27-6 (Status Screen)
- **Banner**: "New Registration" (chargen) -- texture-rendered, still Japanese
- **Header**: "Status" in italic -- pre-rendered graphic
- **HP/MAX 19 19** -- rendered in English via glyph system
- **Stat labels**: All JAPANESE -- 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度
- **Stat values**: Correct numerals (26, 7, 3, 7, 6, 7)
- **Sidebar labels**: All JAPANESE -- 性別, 種族, 属性, 職業
- **Sidebar values**: MIXED -- 男 (Japanese), Human (English!), Fighter (English!)
- **Personality section**: "Personality" header English, "Wary" English, "Sadist" English
- **Personality descriptions**: English but Sadist description overflows/gets cut off

### 27-7 (Confirmation Popup)
- Same underlying status screen as 27-6
- Popup overlay: "Allocate stat points." -- English
- "Bonus Point" label visible below -- partially English
- Background shows same Japanese stat labels and English values

---

## GS Texture Analysis

### Single Font Atlas -- All Text Uses Same Texture

All text on this screen (both Japanese labels and English values) renders through the **same PSMT4 256x256 font atlas** in VRAM:

| Field | Value |
|-------|-------|
| TBP0 | 0x2840 (VRAM byte addr 0x284000) |
| Format | PSMT4 (4-bit indexed, 16 colors) |
| Size | 256x256 pixels |
| CBP | 0x28C0 (CLUT base) |
| Usage count | 144 TEX0 writes in DMA buffer |

Other textures present in the rendering pass:
- TBP0=0x3000 PSMT4 256x512 -- UI background/frame elements (44 uses)
- TBP0=0x3327 PSMT4 256x256 -- Additional UI elements (60 uses)
- TBP0=0x2A68 PSMT4 256x256 -- Character portrait (45 uses)
- TBP0=0x319F PSMT4 256x256 -- Decorative frame (13 uses)
- TBP0=0x3220 PSMT4 512x256 -- Large UI panel (44 uses)

**Key finding**: There is NO separate texture for Japanese vs English text. Both the Japanese stat labels (力, 知恵, etc.) and the English values (Human, Fighter, Wary) are drawn from TBP0=0x2840. The issue is NOT a texture switching problem.

### Comparison: 27-6 vs 27-7

Both save states have identical TEX0 configurations. The 27-7 confirmation popup uses the same font atlas (TBP0=0x2840) for its "Allocate stat points." text.

---

## R38 Translation Verification

### R38 IS English in RAM

The R38 MSG resource loaded at EE address 0x00E14090 contains **English** translations, matching the v27 ISO exactly:

| MSG | Original | Built (in RAM) | On Screen |
|-----|----------|---------------|-----------|
| 1 | hp{NL}{END} | hp{END} | HP/MAX (English) |
| 3 | 力{NL}{END} | str{END} | 力 (JAPANESE!) |
| 4 | 知恵{NL}{END} | int{END} | 知恵 (JAPANESE!) |
| 5 | 信仰心{NL}{END} | fth{END} | 信仰心 (JAPANESE!) |
| 6 | 生命力{NL}{END} | vit{END} | 生命力 (JAPANESE!) |
| 7 | 敏捷度{NL}{END} | agi{END} | 敏捷度 (JAPANESE!) |
| 8 | 幸運度{NL}{END} | lck{END} | 幸運度 (JAPANESE!) |
| 9 | 名前{NL}{END} | nAME{END} | (not visible) |
| 11 | 種族{NL}{END} | rACE{END} | 種族 (JAPANESE!) |
| 12 | 性別{NL}{END} | gENDER{END} | 性別 (JAPANESE!) |
| 14 | 職業{NL}{END} | cLASS{END} | 職業 (JAPANESE!) |
| 30 | 人間{NL}{END} | hUMAN{END} | Human (English) |
| 38 | 戦士{NL}{END} | fIGHTER{END} | Fighter (English) |
| 54 | 武{NL}{END} | cOWARD{END} | (Wary on screen) |

**Full payload verified**: The 8,652-byte R38 payload in EE RAM at 0x00E14090 is a byte-for-byte match with the v27 ISO's PACKDATA.DIG R38 resource.

### Encoding Issues Found

1. **Missing trailing {NL}**: The original R38 messages end with `glyphs FFFE FFFF` ({NL}{END}), but the built versions end with `glyphs FFFF` ({END} only). The missing FFFE newline before the terminator could affect the renderer's message parsing.

2. **Mixed-case glyph IDs**: The encoder outputs first character as lowercase (glyph 33-58 = a-z) but remaining characters use unmapped uppercase IDs (0x41-0x5A = 65-90). These uppercase glyph IDs are NOT in msg_glyph_map.json but DO render correctly on screen (Human, Fighter, Wary all display properly).

3. **Uppercase glyphs work**: Despite being "unmapped" in msg_glyph_map.json, glyph IDs 65-90 clearly render as A-Z on screen. The font atlas HAS uppercase Latin at those positions. These glyphs are just missing from the mapping file.

---

## Root Cause Analysis: WHY Labels Show Japanese

### The Paradox

- R38 in RAM has English stat labels (str, int, fth, vit, agi, lck)
- The same R38 has English race/class/personality names (Human, Fighter, Wary)
- Race/class/personality VALUES render in English
- Stat LABELS and sidebar LABELS render in Japanese
- All text uses the same font atlas (TBP0=0x2840)

### Hypothesis: The chargen/status screen uses TWO rendering paths

**Values** (race name, class name, personality) are drawn by the glyph text renderer, which reads from R38 messages and produces English output correctly.

**Labels** (stat names, sidebar field names) appear to NOT read from R38 at runtime. Instead, they likely use one of:

1. **Pre-rendered glyph slot cache**: The status screen may pre-compute and cache glyph slot arrays at initialization time. If the cache was populated from the original Japanese R38 before patching, the labels would remain Japanese. However, the save state was captured from a fresh boot of the v27 ISO, so this is unlikely.

2. **EXE Table 2C menu struct records** (0x3C3000-0x3C52FF): These 160 records use pre-rendered font tile IDs (0x025F-0x0376 range) baked into the font atlas. If the stat labels are drawn using these tile IDs rather than R38 glyph streams, they would always show Japanese regardless of R38 content. This is the most likely explanation.

3. **The label text uses a DIFFERENT R38 message index path**: The chargen rendering code might use hardcoded glyph ID arrays in the EXE for stat/sidebar labels, while using R38 MSG indices only for values. An EXE table at 0x3C2244 contains the sequence [2, 3, 4, 5, 6, 7, 8, 10, 13, 14, 15, ...] which maps to R38 stat label indices -- but this might only be used for VALUE rendering, not LABEL rendering.

### Most Likely Root Cause: **Menu struct tile rendering (Table 2C)**

The status/chargen screen labels (力, 知恵, 性別, 種族, etc.) are rendered using the **EXE's menu struct system** which references pre-rendered font tiles baked into the font atlas texture. These tiles are at glyph IDs 0x025F+ (604+) in the atlas and contain Japanese-only artwork. Translating these requires:

1. Identifying which Table 2C records correspond to each status screen label
2. Redrawing the font atlas tiles at those positions with English text
3. OR replacing the tile IDs in Table 2C with composable glyph IDs (if the rendering system supports it)

This explains why:
- Values use R38 glyph streams (composable, English-patchable) -> English
- Labels use baked font tiles (pre-rendered Japanese artwork) -> Japanese
- Both use the same VRAM texture (TBP0=0x2840) but different regions of it

---

## Character Data Structure (Bonus Finding)

Character stats found at EE address 0x0055DD20:

| Offset | Field | Value |
|--------|-------|-------|
| +0x00 | Name glyphs | 0x42 'B', 0x41 'A', then FFFF padding |
| +0x1E | Unknown | 0x01 |
| +0x24 | Flags/type | 0x0200 |
| +0x26 | Level? | 0x071B |
| +0x28 | STR | 26 |
| +0x2A | INT | 7 |
| +0x2C | FTH | 3 |
| +0x2E | VIT | 7 |
| +0x30 | AGI | 6 |
| +0x32 | LCK | 7 |
| +0xB8 | HP current | 19 |
| +0xBA | HP max | 19 |
| +0xBC | HP bonus? | 19 |

---

## Overflow Issue: Sadist Description

The "Sadist" personality description overflows its text box on the status screen. The description text reads: "Thrives in hardship Being healed or helped feels worse" -- this is too long for the rendering area. The text gets cut off at the bottom of the screen.

**Root cause**: The English personality descriptions (from R38 MSG 88-116) are longer than the original Japanese. The description rendering area has a fixed height of approximately 3 lines, and the English text exceeds this.

**Fix needed**: Shorten personality descriptions to fit in 3 lines at the current glyph width, OR implement word-wrapping that respects the available height.

---

## Action Items

### P0: Fix R38 Encoding Issues
1. **Add trailing {NL}**: The encoder must append 0xFFFE before 0xFFFF in every R38 message, matching the original format
2. **Fix mixed-case encoding**: Use consistent glyph IDs (either all lowercase 33-58 or add uppercase 65-90 support)
3. **Add uppercase glyph mappings**: Add A-Z (glyph IDs 65-90) to msg_glyph_map.json

### P1: Translate Status Screen Labels
The stat/sidebar labels (力, 知恵, 性別, etc.) are NOT from R38 -- they come from pre-rendered font tiles in the EXE's menu struct system. To translate:
1. Map Table 2C records to specific screen labels
2. Identify which font atlas tile IDs correspond to each label
3. Redraw those tiles in the font atlas with English equivalents
4. OR patch the EXE to use composable glyph rendering instead of tile rendering for these labels

### P2: Fix Personality Description Overflow
1. Audit all 29 personality descriptions for length
2. Shorten to fit in 3 lines at 12-pixel glyph width
3. Test rendering in the chargen status screen

---

## Files Referenced

- `RAMdumps/27-6.p2s` -- Status screen save state
- `RAMdumps/27-7.p2s` -- Confirmation popup save state
- `extracted/packdata_raw/0038_type01.raw` -- Original R38 (7,512 bytes)
- `build/packdata_resources/0038_type01.raw` -- Patched R38 (8,652 bytes)
- `build/BUSIN0_EN_v27.iso` -- Built ISO with patched R38
- `extracted/SLPM_653.78` -- Game EXE with Table 2C at 0x3C3000
- `data/msg_glyph_map.json` -- Glyph ID to character mapping
- `data/translate_chunks/chunk_01_translated.json` -- R38 stat label translations
- `data/translate_chunks/chunk_r38_fix.json` -- R38 fix translations
