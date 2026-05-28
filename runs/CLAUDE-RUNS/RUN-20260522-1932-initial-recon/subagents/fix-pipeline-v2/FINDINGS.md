# Fixed Injection Pipeline v2 -- FINDINGS

**Date:** 2026-05-22
**Output:** `build/build_full_english_v2.py` (572 lines)

---

## Bugs Fixed

### Bug 1: Font Atlas Assembly (palette position)
**Status:** Already fixed in `tools/generate_font_atlas.py` -- no change needed here.

### Bug 2: Message Counting Mismatch
**Root cause:** The v1 pipeline (`build/build_full_english.py`, line 79) splits the glyph stream on `0xFFFF` only, yielding FFFF-group indices. But the translation chunks from the decoder (`build/decode_r43.py`) also used both `0xFFFE` and `0xFFFF` as separators, yielding a different message count.

**Investigation finding:** After examining `data/full_decoded_text.txt` and comparing with the translation chunk files (especially `chunk_r43_fix.json`), the message indices in the translation chunks actually correspond to **FFFF-group numbers** (1-indexed). The ` / ` separators within each translation string represent **FFFE line breaks** within a single FFFF group. This was confirmed by:
- Resource 43: 39 FFFF groups, translations target groups 1-26
- Resource 34: 30 FFFF groups in payload, translations target groups 1-29
- The fix chunks (`chunk_r43_fix.json`) explicitly contain multi-line text like `"Hey there, / how'd that job go? /   / "` targeting a single FFFF group index

**Fix:** The v2 pipeline parses FFFF-delimited groups and replaces entire groups. Internal ` / ` in translation text is converted to `0xFFFE` line-break tokens.

### Bug 3: Offset Table Not Rebuilt
**Root cause:** The v1 pipeline preserves the original offset table bytes (`pre = raw[16:ss]`) but does not update the byte offsets stored in the table. When English translations have different lengths than Japanese originals, every offset after the first modified message is wrong.

**Example (Resource 49):**
- Original message 0 at payload offset 0x01C0
- After injection, message 0 grows, pushing message 1 from 0x01DC to 0x01E4 (+8 bytes)
- Drift compounds: by message 4, the offset is wrong by +98 bytes

**Fix:** The v2 pipeline fully rebuilds the offset table after constructing the new glyph stream. It:
1. Scans the new stream for FFFF boundaries
2. Computes payload-relative byte offsets for each group
3. Writes a new offset table with format: `(count, 0x0000)` + `(offset, 0x0000)` ... `(offset, 0xFFFF)`

### Bug 4: Stream Start Off by 2
**Root cause:** The v1 pipeline scans for the first `0xFFFF` or `0xFFFE` after the sub-header to find the glyph stream start. But the **last entry** of the offset table has `flags = 0xFFFF`. This 0xFFFF is NOT a glyph stream delimiter -- it is the terminator flag of the offset table. The scanner finds this flag and starts the stream 2 bytes too early.

**Affected:** 13 of 21 resources (all Format A resources with offset tables: 36, 37, 38, 40, 41, 42, 43, 44, 45, 48, 49, 1272, 2124).

**Fix:** The v2 pipeline properly parses the offset table structure:
1. Read entry[0] as message count
2. Walk (msg_count + 1) entries of 4 bytes each
3. Stream starts at `table_start + table_size` (after the last entry including its 0xFFFF flag)

### Bug 5: Trailing " / "
**Root cause:** The v1 pipeline's `encode_text()` treats ` / ` as literal characters, encoding space (glyph 1) + slash (glyph 26). But ` / ` in the translation chunks represents FFFE line-break tokens, not visible text.

**Key finding during fix:** The trailing ` / ` is NOT an artifact -- it represents a real FFFE token. Every FFFF-group in the original binary ends with `[glyphs] FFFE FFFF`. The decoder renders this trailing FFFE as ` / ` in the text dump. This FFFE must be preserved when injecting back.

**Example:** `"Healing Stone / "` should produce `[glyphs for Healing Stone] FFFE` -- NOT `[glyphs for Healing Stone] [space glyph] [slash glyph]`.

**Example with multi-line:** `"Check the board? /   /   / "` should produce `[glyphs] FFFE FFFE FFFE` (text + 2 empty lines + trailing FFFE, matching the original 3-FFFE structure).

**Fix:** The v2 pipeline's `clean_and_encode()` function:
1. Splits the entire text on ` / ` to find FFFE boundaries
2. Encodes each non-empty segment via `encode_text()`
3. Inserts FFFE tokens between segments (including trailing empty ones)
4. The trailing FFFE is preserved, matching the original binary structure

---

## Additional Fixes

### Extra Data Preservation
**Discovery:** Resources with type codes 20, 03, 06, 15, 44 have data beyond the declared `payload_size`. For example:
- Resource 34 (type20): payload_size=972 bytes, but file is 69,632 bytes (68,644 bytes of extra data)
- Resource 2654 (type44): payload_size=5,666 bytes, but file is 184,320 bytes (178,638 bytes extra)

The v1 pipeline rebuilds only `sub_header + pre + new_stream + padding`, destroying all data beyond the payload. This corrupts multi-section resources.

**Fix:** The v2 pipeline preserves `extra_data = raw[16+payload_size:]` and appends it after the new payload.

### Identity Translation Filtering
**Discovery:** Resources 1053, 1908, and 2124 have translation entries where `english == japanese` (e.g., both are "..."). These are undecoded/untranslated entries.

**Fix:** The v2 pipeline skips entries where `english.strip() == japanese.strip()`.

### Fix Chunk Override
**Fix:** Fix chunks (`chunk_r38_fix.json`, `chunk_r43_fix.json`) are loaded AFTER the main chunks. When de-duplicating by `(resource, message)`, later entries win, ensuring fix chunks properly override the original translations.

### ISO Extent Discovery Without pycdlib
**Fix:** The v2 pipeline parses the ISO 9660 primary volume descriptor and root directory record directly using `struct`, eliminating the `pycdlib` dependency.

---

## Resource Format Reference

### Sub-header (16 bytes, all LE u32)
```
[0x00] zero1         (always 0)
[0x04] payload_size  (bytes of actual data after sub-header)
[0x08] stride        (16 for type01, 32/48/96/240/320/704 for others)
[0x0C] zero2         (always 0)
```

### Payload Structure
```
[Sequential Table]   0 or N entries of 16 bytes (LE u32 id=1,2,3..., + 12 bytes data)
[Offset Table]       Format A only: (count, 0x0000) + N*(offset, flags) entries, 4 bytes each
[Glyph Stream]       BE u16 glyph IDs separated by FFFF (group) and FFFE (line break)
[Extra Data]         Data beyond payload_size (multi-section resources only)
```

### Offset Table Entry Format
```
entry[0]:  BE u16 msg_count,      BE u16 0x0000
entry[1]:  BE u16 offset_to_grp0, BE u16 0x0000
...
entry[N]:  BE u16 offset_to_grpN, BE u16 0xFFFF  (last entry has terminator flag)
```
Offsets are relative to payload start (byte 16 of the raw file).

---

## Translation Numbering Convention

| Source | Numbering | Meaning |
|--------|-----------|---------|
| `full_decoded_text.txt` | 1-indexed | FFFF-group index within payload glyph stream |
| Translation chunks | Same as above | Message index = FFFF-group index |
| ` / ` in text | N/A | Represents FFFE line break within a FFFF group |
| Trailing ` / ` | N/A | Real FFFE token (every group ends with FFFE before FFFF) -- must be converted to 0xFFFE, NOT stripped |

---

## Files

| File | Purpose |
|------|---------|
| `build/build_full_english_v2.py` | Fixed injection pipeline (this deliverable) |
| `build/build_full_english.py` | Original v1 pipeline (buggy, kept for reference) |
| `data/translate_chunks/chunk_*_translated.json` | Main translation data (10 chunks) |
| `data/translate_chunks/chunk_r38_fix.json` | Override translations for resource 38 |
| `data/translate_chunks/chunk_r43_fix.json` | Override translations for resource 43 |
| `tools/encode_english_text.py` | Character-to-glyph encoder with word wrapping |
| `build/english_font_atlas.bin` | Pre-built English font atlas binary |
| `extracted/packdata_raw/*.raw` | Original resource files from PACKDATA.DIG |
| `extracted/packdata_resources/manifest.json` | TOC manifest for PACKDATA.DIG rebuild |
