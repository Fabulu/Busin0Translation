# Minimal ISO Patch Test

**Date:** 2026-05-28
**Script:** `tools/minimal_test_patch.py`
**Output:** `build/BUSIN0_EN_minimal_test.iso`

## What This Test Does

Bypasses the entire build pipeline. Copies the original Japanese ISO and changes
exactly ONE glyph (2 bytes) directly in the binary, at the correct offset.

### The Change

| Field | Value |
|-------|-------|
| Resource | R38 (character creation / stat labels) |
| Message | MSG 3 (stat label row) |
| Original glyph | 346 (0x015A) = Japanese character for "strength/power" |
| New glyph | 56 (0x0038) = ASCII 'X' |
| ISO file offset | 0x232531C (byte 36,852,508) |
| PACKDATA LBA | 16029 |
| R38 sector offset | 0x7AD (1965 sectors into PACKDATA) |
| R38 absolute ISO offset | 0x2325000 |
| Glyph position | payload offset 780 (after 754-byte offset table) |

### What Was NOT Changed

- No directory entry sizes modified
- No TOC entries modified
- No sector counts changed
- No offset tables rebuilt
- ISO file size: identical (1,274,544,128 bytes)
- Literally 2 bytes changed: `01 5A` -> `00 38`

## How to Test

1. Load `build/BUSIN0_EN_minimal_test.iso` in PCSX2
2. Start a new game or go to character creation
3. Look at the stat labels on the character sheet
4. The label that normally shows the Japanese character for "strength" should show "X" instead

## Interpreting Results

### If 'X' appears where the Japanese character was:

The ISO binary patching approach is fundamentally correct. The game reads
PACKDATA.DIG from the ISO at LBA 16029, parses the TOC, and loads resource
data from the sector offsets. This means the build pipeline has a bug
(wrong offsets, bad TOC rebuild, size mismatch, etc.) that needs to be
tracked down.

### If the original Japanese character still appears:

Something fundamental is different about how the game loads data:
- The game might decompress/cache PACKDATA differently
- The game might read from a different location than expected
- The PACKDATA LBA might be wrong (though PVD parsing shows 16029)
- There could be a secondary data source

## R38 Message Context

The first 10 messages in R38 (original Japanese ISO):

| MSG | Content | Notes |
|-----|---------|-------|
| 0 | (empty) | |
| 1 | hp | ASCII already |
| 2 | hp/mhp | ASCII + JP slash |
| 3 | (strength) | **PATCHED: this character -> 'X'** |
| 4 | (wisdom) | |
| 5 | (faith) | |
| 6 | (vitality) | |
| 7 | (agility) | |
| 8 | (luck) | |
| 9 | (name) | |
| 10 | (level) | |

## Technical Details

The script (`tools/minimal_test_patch.py`) performs these steps:

1. Copies original ISO verbatim
2. Parses ISO9660 PVD (sector 16) to find root directory
3. Walks root directory to find PACKDATA.DIG (LBA=16029, size=839,661,568)
4. Reads R38 TOC entry at PACKDATA offset 38*12: sector_offset=0x7AD, sector_count=4, type=1
5. Reads R38 sub-header: payload_size=7512, stride=16
6. Scans payload for first FFFF delimiter (offset 754 = offset table end)
7. Scans glyph stream for first Japanese glyph (ID >= 95)
8. Finds glyph 346 at payload offset 780 (MSG 3)
9. Computes absolute ISO offset: PACKDATA_base + R38_sector_offset * 2048 + 16 + 780
10. Writes 0x0038 (glyph 'X') at that 2-byte position
11. Verifies read-back matches
