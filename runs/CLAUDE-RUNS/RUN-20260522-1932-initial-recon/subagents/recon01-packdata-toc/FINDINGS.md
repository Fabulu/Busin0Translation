# PACKDATA.DIG Table of Contents (TOC) -- Reverse Engineering Findings

**File:** `C:/Programmieren/wizardrytranslation/extracted/PACKDATA.DIG`
**File size:** 839,661,568 bytes (0x320C3800) = exactly 409,991 sectors of 2048 bytes
**Date:** 2026-05-22

---

## 1. Overall File Layout

```
Offset        Size          Description
----------------------------------------------------------------------
0x00000000    0x8724        Primary TOC (2883 entries x 12 bytes)
0x8724        0x001C        Zero padding (to align to 0x8740)
0x8740        0x00C0        Zeros (gap)
0x8800        0x0040        Secondary index table (4 entries x 16 bytes)
0x8840        ~0x35FC0      Additional metadata / secondary structures
0x3E800       ~0x31C85000   File data (sectors 0x7D through 0x64186)
----------------------------------------------------------------------
Total: 0x320C3800 = 839,661,568 bytes
```

The file is divided into a **header region** (sectors 0x00-0x7C = 125 sectors = 256,000 bytes)
and a **data region** (sectors 0x7D-0x64186).

---

## 2. Primary TOC Structure

**Location:** File offset 0x00000000
**Entry count:** 2,883 entries
**Entry size:** 12 bytes (3 x uint32 little-endian)
**Total TOC size:** 34,596 bytes (0x8724)

### Entry Format

```
struct TOCEntry {
    uint32_t sector_offset;   // Offset in 2048-byte sectors from file start
    uint32_t sector_count;    // Size in 2048-byte sectors
    uint32_t type_code;       // Resource type/category identifier
};
```

### Critical Proof: Sector Size = 2048 bytes (0x800)

The **last TOC entry** (entry #2882, at file offset 0x8718) contains:
- `sector_offset = 0x6403A` (409,658)
- `sector_count  = 0x14D`   (333)
- `type_code     = 0x09`

Calculation: `(409,658 + 333) * 2048 = 409,991 * 2048 = 839,661,568` = **exact file size**

This proves conclusively that:
1. Field 1 is a sector-based offset (sector size = 2048 = 0x800 bytes)
2. Field 2 is a sector count (size of the resource)
3. The entries describe contiguous, non-overlapping blocks covering the entire data region

### Contiguity Verification

Entries are strictly contiguous -- each entry's `sector_offset + sector_count` equals the next entry's `sector_offset`:

| Entry | sector_offset | sector_count | type | Next Expected | Actual Next |
|-------|--------------|-------------|------|---------------|-------------|
| 0     | 0x7D (125)   | 1           | 1    | 126           | 126         |
| 1     | 0x7E (126)   | 1           | 1    | 127           | 127         |
| 2     | 0x7F (127)   | 1           | 1    | 128           | 128         |
| 3     | 0x80 (128)   | 0x90 (144)  | 3    | 272           | 272         |
| 4     | 0x110 (272)  | 0x14 (20)   | 4    | 292           | 292         |
| 5     | 0x124 (292)  | 0x18 (24)   | 4    | 316           | 316         |
| 6     | 0x13C (316)  | 0x1F (31)   | 4    | 347           | 347         |
| ...   | ...          | ...         | ...  | ...           | ...         |
| 2882  | 0x6403A      | 0x14D       | 9    | 409,991       | (EOF)       |

**No gaps, no overlaps.** The entire data region from sector 0x7D to end-of-file is
partitioned into exactly 2,883 contiguous resource blocks.

---

## 3. Type Codes (Field 3)

Observed type codes from sampling across the TOC:

| Code | Hex  | Notes                                                     |
|------|------|-----------------------------------------------------------|
| 1    | 0x01 | Very common; many single-sector (2KB) entries; small data  |
| 2    | 0x02 | Common; various sizes; possibly text/script data           |
| 3    | 0x03 | Medium frequency; data starts with sub-header structure    |
| 4    | 0x04 | Common; many entries; sub-header with offset tables        |
| 6    | 0x06 | Observed in larger entries                                 |
| 7    | 0x07 | Observed in larger entries near end of TOC                 |
| 8    | 0x08 | Observed                                                   |
| 9    | 0x09 | Last entry type; large blocks (333 sectors = 682KB)        |
| 10   | 0x0A | Moderate entries (163 sectors = ~334KB)                    |
| 11   | 0x0B | Large entries (0x408 = 1032 sectors = ~2.1MB)              |
| 12   | 0x0C | Observed near end                                         |
| 13   | 0x0D | Observed                                                   |
| 15   | 0x0F | Observed (0x0D sectors = 13 sectors, and larger)           |
| 20   | 0x14 | Observed (0x22 = 34 entries worth 34 sectors)              |
| 44   | 0x2C | Observed (entry at 0x7C70: type 0x2C)                      |

The majority of type=1 entries are single-sector (2048 bytes), suggesting they are
individual small resources (e.g., palettes, small textures, configuration data).

Type codes likely correspond to resource categories: models (3D), textures, sounds,
scripts, maps, etc. Further investigation of data headers at each type's offsets
is needed to map types to content.

---

## 4. Resource Data Headers

Every resource block (at its sector_offset * 0x800) starts with a consistent
sub-header format:

```
Offset  Size    Description
0x00    4       Always 0x00000000
0x04    4       Data size / sub-block size (varies)
0x08    4       Some count or stride value
0x0C    4       Always 0x00000000
```

Examples:
```
Type 1 @ 0x3E800:  00000000 00000374 00000010 00000000
Type 3 @ 0x40000:  00000000 000043B4 00000030 00000000
Type 4 @ 0x88000:  00000000 00003324 00000040 00000000
Type 2 @ 0x262000: 00000000 000002E0 00000020 00000000
Type 10 @ 0x210800: 00000000 0000DB1C 000000A0 00000000
Type 15 @ 0x3D8800: 00000000 0000099E 000000F0 00000000
Type 9 @ 0x3201D000: 00000000 00000210 00000090 00000000
```

The second word appears to be a "payload size" within the sector-aligned block.
The third word varies and could be a record stride or sub-block count.

---

## 5. Secondary Index Table

**Location:** File offset 0x8800
**Format:** 4 entries of 16 bytes each (uint32 x 4)

```
Entry 0: ( 0,  0x8740,  0x0040,   0 )
Entry 1: ( 1,  0x8740,  0x8780,   0 )
Entry 2: ( 2,  0x8740,  0x10EC0,  0 )
Entry 3: ( 3,  0x8740,  0x19600,  0 )
```

**Interpretation:**
- Field 1: Sequential index (0-3)
- Field 2: 0x8740 (= 34,624) -- this is the primary TOC size padded to alignment (actual TOC = 34,596 bytes + 28 bytes padding)
- Field 3: Absolute file offsets -- 0x0040, 0x8780, 0x10EC0, 0x19600
  - Differences between consecutive offsets: 0x8740, 0x8740, 0x8740
  - These appear to reference 4 equally-spaced data blocks in the header region
- Field 4: Always 0

The data at offset 0x8780 is all zeros (possibly an empty/reserved block).
The data at offsets 0x10EC0 and 0x19600 contains pixel-like data (repeating `ff 8f 33 xx` patterns -- possibly CLUT/palette data or small textures).

After the 4 secondary index entries (at 0x8840), a different data structure begins:
```
0x8840: 0000000A 0000000B 00000000 00000000
0x8850: 00008004 10000000 0000000E 00000000
...
```
This appears to be VU microcode, GS register configs, or other PS2-specific
rendering setup data that persists through the header region up to 0x3E800.

---

## 6. Header Region Analysis (0x8840 - 0x3E7FF)

The ~220KB region between the secondary table and the first data sector contains
additional structured data:

- **0x8840 - 0x8B70:** Repeating 0x60-byte blocks with values like `0x8004`, `0x4100`, `0x400004`
  -- likely PS2 GS (Graphics Synthesizer) register initialization data
- **0x8B78 - onwards:** Entries with pattern `ffff0000 ffffffff 01010001...`
  -- possibly DMA chain descriptors or texture setup
- **0x10EC0, 0x19600:** Palette/CLUT data (4-byte RGBA entries with `ff 8f 33` pattern)
- **0x30000:** Data with `0x80` high-bit patterns -- possibly compressed or encoded PS2 data
- **0x3E000:** Structured data just before the data region begins

This region likely contains PS2 hardware initialization data, default palettes,
and boot-time resources that the game engine loads before accessing individual
file entries via the primary TOC.

---

## 7. Key Numbers Summary

| Property                        | Value                              |
|---------------------------------|------------------------------------|
| File size                       | 839,661,568 bytes (839 MB)         |
| Sector size                     | 2,048 bytes (0x800)                |
| Total sectors                   | 409,991                            |
| TOC entry count                 | 2,883                              |
| TOC entry size                  | 12 bytes                           |
| TOC total size                  | 34,596 bytes                       |
| Header region (sectors 0-124)   | 256,000 bytes (125 sectors)        |
| Data region start               | Sector 0x7D = offset 0x3E800       |
| Data region end                 | Sector 0x64187 = offset 0x320C3800 |
| First data entry                | Entry 0: sector 0x7D, 1 sector, type 1 |
| Last data entry                 | Entry 2882: sector 0x6403A, 333 sectors, type 9 |
| Smallest resource               | 1 sector = 2,048 bytes             |
| Largest observed resource       | 1,131 sectors = ~2.3 MB (type 0x0F)|
| All entries contiguous?         | YES -- no gaps, no overlaps        |
| Last entry end = file size?     | YES -- (0x6403A + 0x14D) * 0x800 = file size |

---

## 8. Extraction Strategy (Next Steps)

To extract all resources from PACKDATA.DIG:

1. Parse the 2,883 x 12-byte TOC at offset 0x0000
2. For each entry: `byte_offset = sector_offset * 2048`, `byte_size = sector_count * 2048`
3. Read `byte_size` bytes from `byte_offset`
4. Use the `type_code` field to determine file extension / decoder
5. The resource sub-header at the start of each block gives the actual payload size
   (as opposed to the sector-padded size)

To determine actual (non-padded) data size within each resource, read the uint32
at offset +4 within the resource block -- this appears to be the true payload size.

---

## 9. Open Questions

1. **What do the type codes map to?** Need to examine actual data content per type
   to determine if types correspond to textures (TIM2), models, scripts, audio (VAG/BD),
   map data, etc.

2. **Sub-header format:** The 16-byte sub-header at the start of each resource needs
   further analysis. The third field might be stride/alignment, record count, or
   compression flags.

3. **Secondary table purpose:** The 4-entry table at 0x8800 may describe boot-time
   resources or PS2 hardware init data. Its exact role is unclear.

4. **Header metadata (0x8840-0x3E7FF):** This ~220KB region needs dedicated analysis.
   It may contain critical information like string tables, file name hashes, or
   resource dependency graphs.

5. **Companion file:** There is no PACKDATA.DIR or separate index file -- the TOC
   is embedded at the start of PACKDATA.DIG itself.
