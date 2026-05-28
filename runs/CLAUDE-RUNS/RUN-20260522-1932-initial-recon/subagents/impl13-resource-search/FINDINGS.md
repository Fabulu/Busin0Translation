# Impl 13: PACKDATA Resource Search for Glyph-to-Character Mapping Table

## Executive Summary

**The glyph-to-character mapping table is NOT stored as explicit SJIS code points in any PACKDATA.DIG resource.** Exhaustive scanning of all 2,883 resources found zero instances of consecutive SJIS hiragana or katakana sequences, and no resources with significant SJIS character density. The mapping is constructed at runtime from multiple data sources through the font configuration system.

## Key Findings

### 1. No SJIS Character Mapping Table Exists in PACKDATA

- Scanned all 2,883 resources for consecutive SJIS hiragana codes (0x829F-0x82F1) at strides 2, 4, and 8 -- **zero resources had 5+ consecutive hiragana**.
- Scanned all resources with size 500-30,000 bytes for SJIS density (% of uint16 values in valid SJIS ranges) -- **zero resources exceeded 30% SJIS density**.
- This definitively rules out Option A (flat SJIS uint16 array) and Option B (JIS code point array) from the search strategy.

### 2. BSS Table Structure Decoded from EXE Code

The BSS table at VA 0x5191F0 uses **80 bytes per entry** with **up to 2048 slots** (loop counter checks `slti $s0, 2048`). The entry stride was decoded from MIPS code at EXE offset 0x094D48:

```
sll  v1, a1, 2      ; v1 = idx * 4
addu v1, v1, a1     ; v1 = idx * 5  
sll  v1, v1, 4      ; v1 = idx * 80
addu v1, a0, v1     ; v1 = base + idx * 80
lh   v1, 26(v1)     ; load signed halfword at struct offset +26
```

There is also a secondary table at VA 0x5181F0: **128 entries of 32 bytes** (4096 bytes total), copied in a separate loop with `slti $a1, 128`.

### 3. Font Configuration Table in EXE Data Section

Found a font configuration table at VA 0x004E8E00 (EXE file offset 0x3E8E80):
- **Entry size: 84 bytes** per font configuration
- **Index computation:** `font_index * 84` where `font_index = gp_relative_var * 7 * 3 * 4`
- Contains packed resource references (uint32 values like 0x08AC0000, 0x08EF0000, etc.)

Font config entry 0 (84 bytes):
```
+00: 0x08AC0000  (base resource group)
+04: 0x08AC0000  (duplicate)
+08: 0x08AC0001  (sub-resource 1)
+12: 0x08AC0002  (sub-resource 2)
+16: 0x08EF0000  (possibly charmap/metrics resource)
+20: 0x004BCAF0  (RAM pointer / data offset)
+24: 0x08F20000  (additional resource ref)
+28: 0x08F00000  (font atlas resource?)
+32: 0x08F10000  (additional resource ref)
+36: 0x004E73C0  (RAM pointer / data offset)
+40: 0xFFFFFFFF  (unused slot)
+44: 0xFFFFFFFF  
+48: 0xFFFFFFFF
+52: 0x00000000
+56: 0x000E002D  (packed config: 14, 45 -- could be glyph dimensions)
+60: 0x09000000  (resource ref or config)
+64: 0x00000002  (font type/variant)
+68: 0x004BD1D0  (RAM pointer)
+72: 0xFFFFFFFF
+76: 0x00000000
+80: 0x00000000
```

The encoded resource IDs (0x08AC, 0x08EF, 0x08F0, 0x08F1, 0x08F2) map to PACKDATA indices 2220, 2287, 2288, 2289, 2290 respectively (assuming direct 1:1 mapping -- encoding scheme not yet confirmed).

### 4. Candidate Resources from Font Config

| Encoded ID | Decimal | PACKDATA idx | Size | Type | Purpose (hypothesis) |
|-----------|---------|-------------|------|------|---------------------|
| 0x08AC | 2220 | 2220 | 79,770 | 3 | Font data group base |
| 0x08EF | 2287 | 2287 | 89,028 | 12 | Charmap/metrics? |
| 0x08F0 | 2288 | 2288 | 160,816 | 1 | Font atlas texture (160,816 / 80 = 2010.2) |
| 0x08F1 | 2289 | 2289 | 73,920 | 1 | Secondary texture/data |
| 0x08F2 | 2290 | 2290 | 37,364 | 22 | Additional font data |

### 5. BSS Initialization Code Flow

Three key functions interact with the BSS table at 0x5191F0:

**Init function** (EXE 0x085130, VA 0x184930):
```
1. Loads font config from table at 0x004E8E00 using gp-relative font index
2. Calls resource manager at 0x00492A70 to load resource data
3. Calls 0x00492700 to process the loaded data
4. Reads config values from loaded data:
   - Offset 0: stored to gp var (font type?)
   - Offset 2: stored to gp var at -28910 (glyph count)
   - Offsets 16-20: stored to gp vars (font dimensions?)
5. Copies entry data from loaded_data+32 to BSS 0x5191F0, one entry at a time
   using function 0x00183E20, looping up to the count from step 4
6. Calls rendering setup functions (0x184A60, 0x185030, 0x181C10)
```

**Save function** (EXE 0x080B00, VA 0x180300):
- Copies FROM source struct+64 TO BSS 0x5191F0, 2048 iterations
- Uses copy function 0x00183F80

**Load function** (EXE 0x0809D0, VA 0x1801D0):
- Copies FROM BSS 0x5191F0 TO dest struct+64, 2048 iterations
- Complementary to save function

### 6. Resource 49 Analysis -- NOT the Mapping Table

Resource 49 (3,458 bytes, type 01) was flagged as a candidate (858 * 4 = 3,432). Analysis shows it is an **offset table** -- monotonically increasing uint32 LE values like 0x006F, 0x01C0, 0x01DC, 0x01FA, etc. These are byte offsets into associated data, not character codes.

### 7. Size-Based Search Results

Resources matching expected sizes for an 80-byte-stride table:

| Size Target | Resources Found |
|------------|----------------|
| 858*2 = 1,716 | idx 588 (1,680), idx 660 (1,622) |
| 858*4 = 3,432 | idx 36 (3,390), idx 49 (3,458) |
| 858*8 = 6,864 | idx 45 (6,950), idx 1160 (6,852) |
| 32 + 858*80 = 68,672 | idx 25 (67,736), idx 1130 (68,800), idx 2401 (68,160) |
| 32 + 128*32 + 858*80 = 72,768 | idx 690 (72,384), idx 2223 (72,730) |

None of these contained recognizable SJIS character data when analyzed.

### 8. Likely Architecture: Character Codes NOT in Resource

Based on all evidence, the most probable architecture is:

**The glyph-to-character mapping is computed algorithmically at runtime, not stored as a table.**

Evidence:
- No SJIS sequences exist anywhere in PACKDATA resources
- The 80-byte BSS structs are populated by a complex init function that reads config values, calls multiple sub-functions, and does processing
- The BSS struct field at offset +26 (accessed via `lh` = signed halfword) likely stores a character identifier that is NOT a raw SJIS code point -- it could be a JIS row/column index, a custom encoding, or a sequential glyph ID that maps to characters via code logic
- The font config in the EXE references multiple resources per font (0x08AC+sub-indices 0,1,2), suggesting the character data is distributed across several resources and assembled at runtime

## Recommendations

1. **Approach C (Known-Text Cross-Reference) is the highest-priority path** -- correlating known Japanese game terms with MSG glyph indices will decode the mapping without needing the resource format
2. **Approach B (Font Atlas OCR)** can independently identify characters from the visual font atlas at resource 1272
3. **To crack the resource format**: disassemble functions 0x00183E20 (entry copy), 0x00492A70 (resource loader), and 0x00492700 (resource processor) to understand how loaded data is transformed into the 80-byte BSS structs
4. **The encoded resource ID scheme** (0x08AC = some mapping to PACKDATA index) needs reverse-engineering via the resource manager function at 0x00492A70

## Files Referenced

- EXE: `C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78` (ELF, MIPS, 4,185,776 bytes)
- Resources: `C:/Programmieren/wizardrytranslation/extracted/packdata_resources/`
- Manifest: `C:/Programmieren/wizardrytranslation/extracted/packdata_resources/manifest.json`
- Font atlas: Resource 1272 (65,792 bytes, PSMT4 256x512, the only font texture)
- Font config table: EXE file offset 0x3E8E80 (VA 0x004E8E00), 84 bytes per font config
- BSS glyph table: VA 0x5191F0, 2048 slots * 80 bytes, field at +26 = character ID
- BSS secondary table: VA 0x5181F0, 128 slots * 32 bytes
- Key EXE functions: Init=0x184930, Save=0x180300, Load=0x1801D0, Copy=0x183E20/0x183F80
- Resource manager: 0x492A70 (load), 0x492700 (process)

## Scripts Created

Scanning scripts left in project root (can be cleaned up):
- `scan_glyphs.py`, `scan_glyphs2.py`, `scan_glyphs3.py` -- SJIS sequence scanners
- `scan_exe.py`, `scan_exe2.py` -- BSS reference finders
- `dis1.py`, `dis3.py`, `dis4.py` -- MIPS disassembly helpers
