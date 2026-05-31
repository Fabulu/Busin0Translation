# EXE Region 0x3AB080-0x3AF080: Structure Analysis

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6
**EXE**: `extracted/SLPM_653.78` (4,185,776 bytes)
**VA range**: 0x004AB000-0x004AF000 (file offset 0x3AB080-0x3AF080)

---

## CRITICAL FINDING: This Is NOT a Stat Label Glyph ID Table

The region 0x3AB080-0x3AF080 does **NOT** contain stat label glyph IDs. The known stat label glyph IDs (346=force, 535=know, 717=wisdom, etc.) are **absent** from this entire 16KB region. A byte-level search for all 45 known chargen-related glyph IDs as LE uint16 values found zero matches for the primary stat glyphs:

| Glyph ID | Character | Hex (LE) | Found in 0x3AB080-0x3AF080? |
|----------|-----------|----------|---------------------------|
| 346 | force (STR) | 5A 01 | **NO** |
| 535 | know (INT) | 17 02 | **NO** |
| 717 | wisdom (INT) | CD 02 | **NO** |
| 308 | faith (FTH) | 34 01 | **NO** |
| 354 | worship (FTH) | 62 01 | **NO** |
| 718 | life (VIT) | CE 02 | **NO** (1 false positive at unaligned offset) |
| 696 | destiny (VIT) | B8 02 | **NO** |
| 582 | agile (AGI) | 46 02 | **NO** (1 false positive at unaligned offset) |
| 719 | quick (AGI) | CF 02 | **NO** |
| 720 | fortune (LCK) | D0 02 | **NO** |
| 721 | luck (LCK) | D1 02 | **NO** |

The few "hits" for common values like 512 (0x0200) are false positives -- 0x0200 appears ubiquitously in binary data.

---

## Where Stat Label Glyph IDs Actually Live

All chargen stat labels are stored in **PACKDATA resource R38** (`extracted/packdata_resources/0038_type01.bin`), a type-01 MSG resource using BE uint16 glyph streams:

| R38 MSG | Byte Offset | Glyph IDs (BE) | Japanese | English Translation |
|---------|-------------|-----------------|----------|-------------------|
| 1 | 0x02F4 | 40, 48 | hp | hp |
| 3 | 0x02FC | 40, 48, 15, 45, 40, 48 | hp/mhp | hp/mhp |
| 5 | 0x030C | 346 | force | str |
| 7 | 0x0312 | 535, 717 | know+wisdom | int |
| 9 | 0x031A | 308, 354, 320 | faith+worship+heart | fth |
| 11 | 0x0324 | 718, 696, 346 | life+destiny+force | vit |
| 13 | 0x032E | 582, 719, 590 | agile+quick+degree | agi |
| 15 | 0x0338 | 720, 721, 590 | fortune+luck+degree | lck |

These are translated via `data/translate_chunks/chunk_r38_fix.json` and patched into R38 during the build pipeline. The EXE does not need patching for stat label content.

The chargen renderer at VA 0x2F1090 does NOT directly render glyphs. It builds a linked list of label descriptors `{next_ptr, type, R38_msg_index, update_flag}` and calls `JAL 0x301E90` to store them into a label slot array. The actual glyph rendering is handled by the generic text system via `JAL 0x1BF140`.

---

## What This Region Actually Contains

### Structure: Rendering Command List

The region 0x3AB080-0x3AF080 is structured as follows:

| File Offset Range | Size | Content |
|-------------------|------|---------|
| 0x3AB080-0x3AB768 | 0x6E8 | MIPS code (JAL/LUI/BEQ instructions present) |
| 0x3AB768-0x3AF078 | 0x38F0 | Data table: rendering command list |

### Data Table Format

Starting at **file offset 0x3AB768** (VA 0x004AB6E8), the data consists of **8-byte entries**:

```
+0x00: u32  command_data    ; packed command word
+0x04: u32  marker          ; always 0x000002FF (with rare variant 0x400002FF)
```

The 4-byte command_data field is structured as `[u16 value_LE][u16 type_LE]`:

| Type (u16) | Count | Meaning | Value Range |
|------------|-------|---------|-------------|
| 0x4000 | 49 | Y-position coordinate | 1-101 (counting down by 2) |
| 0x1001 | 51+ | Primary data reference | Various (106-1811) |
| 0x8000 | 24+ | Group separator | 0x033C (828) typically |
| 0x01E3-0x01FB | ~20 | Glyph/tile references | Various |
| 0x03E4-0x03E7 | ~6 | Extended tile references | Various |
| 0x0881-0x0905 | ~15 | Rendering mode flags | Various |
| 0x5001-0x5208 | ~10 | Scene graph node IDs | Various |
| 0x800A, 0x8001, 0x8003 | ~12 | Extended separators/modes | Various |

### Layout Structure (First Section)

The first section (entries 0-97) contains 49 Y-position + data pairs laid out as a vertical list counting from Y=101 down to Y=1 (screen lines), with two group separators:

```
Group 1 (Y=101 to Y=75): 14 entries -- likely personality trait descriptions
Group 2 (Y=71 to Y=1):   35 entries -- chargen screen layout data
```

The data values in the Y-position entries do NOT correspond to:
- R38 message indices (values exceed 188, the R38 message count)
- R38 byte offsets (content doesn't match)
- R1272 tile indices
- Menu struct glyph IDs

They appear to be **internal rendering engine node IDs** or **display list command arguments** used by the chargen scene graph renderer.

### Complex Entries (After Entry ~103)

After the simple Y-position pairs, the table transitions to a more complex format with varied type codes (0x01E3, 0x0903, 0x5203, etc.). These entries include:

- **Glyph ID references**: Entries with type 0x01F8-0x01FB contain values 0x0AAA-0x0AAD alongside known glyph IDs (504=profession, 505+, 506+, 507+)
- **Scene graph nodes**: Type 0x5001-0x5208 entries appear to be linked scene graph connections
- **Rendering mode**: Type 0x0881-0x0905 entries may control blending, texture selection, or animation state

---

## Implications for Translation

### No EXE patching needed at 0x3AB080-0x3AF080

The stat labels (STR, INT, FTH, VIT, AGI, LCK) are already correctly translated via the R38 MSG resource pipeline. The rendering command list at 0x3AB080-0x3AF080 controls layout/positioning of UI elements but does not contain translatable text content.

### Where "shared glyph" patching IS needed

If specific kanji glyphs need to be shared between different rendering contexts (menu structs vs MSG text), the relevant tables are:

1. **56-byte menu structs** at 0x3C3000-0x3C5300 (contains R1272 tile index pairs per glyph)
2. **R38 MSG resource** in PACKDATA (contains BE uint16 glyph ID streams)
3. **Chargen kana grid** at 0x3C83C0-0x3C93A0 (contains LE uint16 glyph IDs for name entry)

The 0x3AB080-0x3AF080 region is a downstream consumer of these data sources, not a source of glyph IDs itself.

---

## Summary

| Question | Answer |
|----------|--------|
| Does 0x3AB080-0x3AF080 contain stat glyph IDs? | **NO** |
| Where are stat label glyph IDs? | R38 MSG resource (MSG 5-15) |
| What IS in 0x3AB080-0x3AF080? | Rendering command list / scene graph data |
| Entry format? | 8 bytes: {u16 value, u16 type, u32 0x000002FF} |
| Entries count? | ~1600 entries spanning 0x3AB768-0x3AF078 |
| Does this region need patching for translation? | **NO** |
| Which regions DO need patching for shared glyphs? | 0x3C3000-0x3C5300 (menu structs), R38 MSG, 0x3C83C0 (kana grid) |
