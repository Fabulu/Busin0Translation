# Implementation: PACKDATA.DIG Patching and Rebuild Tools

## Files Written

### tools/patch_msg_resource.py (Phase D)
- **Purpose:** Replace glyph stream in a single MSG resource with encoded English data
- **Input:** Original `.raw` from `extracted/packdata_raw/`, encoded `.bin` from Phase C encoder
- **Output:** Patched `.raw` in `build/packdata_resources/`
- **Modes:** Single resource (`<index> <encoded_bin>`) or batch (`--batch <dir>`)

### tools/rebuild_packdata.py (Phase E)
- **Purpose:** Full sequential rebuild of PACKDATA.DIG with updated TOC
- **Input:** Modified `.raw` files from `build/packdata_resources/`, originals from `extracted/packdata_raw/`
- **Output:** `build/PACKDATA.DIG`
- **Modes:** Rebuild (default) or verify (`--verify`)
- **Note:** Replaced the pre-existing buggy version that had manifest format mismatches

## Key Design Decisions

### patch_msg_resource.py

1. **Header preservation boundary:** The tool preserves only the sequential table (16-byte
   entries where field0 counts 1,2,3,...). Everything after the sequential table is replaced
   by the encoded_bin. This means the Phase C encoder must produce:
   - For Format A resources: rebuilt offset table + glyph data
   - For Format B resources: config block + glyph data

2. **Sub-header fields preserved from original:** `stride` (type_code * 16) and `zero2`
   (usually 0, but 64 for entries 2880-2882). Only `payload_size` is updated.

3. **Sector padding:** Output is always padded to a 2048-byte sector boundary with zero bytes.

### rebuild_packdata.py

1. **Outlier entries 1370, 2100:** TOC entries preserved exactly as-is from the original.
   These point into the header region (sectors < 125) and are already covered by the
   header region copy. No resource data is written for them.

2. **Header region:** The full 256,000-byte header region is copied from the original,
   then the first 34,596 bytes (TOC) are overwritten with new entries. This preserves
   any data between the TOC and sector 125.

3. **Resource ordering:** Resources are written strictly sequentially starting at sector 125.
   The tool verifies contiguity -- if the write position doesn't match the expected offset,
   it either gaps with zeros (should not happen) or raises an error on overlap.

4. **Modified resource detection:** Looks for `{index:04d}_type*.raw` in
   `build/packdata_resources/` first, falls back to `extracted/packdata_raw/`.

5. **Memory usage:** All 2881 resource blocks are loaded into memory during Phase 1
   (~840 MB). This is acceptable for a build tool on modern systems. If memory is a
   concern, a streaming approach could be implemented.

## Format Details Confirmed

| Field | Value | Source |
|-------|-------|--------|
| TOC entry size | 12 bytes (3x LE uint32) | extract_packdata_raw.py |
| TOC entries | 2883 | extract_packdata_raw.py |
| Header region | 125 sectors = 256,000 bytes | extract_packdata_raw.py |
| First data sector | 0x7D (125) | Verified in manifest |
| Sub-header | 16 bytes: [zero1, payload_size, stride, zero2] LE uint32 | extract_packdata.py |
| Sector size | 2048 bytes | Universal in codebase |
| Outlier indices | {1370, 2100} | extract_packdata_raw.py |
| zero2 field | 0 for entries 0-2879, 64 for entries 2880-2882 | manifest.json |
| Sequential table | 16-byte entries: [id, field1, field2, field3] LE uint32, id=1,2,3,... | parse_msg_header.py |
| Format A (offset table) | 17 of 296 MSG resources | msg_header_analysis.json |
| Format B (flat stream) | 279 of 296 MSG resources | msg_header_analysis.json |

## Risks and Caveats

1. **Memory:** Loading all ~840 MB of resources into memory. Should work on machines with
   4+ GB RAM.

2. **Encoder contract:** The patch tool assumes the encoded_bin contains EVERYTHING after
   the sequential table. The Phase C encoder must handle offset table rebuilding for
   Format A resources and config block preservation for Format B resources.

3. **Non-MSG resources:** The rebuild tool copies them byte-for-byte from the original
   extraction. Any tool that modifies non-MSG resources (e.g. font atlas at index 1272)
   should place patched `.raw` files in `build/packdata_resources/` with the same naming
   convention.

4. **Original file required:** Both tools require `extracted/PACKDATA.DIG` and the full
   `extracted/packdata_raw/` directory from a prior extraction run.
