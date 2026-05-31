# PCSX2 Texture Dump Cross-Reference: R1188 Atlas Labels

**Date**: 2026-05-28
**Source**: 411 PCSX2 texture dumps in `build/pcsx2_dumps/`
**Method**: Visual identification of each unique texture hash against rendered content

---

## Executive Summary

All stat labels, tab labels, sidebar labels, and button labels on the chargen/status
screens render from a single VRAM page at **TBP0 0x2214** using texture data from
**R1188** (PACKDATA resource 1188, 1024x1024 PSMT4 atlas).

The PCSX2 dumps capture the correctly-rendered sub-rects. Each dump's filename encodes:
`<texture_hash>-<clut_hash>-r<W>x<H>-<TBP0>.png`

### CRITICAL BUG FOUND

**`patch_r1188_direct.py` has ALL 6 stat label hash-to-English mappings WRONG.**
Every hash was assigned the wrong English translation. The PCSX2 texture replacement
PNGs currently show the wrong stat name for each label. See corrected mapping below.

---

## 1. Tab Labels (48x20, CLUT 3cb39bf7659ef15f, TBP0 0x2214)

From R1188 glyph IDs 6400-6403. Used on name entry screen (Phase 1) and sidebar
on later chargen phases.

| Texture Hash | Japanese | English | Glyph ID | Phases |
|---|---|---|---|---|
| `1f839869fab251d` | カナ | Kana | 6400 | 1 |
| `9677cb23da53ff88` | かな | Hira | 6401 | 1 |
| `6f1fb24fad5cd1a` | 英数 | ABC | 6402 | 1 |
| `19a39fbc8a08d7ec` | 記号 | Sym | 6403 | 1 |
| `16625baf9feaeafb` | 性別 | Gender | (sidebar) | 2-8 |
| `88ff8b577084a2a8` | 職業 | Class | (sidebar) | 5-8 |
| `9bec87b4031a7172` | 種族 | Race | (sidebar) | 3-8 |
| `c89b469f7a152a6` | 属性 | Align | (sidebar) | 4-8 |

**PCSX2 replacement filename pattern**: `<tex_hash>-3cb39bf7659ef15f-r48x20-00002214.png`

---

## 2. Stat Labels (64x16, CLUT 3cb39bf7659ef15f, TBP0 0x2214)

**CORRECTED MAPPING** (visually verified from PCSX2 dumps):

| Texture Hash | Japanese | Correct English | R38 MSG | OLD (WRONG) Mapping |
|---|---|---|---|---|
| `280ea82c1c476a98` | 力 | **Strength** | 2 | ~~Luck~~ |
| `4841ef9a2dc4981` | 幸運度 | **Luck** | 7 | ~~Agility~~ |
| `5d0c6327e20384e7` | 敏捷度 | **Agility** | 6 | ~~Vitality~~ |
| `aa43f966ad69195e` | 生命力 | **Vitality** | 5 | ~~Piety~~ |
| `bb20512b10c3128b` | 信仰心 | **Piety** | 4 | ~~IQ~~ |
| `d455234204274c43` | 知恵 | **IQ** | 3 | (missing from script) |
| `f2013a64642252e3` | HP/MAX | HP/MAX (no change) | 0 | ~~Strength~~ |

**PCSX2 replacement filename pattern**: `<tex_hash>-3cb39bf7659ef15f-r64x16-00002214.png`

### What was wrong in patch_r1188_direct.py

The `STAT_LABELS_64x16` dictionary had these incorrect assignments:
```python
# WRONG (current):
STAT_LABELS_64x16 = {
    '280ea82c1c476a98': 'Luck',      # Actually: Strength (力)
    '4841ef9a2dc4981':  'Agility',   # Actually: Luck (幸運度)
    '5d0c6327e20384e7': 'Vitality',  # Actually: Agility (敏捷度)
    'aa43f966ad69195e': 'Piety',     # Actually: Vitality (生命力)
    'bb20512b10c3128b': 'IQ',        # Actually: Piety (信仰心)
    'f2013a64642252e3': 'Strength',  # Actually: HP/MAX (already English!)
}
# ALSO MISSING: 'd455234204274c43' = IQ (知恵)
```

```python
# CORRECT:
STAT_LABELS_64x16 = {
    '280ea82c1c476a98': 'Strength',
    '4841ef9a2dc4981':  'Luck',
    '5d0c6327e20384e7': 'Agility',
    'aa43f966ad69195e': 'Vitality',
    'bb20512b10c3128b': 'Piety',
    'd455234204274c43': 'IQ',
    'f2013a64642252e3': 'HP/MAX',  # Already English, no replacement needed
}
```

---

## 3. Buttons (40x24, CLUT 3cb39bf7659ef15f, TBP0 0x2214)

| Texture Hash | Japanese | English | Glyph ID |
|---|---|---|---|
| `d09a04bdfaf715bc` | 決定 | OK | 6405 |

**PCSX2 replacement filename**: `d09a04bdfaf715bc-3cb39bf7659ef15f-r40x24-00002214.png`

---

## 4. Misc Individual Kanji (16x16, TBP0 0x2214)

### CLUT 704c26684dbf9175

| Texture Hash | Japanese | Meaning | Context |
|---|---|---|---|
| `1b8fa74c8853adcb` | 認 | recognize | Part of 認定 (certification) |
| `1dc85194d22b511d` | 著 | notable | Unknown UI context |
| `53b738ee19b51dae` | 終 | end | Part of 終了 (finish/end) |
| `e742ffb05429e377` | 男 | male | Gender indicator |

### CLUT 7b27dfe35dd96f6

| Texture Hash | Japanese | Meaning | Context |
|---|---|---|---|
| `730fb2bfbf32dfb9` | ボ | bo (katakana) | Part of ボーナス (bonus) |
| `91e79f7dd702b019` | 女 | female | Gender indicator |
| `d3f77f1d275ecfc5` | 悪 | evil | Alignment indicator |
| `d5eb01e8ac2c251a` | 移 | transfer | Part of 移動 (move) or 移す (transfer) |
| `d96bd5d703558b3` | 名 | name | Part of 名前 (name) |

---

## 5. Already-English Elements (no translation needed)

### Decorative Script Headers (TBP0 0x2254, CLUT 29f5bda4efe25375)

Pre-rendered italic script textures, already in English in the original game:

| Texture Hash | Text | Dimensions |
|---|---|---|
| `a88fcdae2ff0841a` | Level | 48x18 |
| `38ce26466e6a2bbf` | Race | 88x48 |
| `6f2abc1deb57e0c8` | Name | 108x48 |
| `abfc67e538bcc9cb` | Gender | 120x48 |
| `2a8ff3a569686d02` | Attribute | 152x48 |
| `ea3022ab9e542ca0` | Personality | 168x48 |
| `fc4f5e514acaf7af` | Status | 168x56 |
| `f841bd94a2e1e7a8` | Class&Parameter | 248x48 |

### Latin Glyphs (TBP0 0x2A94, CLUT 2f77f3ea806d10cb)

35 unique 24x24 Latin alphabet letters (a-z, A-Z, digits) used for character name
display. These are from R1189 or a related resource uploaded to VRAM page 0x2A94
(within the R1188 VRAM range 0x2840-0x2D56). Already English.

### Kana Grid (TBP0 0x2214, CLUT 2396a88fd6b4cb36)

117 unique 16x16 character tiles for the name entry keyboard. Includes hiragana,
katakana, Latin letters, and symbols. Intentionally Japanese for kana input modes.

---

## 6. VRAM Page Map

| TBP0 | Hex | Content | Source Resource | Translation Status |
|---|---|---|---|---|
| 0x1554 | 5460 | Unknown full-page | Unknown | -- |
| 0x1613 | 5651 | Unknown full-page | Unknown | -- |
| 0x1980 | 6528 | Unknown full-page | Unknown | -- |
| 0x1993 | 6547 | Full-page captures | Unknown | -- |
| 0x1994 | 6548 | Full-page captures | Unknown | -- |
| 0x19D3 | 6611 | Full-page captures | Unknown | -- |
| 0x1DD3 | 7635 | Full-page captures (backgrounds) | Unknown | -- |
| 0x1DD4 | 7636 | "Bonus Point" labels (16x40), digits | Unknown | Already English |
| 0x1E13 | 7699 | Full-page captures | Unknown | -- |
| 0x1E14 | 7700 | Small icons, misc UI (16x16) | Unknown | -- |
| 0x2213 | 8723 | Misc textures | Unknown | -- |
| **0x2214** | **8724** | **R1188 atlas: tabs, stats, sidebar, kana, panels** | **R1188** | **NEEDS TRANSLATION** |
| 0x2253 | 8787 | Misc textures | Unknown | -- |
| **0x2254** | **8788** | **Decorative headers (Race, Name, etc.)** | **Unknown (not R1188)** | **Already English** |
| 0x2613 | 9747 | Misc textures | Unknown | -- |
| 0x2614 | 9748 | Medium icons (32x32) | Unknown | -- |
| 0x2640 | 9792 | Misc | Unknown | -- |
| 0x2653 | 9811 | Full-page captures | Unknown | -- |
| 0x2654 | 9812 | Story banners (Nx24) | Separate resource | Different task |
| **0x2A80** | **10880** | **Full screen composites (513x449)** | **R1188 VRAM range** | -- |
| **0x2A94** | **10900** | **Latin glyphs (24x24)** | **R1188 VRAM range** | **Already English** |

### R1188 VRAM Range

R1188 is a 1024x1024 PSMT4 texture = 64 pages = 2048 TBP0 units.
If uploaded starting at TBP0 0x2214, it spans 0x2214 to 0x2A13 (ends just before 0x2A14).
TBP0 0x2A80 and 0x2A94 are slightly OUTSIDE this range, suggesting either:
- R1188 base is slightly lower than 0x2214
- R1189 data is uploaded to a nearby page
- The GS re-configures TEX0 at runtime to read overlapping VRAM regions

---

## 7. JSON Cross-Reference

```json
{
  "tab_labels": {
    "1f839869fab251d":  {"jp": "カナ",   "en": "Kana",   "glyph": 6400, "size": "48x20"},
    "9677cb23da53ff88": {"jp": "かな",   "en": "Hira",   "glyph": 6401, "size": "48x20"},
    "6f1fb24fad5cd1a":  {"jp": "英数",   "en": "ABC",    "glyph": 6402, "size": "48x20"},
    "19a39fbc8a08d7ec": {"jp": "記号",   "en": "Sym",    "glyph": 6403, "size": "48x20"},
    "16625baf9feaeafb": {"jp": "性別",   "en": "Gender", "glyph": null, "size": "48x20"},
    "88ff8b577084a2a8": {"jp": "職業",   "en": "Class",  "glyph": null, "size": "48x20"},
    "9bec87b4031a7172": {"jp": "種族",   "en": "Race",   "glyph": null, "size": "48x20"},
    "c89b469f7a152a6":  {"jp": "属性",   "en": "Align",  "glyph": null, "size": "48x20"}
  },
  "stat_labels": {
    "280ea82c1c476a98": {"jp": "力",     "en": "Strength", "r38_msg": 2, "size": "64x16"},
    "d455234204274c43": {"jp": "知恵",   "en": "IQ",       "r38_msg": 3, "size": "64x16"},
    "bb20512b10c3128b": {"jp": "信仰心", "en": "Piety",    "r38_msg": 4, "size": "64x16"},
    "aa43f966ad69195e": {"jp": "生命力", "en": "Vitality",  "r38_msg": 5, "size": "64x16"},
    "5d0c6327e20384e7": {"jp": "敏捷度", "en": "Agility",   "r38_msg": 6, "size": "64x16"},
    "4841ef9a2dc4981":  {"jp": "幸運度", "en": "Luck",      "r38_msg": 7, "size": "64x16"},
    "f2013a64642252e3": {"jp": "HP/MAX", "en": "HP/MAX",   "r38_msg": 0, "size": "64x16", "note": "already English"}
  },
  "buttons": {
    "d09a04bdfaf715bc": {"jp": "決定",   "en": "OK",   "glyph": 6405, "size": "40x24"}
  },
  "misc_kanji_704c": {
    "1b8fa74c8853adcb": {"jp": "認", "en": "cert.",    "size": "16x16"},
    "1dc85194d22b511d": {"jp": "著", "en": "notable",  "size": "16x16"},
    "53b738ee19b51dae": {"jp": "終", "en": "end",      "size": "16x16"},
    "e742ffb05429e377": {"jp": "男", "en": "M",        "size": "16x16"}
  },
  "misc_kanji_7b27": {
    "730fb2bfbf32dfb9": {"jp": "ボ", "en": "Bo",       "size": "16x16"},
    "91e79f7dd702b019": {"jp": "女", "en": "F",        "size": "16x16"},
    "d3f77f1d275ecfc5": {"jp": "悪", "en": "evil",     "size": "16x16"},
    "d5eb01e8ac2c251a": {"jp": "移", "en": "move",     "size": "16x16"},
    "d96bd5d703558b3":  {"jp": "名", "en": "name",     "size": "16x16"}
  },
  "common_params": {
    "tbp0": "0x2214",
    "clut_tab_stat": "3cb39bf7659ef15f",
    "clut_misc_704c": "704c26684dbf9175",
    "clut_misc_7b27": "7b27dfe35dd96f6"
  }
}
```

---

## 8. Pixel Region Summary

Since R1188 deswizzle is currently broken (dbw_ct32=512 produces garbled output),
we cannot determine exact pixel coordinates within the raw R1188 file.

**What we DO know**:
- All labels share TBP0 0x2214, meaning they come from the same VRAM region
- The GS reads sub-rects of the 1024x1024 atlas using UV coordinates set by the EXE
- UV coordinates are stored in a BSS runtime table at VA 0x4EBBE0 (populated when R1188 loads)
- The EXE function at VA 0x494050 resolves glyph IDs 6400+ via this table
- Each entry in the BSS table is 16 bytes: `{u16 page_ref, ..., u32 position_data, u16 size_data}`

**What we NEED to determine pixel positions**:
1. Correct deswizzle parameters for R1188 (try more DBW values, or trace the DMA upload code)
2. OR: extract UV register values from PCSX2 GS state dumps during rendering
3. OR: reverse-engineer the BSS table population code to find the UV mapping

**Workaround (proven working)**: PCSX2 texture replacement via hash-matched PNGs
bypasses the need to know pixel positions entirely. The replacement PNGs are placed
in `build/pcsx2_texture_replacements/` with the exact hash-based filenames.

---

## File References

| Item | Path |
|---|---|
| PCSX2 texture dumps | `build/pcsx2_dumps/` |
| R1188 raw data | `extracted/packdata_raw/1188_type01.raw` |
| R1188 patcher (HAS BUGS) | `tools/patch_r1188_direct.py` |
| PCSX2 replacement output | `build/pcsx2_texture_replacements/` |
| Contact sheet: tabs | `build/pcsx2_dumps/tabs_all_alpha.png` |
| Contact sheet: stats | `build/pcsx2_dumps/stat_labels_identified.png` |
| Contact sheet: kana grid | `build/pcsx2_dumps/kana_grid.png` |
| Contact sheet: headers | `build/pcsx2_dumps/headers_0x2254.png` |
| Contact sheet: banners | `build/pcsx2_dumps/banners_0x2654.png` |
