# Recon 26: Font Descriptor Struct Deep Analysis

## Summary

13 font descriptor structs at EXE offset 0x3C0700, each 28 bytes (364 bytes total). These are followed immediately by a glyph index mapping table (86 u16 entries), then a rendering parameter pointer table (50 u32 entries pointing to float arrays), then position/offset data. The descriptors define 12 active font configurations (4 groups x 3 sub-variants) plus one 0xFFFF terminator entry.

## Raw Hex Dump (28 bytes per struct)

```
[ 0] 0x003C0700: 02 00 22 00 10 00 10 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 1] 0x003C071C: 02 00 21 00 50 00 10 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 2] 0x003C0738: 02 00 24 00 60 00 10 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 3] 0x003C0754: 02 00 2b 00 38 00 20 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 4] 0x003C0770: 02 00 21 00 50 00 20 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 5] 0x003C078C: 02 00 2c 00 60 00 20 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 6] 0x003C07A8: 02 00 20 00 38 00 30 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 7] 0x003C07C4: 02 00 21 00 50 00 30 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 8] 0x003C07E0: 02 00 23 00 60 00 30 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[ 9] 0x003C07FC: 02 00 2a 00 38 00 40 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[10] 0x003C0818: 02 00 21 00 50 00 40 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[11] 0x003C0834: 02 00 25 00 60 00 40 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
[12] 0x003C0850: ff ff 00 00 00 00 00 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 00 00 00 00
```

## Struct Field Layout (28 bytes)

```c
struct FontDescriptor {  // 28 bytes
    uint16_t type;           // [0:2]   Always 2 for active, 0xFFFF = terminator
    uint16_t param_id;       // [2:4]   Varies (32-44), see analysis below
    uint16_t tex_param_a;    // [4:6]   GS texture param (16/56/80/96)
    uint16_t tex_param_b;    // [6:8]   GS texture param (16/32/48/64)
    uint32_t reserved_0;     // [8:12]  Always 0
    uint8_t  rgba[4];        // [12:16] Default color: 128,128,128,128 (neutral gray, half alpha)
    uint16_t tex_dim_w;      // [16:18] Always 256 (texture width)
    uint16_t tex_dim_h;      // [18:20] Always 256 (texture height or stride)
    uint32_t reserved_1;     // [20:24] Always 0
    uint32_t reserved_2;     // [24:28] Always 0
};
```

## Field Variation Analysis

| Field | Byte offset | Type | Values | Status |
|-------|-------------|------|--------|--------|
| type | 0-1 | u16 | 2, 0xFFFF | 2=active, 0xFFFF=terminator (struct 12) |
| param_id | 2-3 | u16 | 32,33,34,35,36,37,42,43,44 | VARIES - 9 unique values across 12 structs |
| tex_param_a | 4-5 | u16 | 16,56,80,96 | VARIES - 4 values, cyclic pattern |
| tex_param_b | 6-7 | u16 | 16,32,48,64 | VARIES - 4 values, increments by 16 |
| reserved_0 | 8-11 | u32 | 0 | CONSTANT |
| rgba | 12-15 | 4xu8 | 128,128,128,128 | CONSTANT (0x80808080) |
| tex_dim_w | 16-17 | u16 | 256 | CONSTANT |
| tex_dim_h | 18-19 | u16 | 256 | CONSTANT |
| reserved_1 | 20-23 | u32 | 0 | CONSTANT |
| reserved_2 | 24-27 | u32 | 0 | CONSTANT |

## Grouping Pattern (4 groups x 3 sub-variants)

The 12 active structs organize into 4 groups by `tex_param_b`, with 3 sub-variants each selected by `tex_param_a`:

| Group | tex_param_b | Structs | tex_param_a values | param_id values |
|-------|-------------|---------|-------------------|-----------------|
| 0 | 16 (0x10) | 0, 1, 2 | 16, 80, 96 | 34, 33, 36 |
| 1 | 32 (0x20) | 3, 4, 5 | 56, 80, 96 | 43, 33, 44 |
| 2 | 48 (0x30) | 6, 7, 8 | 56, 80, 96 | 32, 33, 35 |
| 3 | 64 (0x40) | 9, 10, 11 | 56, 80, 96 | 42, 33, 37 |

**Key observations:**
- `tex_param_a` follows pattern: sub-variant 0 = 16 or 56, sub-variant 1 = always 80, sub-variant 2 = always 96
- Struct 0 is unique with `tex_param_a=16` while all other group-first entries use 56
- The middle sub-variant always has `param_id=33`
- `tex_param_b` increments by 16 per group: likely a GS VRAM page offset or CLUT base pointer
- `tex_param_a` values (56/0x38, 80/0x50, 96/0x60) likely reference different texture pages or atlas regions

**Interpretation of groups:** The 4 groups likely represent 4 different text rendering contexts (e.g., menu text, dialogue, battle text, system messages). The 3 sub-variants within each group may represent different glyph sets (e.g., ASCII/Latin, katakana/hiragana, kanji) or different font sizes.

## Constant Fields

- **RGBA = 128,128,128,128**: Neutral gray with 50% alpha -- this is a standard "modulate" base color for PS2 GS rendering. When used with GS alpha blending mode MODULATE, 128 = 1.0x multiplier (since PS2 GS treats 128 as 1.0 in its 0-128 alpha range). This means the default text color is full-brightness white when modulated.
- **tex_dim = 256x256**: Each font atlas texture is 256x256 pixels (NOT the full 256x512 found elsewhere -- the 512-height atlas may be two 256x256 pages stacked, addressed by the descriptor groups).

## Data After Descriptors

### Glyph Index Mapping Table (0x3C086C, 86 entries)

Immediately after the 13 structs, 86 uint16 values map glyph index to character/style code:

```
Values: [0, 0, 1, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
         33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
         58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82,
         83, 84, 85, 86, 89, 90, 91, 92, 93]
```

**Missing values (gaps):** 2, 3, 4, 11, 12, 31, 32, 87, 88

This is NOT a glyph-to-codepoint mapping but rather an index array that maps sequential indices (0-85) to a sparse ID space (0-93) with 9 values skipped. The skipped IDs likely correspond to unused or special-purpose entries. This could index into the rendering parameter pointer table below.

### Rendering Parameter Pointer Table (0x3C091C, 50 entries)

50 uint32 pointers to float parameter arrays. Each pointer targets an address in the range 0x004EA1A0-0x004EB550 (RAM addresses, file offsets 0x3EA220-0x3EB5D0).

Each pointed-to block is exactly **112 bytes = 28 floats**, containing rendering parameters:

**Sample block (Ptr[1] = 0x004EA1A0 -> file 0x3EA220):**

```
Float[0-3]:   0.0000,  0.1700,  0.1800,  0.1900   -- Color set 1 (RGBA?)
Float[4-7]:   1.0000,  0.3000,  0.2800,  0.2500   -- Color set 2 (RGBA?)
Float[8-11]:  1.0000,  0.5500,  0.5500,  0.5500   -- Color set 3
Float[12-15]: 1.0000,  0.2700,  0.2700,  0.2000   -- Color set 4
Float[16-19]: 1.0000,  0.2500,  0.2700,  0.2700   -- Color set 5
Float[20-23]: 1.0000,  0.0000,  0.0000,  0.0000   -- Color set 6 (background?)
Float[24]:    0.0000                                -- Param
Float[25]:    0.9500                                -- Scale or opacity
Float[26]:   55.0000                                -- Size or spacing
Float[27]: 1000.0000                                -- Distance or depth
```

These appear to be **text style/color palettes** -- groups of RGBA float colors used for different text rendering states (normal, highlighted, selected, disabled, shadowed, etc.). The final values (55.0, 1000.0) could be text size and render distance/depth parameters.

**Notable pointer patterns:**
- Pointers are spaced 112 bytes (0x70) apart = one parameter block each
- Indices 11, 12, and 24 all point back to the same address (0x004EA1A0) -- default/fallback style
- Index 0 is NULL (no style for index 0)
- 50 active pointers for 86 index entries suggests the index table maps into this pointer table

### Position/Offset Data (0x3C09E4+)

After the pointer table, data changes to triplets of (u32 index, float x, float y):

```
Example entries:
  index=0x00030000  x=  7.00  y=-12.00
  index=0x00030002  x=-17.00  y=-29.00
  index=0x00030003  x=-10.00  y=-13.00
  index=0x00030005  x= 52.00  y=-33.00
  ...
```

The upper 16 bits of the index (0x0003) appear to be a type/group ID, while the lower 16 bits select which text element. The x,y floats are screen-space offsets for text positioning in specific UI contexts.

## No Width Tables Found

Scanning 0x3C0800-0x3C1000 for arrays of small byte values (1-20 range, 16+ consecutive) found **no glyph width tables**. The per-glyph advance widths are likely either:
1. Computed algorithmically from the glyph cell size (fixed-width rendering)
2. Stored alongside the font texture data in PACKDATA.DIG
3. Embedded in the 112-byte rendering parameter blocks (e.g., float[26]=55.0 could be a fixed pixel advance)

## Cross-Reference with Atlas Properties

The constant `tex_dim = 256x256` per descriptor (NOT the 256x512 previously assumed) changes the atlas math:

| Glyph size | Cols | Rows | Total glyphs | Notes |
|-----------|------|------|-------------|-------|
| 8x8 | 32 | 32 | 1024 | Too many, too small |
| 10x10 | 25 | 25 | 625 | Plausible |
| 12x12 | 21 | 21 | 441 | Close to some counts |
| 14x14 | 18 | 18 | 324 | Plausible |
| 16x16 | 16 | 16 | 256 | Powers of 2, clean |

If the 256x512 atlas is actually two 256x256 pages (addressed via `tex_param_b` groups), then:
- Page 0 (tex_param_b=16) + Page 1 (tex_param_b=32) = 512 or 882 glyphs at 12x12

## Struct Similarity

All 13 structs share identical bytes at positions 8-27 (the constant tail: reserved, rgba, tex_dims, padding). They differ only in bytes 0-7 (type, param_id, tex_param_a, tex_param_b).

No two structs are fully identical.

## Complete Memory Layout

```
0x3C0700 - 0x3C086C : 13 font descriptor structs (28 bytes x 13 = 364 bytes)
0x3C086C - 0x3C0918 : Glyph/style index table (86 uint16 entries = 172 bytes)
0x3C0918 - 0x3C091C : Padding (4 zero bytes)
0x3C091C - 0x3C09E4 : Rendering param pointer table (50 uint32 = 200 bytes)
0x3C09E4 - 0x3C0A?? : UI text position data (index + x,y float triplets)
```

Pointed-to rendering data at 0x3EA220-0x3EB5D0 (RAM 0x4EA1A0-0x4EB550): 50 blocks of 112 bytes = 5600 bytes of float color/style parameters.

## Key Findings for Translation

1. **12 font configurations, not just 1.** The game uses 4 groups of 3 font variants, likely for different rendering contexts and glyph sets. A font replacement must handle all 12 configurations.

2. **256x256 per atlas page.** Each descriptor references a 256x256 texture, not 256x512. The larger atlases may be composed of multiple pages.

3. **Text colors/styles are float-based.** 50 unique style palettes with RGBA float colors and sizing parameters. These can be modified to adjust text appearance without touching the font atlas.

4. **The RGBA default (128,128,128,128) is a PS2 GS modulation base**, not a literal gray. It means "full brightness, full opacity" in GS MODULATE blending.

5. **No glyph width tables in EXE.** Per-character advance widths must be stored elsewhere (PACKDATA.DIG) or computed at fixed width.

6. **tex_param_a and tex_param_b are likely GS VRAM addresses** (TBP0 and CBP in 256-byte block units) that select which texture page and CLUT to use for each font variant.
