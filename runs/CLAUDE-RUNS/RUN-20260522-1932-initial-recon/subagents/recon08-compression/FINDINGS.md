# PACKDATA.DIG Compression Analysis Findings

**File:** `extracted/PACKDATA.DIG` (839,661,568 bytes / 800.8 MB)
**Date:** 2026-05-22

## Executive Summary

**PACKDATA.DIG contains NO standard compression.** The file is raw, uncompressed game data throughout its entire 839MB. This is good news for translation work -- text and data can be edited in-place without needing to decompress/recompress.

## Compression Signature Scan Results

| Format | Scan Method | Hits Found | Verified |
|--------|-------------|------------|----------|
| zlib (78 9C/DA/01/5E) | Every 2048 bytes, full file | 17 false positives | 0 of 17 decompress successfully |
| gzip (1F 8B) | Every 1MB boundary | 0 | N/A |
| SLLZ | Every 4 bytes, first 50MB | 0 | N/A |
| LZ* custom | Every 4 bytes, first 50MB | 75 (all false: 0x4C 0x5A byte coincidences) | N/A |
| TIM2 / VAGp / RIFF / OggS / PNG | Every 1MB, full file | 0 each | N/A |

All 17 zlib-header candidates failed decompression with errors like "invalid block type" and "invalid distance too far back" -- these are byte coincidences, not real zlib streams.

## Entropy Analysis

### Distribution (201 samples at 4MB intervals)

| Entropy Range | Count | Percentage | Interpretation |
|---------------|-------|------------|----------------|
| 0.0 - 4.0 (low) | 25 | 12.4% | Padding, sparse tables, simple structured data |
| 4.0 - 7.0 (medium) | 156 | 77.6% | Raw uncompressed game data (textures, models, tables) |
| 7.0 - 8.0 (high) | 20 | 10.0% | Dense data (high-color textures, audio, complex data) |

- **Min entropy:** 0.0000 (at ~764MB -- null padding region)
- **Max entropy:** 7.6297 (at ~328MB)
- **Mean entropy:** 5.7294
- **Median entropy:** 6.2448

### Entropy Profile Highlights

- **0-4 MB:** Very low entropy (2.3, then 0.1) -- file header / TOC area
- **80-88 MB:** High entropy spike (6.88-7.21) -- likely dense texture/model data
- **316-368 MB:** Sustained high entropy (7.0-7.6) -- probable texture atlas region
- **400-436 MB:** Mixed with low entropy dips (1.76, 2.39, 2.61) -- structured data / text tables
- **440-576 MB:** Remarkably uniform ~6.0-6.7 entropy -- large homogeneous data region (likely 3D models or level data)
- **604-624 MB:** Low entropy dips (1.52, 2.73-2.76) -- more structured/table data
- **608 MB:** Entirely filled with 0x53 ("SSSS") -- padding/alignment
- **764 MB:** Entirely null (entropy 0.0) -- empty padding

## Region Classification (50-sample survey)

| Category | Samples | Notes |
|----------|---------|-------|
| MEDIUM-ENTROPY (structured) | 23 | Dominant -- raw game data |
| HIGH-ENTROPY (image/compressed) | 8 | Dense but NOT compressed |
| SHIFT-JIS TEXT | 7 | Japanese text at ~64, 400, 416, 464, 640, 656, 784 MB |
| LOW-MEDIUM (text/structured) | 7 | Tables, indices, sparse data |
| SPARSE-STRUCTURED | 5 | Pointer tables, padding |

## 16MB Boundary Observations

The hex dumps at 16MB boundaries show no repeating container headers -- confirming this is one monolithic data blob, not a series of individually-packed archives.

Notable patterns:
- **0 MB:** TOC header with small u32 values (125, 126, 127...)
- **16 MB:** Structured records with incrementing counters
- **144 MB:** IEEE 754 float values (0x3F800000 = 1.0) -- 3D vertex/transform data
- **288 MB:** More floats (0x3F800000) -- geometry data
- **320 MB:** Repeating RGBA-like patterns (B2 B2 B2 80) -- raw texture pixels
- **416 MB:** All 0xFF bytes -- empty/unused region
- **432 MB:** Null padding transitioning to structured data
- **608 MB:** All 0x53 bytes -- filler padding
- **624 MB:** Float values again (0x3F7E0000) -- more geometry
- **768 MB:** Repeating color values (AA AA AA 80) -- more raw texture data

## Header/TOC Structure

The first ~312 bytes contain a table of contents with triplet entries:
```
(cumulative_byte_offset, element_count, type_code)
```

- First 3 entries are special (values 125-127, count=1, type=1)
- Subsequent entries: offset is cumulative (each = previous offset + previous size)
- Type codes observed: 1, 2, 3, 4, 10, 15, 20
- Offsets are very small (0-2063 range), suggesting these index into a **secondary lookup structure**, not directly into the 839MB file

This TOC likely maps to game resource entries (items, spells, stats) rather than file-level offsets.

## Implications for Translation

1. **No decompression needed** -- all data is raw and directly editable
2. **Shift-JIS text regions identified** at approximately: 64, 400, 416, 464, 640, 656, 784 MB
3. **No container format wrapping** -- changes can be made in-place if sizes are preserved
4. **The TOC at offset 0** needs further analysis to understand how it maps to the game's resource system
5. **Padding regions** (null, 0xFF, 0x53) provide potential space for expanded text if needed

## Output Files

- Full analysis: `dumps/compression_analysis.txt`
