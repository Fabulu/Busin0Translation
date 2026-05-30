# MASTER LIST: All Japanese Text in PCSX2 Texture Dumps

**Date**: 2026-05-28
**Methodology**: Comprehensive visual inspection of all 411 PCSX2 texture dumps
**Verified by**: Full-image review of every CLUT group and every full-atlas dump

---

## SUMMARY

| Category | Count | Status |
|----------|-------|--------|
| Total PCSX2 dumps analyzed | 411 | Complete |
| Dumps containing Japanese text | 17 | Identified |
| Dumps containing English text (no action) | ~30 | Already English |
| Dumps that are art/icons/UI frames (no text) | ~364 | Cleared |
| Demo-only textures (never shown in retail) | 5 (R2118-R2122) | LOWEST priority |

---

## SECTION 1: CONFIRMED JAPANESE TEXT TEXTURES

### 1A. Character Creation/Status Tab Labels (16 labels)

- **Source CLUT**: `3cb39bf7659ef15f`
- **VRAM page**: 0x2214
- **PACKDATA resource**: R1188 (PSMT4 1024x1024, name entry UI atlas)
- **Format**: White semi-transparent text (alpha=128) on transparent background
- **Editable**: YES (PSMT4 deswizzle pipeline working)
- **Priority**: HIGH (visible on every character creation and status screen)

| # | Filename | Size | Japanese | English | Notes |
|---|----------|------|----------|---------|-------|
| 1 | `16625baf...-r48x20-00002214.png` | 48x20 | 性 (sei) | Gender | Tab label |
| 2 | `19a39fbc...-r48x20-00002214.png` | 48x20 | 記号 (kigou) | Symbols | Name entry tab |
| 3 | `88ff8b57...-r48x20-00002214.png` | 48x20 | 職業 (shokugyou) | Class | Tab label |
| 4 | `9bec87b4...-r48x20-00002214.png` | 48x20 | 種族 (shuzoku) | Race | Tab label |
| 5 | `1f839869...-r48x20-00002214.png` | 48x20 | カナ (kana) | Kana | Name entry tab |
| 6 | `6f1fb24f...-r48x20-00002214.png` | 48x20 | 英数 (eisuu) | A-Z/0-9 | Name entry tab |
| 7 | `9677cb23...-r48x20-00002214.png` | 48x20 | かな (kana) | Hiragana | Name entry tab |
| 8 | `c89b469f...-r48x20-00002214.png` | 48x20 | 属性 (zokusei) | Alignment | Tab label |
| 9 | `5d0c6327...-r64x16-00002214.png` | 64x16 | 敏捷度 (binshoudo) | Agility | Stat label |
| 10 | `aa43f966...-r64x16-00002214.png` | 64x16 | 生命力 (seimeiryoku) | Vitality | Stat label |
| 11 | `4841ef9a...-r64x16-00002214.png` | 64x16 | 幸運度 (kouundo) | Luck | Stat label |
| 12 | `bb20512b...-r64x16-00002214.png` | 64x16 | 信仰心 (shinkoushin) | Piety | Stat label |
| 13 | `d455234204...-r64x16-00002214.png` | 64x16 | 知恵 (chie) | Wisdom | Stat label |
| 14 | `280ea82c...-r64x16-00002214.png` | 64x16 | 力 (chikara) | Strength | Stat label |
| 15 | `f2013a64...-r64x16-00002214.png` | 64x16 | HP/MAX | HP/MAX | Already English |
| 16 | `d09a04bd...-r40x24-00002214.png` | 40x24 | 決定 (kettei) | Confirm | Button label |

**Action required**: Edit R1188 PSMT4 atlas to replace 15 Japanese labels with English equivalents. HP/MAX is already fine.

---

### 1B. Guild Screen Header (1 label)

- **Source CLUT**: `e786e0650b284c64`
- **VRAM page**: 0x2214
- **PACKDATA resource**: R1188 or separate sub-region of same atlas
- **Format**: White semi-transparent text on transparent background
- **Editable**: YES (same PSMT4 atlas as 1A)
- **Priority**: HIGH (visible every time guild screen opens)

| # | Filename | Size | Japanese | English |
|---|----------|------|----------|---------|
| 1 | `a2d3fce3...-r120x24-00002214.png` | 120x24 | 新規登録 (shinki touroku) | New Registration |

---

### 1C. In-World 3D Sign Textures (2 signs)

- **VRAM page**: 0x1dd3 (dungeon environment textures)
- **Format**: 128x128 RGBA environment texture with baked text on signs
- **Editable**: Theoretically yes (edit raw texture bytes), but very difficult
- **Priority**: LOW (small text on 3D signs, barely readable in-game)

| # | Filename | Size | Japanese/Text | English | Notes |
|---|----------|------|---------------|---------|-------|
| 1 | `25a723d0...-00001dd3.png` | 128x128 | ギルド (guild) on diamond sign | Guild | Very small text on 3D object |
| 2 | `ff5bd5bc...-00001dd3.png` | 128x128 | Decorative lettering on sign | ADVENTURERS(?) | May already be stylized English |

**Action required**: LOW priority. These are 3D environment model textures. The text is very small in-game and would require locating the exact resource, decoding the 3D model texture, editing individual pixels, and re-encoding. Not worth the effort for a fan translation.

---

## SECTION 2: RUNTIME-RENDERED JAPANESE TEXT (NOT texture edits)

### 2A. Narration Text Overlay Lines (25 lines)

- **Source CLUT**: `be78468b72d277cd`
- **VRAM page**: 0x2654
- **What these are**: The game engine renders Japanese text strings at runtime using the main font atlas (R1272, 24x24 glyphs). These dumps captured the rendered output in VRAM, not a source texture.
- **Content**: Story narration fragments ("死霊に取り憑かれた", "ドゥーハン王国を血と恐怖に", etc.)
- **Fix method**: These are already handled by the MSG text translation pipeline (type-2 resources). When the translated MSG data is injected, these will render in English automatically.
- **Priority**: N/A (already addressed by text translation, not a texture problem)

### 2B. EXE Table 2C Menu Button Labels (not captured in dumps)

- **What**: Camp menu, equipment menu, shop menu button labels are rendered from glyph ID pairs hardcoded in the EXE at offset 0x3C3000
- **Fix method**: Replace glyph tiles in R1272 font atlas + patch EXE spacing tables
- **Priority**: HIGH (M1 in REMAINING_WORK.md -- 62 additional glyph IDs needed)

---

## SECTION 3: DEMO DISC TEXTURES (retail players never see these)

- **Resources**: R2118-R2122
- **Content**: Demo version disclaimers, trial version notices, "Now on sale!" advertisement
- **Priority**: LOWEST (confirmed demo-only, not shown in retail game)

| Resource | Format | Content |
|----------|--------|---------|
| R2118 | PSMT8 512x512 | "This disc contains a trial version..." disclaimer |
| R2119 | PSMT8 512x64 | "Not compatible with PS2 memory cards" notice |
| R2120 | PSMT8 512x64 | "Enjoy the rest in the retail version" |
| R2121 | PSMT8 512x512 | Full-game advertisement with price |
| R2122 | PSMT8 512x64 | "Demo Version" label |

---

## SECTION 4: TEXTURES CONFIRMED CLEAR (No Japanese Text)

### Already English (no action needed)
| CLUT | Content | Count |
|------|---------|-------|
| `29f5bda4efe25375` | Chargen headers: Race, Name, Gender, Personality, Attribute, Class&Parameter, Status | 7 |
| `c3a3794aa961b0e8` | "Bonus Point", decorative numbers 1-9 | 11 |
| `c6cd31dd61d9b711` | "Duhan - The Imperial City" | 1 |
| Various 00001613 | "New Game", "Press START button" | 3 |
| `46c150f63aead96` | Copyright notice | 1 |
| `48b49f82950d9907` | "BUSIN0 Wizardry Alternative NEO" title logo | 1 |
| `6ebaf383420d9be2` | "Racjin" developer logo | 1 |
| `aa98f608c1efd1e1` | "ATLUS" logo | 1 |
| `3e45bbd4820ff3a2` | Demo texture atlas (English: "Treasure", "Battle", etc.) | 1 |
| `da9362fc4980d364` | "FIG" label | 1 |
| `f2013a64...(3cb39bf7)` | "HP/MAX" | 1 |

### Pure Art/Environment (no text at all)
| Category | Count | VRAM Pages |
|----------|-------|------------|
| Dungeon wall/floor textures | 28 | 0x1dd3 |
| Scene backgrounds | 7 | 0x2653 |
| NPC/character portraits | 7 | 0x2213 |
| Environment textures (clouds, trees) | 12 | 0x1993, 0x1994, 0x19d3, 0x1e13 |
| Status/buff icons (16x16) | 117 | 0x2214 |
| Font atlas glyph tiles (24x24) | 35 | 0x2a94 |
| Minimap/compass icons | 35 | 0x2a94 |
| Particle effects (fire, smoke) | 29 | 0x2214 |
| Digit/number glyphs (10x16) | 24 | 0x2214 |
| UI frames/borders (no text) | 30 | 0x1e14, 0x2254, 0x2614 |
| Decorative numbers (16x40) | 11 | 0x1dd4 |
| Cursor/arrow icons | 12 | 0x2614, 0x1980 |
| Framebuffer dumps (near empty) | 2 | 0x2a80 |
| Gradient bars (no text) | 6 | 0x2214 |

---

## SECTION 5: ACTION PLAN

### Immediate (blocks release)
1. **Edit R1188** to replace 15 Japanese tab/stat/button labels with English (Section 1A + 1B)
   - This is already tracked as **M3 in REMAINING_WORK.md**
   - PSMT4 deswizzle pipeline is working and round-trip verified

### Already Handled (no additional texture work)
2. **Narration text** (Section 2A) -- handled by MSG translation pipeline
3. **Menu button labels** (Section 2B) -- handled by R1272 font atlas + EXE table patches (M1)

### Skip
4. **Demo disc textures** (Section 3) -- never shown to retail game players
5. **3D sign textures** (Section 1C) -- too small/difficult to edit for minimal impact

---

## CONCLUSION

**Only 1 texture resource needs manual editing: R1188** (the name entry / character creation UI atlas). It contains 16 pre-rendered Japanese labels (15 needing translation + 1 already English). This is the ONLY remaining pre-rendered Japanese text that retail game players will see.

Everything else is either:
- Already in English
- Rendered at runtime (handled by text translation pipeline)
- Demo-only content (never displayed)
- Art/environment textures (no text)
- 3D environment signs (too small to matter)
