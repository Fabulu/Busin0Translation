# Recon 16: PACKDATA.CIG Header/TOC Analysis -- BUSIN 1 vs BUSIN 0

**Date:** 2026-05-22
**Status:** Complete (significant structural differences found)

---

## Key Finding: PACKDATA.CIG Has No Embedded TOC

**BUSIN 1's PACKDATA.CIG is fundamentally different from BUSIN 0's PACKDATA.DIG.**

The same unpacker CANNOT be used for both. The CIG file does not contain a table of contents at its start -- it begins immediately with raw 3D vertex/model data.

---

## BUSIN 0: PACKDATA.DIG (Confirmed Format)

| Property | Value |
|----------|-------|
| File size | 839,661,568 bytes (800.8 MB) |
| TOC location | Byte 0 of file |
| Entry format | 12 bytes: (sector_offset, sector_count, type_code) as uint32 LE |
| Entry count | 2,883 |
| Sector size | 2,048 bytes |
| Contiguity | A[i+1] == A[i] + B[i] (perfectly contiguous, 2 outlier entries) |
| Sub-header | 16 bytes per resource: (0x00000000, payload_size, stride, 0x00000000) |
| EXE API | "GetLoadAdr" / "GetLoadSize" with FileID-based lookup |
| TOC byte size | 2,883 x 12 = 34,596 bytes |

The first 3 entries are:
```
Entry 0: A=0x7d  B=0x1  C=0x1   (sector 125, 1 sector, type 1)
Entry 1: A=0x7e  B=0x1  C=0x1   (sector 126, 1 sector, type 1)
Entry 2: A=0x7f  B=0x1  C=0x1   (sector 127, 1 sector, type 1)
```

First entry starts at sector 0x7D = byte offset 0xFA00, leaving room for the TOC itself.

---

## BUSIN 1: PACKDATA.CIG (New Analysis)

| Property | Value |
|----------|-------|
| File size | 535,351,296 bytes (510.4 MB) |
| File size in sectors (2048) | 261,402 (0x3FCB2) |
| TOC at byte 0? | **NO** -- starts with 3D model/vertex data |
| TOC at end of file? | **NO** -- ends with compressed/encoded data |
| Separate index file? | **NO** -- no DSI or equivalent on disc |
| EXE API | No "GetLoadAdr"/"GetLoadSize"/"FileID" strings found (different or stripped) |

### First 16 Bytes of PACKDATA.CIG

```
02 00 00 00 20 00 00 00 01 00 00 00 10 00 00 00
```

This is NOT a TOC entry. As uint32 LE: (2, 32, 1, 16). The following data contains:
- Float values 3F800000 (1.0f) -- identity matrix w-components
- Bounding box values (C0A00000 = -5.0, 40A00000 = 5.0)
- VIF/GIF tags (01000101, 01000103) starting around offset 0x140

This is clearly a 3D model resource starting at byte 0.

### Magic Number Scan Results

| Signature | Found in CIG? | Notes |
|-----------|--------------|-------|
| TIM2 | No | No TIM2 textures in CIG |
| VAGp | No | No VAG audio headers |
| SShd | 5 occurrences | All are false positives (data in compressed blocks, not real sound headers) |
| SSbd | 11 occurrences | Also false positives (not sector-aligned) |
| RIFF | Not found | |
| PNG | Not found | |

Only one SShd occurrence was sector-aligned (offset 46,319,488 = sector 22,617), but it contained identical byte patterns to non-aligned occurrences, confirming these are coincidental matches in compressed/encoded data.

### Data Sample at Various Offsets

| Offset | Content |
|--------|---------|
| 0x000000 | 3D model vertex data (floats, matrices) |
| 0x100000 (1MB) | 0xFF padding/unused |
| 0xA00000 (10MB) | Float data (43000000 = 128.0, etc.) |
| 0x5F5E100 (100MB) | Structured data with small integers |
| 0x11E1A300 (300MB) | Encoded/compressed-looking data |

---

## Resource Lookup: EXE-Embedded Size Table

A large resource size table was found in the BUSIN 1 EXE at file offset **0x487E78**:

```
Format: 8-byte entries (uint32 resource_size, uint32 index)
```

Grouped by resource size class:

| Size (hex) | Size (dec) | Index range | Count |
|-----------|-----------|-------------|-------|
| 0x0400 | 1,024 | 1 - 0x6A | 106 |
| 0x1800 | 6,144 | 1 - 0x2D | 45 |
| 0x2800 | 10,240 | 0x2E - 0x34 | 7 |
| 0x4800 | 18,432 | 0x35 - 0x4F | 27 |
| 0x8800 | 34,816 | 0x47 - 0x4F | 9 |
| 0x0200 | 512 | 1 - 0x1E | 30 |
| 0x10000 | 65,536 | 1 - 0x3D | 61 |
| 0x20000 | 131,072 | 0 - 0x3A | 59 |

This suggests the game computes file offsets from (resource_type, index) using cumulative size calculations rather than a direct lookup table. Each resource type has a fixed size per entry, and the game multiplies type_size x index (plus a base offset for each type group) to find the byte position in PACKDATA.CIG.

---

## Disc Structure Comparison

### BUSIN 0 (JP, SLPM-65378)
```
SLPM_653.78        4.0 MB   (executable)
BSN2_0.DSI        60.3 MB   (data archive -- contains MPEG video + other data)
PACKDATA.DIG     800.8 MB   (packed game data with embedded TOC)
TEMP1.LZH          ???      (LZH compressed data)
MOVIE/                      (FMV cutscenes)
```

### BUSIN 1 (EN, SLUS-20259)
```
SLUS_202.59        4.8 MB   (executable -- larger, may contain TOC/tables)
PACKDATA.CIG     510.4 MB   (packed game data, NO embedded TOC)
ZERONOP.DAT       36.6 MB   (LZH archive -- equivalent to TEMP1.LZH)
IMAGE/                      (separate asset files: TMX textures, MDB/MDT models, EVE/MSG scripts)
SOURCE/                     (battle data: DAT, SAV, SSD files)
```

Notable differences:
- BUSIN 1 has no BSN2_0.DSI equivalent
- BUSIN 1 has separate IMAGE/ and SOURCE/ directories with individual files
- BUSIN 1's EXE is ~800KB larger (could hold the resource index)
- BUSIN 1 has no MOVIE/ directory (movies may be in CIG or ZERONOP)

---

## EXE Debug Strings

### BUSIN 0 (has rich file-system debug strings)
```
\PACKDATA.DIG;1
LoadClose : 0x%x
GetLoadAdr:Not Found FileID %x!!
GetLoadSize:Not Found FileID!!
Packet Use(%p -> %p) / Last(%x)
```

### BUSIN 1 (different/stripped debug strings)
```
NTSC or USA!!!
\PACKDATA.CIG;1
CD READ RETRY NOW!!!(%d)
CD READ RETRY!!!(%d)
SRP Size Over!! (%d)
WSEPACK_BTL_MAGIC
WSEPACK_BS_ALLIED
WSEPACK_D_ALLIED
WSEPACK_MONBOSS_EV
WSE_BTL_PL_M01
WSE_BS_ALLIED_00
WSE_D_ALLIED_00
WSE_MONBOSS_EV00
source/game/battle/data/status.ssd
```

The "WSEPACK" strings indicate a named-resource packing system (WSE = Wizardry Story Edition?). Resources are accessed by name rather than numeric FileID.

---

## Conclusions

1. **The BUSIN 0 unpacker CANNOT be reused for BUSIN 1.** The formats are fundamentally different.

2. **PACKDATA.CIG has no embedded TOC.** Resource offsets are computed at runtime using tables embedded in the EXE, or via the WSEPACK name-based system.

3. **The CIG format uses fixed-size resource groups.** The EXE at offset 0x487E78 contains a size/index table suggesting resources are organized by type, each type having a fixed size. Offsets are computed as: `base_offset[type] + index * fixed_size[type]`.

4. **BUSIN 1 partially unpacks assets to disc.** Unlike BUSIN 0 which packs everything in DIG+DSI, BUSIN 1 has separate IMAGE/ and SOURCE/ directories for some assets. PACKDATA.CIG likely contains only 3D models, maps, and other runtime-streamed data.

5. **Next steps for CIG reverse-engineering:**
   - Disassemble the BUSIN 1 EXE (MIPS R5900 code) to find the CIG reading functions
   - Map the complete EXE-embedded size table at 0x487E78
   - Determine the base offset for each resource type group
   - Cross-reference WSEPACK names with resource types
   - Check if ZERONOP.DAT (LZH) contains additional resources

---

## Files Referenced

- `C:/Programmieren/wizardrytranslation/extracted_busin1/PACKDATA.CIG` (535,351,296 bytes)
- `C:/Programmieren/wizardrytranslation/extracted_busin1/SLUS_202.59` (5,038,496 bytes)
- `C:/Programmieren/wizardrytranslation/extracted/PACKDATA.DIG` (839,661,568 bytes)
- `C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78` (4,185,776 bytes)
- `C:/Programmieren/wizardrytranslation/dumps/packdata_toc_analysis.txt` (BUSIN 0 TOC analysis)
- `C:/Programmieren/wizardrytranslation/tools/parse_packdata_toc.py` (BUSIN 0 TOC parser)
