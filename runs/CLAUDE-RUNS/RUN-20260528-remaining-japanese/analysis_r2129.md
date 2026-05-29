# R2129 Analysis (Resource Index 2129, Type 15)

Generated: 2026-05-28

## Verdict: 3D Model/Scene Data -- NOT Translatable

R2129 is a large (2.3 MB) type-15 resource containing 3D geometry, transformation
matrices, and PS2 GPU rendering packets. It contains no translatable text.

## File Structure

```
File size:     2,357,248 bytes (2,302 KB)
Sub-sections:  15 (indexed 0-14 in a 16-byte-per-entry TOC at file offset 0)
TOC format:    LE uint32 x 4: index, size, offset, zero
```

### Section Table

| Idx | Offset     | Size (bytes) | Type                    |
|-----|------------|-------------|-------------------------|
|  0  | 0x0000F0   |    326,612  | 3D geometry + transforms |
|  1  | 0x04FCD0   |    185,040  | PS2 GS/VIF GPU packets  |
|  2  | 0x07CFA0   |    139,072  | PS2 GS/VIF GPU packets  |
|  3  | 0x09EEE0   |    160,020  | 3D geometry + transforms |
|  4  | 0x0C6000   |    178,624  | PS2 GS/VIF GPU packets  |
|  5  | 0x0F19C0   |     36,512  | PS2 GS/VIF GPU packets  |
|  6  | 0x0FA860   |    194,324  | 3D geometry + transforms |
|  7  | 0x129F80   |    207,568  | PS2 GS/VIF GPU packets  |
|  8  | 0x15CA50   |     48,688  | PS2 GS/VIF GPU packets  |
|  9  | 0x168880   |    169,300  | 3D geometry + transforms |
| 10  | 0x191DE0   |    248,784  | PS2 GS/VIF GPU packets  |
| 11  | 0x1CE9B0   |     20,640  | PS2 GS/VIF GPU packets  |
| 12  | 0x1D3A50   |    163,652  | 3D geometry + transforms |
| 13  | 0x1FB9A0   |    246,736  | PS2 GS/VIF GPU packets  |
| 14  | 0x237D70   |     30,112  | PS2 GS/VIF GPU packets  |

### Section Type Details

**Geometry sections (0, 3, 6, 9, 12):**
- 16-byte header: LE uint32 x 4, format: (vertex_count?, param1, param2, 2)
- Contain thousands of IEEE 754 float 1.0 values (identity matrix components)
- Contain 4x4 transformation matrices (position, rotation, scale)
- FFFF values here are float NaN/sentinel, NOT text end markers
- No FFFE (line break) markers at 2-byte aligned positions

**GPU packet sections (1, 2, 4, 5, 7, 8, 10, 11, 13, 14):**
- Header: LE uint32 x 4, format: (count, 2*count, 0, 0)
- Characteristic PS2 VIF command patterns (0x04800000, 0x10000000)
- GS register writes and DMA transfer descriptors
- No text content

## Evidence Against Text Content

1. No valid FFFE (line break) glyph markers at aligned positions in any section
2. FFFF occurrences are embedded within float sequences (3D vertex/matrix data)
3. "ASCII strings" found are sequential byte runs (0x20-0x2F etc.), not real text
4. Section headers do not match the MSG/type-15 text format (R39 style)
5. GPU packet sections have PS2 VIF/GS command signatures

## Conclusion

This resource is likely a dungeon map, 3D scene, or model pack consisting of
5 geometry chunks paired with their corresponding GPU rendering data. No
translation action is needed.
