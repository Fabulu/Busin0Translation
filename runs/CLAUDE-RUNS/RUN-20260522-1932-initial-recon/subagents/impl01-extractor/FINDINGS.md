# PACKDATA.DIG Extractor -- Findings

## Scripts Written
- `tools/extract_packdata.py` -- extracts payload-only .bin files (no header, no padding)
- `tools/extract_packdata_raw.py` -- extracts raw .raw files (16-byte header + sector-padded)

## Verification Results
All three structural assertions passed:
- First valid entry starts at sector 0x7D (byte 256,000) -- **CONFIRMED**
- Outlier indices 1370 (sector_offset=0x55) and 2100 (sector_offset=0x11) skipped -- **CONFIRMED**
- Last entry ends at byte 839,661,568 = file size -- **CONFIRMED** (perfect coverage)

## Extraction Summary
- **2,881 files** extracted (2,883 TOC entries minus 2 outliers)
- **0 errors** during extraction
- Payload extraction: 260,033,031 bytes total
- Raw extraction: 839,405,568 bytes total (839,661,568 minus 256,000 byte TOC region)

## Type Distribution (36 distinct type codes)
| Type | Count | Type | Count |
|------|-------|------|-------|
|  1   | 1642  |  2   |  617  |
|  3   |  226  |  4   |  201  |
|  5   |   33  |  6   |   46  |
|  7   |   10  |  8   |   16  |
|  9   |    4  | 10   |   11  |
| 11   |    7  | 12   |   15  |
| 13   |    3  | 14   |    7  |
| 15   |    4  | 16   |    3  |
| 17   |    3  | 18   |    1  |
| 19   |    2  | 20   |    3  |
| 22   |    7  | 24   |    2  |
| 26   |    1  | 27   |    3  |
| 29   |    2  | 31   |    1  |
| 32   |    1  | 36   |    1  |
| 41   |    1  | 44   |    1  |
| 46   |    1  | 57   |    1  |
| 59   |    1  | 62   |    1  |
| 66   |    1  | 104  |    1  |
| 181  |    1  |      |       |

Type 1 dominates (57% of entries), followed by type 2 (21%) and type 3 (8%).

## Output Locations
- Payload files: `extracted/packdata_resources/NNNN_typeNN.bin`
- Raw files: `extracted/packdata_raw/NNNN_typeNN.raw`
- Manifest: `extracted/packdata_resources/manifest.json`

## Key Observations
- The overhead ratio (raw 839MB vs payload 260MB) shows significant sector padding (~69% padding).
- 36 distinct type codes suggests a rich variety of resource formats to classify.
- The sub-header stride field equals type_code * 16, as documented.
- No header anomalies detected (header_zero fields were always 0 for all entries based on zero errors).
