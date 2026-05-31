# Extended Menu Tiles: Glyph IDs 867-931

**Date:** 2026-05-28

## Summary

Added 33 new entries (62 glyph IDs) to `data/menu_labels.csv` covering glyph IDs 867-931. These are the "gap" entries identified by font_tile_gap_analysis.md -- menu struct records for shop, church, quest, dungeon, and system menus that were previously uncovered.

## Changes Made

### 1. data/menu_labels.csv -- 33 new rows (IDs 106-138)

| CSV ID | Glyph IDs | Japanese | English | Strategy | Context |
|--------|-----------|----------|---------|----------|---------|
| 106 | 867,868 | assist | assist | tile_pair | personality trait |
| 107 | 869,870 | co-op | co-op | tile_pair | party management |
| 108 | 871,872 | sell | sell | abbrev | guild shop |
| 109 | 873,874 | setup | setup | tile_pair | guild place request |
| 110 | 875,876 | quest | quest | tile_pair | guild quest flag |
| 111 | 877,878 | enlist | enlist | tile_pair | guild recruit |
| 112 | 879,880 | update | update | tile_pair | guild renew |
| 113 | 881,882 | misc | misc | abbrev | guild misc |
| 114 | 883,884 | church | church | tile_pair | church service |
| 115 | 885,886 | temple | temple | tile_pair | temple/repair |
| 116 | 887,888 | floor | floor | tile_pair | dungeon level |
| 117 | 889,890 | rank up | rank up | tile_pair | level up |
| 118 | 891,892 | cure | cure | abbrev | church healing |
| 119 | 893,894 | rank | rank | abbrev | hidden rank |
| 120 | 895,896 | like | like | abbrev | affinity |
| 121 | 897,898 | hate | hate | abbrev | affinity |
| 122 | 902,903 | accept | accept | tile_pair | quest accept |
| 123 | 904,905 | trade | trade | tile_pair | shop commerce |
| 124 | 906,907 | train | train | tile_pair | training |
| 125 | 908,909 | sorry | sorry | tile_pair | regret/unavailable |
| 126 | 910,911 | sort | sort | abbrev | display arrange |
| 127 | 912,913 | check | check | tile_pair | status check |
| 128 | 914,915 | relics | relics | tile_pair | collection |
| 129 | 916,917 | ruins | ruins | tile_pair | dungeon ruins |
| 130 | 918,919 | ancient | ancient | tile_pair | far/decay |
| 131 | 920,921 | loyal | loyal | tile_pair | wait/loyal |
| 132 | 922,0 | real | real | abbrev | system |
| 133 | 923,0 | war | war | abbrev | system |
| 134 | 924,0 | ? | ? | abbrev | system unknown |
| 135 | 925,0 | info | info | abbrev | system report |
| 136 | 926,927 | reward | reward | tile_pair | quest reward |
| 137 | 928,929 | config | config | tile_pair | settings |
| 138 | 930,931 | quit | quit | abbrev | retreat |

### 2. tools/generate_font_atlas.py -- Extended atlas dimensions

Changes:
- `ATLAS_H`: 512 -> 540 (45 rows of 12px cells)
- `ROWS`: 42 -> 45 (dynamic: `ATLAS_H // CELL_H`)
- TEX0 TH field patched: 9 -> 10 (2^10 = 1024 pixel height) when atlas exceeds 512px
- Page layout: 8 pages -> 10 pages (5 page-rows x 2 columns)
- Pixel data: 65,536 -> 81,920 bytes
- Output file: 65,792 -> 82,176 bytes (header + pixels + palette)

### 3. Atlas regeneration results

```
Injected 256 menu tiles into atlas (was 184)
Atlas preview: 256x540 pixels
Output binary: 82,176 bytes
```

## Atlas Capacity Analysis

| Range | Glyph IDs | Atlas Row | Y Position | Status |
|-------|-----------|-----------|------------|--------|
| Original (0-881) | 0-881 | 0-41 | 0-503 | Fits in 256x512 |
| Extended row 42 | 882-902 | 42 | 504-515 | BEYOND original 512px |
| Extended row 43 | 903-923 | 43 | 516-527 | BEYOND original 512px |
| Extended row 44 | 924-944 | 44 | 528-539 | BEYOND original 512px |

## TEX0 TH Patch (Critical)

The original R1272 header contains a GS TEX0 register value at offset 0x50 with TH=9 (height=512). Since our atlas extends to 540 rows, we patch TH to 10 (height=1024) so the PS2 GS texture sampler can address cells beyond row 42.

**Risk assessment**: The GS DMA upload code in the EXE may use a separate TRXREG value to control how many rows are actually transferred to VRAM. If the DMA transfer height is hardcoded to 512 in the EXE, only the first 512 rows will be uploaded regardless of TEX0 TH. In that case:

- IDs 867-881 (row 41, y=492-503): **Fully visible** -- within 512px
- IDs 882-902 (row 42, y=504-515): **Partially visible** -- top 8px uploaded, bottom 4px clipped
- IDs 903-931 (rows 43-44, y=516-539): **Not visible** -- fully beyond 512px DMA transfer

**Mitigation**: If in-game testing shows rows 42+ are blank, the EXE DMA transfer code at the R1272 upload site needs to be patched to transfer more rows. The sub-header payload_size field is already updated by `build_full_english_v2.py`, so if the upload code reads the size dynamically, it should work.

## Build Pipeline Compatibility

The `build_full_english_v2.py` pipeline at STEP 3 writes `len(font_data)` as the payload size in the sub-header:
```python
new_sub = struct.pack('<IIII', h0, len(font_data), h2, h3)
```

This means the larger atlas (82,176 bytes vs 65,792) is automatically handled -- the sub-header's size field will reflect the new size, and the packdata rebuild pipeline will allocate enough sectors.

## Verification

- 256 menu tiles rendered (97 original glyphs + 159 menu label entries minus skips/empties)
- All tile_pair entries confirmed to have foreground pixels on both halves
- Atlas preview at `build/english_font_atlas_preview.png` shows 256x540 image
- Binary output at `build/english_font_atlas.bin` (82,176 bytes)

## Next Steps

1. **In-game testing**: Build ISO with new atlas, verify shop/church/dungeon menus show English
2. **DMA check**: If rows 42+ are blank in-game, investigate EXE R1272 upload code and patch TRXREG height
3. **Glyph IDs 677-682**: These 6 additional glyph IDs (from idx 47-49 in the all_screens report) are NOT in the 867-931 range and need separate handling -- they are at rows 32-33 (y=384-407), well within the original 512px atlas
