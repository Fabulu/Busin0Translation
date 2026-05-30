# Type-02 Resource Verification: R600-R799

Date: 2026-05-28

## Summary

**No untranslated dialogue found in R600-R799 type-02 resources.**

All 96 type-02 resources in this range were scanned. Every one is either:
- Already processed (16 resources, all tagged as [DATA] layout/coordinate tables)
- Binary data (3D models, dungeon geometry, animation data, texture/palette data)

## Methodology

Three-pass analysis was performed:

### Pass 1: FFFE Line Break Count
Counted FFFE (line break), FFFF (terminator), and FB00 (speaker tag) occurrences across entire files. 76 of 96 files had FFFE > 0, but further analysis showed these are false positives.

### Pass 2: Context Decoding Around FFFE
Decoded uint16 values surrounding each FFFE position using the glyph map. Results showed 3D floating-point data (3F80=1.0, 4000=2.0, BF4C, etc.) around every FFFE occurrence, confirming these are coincidental pattern matches in vertex/animation data, not MSG line breaks.

### Pass 3: Consecutive Non-Zero Glyph Runs
Scanned for runs of consecutive uint16 values that map to glyphs in msg_glyph_map.json, excluding 0x0000. Real dialogue produces runs of varied kanji/kana forming grammatical sentences. Instead, we found:
- Repeated single characters ("誉誉誉誉" = same uint16 value repeating)
- Alternating pairs ("誉...荷...誉...荷" = two alternating binary values)
- No grammatical Japanese sentences anywhere in the range

## Key Evidence: Already-Translated Resources

The 16 "translated" resources in this range (R677, R690, R712, R715, R726, R741, R750, R757, R769, R780, R785, R787, R793, R795, R797, R799) were all tagged as:
```
[DATA] Status screen layout / coordinates table
[DATA] Battle UI layout / coordinates table
[DATA] UI control data / coordinates table
```
None contain actual dialogue text.

## Detailed Results

| RID | Size | FFFF | FFFE | FB00 | Verdict | Status |
|-----|------|------|------|------|---------|--------|
| 600 | 2,048 | 0 | 0 | 0 | BINARY | untranslated |
| 603 | 2,048 | 0 | 0 | 0 | BINARY | untranslated |
| 675 | 825,344 | 38 | 16 | 12 | BINARY (3D model) | untranslated |
| 677 | 956,416 | 84 | 65 | 10 | BINARY (3D model) | [DATA] translated |
| 679 | 1,343,488 | 19 | 18 | 14 | BINARY (3D model) | untranslated |
| 680 | 135,168 | 152 | 0 | 1 | BINARY | untranslated |
| 681 | 2,269,184 | 81 | 40 | 25 | BINARY (3D model) | untranslated |
| 683 | 700,416 | 47 | 44 | 6 | BINARY (3D model) | untranslated |
| 684 | 120,832 | 62 | 1 | 0 | BINARY | untranslated |
| 685 | 1,042,432 | 13 | 13 | 26 | BINARY (3D model) | untranslated |
| 686 | 106,496 | 96 | 0 | 0 | BINARY | untranslated |
| 687 | 1,085,440 | 69 | 54 | 11 | BINARY (3D model) | untranslated |
| 688 | 131,072 | 125 | 0 | 0 | BINARY | untranslated |
| 689 | 923,648 | 102 | 226 | 8 | BINARY (3D model) | untranslated |
| 690 | 96,256 | 1104 | 2 | 0 | BINARY | [DATA] translated |
| 691 | 970,752 | 106 | 102 | 12 | BINARY (3D model) | untranslated |
| 693 | 743,424 | 83 | 188 | 6 | BINARY (3D model) | untranslated |
| 694 | 51,200 | 86 | 0 | 0 | BINARY | untranslated |
| 695 | 479,232 | 8 | 6 | 3 | BINARY (3D model) | untranslated |
| 697 | 706,560 | 23 | 37 | 4 | BINARY (3D model) | untranslated |
| 698 | 124,928 | 104 | 0 | 0 | BINARY | untranslated |
| 699 | 1,058,816 | 9 | 18 | 18 | BINARY (3D model) | untranslated |
| 701 | 958,464 | 91 | 70 | 12 | BINARY (3D model) | untranslated |
| 703-709 | various | various | various | various | BINARY (3D models) | untranslated |
| 711-739 | various | various | various | various | BINARY (3D models) | untranslated |
| 741 | 2,670,592 | 256 | 209 | 79 | BINARY (3D model) | [DATA] translated |
| 745-799 | various | various | various | various | BINARY (3D models) | mixed |

## Conclusion

The R600-R799 type-02 range contains **dungeon/battle scene composite resources** (3D models with associated layout data). The FFFE/FFFF/FB00 patterns that initially suggested dialogue are coincidental matches in floating-point vertex data, animation curves, and coordinate tables.

No batch_verify_600_750.json was created because no translatable dialogue exists in this range.
