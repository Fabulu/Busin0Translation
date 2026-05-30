# Equipment Type Icon Sprite Analysis

**Date**: 2026-05-28

## Summary

The equipment type icon sprites (glyph IDs 2035-2086) are NOT stored in a single font atlas texture. They are rendered via a **3D scene/sprite system** using four cooperating PACKDATA resources:

| Resource | Type | Size | Role |
|----------|------|------|------|
| **R2155** | 10 | 35,456 | GS texture setup (16 TEX0_1 entries, PSMT4 256x256) |
| **R2156** | 16 | 66,720 | Texture pixel data (PSMT8 256x256 sub-textures, 15 pages) |
| **R2157** | 17 | 3,368 | Model/mesh descriptors (31 sub-resource TOC) |
| **R2159** | 32 | 10,756 | Scene container (31 sub-resources: transforms, models, animations) |

The primary texture resource is **R2156**, which contains the actual pixel data for the equipment icon sprites as PSMT8 256x256 texture pages.

---

## Evidence Chain

### 1. Icon Animation Table (EXE 0x3F9CF0)

52 icons, each with 4 variant entries (16 bytes per icon):
- Glyph IDs 2035-2086 (contiguous)
- Format: `{u16 variant, u16 glyph_id}` x 4
- Variants: {normal=0, normal-dup=0, hover=1, pressed=2}

### 2. EXE Code Path (VA 0x001901C0)

The function at VA 0x001901C0 (file 0x090240) is a state machine handling icon display:

| State | Code VA | Action |
|-------|---------|--------|
| 0 | 0x00190210 | Load R2159 sub-resource 1 via `combine(0x086F0000, 1)` + `get_data()`, initialize sprite system via `0x004862F0` |
| 1 | 0x00190248 | Wait for animation completion check via `0x004865E0` |
| 2 | 0x00190268 | Retrieve R2159 data, call rendering pipeline (`0x0047E8A0`, `0x00127060`, `0x00126798`) |
| 3 | 0x001902C0 | Pass icon animation table (VA 0x004F9C70) to display-list builder `0x00120E20`, reset state |

### 3. Resource Acquisition

At VA 0x004981A0, a compact init function acquires both resources together:
```
jal acquire()   ; R2157 (0x086D) - model descriptors
jal acquire()   ; R2159 (0x086F) - scene container
```

R2156 is acquired separately at VA 0x0013D298, with its own state machine that also calls `0x00120E20` (the same display-list builder used for icons).

### 4. Item Glyph Base Table (EXE 0x3B38EA)

130 entries mapping item categories to base glyph IDs:
- Range: 1604-2394
- Step: ~7 per entry (7 animation sub-sprites per category)
- Equipment type icons at entries 60-67: base glyphs 2036, 2043, 2050, 2057, 2064, 2071, 2078, 2085

These glyph IDs are NOT font atlas cell indices. They are scene entity/sprite indices within the R2159 3D scene system.

### 5. Resource Structure Details

**R2156 (texture):**
- TOC: 15 sub-resources, each 66,720 bytes = PSMT8 256x256 with 0x4A0-byte GS header
- GS TEX0_1: TBP0=0, TBW=4, PSM=19(PSMT8), 256x256
- Pixel data: 65,536 bytes per sub-texture, starting at offset 0x4A0

**R2159 (scene):**
- TOC: 31 sub-resources (sizes 88 to 42,644 bytes)
- Data after TOC: transform matrices (many float 1.0/-1.0 values)
- Sub-resource offsets point into runtime aggregate (0x2C10 to 0x42670)

**R2155 (layout):**
- 16 TEX0_1 register setups, all PSM=20(PSMT4) 256x256
- Different texture setup from R2156 (PSMT4 vs PSMT8)
- May handle different rendering passes

---

## Item Icon Pair Table (EXE 0x3B376C)

338 entries pairing two glyph bases per item. Glyph range 112-2500+. Likely two-part composite icons (left-half/right-half). 338 entries corresponds to the full item catalog.

---

## Implications for Translation

### NOT a simple texture replacement
Unlike R1272 (the font atlas, which is a single PSMT4 256x512 texture), the equipment icons are 3D scene entities. Translation requires:

1. **Identifying which sub-textures in R2156 contain the Japanese text labels** - need to deswizzle and render the PSMT8 data with correct palette
2. **Replacing the Japanese text on those texture pages** - redraw with English labels
3. **Possibly adjusting UV coordinates in R2159** - if English labels are different sizes
4. **Re-injecting R2156** into PACKDATA.DIG

### Alternative approach: EXE patch
Instead of modifying textures, patch the EXE to:
- Skip the icon animation system entirely for equipment types
- Replace glyph IDs 2036-2047 references in the equipment type suffix table (EXE 0x3F9D00) with standard font atlas glyph IDs (0-94 range)
- This would render equipment types as regular text characters instead of animated sprites

### Difficulty assessment
- **Texture approach**: HIGH difficulty (PSMT8 deswizzle, palette handling, UV mapping)
- **EXE patch approach**: MEDIUM difficulty (need to understand how the rendering dispatches between font-atlas and 3D-sprite systems based on glyph ID ranges)

---

## Key File Paths

- Icon animation table: EXE file offset 0x3F9CF0 (VA 0x4F9C70)
- Equipment type suffix table: EXE file offset 0x3F9D00 (VA 0x4F9C80)  
- Item glyph base table: EXE file offset 0x3B38EA (VA 0x4B386A)
- Item icon pair table: EXE file offset 0x3B376C (VA 0x4B36EC)
- Icon handler function: EXE VA 0x001901C0 (file 0x090240)
- Resource init function: EXE VA 0x004981A0 (file 0x388220)
- R2155: `extracted/packdata_resources/2155_type10.bin`
- R2156: `extracted/packdata_resources/2156_type16.bin`
- R2157: `extracted/packdata_resources/2157_type17.bin`
- R2159: `extracted/packdata_resources/2159_type32.bin`
