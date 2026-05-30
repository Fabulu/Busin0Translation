# packdata_resources/ Debug Report
Date: 2026-05-28

## Directory Contents

`build/packdata_resources/` contains **49 files** (out of 2883 total resources in the manifest).

This is expected -- only patched/modified resources are placed here. The rebuild script
(`build/rebuild_packdata.py`) falls back to `extracted/packdata_raw/` for unmodified resources.

### Full File Listing

| File | Size | Date |
|------|------|------|
| 0034_type20.raw | 69,632 | May 30 15:14 |
| 0035_type02.raw | 6,144 | May 30 15:14 |
| 0036_type01.raw | 4,096 | May 30 15:14 |
| 0037_type01.raw | 4,096 | May 30 15:14 |
| **0038_type01.raw** | **8,192** | **May 30 15:14** |
| 0040_type01.raw | 4,096 | May 30 15:14 |
| 0041_type01.raw | 2,048 | May 30 15:14 |
| 0042_type01.raw | 2,048 | May 30 15:14 |
| 0043_type01.raw | 2,048 | May 30 15:14 |
| 0044_type01.raw | 4,096 | May 30 15:14 |
| 0045_type01.raw | 8,192 | May 30 15:14 |
| 0046_type03.raw | 22,528 | May 30 01:57 |
| 0047_type03.raw | 4,096 | May 30 01:57 |
| 0048_type01.raw | 4,096 | May 30 15:14 |
| 0049_type01.raw | 4,096 | May 30 15:14 |
| 0989_type02.raw | 550,912 | May 30 15:14 |
| 0990_type02.raw | 624,640 | May 30 15:14 |
| 1034_type02.raw | 573,440 | May 30 15:14 |
| 1188_type01.raw | 528,384 | May 30 10:00 |
| 1193_type02.raw | 6,144 | May 30 15:14 |
| 1194_type02.raw | 10,240 | May 30 15:14 |
| 1196_type02.raw | 133,120 | May 30 15:14 |
| 1197_type02.raw | 137,216 | May 30 15:14 |
| 1198_type02.raw | 24,576 | May 30 15:14 |
| 1199_type02.raw | 45,056 | May 30 15:14 |
| 1200_type02.raw | 55,296 | May 30 15:14 |
| 1201_type02.raw | 34,816 | May 30 15:14 |
| 1202_type02.raw | 61,440 | May 30 15:14 |
| 1203_type02.raw | 223,232 | May 30 15:14 |
| 1204_type02.raw | 135,168 | May 30 15:14 |
| 1205_type02.raw | 135,168 | May 30 15:14 |
| 1206_type02.raw | 79,872 | May 30 15:14 |
| 1207_type02.raw | 77,824 | May 30 15:14 |
| 1208_type02.raw | 133,120 | May 30 15:14 |
| 1209_type02.raw | 118,784 | May 30 15:14 |
| 1210_type02.raw | 114,688 | May 30 15:14 |
| 1211_type02.raw | 96,256 | May 30 15:14 |
| 1212_type02.raw | 75,776 | May 30 15:14 |
| 1213_type02.raw | 22,528 | May 30 15:14 |
| 1272_type01.raw | 67,584 | May 25 00:56 |
| 1347_type02.raw | 6,144 | May 30 15:14 |
| 1348_type02.raw | 14,336 | May 30 15:14 |
| 1349_type02.raw | 4,096 | May 30 15:14 |
| 1351_type02.raw | 6,144 | May 30 15:14 |
| 1353_type02.raw | 67,584 | May 30 15:14 |
| 1354_type02.raw | 38,912 | May 30 15:14 |
| 1355_type02.raw | 14,336 | May 30 15:14 |
| 2124_type01.raw | 34,816 | May 30 15:14 |
| 2654_type44.raw | 184,320 | May 30 15:14 |

## R38 (0038_type01.raw) Analysis

- **Present**: YES
- **Size**: 8,192 bytes (same as original)
- **Identical to original**: NO (4,960 bytes differ -- heavily patched)
- **Content**: Big-endian uint16 glyph indices
  - 2,774 non-zero values out of 4,096 total uint16s
  - 66 unique glyph values used
  - Value range: 2 to 65535
  - Sample from mid-file: `73 76 69 0 65 78 68 0 76 85 67 75 89` = "ILE" "AND" "LUCKY"
- **Verdict**: Contains ENGLISH glyph indices. The patching is working correctly.

## rebuild_packdata.py Behavior

The script reads from TWO directories with priority:
1. **`build/packdata_resources/{idx}_type{tc}.raw`** -- checked FIRST (patched files)
2. **`extracted/packdata_raw/{idx}_type{tc}.raw`** -- fallback (original files)

Only 49 of 2883 resources have patched versions. The remaining 2834 are read from the
original extracted directory. This is the correct and expected design.

## File Count Discrepancy Explained

- Manifest entries: 2,883
- Files in packdata_resources/: 49
- This is NOT a problem. The 49 files are the patched overrides.
  All other resources come from `extracted/packdata_raw/`.
