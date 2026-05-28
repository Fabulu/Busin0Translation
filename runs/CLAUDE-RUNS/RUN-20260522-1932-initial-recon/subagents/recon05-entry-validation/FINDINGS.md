# PACKDATA.DIG TOC Structure - Complete Analysis

## File Overview

- **File**: `extracted/PACKDATA.DIG`
- **Size**: 839,661,568 bytes (800.8 MB), hex 0x320C3800
- **Sector size**: 2048 bytes (confirmed: last_sector * 2048 == file_size exactly)

## TOC (Table of Contents) Format

### Header Structure

The file begins with a flat array of **12-byte entries** at offset 0, each consisting of 3 little-endian uint32 values:

```
struct TOCEntry {
    uint32_t sector_offset;   // A: starting sector (multiply by 2048 for byte offset)
    uint32_t sector_count;    // B: number of 2048-byte sectors this sub-file occupies
    uint32_t type;            // C: type/category identifier
};
```

### Key Property: Cumulative Offsets

**Confirmed with 100% accuracy**: `A[i+1] == A[i] + B[i]` for all consecutive valid entries. Each sub-file's data immediately follows the previous one with no gaps (at sector granularity). The entries are essentially a packed allocation table.

### TOC Layout in File

The TOC occupies **2883 entries x 12 bytes = 34,596 bytes** (0x8724 bytes), covering file offsets 0x0000 through 0x8723. After that is zero-padding/garbage until sector 0x7d (the first data sector).

### Entry Groups and "Outlier" Markers

The 2883 entries divide into **3 contiguous groups** separated by 2 special "outlier" entries:

| Group | Entry Range | Count | Sector Range | Byte Range |
|-------|-------------|-------|--------------|------------|
| 1 | 0 - 1369 | 1370 | 0x7d - 0x35ea8 | 0x3E800 - 0x6BD5_0000 |
| *outlier* | 1370 | 1 | A=0x55, B=0x28, C=4 | (not data) |
| 2 | 1371 - 2099 | 729 | 0x35eaa - 0x485d6 | 0x6BD5_4000 - 0x90BA_C000 |
| *outlier* | 2100 | 1 | A=0x11, B=0x44, C=4 | (not data) |
| 3 | 2101 - 2882 | 782 | 0x486d8 - 0x64187 | 0x90DB_0000 - 0x320C_3800 |

**Total valid data entries: 2881** (1370 + 729 + 782)

### Outlier Entries Form a Recursive Chain

The outlier entries encode the cumulative structure of the TOC header itself:

- Entry 2100: A=0x11, B=0x44 --> A+B = 0x55 (links to entry 1370's A)
- Entry 1370: A=0x55, B=0x28 --> A+B = 0x7d (links to entry 0's A)
- Entry 0: A=0x7d (first data sector)

This means: the first 0x11 sectors (0-0x10) hold some metadata/TOC, then 0x44 sectors (0x11-0x54) hold more, then 0x28 sectors (0x55-0x7C) hold more, and actual sub-file data starts at sector 0x7d.

### Type Values (Field C)

Distribution across 2881 valid entries:

| C Value | Hex | Count | Meaning (inferred) |
|---------|-----|-------|---------------------|
| 1 | 0x01 | ~409 | Small data blocks (many are single-sector) |
| 2 | 0x02 | ~62 | Medium data blocks |
| 3 | 0x03 | 5 | Larger structures |
| 4 | 0x04 | ~20 | Common data type (textures/models?) |
| 6 | 0x06 | 1 | Rare type |
| 10 | 0x0A | 1 | Rare type |
| 15 | 0x0F | 1 | Rare type |
| 20 | 0x14 | 1 | Rare type |
| 62 | 0x3E | (seen) | Rare type |

## Sub-File Internal Header

Each sub-file at `sector_offset * 2048` begins with a **16-byte internal header**:

```
Offset  Size  Description
0x00    4     Always 0x00000000 (reserved/padding)
0x04    4     uint32 LE: actual data size in bytes
0x08    4     uint32 LE: type code = C * 0x10  (e.g., C=4 -> 0x40)
0x0C    4     Always 0x00000000
```

**Confirmed for all tested entries**: `type_code == C * 16` and `actual_size <= B * 2048`.

The actual sub-file payload begins at byte offset 16 within each sector-aligned block. The `actual_size` field gives the exact byte length of the payload (excluding the 16-byte header), which is always <= `(sector_count * 2048) - 16`.

## Known Magic Numbers Found

Within the data region:
- **RIFF** (WAV audio): found at 0x5072D (inside entry 3, C=3, which covers 0x40000-0x88000)
- **BMP** fragments: found at various offsets within data entries
- **PS2 VIF/GIF** data: at sector-aligned boundaries within entries

## How to Unpack PACKDATA.DIG

Algorithm:

```
1. Read 12-byte entries starting at offset 0
2. Stop when entry A drops (outlier) or all-zero triple found at index > 4
3. Skip outlier entries (where A[i+1] != A[i] + B[i] but A[i+2] == A[i] + B[i])
4. For each valid entry:
   a. Seek to sector_offset * 2048
   b. Read 16-byte sub-header
   c. Extract actual_size from bytes 4-7 (uint32 LE)
   d. Extract type_code from bytes 8-11 (uint32 LE, should == C * 16)
   e. Read actual_size bytes starting at (sector_offset * 2048) + 16
   f. Save as sub-file (name: entry index or sector offset, ext based on type)
```

## Files

- **Script**: `tools/parse_packdata_toc.py` (full analysis script)
- **Raw analysis output**: `dumps/packdata_toc_analysis.txt`
- **Verification output**: `dumps/packdata_toc_analysis2.txt`
