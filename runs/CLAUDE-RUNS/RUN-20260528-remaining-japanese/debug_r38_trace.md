# R38 Debug Trace -- Root Cause Found

## Summary

R38 translations are NOT showing in-game because **build_v9.py Step 2 destroys the sub-header** of the R38 resource file, making it unparseable by the game engine.

## Root Cause

`build_v9.py` Step 2 (line 84) scans for `0xFFFF` from byte 0 of the raw file:

```python
fp = [i for i in range(0, len(orig) - 1, 2) if struct.unpack_from('>H', orig, i)[0] == 0xFFFF]
```

This treats the **entire file** as a flat glyph stream. But R38 (type-01) has structure:

| Bytes     | Content                                      |
|-----------|----------------------------------------------|
| 0-15      | 16-byte sub-header (zero1, payload_size=7512, stride=16, zero2) |
| 16-771    | Offset table: 188 entries + count entry = 189 x 4 bytes = 756 bytes |
| 770-771   | **Offset table FFFF flag** (flags field of last entry) |
| 772+      | Actual glyph stream (188 FFFF-terminated groups) |

The offset table's last entry has `flags = 0xFFFF` at byte 770. Step 2's scan from byte 0 picks this up as the **first** FFFF, creating:

- **Group 0** = bytes 0..772 (sub-header + entire offset table)
- **Groups 1-188** = the real glyph groups

Translation message 1 (`"hp/mhp /"`) maps to `mi = gi + 1 = 1`, so group 0 gets "translated" -- its content (the sub-header + offset table) is **overwritten with glyph data**.

### Result in the patched file

```
Original byte 0:  00 00 00 00 58 1d 00 00 10 00 00 00 ...  (valid sub-header)
Patched  byte 0:  00 48 00 50 00 0f 00 4d 00 48 00 50 ...  (glyphs: "hp/mhp")
```

The game reads the sub-header, gets `payload_size = 0x00500048` (garbage), and fails.

## Pipeline Trace

1. **Step 1** (`build_full_english_v2.py`): Runs silently, writes `build/PACKDATA.DIG` and `build/packdata_resources/0038_type01.raw`. The v2 pipeline correctly parses the offset table and preserves the sub-header. However...

2. **Step 2** (fixed-size injection): Reads `extracted/packdata_raw/0038_type01.raw` (original) and writes `build/packdata_resources/0038_type01.raw`, **overwriting** Step 1's output. This is where the corruption happens.

3. **Step 6** (merge): Copies `build/patched_type2/*` into `build/packdata_resources/`. R38 is NOT in `patched_type2/` (it's type-01, not type-02), so the corrupted file from Step 2 survives.

4. **Step 7** (`rebuild_packdata.py`): Reads `build/packdata_resources/0038_type01.raw` (the corrupted one) and packs it into `build/PACKDATA_v3.DIG`.

5. **Step 8**: Writes `PACKDATA_v3.DIG` into the ISO. The corruption is baked in.

## Verification

```
PACKDATA_v3.DIG TOC[38]: sector_offset=1966, sector_count=4, type_code=1
R38 in PACKDATA_v3 matches corrupted patched file: True
R38 in PACKDATA_v3 matches original: False
R38 in ISO matches PACKDATA_v3: True  (corruption is in the ISO)
```

## Fix

In `build_v9.py` Step 2, the FFFF scan must skip the sub-header and offset table. The glyph stream starts **after** the offset table (at byte 772 for R38). The scan should be:

```python
# Parse sub-header to find payload region
h_payload = struct.unpack_from('<I', orig, 4)[0]
# Parse offset table to find glyph stream start
# (reuse the same logic as build_full_english_v2.py)
# Then scan for FFFF only within the glyph stream
fp = [i for i in range(stream_start, 16 + h_payload, 2)
      if struct.unpack_from('>H', orig, i)[0] == 0xFFFF]
```

The message numbering must also be adjusted: group index 0 in the glyph stream corresponds to message 1 in the translations.

## Affected Resources

This bug affects ALL type-01 resources with offset tables processed in Step 2: **R36, R37, R38, R40, R41, R42, R43, R44, R45, R48, R49**. Each one has its sub-header destroyed the same way. R34 (type-20), R35 (type-02), R2124 (type-01), and R2654 (type-44) may also be affected depending on their internal structure.

## File Timestamps

- `build/packdata_resources/0038_type01.raw`: 2026-05-30 15:14 (corrupted)
- `build/PACKDATA_v3.DIG`: 2026-05-28 20:39 (also corrupted, from earlier build)
- `build/BUSIN0_EN_v9.iso`: 2026-05-30 15:14 (contains corrupted R38)
- `extracted/packdata_raw/0038_type01.raw`: 2026-05-22 22:29 (pristine original)
