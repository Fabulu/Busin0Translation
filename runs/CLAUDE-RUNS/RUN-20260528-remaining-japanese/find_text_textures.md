# Pre-Rendered Japanese Text Texture Analysis
**Date**: 2026-05-28
**Source**: 411 PCSX2 texture dumps cross-referenced with PACKDATA manifest

---

## PCSX2 Dump Summary

411 texture dumps analyzed. Filename format: `{texhash}-{cluthash}-r{W}x{H}-{TEX0}.png`

### All Unique CLUT Groups (sorted by dump count)

| CLUT Hash | Dumps | Rect Sizes | TEX0 | Full Atlas | Content |
|-----------|-------|------------|------|------------|---------|
| `2396a88fd6b4cb36` | 117 | 16x16 | 00002214 | 256x256 | **Status/buff icons** (16x16 grid) |
| `2f77f3ea806d10cb` | 35 | 24x24 | 00002a94 | 24x24 | **Minimap/compass icons** |
| `be78468b72d277cd` | **25** | 72-336 x 24 | 00002654 | **512x512** | **JAPANESE TEXT STRINGS** -- narration overlay |
| `3cb39bf7659ef15f` | **16** | 48x20, 64x16, 40x24 | 00002214 | 256x256 | **JAPANESE TAB/BUTTON LABELS** |
| `8cef486a60d73b78` | 16 | 64x64 | 00002214 | 256x256 | Character portrait icons |
| `5426a3daf294bef2` | 12 | 64x64 | 00002214 | 256x256 | Character portrait icons |
| `c3a3794aa961b0e8` | 11 | 16x40, 90x56 | 00001dd4 | 128x128 | Decorative numbers (1-9), "Bonus Point" (English) |
| `e5121c8caf7d1dd` | 10 | 10x16 | 00002214 | 256x256 | Tiny digit/symbol glyphs |
| `83b395554335bd47` | 10 | 8-10x16 | 00002214 | 256x256 | Tiny digit/symbol glyphs |
| `29f5bda4efe25375` | 7 | 88-248 x 48-56 | 00002254 | 512x256 | Chargen headers (already English: Race, Name, Gender, etc.) |
| `2c185630146e6fea` | 5 | 0x20, 16x16, 96x36 | 00001e14 | 256x20 | Button background frames (no text) |
| `8b8569d0ffa6521e` | 5 | 10x16 | 00002214 | 256x256 | Tiny digit/symbol glyphs |
| `2ffb6918c12c256e` | 5 | 32x32 | 00002614 | 32x32 | Arrow/cursor icons |
| `71c19dc32b6d752a` | 5 | 0x20, 16x16, 96x36 | 00001e14 | 256x20 | Button background frames |
| `4143b4401f775695` | 5 | 0x20, 16x16, 96x36 | 00001e14 | 256x20 | Button background frames |
| `7b27dfe35dd96f6` | 5 | 16x16 | 00002214 | 256x256 | Small icons |
| `743772910fc165a` | 4 | 0x120, 24x56, 32x56 | 00002254 | 512x256 | UI frames |
| `704c26684dbf9175` | 4 | 16x16 | 00002214 | 256x256 | Small icons |
| `47c4ff7756c15630` | 4 | 16x112, 24x24, 56x40, 88x38 | 00001dd4 | 128x128 | Vertical scroll/stat elements |
| `73d6533c7af7f8fd` | 4 | 0x32, 128x32, 128x160, 176x24 | 00002214 | 256x256 | Button bg, gradient bars |
| `e786e0650b284c64` | **1** | 120x24 | 00002214 | 256x256 | **"新規登録" (New Registration) -- JAPANESE** |
| `d19edd380a0f085b` | 1 | 176x24 | 00002214 | 256x256 | Gradient bar (no text) |
| `da9362fc4980d364` | 1 | 32x12 | 00002214 | 256x256 | "FIG" label |
| Various 00001dd3 | 28 | (full atlas) | 00001dd3 | 128x128 | Dungeon wall/floor textures |
| Various 00002653 | 9 | (full atlas) | 00002653 | 512x512 | Character art, logos, backgrounds |
| Various 00002213 | 7 | (full atlas) | 00002213 | 256x256 | NPC portraits |
| Various 00001993 | 7 | (full atlas) | 00001993 | 64x64 | Small env textures |

---

## Confirmed Japanese Text Textures

### Atlas 1: Narration Text Overlay (512x512 PSMT4/PSMT8)
- **CLUT**: `be78468b72d277cd`
- **TEX0**: `00002654` (TBP0 = GS VRAM 0x2654)
- **Dump count**: 25 unique text strings
- **Rect height**: All exactly 24px (variable width 72-336px)
- **Content**: Pre-rendered Japanese narrative text strings
  - Examples: "死霊に取り憑かれた", "ドゥーハン王国を血と恐怖に", "地上から消えていたであろう。", "バンクーー", "の戦役と", "である", "かつて"
- **Purpose**: TextEventImage intro slideshow / story narration overlays
- **Likely PACKDATA resource**: **R2118** (263,360 bytes, PSMT8 512x512) -- confirmed via GS header parse and grayscale dump shows text-like patterns at expected positions

### Atlas 2: Tab/Button Labels (256x256 PSMT4)
- **CLUT**: `3cb39bf7659ef15f`
- **TEX0**: `00002214` (TBP0 = GS VRAM 0x2214)
- **Dump count**: 16 labels
- **Rect sizes**: 48x20 (8 dumps), 64x16 (7 dumps), 40x24 (1 dump)
- **Content**: Small Japanese labels for UI tabs/buttons
  - Tab labels for name entry screen (ひらがな, カタカナ, etc.)
  - Menu button labels
- **Purpose**: Name entry tabs, UI button labels
- **Likely PACKDATA resource**: One of the 256x256 PSMT4 resources near R2124 or R2548
  - **R2124** (33,808 bytes, PSMT4 256x256, multi-packet GS header with 6 sections) -- camp/dungeon menu overlay
  - **R2548** (34,880 bytes, PSMT4 256x256, 16-section GS header) -- UI element atlas with icons

### Atlas 3: Guild Screen "新規登録" Label
- **CLUT**: `e786e0650b284c64`
- **TEX0**: `00002214`
- **Dump count**: 1
- **Rect size**: 120x24
- **Content**: "新規登録" (New Registration) -- guild header text
- **Likely PACKDATA resource**: **R2121** (263,360 bytes, PSMT8 512x512) -- guild cockpit background

---

## Confirmed CockpitImg Resources with Japanese Text

These were already identified in REMAINING_JAPANESE.md Section 3, confirmed here:

| Resource | Size | Format | Content | Japanese Text |
|----------|------|--------|---------|---------------|
| **R2118** | 263,360 B | PSMT8 512x512 | Bar/Tavern background | "酒場" header + text overlay strings |
| **R2119** | 33,984 B | PSMT8 512x64 | Bar button sheet (normal) | 依頼, 王国掲示板, 達成履歴, トラップゲーム, 外に出る |
| **R2120** | 33,984 B | PSMT8 512x64 | Bar button sheet (selected) | Same as R2119, alternate state |
| **R2121** | 263,360 B | PSMT8 512x512 | Guild background | "新規登録" header |
| **R2122** | 33,984 B | PSMT8 512x64 | Guild button sheet | Guild menu options |
| **R2124** | 33,808 B | PSMT4 256x256 | Camp/dungeon menu overlay | Possibly contains tab labels |

---

## Other Texture Resources Checked (NO Japanese Text)

| Resource Area | Size | Content | Verdict |
|--------------|------|---------|---------|
| R1215-R1270 (132-263KB) | 132,288 / 263,360 B | Scene background textures | Environment art, no text |
| R1274-R1346 (263KB) | 263,328-263,360 B | Scene backgrounds | Environment art, no text |
| R1330-R1346 (263KB) | 263,360 B | Scene backgrounds (17 resources) | Art only |
| R1900 | 263,360 B | PSMT8 512x512 | Unknown scene, likely art |
| R2545-R2547 (66.7KB) | 66,720 B | PSMT8 256x256 | NPC/monster portraits |
| R2662-R2773 (132KB x 112) | 132,288 B | PSMT8 256x512 | Monster/character textures |
| R2777-R2876 (66.7KB x 103) | 66,720 B | PSMT8 256x256 | Monster/character portraits |
| R2123 | 736 B | Tiny resource | Cursor/icon, too small for text |
| R2125 | 308 B | Tiny resource | Cursor/icon |

---

## PCSX2 Dumps Already in English (No Action Needed)

| CLUT | Content | Status |
|------|---------|--------|
| `29f5bda4efe25375` | "Race", "Name", "Gender", "Personality", "Attribute", "Class&Parameter", "Status" | Already English |
| `c3a3794aa961b0e8` | "Bonus Point", decorative numbers 1-9 | Already English |
| `c6cd31dd61d9b711` | "Duhan - The Imperial City" | Already English |
| Various 00001613 | "New Game", "Press START button" | Already English |
| `46c150f63aead96` | Copyright notice (Atlus, 1259190 Ontario) | Already English |
| `48b49f82950d9907` | "BUSIN0 Wizardry Alternative NEO" title logo | Already English |
| `6ebaf383420d9be2` | "Racjin" developer logo | Already English |
| `aa98f608c1efd1e1` | "ATLUS" logo | Already English |

---

## Equipment Type Icons (Glyph IDs 2036-2047)

The user asked about equipment type icons at glyph IDs 2036-2047. These are NOT in the PCSX2 dumps (they would be from the main glyph font atlas, R1272 or R1188). Since glyph IDs 2036-2047 fall outside the main MSG glyph range (0-858) and outside the bitmap font range (6400+), they likely:
- Come from R1188 (1024x1024 PSMT4 font atlas, 527,360 bytes) -- the large font atlas
- Or are rendered by a different text system not captured in these dumps

**Action needed**: Examine R1188 to determine if it contains equipment type icon glyphs in the 2036-2047 range.

---

## Compass HUD Directions

No compass-related textures were identified in the PCSX2 dumps. The compass direction labels (N, S, E, W or 北, 南, 東, 西) may be:
1. Rendered via the MSG glyph system (not pre-rendered textures)
2. Part of a 3D cockpit model texture not captured in these dumps
3. Hardcoded in the EXE as glyph IDs

---

## Summary: All PACKDATA Resources Requiring Japanese Text Replacement

| Priority | Resource | Format | Japanese Content | Action |
|----------|----------|--------|-----------------|--------|
| HIGH | **R2118** | PSMT8 512x512 | Narration text overlay + bar header | Replace 25 text strings with English |
| HIGH | **R2119** | PSMT8 512x64 | Bar menu buttons | Replace 5 button labels |
| HIGH | **R2120** | PSMT8 512x64 | Bar menu buttons (selected) | Replace 5 button labels |
| HIGH | **R2121** | PSMT8 512x512 | Guild header "新規登録" | Replace header text |
| HIGH | **R2122** | PSMT8 512x64 | Guild menu buttons | Replace button labels |
| MEDIUM | **R2124** | PSMT4 256x256 | Camp/menu overlay (possibly tab labels) | Dump and verify content |
| MEDIUM | **R2548** | PSMT4 256x256 | UI element atlas (possibly tab labels) | Dump and verify content |
| LOW | **R1188** | PSMT4 1024x1024 | Equipment type icons (glyph 2036-2047) | Identify and replace if Japanese |

**Total confirmed Japanese text texture resources: 5 (R2118-R2122)**
**Total suspected: 2-3 more (R2124, R2548, R1188)**
**Resources checked and cleared: ~300+ (art/environment/portraits/icons)**
