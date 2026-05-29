# Analysis: R2217, R2218, R2219 -- NOT Text Data

**Date**: 2026-05-28
**Verdict**: FALSE POSITIVE -- these resources contain 3D coordinate/position data, not translatable text.

## Summary

R2217-R2219 were flagged as "the largest untranslated text block (~2,500 groups)" by the
earlier dialogue scan. This analysis proves they contain **structured binary float data**
(3D coordinates), not text. The earlier scan was reading the entire raw resource file as a
flat BE-uint16 glyph stream, which caused Section 1 (model/map data) to be misinterpreted
as text with FFFF "delimiters" appearing naturally in the binary data.

## Evidence

### Section 2 is tiny and non-textual

| Resource | File Size | Section 1 | Section 2 | Records |
|----------|-----------|-----------|-----------|---------|
| R2217    | 65,536 B  | 63,808 B  | 1,316 B   | 38      |
| R2218    | 45,056 B  | 43,088 B  | 836 B     | 23      |
| R2219    | 45,056 B  | 44,208 B  | 516 B     | 15      |

Section 2 (the text section in dialogue resources) is less than 2% of the file.

### Section 2 contains fixed-size 32-byte float records

Structure per record:
```
Offset  Size  Content
+0x00   4     Two LE uint16 values (type/ID fields)
+0x04   12    Zero padding
+0x10   4     LE float (X coordinate, e.g. 3360.0, 5220.0)
+0x14   4     LE float (-0.0 or 0.0)
+0x18   4     LE float (Y coordinate, e.g. -392.0, -1622.0)
+0x1C   4     LE float (always 1.0 = 0x3F800000)
```

The `0x3F800000` (1.0f) at every 32-byte boundary is the homogeneous W coordinate,
confirming these are 3D/4D position vectors.

### How the earlier scan was fooled

The scan read `.raw` files as flat binary and split on `0xFFFF` bytes. Section 1
(62-44 KB of 3D model/mesh data) naturally contains many `0xFF` bytes that align
to form `0xFFFF` when read as BE uint16. This produced the false "1028 groups" /
"641 groups" / "855 groups" counts.

- No FFFE (line break) markers exist in section 2
- No control codes (>= 0xFB00) exist in section 2
- The glyph "hit rate" of ~72% was coincidental (many small values happen to
  map to valid glyph indices)

### Likely purpose

These appear to be **map waypoint / NPC spawn point tables** for dungeon floors.
The coordinate values (hundreds to thousands) are consistent with PS2 world-space
positions. The varying record counts (38, 23, 15) could represent different
dungeon floors or areas.

## Conclusion

- **Translatable text**: NONE
- **Action required**: Remove R2217-R2219 from the untranslated dialogue inventory
- **Impact on remaining work**: The "~2,500 groups" was an overcount; the actual
  untranslated text is in other resources (dungeon events R680-R911, system text
  R1067/R1095/R1103, etc.)

No translation batch file was created since there is nothing to translate.
