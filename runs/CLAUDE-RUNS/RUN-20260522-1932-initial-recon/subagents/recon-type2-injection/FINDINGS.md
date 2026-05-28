# Type-2 Resource Injection Plan: Replacing Dialogue in Multi-Section Binary Resources

**Date:** 2026-05-22
**Scope:** How to inject translated English text into Section 2 of type-2 PACKDATA resources

---

## 1. The Real Scale: Not 43 Resources, But 350+

The original task referenced "43 type-2 resources with dialogue." The actual count is much larger:

| Category | Count |
|----------|-------|
| Total type-2 resources with >5 messages | 436 |
| Of those, with actual dialogue lines (line_count > 0) | 350 |
| Data-only type-2 resources (msgs but no line breaks) | 86 |

All 510 resources in `dialogue_resource_map.json` have PACKDATA type_code=2. The small pure-MSG resources (R34-R49) that the existing pipeline handles are type_code=1 -- they are a completely separate set.

The type-2 resources span indices R29 through R2659 and range from 4 KB to 5 MB in size.

---

## 2. Type-2 Resource Internal Structure

### Binary Layout (verified across multiple resources)

```
Offset  Size  Field                    Notes
------  ----  -----                    -----
0x00    4     zero                     Always 0x00000000
0x04    4     payload_size (LE)        Section 1 data size in bytes
0x08    4     stride (LE)              Always 0x20 (= type_code 2 * 16)
0x0C    4     flags0                   Values: 0, 1, or 64
0x10    4     section_count (LE)       Always 1 (meaning "1 additional section")
0x14    4     section2_total_size (LE) SIZE FIELD FOR SECTION 2
0x18    4     section2_offset (LE)     Byte offset from start of raw resource
0x1C    4     flags1                   Values: 0 or 2
0x20    ...   Section 1 data           3D models, textures, event scripts, etc.
...     ...   (alignment padding)      0-28 bytes of zeros
s2o     ...   Section 2 data           Dialogue glyph stream (BE uint16)
...     ...   (sector padding)         Zeros to fill remaining sector space
```

### Critical Discovery: Section 2 HAS a Size Field

**YES -- the Section 2 header at offset 0x14 contains the Section 2 size (LE uint32).**

This field MUST be updated when Section 2 grows or shrinks. The game engine reads this field to know how many bytes of dialogue data to load.

### Verified Relationships

For every resource checked:
- `section2_offset + section2_total_size <= file_size` (always true)
- `section2_offset >= 16 + payload_size` (Section 2 starts after Section 1)
- Gap between Section 1 end and Section 2 start: 16-28 bytes (alignment)
- Sector padding after Section 2: `file_size - (s2o + s2t)` bytes

### Flags at 0x0C and 0x1C

| flags0 (0x0C) | flags1 (0x1C) | Count | Interpretation |
|---------------|---------------|-------|----------------|
| 0 | 0 | 295 | Standard (most resources) |
| 1 | 2 | 131 | Alternate layout variant |
| 64 | 0 | 10 | Special (high-index resources like R2651) |

These flags must be PRESERVED exactly when patching. Do not modify them.

---

## 3. Section 2 Space Analysis

### Section 2 as Percentage of Total Resource

| Metric | Dialogue Resources (350) | All MSG Resources (436) |
|--------|-------------------------|------------------------|
| Average S2 % of total | 68.0% | 59.1% |
| Min S2 % | 0.7% (R756, 912 bytes in 125 KB) | 0.7% |
| Max S2 % | 99.2% (R2651, 148 KB of 150 KB) | 99.2% |
| Total S2 bytes | 144,510,268 (~138 MB) | ~151 MB |

### Size Distribution

Most type-2 resources are large binary files where Section 2 (dialogue) occupies 20-90% of the total:

```
S2 as % of total    Resources    Description
-----------------   ----------   -----------
  0 - 10%              30       Mostly binary (models/textures), tiny dialogue
 10 - 30%              45       Significant binary, moderate dialogue
 30 - 50%              60       Mixed content
 50 - 70%              65       Dialogue-heavy
 70 - 90%             150       Dialogue-dominant
 90 - 100%             86       Almost entirely dialogue
```

### Top Resources by Section 2 Size

| Resource | File Size | Section 1 | Section 2 | S2% | Messages | Lines |
|----------|-----------|-----------|-----------|-----|----------|-------|
| R897 | 5,063 KB | 920 KB | 4,025 KB | 81% | 398 | -- |
| R918 | 3,086 KB | 507 KB | 2,580 KB | 84% | 25 | -- |
| R783 | 2,930 KB | 525 KB | 2,405 KB | 82% | 126 | -- |
| R741 | 2,608 KB | 506 KB | 2,102 KB | 81% | 213 | -- |
| R681 | 2,216 KB | 347 KB | 1,868 KB | 84% | 80 | 16 |

---

## 4. 2x Expansion Overflow Analysis

### Will English Text Fit In-Place?

**Almost never.** With a 2x expansion ratio (English ~2x longer than Japanese in glyph count):

| Expansion | Fits In-Place | Overflows | Overflow % |
|-----------|--------------|-----------|------------|
| 2.0x | 8 of 350 | 342 | 98% |
| 1.5x | ~30 (est.) | ~320 | ~91% |

The 8 resources that fit at 2x are tiny resources where Section 2 is very small relative to the sector padding.

### Why In-Place Replacement Is Impossible for Most Resources

Consider R1203 (a typical large type-2 resource):
- File size: 169,984 bytes (83 sectors)
- Section 1: 69,445 bytes (3D models, scripts)
- Section 2: 100,462 bytes (dialogue, 1,633 messages)
- Sector padding: 34 bytes

If English Section 2 is 200,924 bytes (2x), we need 200,924 + 69,488 = 270,412 bytes total. That is 100,428 bytes more than the current file. **There is only 34 bytes of padding.**

### Total Overflow

If all Section 2 data doubles in size: total overflow = ~144 MB across all resources.

---

## 5. Section 2 Internal Format

### Two Sub-Formats Within Section 2

Section 2 itself has two internal layouts, matching the Format A / Format B distinction from the type-01 MSG resources:

**Format A (with offset table): ~84 of 200 checked resources**
```
Section 2 layout:
  [offset_table]    Pairs of (BE u16 byte_offset, BE u16 0x0000)
                    First pair: offset to glyph stream start
                    Subsequent pairs: offset to each message
  [glyph_stream]   BE uint16 glyph indices separated by 0xFFFF
```

Example from R35 (37 messages):
```
S2+0x00: 0024 0000   <- glyph stream at S2+0x24 (first message at offset 0x0024)
S2+0x04: 0094 0000   <- message 1 at offset 0x0094
S2+0x08: 009A 0000   <- message 2 at offset 0x009A
...
S2+0x24: [glyph data begins]
```

**Format B (flat stream): ~116 of 200 checked resources**
```
Section 2 layout:
  [glyph_stream]   BE uint16 glyph indices, 0xFFFF between messages
                    Starts immediately at Section 2 offset
```

Example from R1203 (1,633 messages):
```
S2+0x00: 0377 0088 01C1 009C   <- glyph data starts immediately
S2+0x08: 03EA 02D5 007B 007F
...
S2+0xNN: FFFF                  <- message separator
```

### Implication for Injection

- **Format A resources**: After replacing glyph data, the offset table MUST be rebuilt with new byte positions for each message. This is the same bug found in the type-01 pipeline (see `diag-injection/FINDINGS.md`).
- **Format B resources**: Simpler -- just replace the glyph stream. No offset table to update.

---

## 6. Recommended Injection Approach

### Decision: PACKDATA Rebuild (Not In-Place Patching)

In-place patching is not viable because:
1. 98% of resources overflow with 2x English text
2. Expanding Section 2 in-place shifts Section 2's end past the sector boundary
3. Sector reallocation requires TOC updates, which means rebuilding anyway

**The correct approach is the full PACKDATA rebuild already planned in Phase E of the REINSERTION_PLAN.** Each resource gets new sector allocations based on its new size.

### Byte-Level Process for Modifying One Type-2 Resource

Here is the exact process for injecting English text into resource R1203:

```
STEP 1: Read the original raw resource
  - File: extracted/packdata_raw/1203_type02.raw (169,984 bytes)
  - Parse sub-header (0x00-0x0F): payload_size=69,445, stride=32
  - Parse Section 2 descriptor (0x10-0x1F):
      section_count=1, s2_total=100,462, s2_offset=69,488, flags1=0

STEP 2: Preserve everything BEFORE Section 2
  - preserved_data = raw[0x00 : s2_offset]  (69,488 bytes)
  - This includes: sub-header + section descriptor + Section 1 data + alignment padding
  - DO NOT MODIFY ANY OF THIS

STEP 3: Determine Section 2 sub-format
  - Read first 8 bytes at s2_offset
  - R1203: starts with 0x0377 -- NOT an offset table pattern
  - Classification: Format B (flat stream)

STEP 4: Build new Section 2 glyph stream
  For Format B:
    new_s2 = bytearray()
    for each message in resource:
        if translated:
            new_s2 += encode_english(translation)   # BE uint16 glyph indices
        else:
            new_s2 += original_message_glyphs        # preserve original
        new_s2 += struct.pack(">H", 0xFFFF)          # message terminator

  For Format A:
    # First pass: encode all messages to get their sizes
    encoded_msgs = []
    for each message:
        encoded_msgs.append(encode_or_preserve(message))

    # Build offset table
    table_size = (len(encoded_msgs) + 1) * 4   # +1 for header entry
    offset_table = bytearray()
    running_offset = table_size
    for msg_bytes in encoded_msgs:
        offset_table += struct.pack(">HH", running_offset, 0x0000)
        running_offset += len(msg_bytes) + 2   # +2 for FFFF
    # Last entry gets flags=0xFFFF instead of 0x0000

    new_s2 = offset_table
    for msg_bytes in encoded_msgs:
        new_s2 += msg_bytes + struct.pack(">H", 0xFFFF)

STEP 5: Update the Section 2 size field
  - Write new s2_total_size at offset 0x14 (LE uint32):
    preserved_data[0x14:0x18] = struct.pack("<I", len(new_s2))

STEP 6: Assemble the new resource
  new_raw = preserved_data + new_s2

STEP 7: Update the sub-header payload_size field
  - The payload_size at 0x04 refers to Section 1 only
  - DO NOT CHANGE IT (Section 1 is unchanged)
  - BUT: some resources may use payload_size differently (see Risk #2)

STEP 8: Pad to sector boundary
  needed_sectors = ceil(len(new_raw) / 2048)
  new_raw += b'\x00' * (needed_sectors * 2048 - len(new_raw))

STEP 9: Write to build directory
  Output: build/packdata_resources/1203_type02.raw

STEP 10: During PACKDATA rebuild (Phase E)
  - The TOC entry for R1203 gets updated:
    sector_offset = new_position
    sector_count = needed_sectors
    type_code = 2 (unchanged)
```

### Fields That MUST Be Updated

| Field | Offset | When to Update |
|-------|--------|---------------|
| section2_total_size | 0x14 | ALWAYS (when Section 2 changes size) |
| TOC sector_count | PACKDATA TOC | During rebuild (if resource grows beyond original sector count) |
| Format A offset table | Inside Section 2 | When any message changes length |

### Fields That Must NOT Change

| Field | Offset | Why |
|-------|--------|-----|
| payload_size | 0x04 | Describes Section 1 (unchanged) |
| stride | 0x08 | Type identifier (always 0x20) |
| flags0 | 0x0C | Unknown purpose, preserve exactly |
| section_count | 0x10 | Always 1, no change needed |
| section2_offset | 0x18 | Section 1 size is unchanged, so offset stays the same |
| flags1 | 0x1C | Unknown purpose, preserve exactly |
| All Section 1 data | 0x20 to s2o | 3D models, textures, scripts -- untouched |

---

## 7. Format A Offset Table Rebuild Algorithm

For the ~84 Format A resources in Section 2, the offset table must be rebuilt when message sizes change:

```python
def rebuild_format_a_section2(original_s2, translations, glyph_table):
    """
    Rebuild Section 2 with Format A offset table.
    
    original_s2: bytes of the original Section 2
    translations: dict mapping message_index -> english_text (or None for untranslated)
    glyph_table: char -> glyph_index mapping
    """
    # 1. Parse the original offset table
    #    First entry value = byte offset to first message = table_size
    table_first = struct.unpack_from(">H", original_s2, 0)[0]
    num_entries = table_first // 4  # each entry is 4 bytes (u16 offset + u16 flags)
    
    # 2. Parse original messages using the offset table
    offsets = []
    for i in range(num_entries):
        off = struct.unpack_from(">H", original_s2, i * 4)[0]
        offsets.append(off)
    
    # Extract original messages
    original_msgs = []
    for i, off in enumerate(offsets):
        end = offsets[i + 1] if i + 1 < len(offsets) else len(original_s2)
        # Scan for FFFF terminator
        msg_data = original_s2[off:end]
        # Strip trailing FFFF
        if len(msg_data) >= 2 and msg_data[-2:] == b'\xFF\xFF':
            msg_data = msg_data[:-2]
        original_msgs.append(msg_data)
    
    # 3. Encode translations (or preserve originals)
    encoded_msgs = []
    for i, orig in enumerate(original_msgs):
        if i in translations and translations[i]:
            encoded = encode_text_to_glyphs(translations[i], glyph_table)
            encoded_msgs.append(encoded)
        else:
            encoded_msgs.append(orig)
    
    # 4. Build new offset table
    new_table_size = num_entries * 4
    new_offsets = []
    running = new_table_size
    for msg in encoded_msgs:
        new_offsets.append(running)
        running += len(msg) + 2  # +2 for FFFF terminator
    
    # 5. Assemble
    new_s2 = bytearray()
    for i, off in enumerate(new_offsets):
        flags = 0xFFFF if i == num_entries - 1 else 0x0000
        new_s2 += struct.pack(">HH", off, flags)
    
    for msg in encoded_msgs:
        new_s2 += msg
        new_s2 += struct.pack(">H", 0xFFFF)
    
    return bytes(new_s2)
```

---

## 8. Risk Assessment

### Risk 1: payload_size Field Semantics (MEDIUM)

The field at 0x04 is labeled `payload_size` and always equals `section2_offset - 16` (approximately). It describes Section 1 size. **If the game uses this field to compute Section 2 offset** (as `16 + payload_size` with alignment), then it must NOT change. Since we keep Section 1 intact, this is not a problem.

However, if `payload_size` means "total resource payload including all sections," then it would need updating. Evidence from the data suggests it refers to Section 1 only:
- R35: payload_size=524, s2o=560. Difference = 36 bytes (20 bytes for section descriptor + 16 bytes alignment).
- R1203: payload_size=69,445, s2o=69,488. Difference = 43 bytes.

**Mitigation:** Test with payload_size unchanged first. If dialogue fails to display, try updating it to `s2o + new_s2t - 16`.

### Risk 2: Section 2 Contains Non-Dialogue Data (LOW-MEDIUM)

Some "Section 2" regions may contain data OTHER than dialogue glyphs -- such as event script bytecode, lookup tables, or animation triggers interspersed with text. The msg_count and line_count in `dialogue_resource_map.json` represent FFFF and FFFE markers respectively, which could be coincidental matches in non-text data.

Resources with high msg_count but zero line_count (86 resources) are especially suspect. They may contain structured data with coincidental FFFF values, not actual dialogue.

**Mitigation:** Only inject translations into resources where we have verified, decoded dialogue text. Resources with line_count=0 should be left untouched unless manually verified.

### Risk 3: Section 2 Offset Alignment Requirements (LOW)

The gap between Section 1 end and Section 2 start varies (16-28 bytes), suggesting possible alignment requirements (e.g., 16-byte or 32-byte alignment).

Since we do NOT change Section 2's offset (only its content and size), alignment is not a concern for injection.

### Risk 4: Game Engine Caches Section 2 Sizes (LOW)

The game might cache the Section 2 size from the TOC or sub-header during loading. If so, a mismatch between the declared size and actual data could cause truncation or buffer overflow.

**Mitigation:** Always update the s2_total_size field at 0x14. The PACKDATA rebuild also updates the TOC sector_count, so the game will allocate enough memory.

### Risk 5: Control Codes in Section 2 Have Context Dependencies (MEDIUM)

Section 2 dialogue uses control codes (FFFE, FFD2-FFD4, FFF9, etc.) that the game engine interprets. If English text introduces different line-break patterns (more FFFE codes, more page breaks), the game's event scripting in Section 1 might not expect the new structure.

For example, if Section 1 contains a script instruction "wait for 3 page advances before continuing," and the English text has 5 page advances, the game could get stuck or skip dialogue.

**Mitigation:** Preserve the same number of page breaks (FFD2/FFD3/FFD4) as the original. Add extra FFFE line breaks within existing pages, but do not add new pages unless the game handles dynamic page counts.

---

## 9. Implementation Checklist

### Phase 1: Section 2 Extraction and Decoding (prerequisite)

- [ ] Write `tools/extract_section2.py` to extract Section 2 data from all type-2 resources
- [ ] Detect Format A vs Format B for each resource
- [ ] Decode all Section 2 glyph streams to Japanese text using the glyph map
- [ ] Identify which resources have actual dialogue vs data-only Section 2

### Phase 2: Translation Encoding for Section 2

- [ ] Extend `tools/encode_all_translations.py` to handle type-2 resources
- [ ] Implement Format A offset table rebuilding
- [ ] Implement Format B flat stream replacement
- [ ] Validate encoded output decodes back to expected English text

### Phase 3: Section 2 Injection

- [ ] Write `tools/inject_section2.py` implementing the byte-level process from Section 6
- [ ] Update section2_total_size at offset 0x14
- [ ] Preserve all Section 1 data and header fields
- [ ] Pad to sector boundary

### Phase 4: PACKDATA Rebuild Integration

- [ ] Extend `build/full_patch_pipeline.py` to handle type-2 resources
- [ ] Add type-2 patched resources to the PACKDATA rebuild step
- [ ] Update TOC sector counts for resources that grew

### Phase 5: Validation

- [ ] Verify Section 1 data is byte-identical before/after patching
- [ ] Verify section2_total_size matches actual Section 2 data length
- [ ] Verify Format A offset tables are self-consistent
- [ ] Boot-test in PCSX2: trigger dialogue in patched resources
- [ ] Test edge cases: very long messages, empty messages, control-code-only messages

---

## 10. Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| In-place vs rebuild | PACKDATA rebuild | 98% of resources overflow with 2x English |
| Section expansion vs text abbreviation | Section expansion | Abbreviation would require manual editing of 350+ resources |
| Append overflow to end of resource | No | Simpler to just grow Section 2 in place; rebuild handles sector allocation |
| Update payload_size at 0x04 | No (initially) | Field refers to Section 1 which is unchanged; test first |
| Update s2_total_size at 0x14 | YES (always) | This is the Section 2 size field; must match actual data |
| Update s2_offset at 0x18 | No | Section 1 is unchanged, so offset stays the same |
| Handle Format A offset tables | YES | ~84 resources need offset table rebuild |
| Handle data-only resources (line_count=0) | Skip | Risk of corrupting non-dialogue data; verify individually first |

---

## Appendix A: Sample Resources for Testing

| Resource | Size | S2 Size | Format | Messages | Lines | Good Test Because |
|----------|------|---------|--------|----------|-------|-------------------|
| R35 | 4 KB | 2.4 KB | A | 37 | 69 | Small, Format A, easy to verify |
| R675 | 806 KB | 685 KB | B | 22 | 8 | Large, Format B, few messages |
| R1203 | 166 KB | 98 KB | B | 1,633 | 2,185 | Confirmed Ingo dialogue, most-analyzed |
| R2659 | 100 KB | 96 KB | A/B? | 6,276 | 439 | Very high message count |
| R1084 | 576 KB | 209 KB | -- | 9,117 | 518 | Highest line count, stress test |

## Appendix B: Header Field Summary (Quick Reference)

```
TYPE-2 RESOURCE RAW LAYOUT (from packdata_raw/)

Bytes 0x00-0x0F: Sub-header (same as type-01)
  0x00: u32 LE  zero (always 0)
  0x04: u32 LE  payload_size (Section 1 data size) -- DO NOT CHANGE
  0x08: u32 LE  stride (always 0x20 for type-2) -- DO NOT CHANGE
  0x0C: u32 LE  flags0 (0, 1, or 64) -- PRESERVE

Bytes 0x10-0x1F: Section 2 descriptor
  0x10: u32 LE  section_count (always 1) -- DO NOT CHANGE
  0x14: u32 LE  section2_total_size -- MUST UPDATE when S2 changes size
  0x18: u32 LE  section2_offset -- DO NOT CHANGE (S1 is unchanged)
  0x1C: u32 LE  flags1 (0 or 2) -- PRESERVE

Bytes 0x20 to (s2o-1): Section 1 data -- DO NOT TOUCH
Bytes s2o to (s2o + s2t - 1): Section 2 data -- REPLACE WITH ENGLISH
Bytes after S2: sector padding -- RECALCULATE
```
