# PACKDATA.DIG Rebuild Mechanics -- Research Findings

**Date:** 2026-05-22

---

## 1. Extraction Format (extract_packdata_raw.py)

The raw extractor (`tools/extract_packdata_raw.py`) dumps each resource as a complete sector-aligned block:

- Reads the TOC (2883 entries x 12 bytes) from offset 0
- For each non-outlier entry: seeks to `sector_offset * 2048`, reads `sector_count * 2048` bytes
- Writes the entire raw block (including the 16-byte sub-header AND all trailing padding) to `NNNN_typeXX.raw`
- Skips outlier indices 1370 and 2100

The payload extractor (`tools/extract_packdata.py`) strips the header:

- Reads the 16-byte sub-header: `(zero1, payload_size, stride, zero2)` as 4x uint32 LE
- Reads exactly `payload_size` bytes after the header
- Writes only the payload (no header, no padding) to `NNNN_typeXX.bin`
- Records everything in `manifest.json`

**Key structural insight:** The `stride` field is `type_code * 16` (e.g., type 1 has stride 16, type 4 has stride 64). This is consistent across all entries.

---

## 2. What Needs Updating When a Resource Payload Changes

### If payload SHRINKS (translated text is shorter):

- **Sub-header `payload_size` field:** MUST update to reflect new size
- **TOC `sector_count`:** Does NOT need to change (resource still fits in allocated sectors)
- **Trailing padding:** Increases automatically (just zero-fill remaining bytes after payload)
- **Other TOC entries:** No changes needed -- nothing shifts

**Verdict: Shrinking is trivially safe.** Just update the payload_size in the 16-byte sub-header and zero-fill the rest.

### If payload GROWS (translated text is longer):

Two scenarios:

#### Scenario A: New payload fits within existing sector allocation

- Condition: `16 + new_payload_size <= sector_count * 2048`
- **Sub-header `payload_size`:** Update
- **TOC:** No changes needed
- **Trailing padding:** Decreases (less zero-fill)
- **Other entries:** Unaffected

#### Scenario B: New payload exceeds existing sector allocation

- Condition: `16 + new_payload_size > sector_count * 2048`
- **Sub-header `payload_size`:** Update
- **TOC `sector_count` for this entry:** Must increase
- **ALL subsequent TOC entries:** ALL `sector_offset` values must shift forward
- **All subsequent data:** Must be physically relocated in the file

**This is a cascading rebuild** -- every byte after the grown resource shifts.

---

## 3. Contiguity Analysis

**Resources are perfectly contiguous.** Verified across the entire file:

- Entry N ends at sector `sector_offset + sector_count`
- Entry N+1 starts at exactly that sector
- No gaps, no overlaps (confirmed at outlier boundaries: entries 1369/1371 are contiguous across skipped index 1370, and entries 2099/2101 are contiguous across skipped index 2100)
- First data entry starts at sector 125 (= 256,000 bytes, after the 125-sector TOC/header region)
- Last entry (index 2882) ends at sector 409,991 (= 839,601,568 bytes = exact file size)

**Implication:** If ANY resource grows beyond its sector allocation, ALL subsequent resources physically shift. There is no free space between resources.

---

## 4. Is Full Rebuild Feasible?

**Yes, absolutely.** A full rebuild is straightforward:

1. Read the original TOC (34,596 bytes = 2883 * 12)
2. For each non-outlier entry in order:
   - Determine the new payload (modified or original)
   - Compute new sector_count = ceil((16 + new_payload_size) / 2048)
   - Assign sector_offset = running sector counter (starting at 125)
   - Write: sub-header (16 bytes) + payload + zero-pad to sector boundary
   - Advance running counter by sector_count
3. For outlier entries (1370, 2100): preserve original TOC bytes as-is
4. Write new TOC at offset 0
5. Zero-fill TOC region to sector 125

The approach is simple because:
- There are only 2,881 data entries (trivial to iterate)
- Resources are already extracted with full metadata in `manifest.json`
- The format has no cross-references between resources (each is self-contained)
- The file is ~839 MB, which can be written sequentially in seconds

---

## 5. In-Place Replacement (Preferred Strategy)

**The safest and simplest approach: keep all resources at their ORIGINAL sector-padded sizes.**

Procedure:
1. For each modified resource, check: does `16 + new_payload_size <= sector_count * 2048`?
2. If YES: write new sub-header and payload at the original byte offset, zero-fill remainder
3. If NO: fall back to full rebuild (Scenario B above)

**Advantages:**
- TOC is unchanged (no sector_offset or sector_count updates)
- Only modified sectors are touched
- No risk of corrupting unrelated resources
- Can be done as in-place binary patching of the original file

---

## 6. Padding/Slack Analysis for Type 1 (MSG Text) Resources

Type 1 resources are the MSG files containing all translatable text (16-bit glyph indices). There are **1,700 type 1 entries** in PACKDATA.DIG.

### Typical small MSG resources (majority):

Most MSG resources use 1-5 sectors with small payloads:

| Index | Sectors | Allocated | Payload | Slack (bytes) | Slack % |
|-------|---------|-----------|---------|---------------|---------|
| 0     | 1       | 2,048     | 884     | 1,148         | 56.1%   |
| 1     | 1       | 2,048     | 1,972   | 60            | 2.9%    |
| 2     | 1       | 2,048     | 644     | 1,388         | 67.8%   |
| 33    | 2       | 4,096     | 2,084   | 1,996         | 48.7%   |
| 36    | 2       | 4,096     | 3,390   | 690           | 16.8%   |
| 38    | 4       | 8,192     | 7,512   | 664           | 8.1%    |
| 45    | 4       | 8,192     | 6,950   | 1,226         | 15.0%   |
| 50    | 1       | 2,048     | 116     | 1,916         | 93.6%   |
| 58    | 1       | 2,048     | 44      | 1,988         | 97.1%   |
| 81    | 1       | 2,048     | 60      | 1,972         | 96.3%   |

**Pattern:** Small MSG resources (1-2 sectors) have hundreds to ~2,000 bytes of slack. Payload sizes range from 44 bytes to ~8,000 bytes for dialogue-heavy resources.

### Large type 1 entries (NOT text -- likely misclassified texture data):

Entries in the 1300-1370 range have payload_size of 263,360 (129 sectors) or 132,288 (65 sectors). These are texture data stored with type_code=1, not MSG text. They are essentially full: `129 * 2048 = 264,192; 264,192 - 16 - 263,360 = 816 bytes slack`.

### Larger MSG resources (dialogue-heavy):

| Index | Sectors | Allocated | Payload | Slack (bytes) | Slack % |
|-------|---------|-----------|---------|---------------|---------|
| 1371  | 5       | 10,240    | 8,416   | 1,808         | 17.7%   |
| 1372  | 5       | 10,240    | 8,448   | 1,776         | 17.3%   |
| 2559  | 5       | 10,240    | 8,416   | 1,808         | 17.7%   |

### Translation size change estimate:

Japanese text uses 16-bit glyph indices (2 bytes per character). English text would also use 16-bit glyph indices. The question is whether English translations require more or fewer glyph indices than Japanese:

- Japanese is very information-dense (1 kanji = 1 concept, 1 glyph index)
- English typically needs 2-5x more characters for the same meaning
- BUT: if the game uses a fixed-width glyph system where each English character = 1 glyph index, then English text could be 2-5x LARGER
- HOWEVER: the glyph-index system is inherently per-character, so even English "Hello" = 5 glyph indices = 10 bytes

**Worst case growth estimate:** A typical small MSG resource with payload 1,000 bytes might grow to 2,500 bytes for English. With 1 sector (2,048 bytes allocated), this exceeds the allocation. But with 2 sectors (4,096), it fits easily.

---

## 7. Recommended Rebuild Strategy

### Strategy: Hybrid (In-Place + Overflow Rebuild)

1. **First pass:** For each text resource, compute new payload size
2. **Check fit:** Does `16 + new_payload_size <= sector_count * 2048`?
3. **If all fit:** Do in-place patching only (update sub-headers and payloads)
4. **If any overflow:** Do a full sequential rebuild with recomputed TOC

### Implementation outline for full rebuild tool:

```python
def rebuild_packdata(manifest, modified_payloads, output_path):
    SECTOR = 2048
    TOC_ENTRIES = 2883
    HEADER_SECTORS = 125
    OUTLIER_INDICES = {1370, 2100}
    
    # Phase 1: Compute new TOC
    new_toc = []
    running_sector = HEADER_SECTORS
    for entry in manifest:
        if entry.get('skipped'):
            # Preserve original outlier TOC bytes
            new_toc.append(original_toc_bytes[entry['index']])
            continue
        idx = entry['index']
        payload = modified_payloads.get(idx, original_payload(idx))
        payload_size = len(payload)
        needed_sectors = math.ceil((16 + payload_size) / SECTOR)
        new_toc.append((running_sector, needed_sectors, entry['type_code']))
        running_sector += needed_sectors
    
    # Phase 2: Write file
    with open(output_path, 'wb') as f:
        # Write TOC
        for so, sc, tc in new_toc:
            f.write(struct.pack('<III', so, sc, tc))
        # Pad TOC region to sector 125
        f.write(b'\x00' * (HEADER_SECTORS * SECTOR - f.tell()))
        # Write resources
        for entry in manifest:
            if entry.get('skipped'):
                continue
            idx = entry['index']
            payload = modified_payloads.get(idx, original_payload(idx))
            sub_header = struct.pack('<IIII', 0, len(payload), 
                                     entry['type_code'] * 16, 0)
            block = sub_header + payload
            pad_len = (math.ceil(len(block) / SECTOR) * SECTOR) - len(block)
            f.write(block + b'\x00' * pad_len)
```

### Key edge cases to handle:

1. **Outlier entries (1370, 2100):** Their TOC bytes must be preserved exactly as-is. They don't correspond to data in the file.
2. **Sub-header field `header_zero2`:** Most entries have 0, but late entries (2880+) have value 64. Must preserve original value.
3. **Non-text resources:** Must be copied byte-for-byte (raw block) from the original file.
4. **Sector alignment:** Every resource must start on a sector boundary and occupy exactly `sector_count` sectors.

---

## 8. Summary of Key Facts

| Property | Value |
|----------|-------|
| Total entries | 2,883 (2,881 data + 2 outliers) |
| Type 1 (MSG) entries | 1,700 |
| Sector size | 2,048 bytes |
| Sub-header size | 16 bytes |
| Resources contiguous | YES (no gaps) |
| Header region | Sectors 0-124 (256,000 bytes) |
| File size | 839,601,568 bytes (409,991 sectors) |
| Outlier indices | 1370, 2100 (skipped, no data) |
| In-place patching viable | YES, if payloads fit within existing sector allocation |
| Full rebuild viable | YES, straightforward sequential write |
| Minimum slack for 1-sector type 1 | 60 bytes (index 1, payload 1,972) |
| Maximum slack for 1-sector type 1 | 1,988 bytes (index 58, payload 44) |
| Typical slack for 1-sector type 1 | ~1,000-1,500 bytes |
