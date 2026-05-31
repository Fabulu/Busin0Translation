# R1188 Stat Label Editor

**Date**: 2026-05-28

---

## Summary

Implemented `tools/patch_r1188_stats.py` which replaces Japanese stat label kanji
in the R1188 1024x1024 PSMT4 glyph atlas with English letters. Added to the
build pipeline in `build/build_full_english_v2.py` as Step 3b.

---

## Technical Approach

### VRAM Address Mapping

The key challenge was mapping cell coordinates (U, V, VRAM_block) to pixel
positions in the deswizzled 1024x1024 atlas. The game reads glyphs using
PSMT4 with TBW=4 (256px wide sub-atlas), while the atlas is uploaded as a
single 1024x1024 texture with dbw_ct32=512.

**Solution**: Built a reverse nibble-address map that translates any VRAM
address back to its (x, y) position in the deswizzled atlas:

```
For each pixel (x, y) in the 1024x1024 atlas:
  nibble_addr = psmt4_nibble_addr(x, y, bw=1024)
  reverse_map[nibble_addr] = (x, y)

For a cell with (U, V, VRAM_block):
  local_nib = psmt4_nibble_addr(U, V, bw=256)
  global_nib = (VRAM_block - 0xA140) * 512 + local_nib
  atlas_pos = reverse_map[global_nib]
```

This handles page-boundary wrapping correctly -- some glyphs span across
PSMT4 pages and their pixels are non-contiguous in the deswizzled view,
but the VRAM mapping resolves each pixel individually.

### Cell Data (from EXE at file offsets 0x3D8C90 - 0x3D9A00)

| Label  | Glyph ID | U | V  | VRAM   | Atlas Position | English |
|--------|----------|---|----|--------|----------------|---------|
| STR    | 346      | 1 | 60 | 0xA450 | (1, 508)       | T       |
| INT-1  | 535      | 0 | 67 | 0xA1F0 | (768, 3)       | I       |
| INT-2  | 717      | 3 | 88 | 0xA700 | (771, 728)     | Q       |
| PIE-1  | 308      | 0 | 76 | 0xA238 | (64, 140)      | P       |
| PIE-2  | 354      | 0 | 66 | 0xA390 | (384, 258)     | I       |
| PIE-3  | 320      | 0 | 62 | 0xA290 | (256, 254)     | E       |
| VIT-1  | 718      | 4 | 60 | 0xA708 | (836, 700)     | V       |
| VIT-2  | 696      | 3 | 67 | 0xA658 | (195, 643)     | I       |
| AGI-1  | 582      | 0 | 60 | 0xA2E0 | (640, 188)     | A       |
| AGI-2  | 719      | 4 | 61 | 0xA710 | (772, 765)     | G       |
| AGI-3  | 590      | 0 | 60 | 0xA318 | (832, 252)     | I       |
| LCK-1  | 720      | 4 | 62 | 0xA718 | (836, 766)     | L       |
| LCK-2  | 721      | 4 | 63 | 0xA720 | (900, 703)     | C       |

### Shared Glyph Constraints

Two glyphs are shared between stat labels:
- **Glyph 346** (chikara/power): Used as the SOLE glyph for STR, AND as the 3rd glyph of VIT
- **Glyph 590** (do/degree): Used as the 3rd glyph of AGI AND the 3rd glyph of LCK

Since one glyph cell can only have one rendering, compromises are necessary:

| Stat | Japanese | English Display | Notes |
|------|----------|-----------------|-------|
| STR  | power    | T               | Compromise: shared glyph renders 'T' (from VIT) |
| INT  | wisdom   | IQ              | "Intelligence Quotient" -- fits perfectly |
| PIE  | faith    | PIE             | Piety |
| VIT  | vitality | VIT             | Correct: shared glyph 'T' completes it |
| AGI  | agility  | AGI             | Correct: shared glyph 'I' completes it |
| LCK  | luck     | LCI             | Compromise: shared glyph renders 'I' (from AGI) |

### Glyph Cell Size

Each glyph occupies approximately 20x20 pixels in the atlas. The cell data
has W=100 (percentage width) and the rendering quad on screen is determined
by the game's sprite rendering code (approximately 20px per kanji).

---

## Files

| File | Purpose |
|------|---------|
| `tools/patch_r1188_stats.py` | Main implementation |
| `tools/patch_r1188_direct.py` | Pre-existing tab label patcher (Kana/Hira/ABC/Sym etc.) |
| `tools/psmt4_deswizzle.py` | PSMT4 deswizzle/swizzle functions |
| `build/build_full_english_v2.py` | Build pipeline (Step 3b calls both R1188 patchers) |

### Output Files

| File | Description |
|------|-------------|
| `build/packdata_resources/1188_type01.raw` | Patched atlas (sector-aligned) |
| `build/textures_to_edit/R1188_stat_labels_patched.png` | Full atlas debug view |
| `build/textures_to_edit/R1188_stat_closeups.png` | VRAM-mapped closeup of all 13 glyphs |

---

## Build Integration

Added to `build/build_full_english_v2.py` after Step 3 (font atlas injection):

```python
# STEP 3b -- Patch R1188 kanji atlas (name-entry labels + stat labels)
os.system('python tools/patch_r1188_direct.py')   # tab labels
os.system('python tools/patch_r1188_stats.py')     # stat labels (stacks on top)
```

The stat label patcher detects if a previously-patched file exists at the
output path and uses it as the base, so both patches stack correctly.

---

## Future Improvements

1. **EXE cell data patching**: Redirect shared glyphs (346, 590) to dedicated
   atlas positions, eliminating the STR='T' and LCK='LCI' compromises.
   This requires patching 8 bytes per cell at known EXE offsets.

2. **Multi-character cells**: Render full abbreviations (e.g., "STR") within
   a single 20px glyph cell using a smaller font size.

3. **Wider glyph approach**: If the game's rendering quad is larger than 20px
   per cell, expand GLYPH_W to fill the actual rendered area.
