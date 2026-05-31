# R1188 Comprehensive Patcher

## Overview

`tools/patch_r1188_comprehensive.py` is the single consolidated patcher for the R1188 name-entry / character-creation screen atlas. It replaces the three previous partial scripts (`patch_r1188_direct.py`, `patch_r1188_overwrite.py`, `patch_r1188_tabs.py`) and handles ALL needed edits in one pass.

## What R1188 Is

R1188 is a 1024x1024 PSMT4 (4-bit palettized) texture atlas used by the name-entry and character-creation screens. It stores:
- **Rows 0-1**: ASCII characters (numbers, punctuation, A-Z, a-z)
- **Rows 2-3**: Hiragana keyboard characters
- **Rows 4-5**: Katakana keyboard characters
- **Rows 6-42** (y=144-1008): ~850 kanji used for composing UI labels at runtime
- **Rows 42-43** (y=1008-1024): Mostly empty space

The game draws label sprites (tab labels, stat names, etc.) by composing individual kanji from this atlas at runtime, not from pre-rendered label textures.

## File Format

| Field | Value |
|-------|-------|
| Format | PSMT4 (4bpp, 16 palette entries) |
| Dimensions | 1024x1024 |
| Header | 3072 bytes (0xC00) in .bin; +0x10 outer container in .raw |
| Pixel data | 524,288 bytes |
| Deswizzle params | `dbw_ct32=512`, `bw_psmt4=1024` |
| Round-trip | Verified exact byte match |

## Three Phases of Patching

### Phase 1: Kana Cell Overwriting (106 cells)

Replaces hiragana and katakana glyphs with their romaji equivalents directly in the atlas. This makes the on-screen keyboard grid show English characters instead of Japanese.

| Row | Y range | Content | Cells |
|-----|---------|---------|-------|
| 2 left | 48-71 | Hiragana a-so | 15 |
| 3 left | 72-95 | Hiragana ya-zo | 20 |
| 4 left | 96-119 | Small kana + Katakana A-Chi | 21 |
| 4 right | 96-119 | Katakana Tu-Mo | 18 |
| 5 left | 120-143 | Katakana Ra-Du | 20 |
| 5 right | 120-143 | Katakana De-Po | 12 |

Each cell is cleared to index 0 (transparent) then the romaji text is rendered with Consolas 11pt, centered, using palette indices 0-15.

### Phase 2: Bottom-Row English Labels (16 labels at y=1009-1020)

Pre-renders English label sprites into the empty bottom rows of the atlas. These are positioned for potential future EXE UV-redirect patching.

Labels rendered:
- **Sidebar**: Gender, Class, Race, Align
- **Tabs**: (overlap with sidebar in current layout)
- **Buttons**: OK, M.Name, F.Name, Delete, Clear
- **Banner**: New Character
- **Stats**: Strength, IQ, Piety, Vitality, Agility, Luck

### Phase 3: PCSX2 Texture Replacements (16 PNGs)

Creates PCSX2-format texture replacement PNG files for emulator-based overlay. These are white-on-transparent RGBA images with alpha quantized to PS2's 16 levels.

| Type | Dimensions | Count | Examples |
|------|-----------|-------|----------|
| Tab labels | 48x20 | 8 | Kana, Hira, ABC, Sym, Gender, Class, Race, Align |
| Buttons | 40x24 | 1 | OK |
| Title banner | 120x24 | 1 | New Character |
| Stat labels | 64x16 | 6 | Strength, IQ, Piety, Vitality, Agility, Luck |

Output directory: `build/pcsx2_texture_replacements/`

## Build Integration

The patcher is called from `build/build_v9.py` at Step 3.6:
```
os.system('python tools/patch_r1188_comprehensive.py')
```

## Input/Output

- **Input**: `extracted/packdata_resources/1188_type01.bin` (preferred) or `extracted/packdata_raw/1188_type01.raw`
- **Output**: `build/packdata_resources/1188_type01.raw` (sector-padded to 528,384 bytes)
- **Debug images**: `build/textures_to_edit/R1188_patched_*.png`

## Verification

- Round-trip test: deswizzle -> edit -> reswizzle -> deswizzle = exact match on all pixels (PASS)
- Full build v9: completed successfully with R1188 comprehensive patcher integrated
- Output file size: 528,384 bytes (sector-aligned, matches original)

## Previous Scripts (Superseded)

| Script | What it did | Status |
|--------|------------|--------|
| `patch_r1188_tabs.py` | PCSX2 replacements + raw file copy | Superseded |
| `patch_r1188_direct.py` | PCSX2 replacements + bottom-row labels | Superseded |
| `patch_r1188_overwrite.py` | Kana cell overwriting + bottom labels | Superseded |
| **`patch_r1188_comprehensive.py`** | **All of the above in one pass** | **Active** |
