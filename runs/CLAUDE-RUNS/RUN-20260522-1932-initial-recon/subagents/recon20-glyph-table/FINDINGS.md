# Recon 20: Glyph Index Table Decode

## Summary

Complete analysis of the font/glyph data structures in the BUSIN 0 EXE (SLPM_653.78) at offsets 0x3C0600-0x3C1D04. Found and decoded:
- Two groups of font descriptor structs (28 bytes each) with 0xFFFF terminators
- An 84-entry ASCII glyph index lookup table (uint16 LE)
- A 133-entry per-glyph property table (28 bytes per entry, floats + atlas coords)
- MIPS code that performs linear search through the glyph table
- **Critical finding**: Japanese glyph mapping is NOT in the EXE; it lives in BSS RAM loaded from resources at runtime

## 1. Font Descriptor Structs

**Location:** Two groups at file offsets 0x3C0630 and 0x3C0700
**Struct size:** 28 bytes
**Total:** 20 entries (6 + TERM + 12 + TERM)

### Struct Layout
```c
struct FontDescriptor {     // 28 bytes
    uint16_t type;          // [0:2]   0x0002 = active, 0xFFFF = terminator
    uint16_t param_id;      // [2:4]   Glyph count or parameter (32-44)
    uint16_t tex_param_a;   // [4:6]   GS texture parameter / atlas Y offset
    uint16_t tex_param_b;   // [6:8]   GS texture parameter / glyph height or page
    uint32_t reserved;      // [8:12]  Always 0
    uint8_t  rgba[4];       // [12:16] Color: always 0x80808080 (neutral modulate)
    uint16_t tex_dim_w;     // [16:18] Always 0x0100 (256)
    uint16_t tex_dim_h;     // [18:20] Always 0x0100 (256)
    uint32_t pad[2];        // [20:28] Always 0
};
```

### Group A (0x3C0630): Small font, texB=0x0008

| # | Offset   | param_id | texA   | texB   |
|---|----------|----------|--------|--------|
| 0 | 0x3C0630 | 32       | 0x0018 | 0x0008 |
| 1 | 0x3C064C | 33       | 0x0030 | 0x0008 |
| 2 | 0x3C0668 | 35       | 0x0040 | 0x0008 |
| 3 | 0x3C0684 | 42       | 0x0068 | 0x0008 |
| 4 | 0x3C06A0 | 33       | 0x0080 | 0x0008 |
| 5 | 0x3C06BC | 37       | 0x0090 | 0x0008 |
|   | 0x3C06D8 | TERMINATOR (0xFFFF) | | |

### Group B (0x3C0700): 4 size groups x 3 sub-variants

| Group | texB (size) | Entries | param_id values | texA values |
|-------|-------------|---------|-----------------|-------------|
| 0     | 0x0010 (16) | 3       | 34, 33, 36      | 0x10, 0x50, 0x60 |
| 1     | 0x0020 (32) | 3       | 43, 33, 44      | 0x38, 0x50, 0x60 |
| 2     | 0x0030 (48) | 3       | 32, 33, 35      | 0x38, 0x50, 0x60 |
| 3     | 0x0040 (64) | 3       | 42, 33, 37      | 0x38, 0x50, 0x60 |

Each group likely represents a different font size/context. The 3 sub-variants within each group use different atlas regions (texA). The middle sub-variant always has param_id=33.

## 2. ASCII Glyph Index Table

**Location:** File 0x3C0870 (RAM 0x004C07F0)
**Entry size:** 2 bytes (uint16 LE)
**Entries:** 84
**Maps:** ASCII 0x20 (space) through 0x73 ('s') to glyph indices 1-93

### Complete Mapping

```
ASCII 0x20 ' ' -> glyph  1    ASCII 0x4A 'J' -> glyph 50
ASCII 0x21 '!' -> glyph  5    ASCII 0x4B 'K' -> glyph 51
ASCII 0x22 '"' -> glyph  6    ASCII 0x4C 'L' -> glyph 52
ASCII 0x23 '#' -> glyph  7    ASCII 0x4D 'M' -> glyph 53
ASCII 0x24 '$' -> glyph  8    ASCII 0x4E 'N' -> glyph 54
ASCII 0x25 '%' -> glyph  9    ASCII 0x4F 'O' -> glyph 55
ASCII 0x26 '&' -> glyph 10    ASCII 0x50 'P' -> glyph 56
ASCII 0x27 ''' -> glyph 13    ASCII 0x51 'Q' -> glyph 57
ASCII 0x28 '(' -> glyph 14    ASCII 0x52 'R' -> glyph 58
ASCII 0x29 ')' -> glyph 15    ASCII 0x53 'S' -> glyph 59
ASCII 0x2A '*' -> glyph 16    ASCII 0x54 'T' -> glyph 60
ASCII 0x2B '+' -> glyph 17    ASCII 0x55 'U' -> glyph 61
ASCII 0x2C ',' -> glyph 18    ASCII 0x56 'V' -> glyph 62
ASCII 0x2D '-' -> glyph 19    ASCII 0x57 'W' -> glyph 63
ASCII 0x2E '.' -> glyph 20    ASCII 0x58 'X' -> glyph 64
ASCII 0x2F '/' -> glyph 21    ASCII 0x59 'Y' -> glyph 65
ASCII 0x30 '0' -> glyph 22    ASCII 0x5A 'Z' -> glyph 66
ASCII 0x31 '1' -> glyph 23    ASCII 0x5B '[' -> glyph 67
ASCII 0x32 '2' -> glyph 24    ASCII 0x5C '\' -> glyph 68
ASCII 0x33 '3' -> glyph 25    ASCII 0x5D ']' -> glyph 69
ASCII 0x34 '4' -> glyph 26    ASCII 0x5E '^' -> glyph 70
ASCII 0x35 '5' -> glyph 27    ASCII 0x5F '_' -> glyph 71
ASCII 0x36 '6' -> glyph 28    ASCII 0x60 '`' -> glyph 72
ASCII 0x37 '7' -> glyph 29    ASCII 0x61 'a' -> glyph 73
ASCII 0x38 '8' -> glyph 30    ASCII 0x62 'b' -> glyph 74
ASCII 0x39 '9' -> glyph 33    ASCII 0x63 'c' -> glyph 75
ASCII 0x3A ':' -> glyph 34    ASCII 0x64 'd' -> glyph 76
ASCII 0x3B ';' -> glyph 35    ASCII 0x65 'e' -> glyph 77
ASCII 0x3C '<' -> glyph 36    ASCII 0x66 'f' -> glyph 78
ASCII 0x3D '=' -> glyph 37    ASCII 0x67 'g' -> glyph 79
ASCII 0x3E '>' -> glyph 38    ASCII 0x68 'h' -> glyph 80
ASCII 0x3F '?' -> glyph 39    ASCII 0x69 'i' -> glyph 81
ASCII 0x40 '@' -> glyph 40    ASCII 0x6A 'j' -> glyph 82
ASCII 0x41 'A' -> glyph 41    ASCII 0x6B 'k' -> glyph 83
ASCII 0x42 'B' -> glyph 42    ASCII 0x6C 'l' -> glyph 84
ASCII 0x43 'C' -> glyph 43    ASCII 0x6D 'm' -> glyph 85
ASCII 0x44 'D' -> glyph 44    ASCII 0x6E 'n' -> glyph 86
ASCII 0x45 'E' -> glyph 45    ASCII 0x6F 'o' -> glyph 89
ASCII 0x46 'F' -> glyph 46    ASCII 0x70 'p' -> glyph 90
ASCII 0x47 'G' -> glyph 47    ASCII 0x71 'q' -> glyph 91
ASCII 0x48 'H' -> glyph 48    ASCII 0x72 'r' -> glyph 92
ASCII 0x49 'I' -> glyph 49    ASCII 0x73 's' -> glyph 93
```

**Key observations:**
- Mapping is NOT 1:1 -- glyph indices have gaps: `[2, 3, 4, 11, 12, 31, 32, 87, 88]` are skipped
- Coverage stops at 's' (0x73) -- letters t-z and symbols ~}| are NOT in this table
- The gaps suggest glyph indices 2-4, 11-12, 31-32, 87-88 are reserved for other purposes (control codes, icons, etc.)
- Table terminated by 4+ zero bytes at 0x3C0918

## 3. Per-Glyph Property Structs

**Location:** File 0x3C0E78 (RAM 0x004C0DF8)
**Struct size:** 28 bytes
**Total:** 133 entries in 3 groups

### Groups

| Group | Float value | Count | File range          |
|-------|------------|-------|---------------------|
| 1     | 240.0      | 105   | 0x3C0E78-0x3C19F4   |
| 2     | 480.0      | 20    | 0x3C19F4-0x3C1C24   |
| 3     | 240.0      | 8     | 0x3C1C24-0x3C1D04   |

### 240.0-Group Struct Layout
```c
struct GlyphProperty {     // 28 bytes
    float    scale_x;      // [0:4]   Always 240.0
    float    scale_y;      // [4:8]   Always 240.0
    uint8_t  pad0;         // [8]     Always 0
    uint8_t  metric;       // [9]     Glyph metric/property value
    uint16_t pad1;         // [10:12] Always 0
    uint32_t pad2;         // [12:16] Always 0
    uint8_t  pad3;         // [16]    Always 0
    uint8_t  atlas_row;    // [17]    Atlas row index (0-6)
    uint8_t  atlas_col;    // [18]    Atlas column index (0-3)
    uint8_t  pad4;         // [19]    Always 0
    uint64_t pad5;         // [20:28] Always 0
};
```

### 480.0-Group Struct Layout (different)
Contains additional non-zero fields at bytes 8-16 and floats 60.0/-60.0 at bytes 20-27. These appear to be for a different rendering system (3D billboard text, damage numbers, etc.).

### Code Access Pattern

Function at RAM 0x001F7770 (file 0x0F77F0) accesses these structs:
```
addr = 0x004C0E01 + glyph_index * 28 + (arg2 & 0xFF) * 2
return byte_at(addr)
```
This reads byte 9 of the aligned struct (the `metric` field) when arg2=0.

## 4. Code Analysis: Glyph Lookup Function

**Function:** RAM 0x001A4B90 (file 0x0A4B90)

### Algorithm
1. Loads a character from an 80-byte struct table at BSS RAM 0x5191F0
2. Validates the character type (checks bytes 4-7 of the 80-byte struct against constants 2,5,6,7,8)
3. Builds a hash/encoded byte value from 4 sub-bytes via shifts and ORs
4. Linear-searches the 84-entry glyph table at 0x4C07F0
5. For each table entry, calls function at 0x1F7770 to get the glyph's metric value
6. Compares the encoded byte against the metric value
7. Returns the matching glyph index, or -1 if not found

### Key Constants
- Glyph table: RAM 0x004C07F0, 84 entries, searched linearly (limit check: `slti $r, $17, 84`)
- Per-glyph struct base: RAM 0x004C0E01 (byte 9 of aligned struct at 0x4C0DF8)
- Character struct table: BSS RAM 0x005191F0 (80-byte structs, loaded at runtime)
- Jump table for switch statement: RAM 0x004EA160 (file 0x3EA1E0)

## 5. Japanese Glyph Mapping: NOT in EXE

**This is the critical finding for the translation project.**

The Japanese glyph mapping (for the ~858 glyphs used in MSG files) is NOT stored in the EXE binary. It resides in BSS memory:

- **ELF file size:** 0x3FDC80 bytes
- **ELF memory size:** 0x479800 bytes
- **BSS segment:** RAM 0x4FDC80 to 0x579800 (506,752 bytes)
- **Character struct table:** RAM 0x5191F0 (within BSS, loaded from game resources)
- **Struct size:** 80 bytes per character

The code at RAM 0x00183500 (file 0x08351C) references this BSS table and the font rendering pointer table at RAM 0x4C08A0. The character data must be loaded from PACKDATA.DIG resources at runtime.

### Implications for Translation
- The glyph-to-character mapping cannot be extracted from the EXE alone
- The mapping is loaded dynamically, likely from the same resource that contains the font atlas texture
- To modify the glyph mapping, one would need to either:
  1. Identify and modify the resource file that populates the BSS character table
  2. Patch the EXE code to use a custom mapping
  3. Replace the font atlas texture and the ASCII glyph index table at 0x3C0870

## 6. Pointer Table at 0x3C0920 (NOT glyph-related)

**Location:** File 0x3C0920 (RAM 0x004C08A0)
**Entries:** 49 uint32 LE pointers
**Target range:** RAM 0x004EA1A0-0x004EB550

These pointers target floating-point data (material colors, lighting parameters) -- NOT glyph mapping data. The data at the targets consists of floats like 1.0 (0x3F800000), 0.3, 0.55, etc. One debug string at 0x3EA210 reads "Map Init!!!" confirming this is map/material initialization data.

## 7. Data Region Map (0x3C0600-0x3C1D04)

```
0x3C0600-0x3C062F  Unknown data (pre-font)
0x3C0630-0x3C06D8  Font Descriptor Group A (6 entries + TERM, texB=8)
0x3C06D8-0x3C06F4  Terminator + padding
0x3C06F4-0x3C0700  Zeros
0x3C0700-0x3C0850  Font Descriptor Group B (12 entries, 4 sizes x 3 variants)
0x3C0850-0x3C086C  Terminator + padding
0x3C086C-0x3C0870  Zeros
0x3C0870-0x3C0918  ASCII Glyph Index Table (84 entries, uint16 LE)
0x3C0918-0x3C0920  Zero padding (table terminator)
0x3C0920-0x3C09E4  Pointer table (49 entries to material/color data)
0x3C09E4-0x3C09F0  Zeros
0x3C09F0-0x3C0A00  Unknown float data
0x3C0A00-0x3C0C00  Float pairs + indices (rendering parameters, position offsets)
0x3C0C00-0x3C0C88  Repeating 0xE09304 values (17 entries of 8 bytes each)
0x3C0C88-0x3C0CB0  Coordinate pairs (int16 x,y for sprite positioning)
0x3C0CB0-0x3C0E30  Binary mask data (7-byte patterns, possibly tile collision)
0x3C0E30-0x3C0E68  Another pointer table (13 entries to RAM 0x4C0xxx)
0x3C0E68-0x3C0E78  Float pairs (240.0 x 2) + padding
0x3C0E78-0x3C19F4  Per-glyph property structs, 240.0 group (105 entries)
0x3C19F4-0x3C1C24  Per-glyph property structs, 480.0 group (20 entries)
0x3C1C24-0x3C1D04  Per-glyph property structs, 240.0 group (8 entries)
```

## Analysis Script

Written to: `analyze_glyph_table.py` in this directory.
