# R1186 Analysis (type-20)

## Verdict: NOT TRANSLATABLE - 3D Scene/Cutscene Data

## File Details
- **Path**: `extracted/packdata_raw/1186_type20.raw`
- **Size**: 997,376 bytes (997 KB)
- **Format**: Type-20 container with 20 sub-entries (indices 0-19)

## Structure

The file has a 16-byte-per-entry LE TOC at offset 0x00:
```
[idx:u32] [size:u32] [offset:u32] [zero:u32]
```

### Sub-entry Summary

| Index | Size     | Offset   | Content Type |
|-------|----------|----------|--------------|
| 0     | 500,328  | 0x140    | 3D transform data (float 1.0 matrices) |
| 1     | 433,580  | 0x7A3B0  | Binary blob (0x13 padding header) |
| 2     | 29,068   | 0xE4160  | TCAM - Camera animation |
| 3-7   | 140 each | various  | TLIM - Light/limit data |
| 8     | 164      | 0xEB5C0  | TLIM variant |
| 9-13  | 140 each | various  | TLIM - Light/limit data |
| 14    | 18,692   | 0xEB940  | TCAM - Camera animation |
| 15    | 10,996   | 0xF0250  | Unknown binary |
| 16-18 | 140 each | various  | TLIM - Light/limit data |
| 19    | 1,348    | 0xF2F00  | TLIM - Light/limit data |

## Evidence Against Text

1. **TCAM magic bytes** (0x5443414D) in sub-entries 2 and 14 - camera animation format
2. **TLIM magic bytes** (0x544C494D) in sub-entries 3-13, 16-19 - light/limit definitions
3. **IEEE 754 floats throughout**: 0x3F800000 (1.0) in sub-entry 0 header (identity matrices)
4. **No glyph markers**: Only 6 occurrences of 0xFFFF in 500KB (noise, not terminators), zero FFFE line breaks
5. **No offset tables** pointing to glyph streams

## Conclusion

R1186 is a 3D cutscene resource containing camera paths (TCAM) and lighting definitions (TLIM) with floating-point coordinate data. No text content exists. Skipping translation.
