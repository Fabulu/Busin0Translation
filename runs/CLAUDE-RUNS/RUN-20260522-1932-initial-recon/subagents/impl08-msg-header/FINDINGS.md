# MSG Resource Header Parser - Findings

## Overview

Parsed all 296 MSG resources from PACKDATA.DIG. Discovered two distinct header formats and fully decoded the message offset table structure for 17 "Format A" resources.

## Header Structure

### Two Major Formats

**Format A - With BE uint16 Offset Table (17 resources)**
Resources: 34-49 (story/dialogue), 2654
These contain a readable message offset table that directly indexes every FFFF separator.

**Format B - With Binary Config Block (279 resources)**
Resources: 636+, 690+, 720+, etc.
These have a fixed-size binary config block (commonly 82 bytes for type01) instead of an offset table. The config block contains rendering/display parameters, not message offsets.

---

## Format A: Detailed Structure

### Layout

```
[Sequential Table] [BE uint16 Offset Table] [Glyph Stream]
 N * 16 bytes        variable                 to EOF
```

### Sequential Table (optional, 262/296 resources have it)

- Present when first LE uint32 == 1
- 16-byte entries: `[id(LE32), field1(LE32), field2(LE32), field3(LE32)]`
- `id` starts at 1 and increments sequentially
- `field1` and `field2` are large values (possibly related to rendering/texture data)
- `field3` is usually 0
- Entry count varies: 1 to 58 entries

### BE uint16 Offset Table

- Encoded as pairs: `[value, 0x0000, value, 0x0000, ...]` (BE uint16 with zero padding)
- First value = message count (equals FFFF count - 1)
- Remaining values = byte offsets to the start of each message's glyph data (the byte immediately after each FFFF separator)
- **For sequential-table resources**: offsets are relative to `table_end` (end of sequential table)
- **For flat resources (no sequential table)**: offsets are absolute byte positions

### Verification

For all 17 Format A resources, 100% of offset values match `FFFF_position + 2` exactly. The first FFFF at glyph_start is implicit (not listed in the offset table).

### Glyph Stream

- Starts at first FFFF/FFFE occurrence
- Messages delimited by `FFFF` (message start) and `FFFE` (message end)
- Each glyph is a BE uint16 index (range 0x0000-0x035A typically)
- Pattern: `FFFF [glyphs...] FFFE FFFF [glyphs...] FFFE ...`
- First message often starts with `FFFF 0000 FFFE FFFF` (empty first entry)

---

## Format B: Structure (279 resources)

### Layout

```
[Sequential Table] [Config Block] [Glyph Stream]
 1 * 16 bytes        82 bytes       to EOF
```

### Config Block

- Most common size: 82 bytes (160 resources)
- Also seen: 70 bytes (14 resources), and other sizes
- Contains LE uint32 values that appear to be display/rendering parameters
- Typical values: `32772 (0x00008004)`, `268435456 (0x10000000)`, `4194308 (0x00400004)` -- likely GPU/VIF register values
- NOT a message offset table

### Special Cases

- Resources 899, 900, 901: Magic `0x13131313`, very large (378K-944K), have huge headers (98K-196K bytes before first FFFF). These are likely combined data resources with embedded MSG streams.
- Resources 636, 638: Start with `0x00030032` instead of `0x00000001`. Different sub-format entirely.

---

## Key Statistics

| Metric | Value |
|--------|-------|
| Total MSG resources | 296 |
| With sequential table prefix | 262 |
| With BE uint16 offset table | 17 |
| With binary config block | 279 |
| Most common header size | 98 bytes (160 resources) |
| Header size range | 40 - 196,182 bytes |

### Header Size Distribution (top 5)

- 98 bytes: 160 resources (16-byte table + 82-byte config)
- 86 bytes: 60 resources (16-byte table + 70-byte config)
- 70 bytes: 15 resources (no table, 70-byte flat header)
- 130 bytes: 7 resources
- 166 bytes: 3 resources

### By type_code

| Type | Count | Has Seq Table | Has Offset Table |
|------|-------|---------------|-----------------|
| type01 | 195 | 161 | 11 |
| type02 | 65 | 65 | 1 |
| type03 | 12 | 12 | 2 |
| type04 | 9 | 9 | 0 |
| type20 | 2 | 2 | 1 |
| Others | 13 | 13 | 2 |

---

## Output Files

- `C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json` - Full per-resource analysis
- `C:/Programmieren/wizardrytranslation/tools/parse_msg_header.py` - Parser script

## Implications for Translation

1. **Format A resources (17)** have clean offset tables -- message boundaries are trivially extractable. These are likely the main story/dialogue text.

2. **Format B resources (279)** lack offset tables but FFFF/FFFE delimiters still reliably mark message boundaries in the glyph stream. A linear scan from `glyph_start_offset` suffices.

3. **glyph_start_offset** is reliably found by scanning for the first `0xFFFF` or `0xFFFE` as BE uint16 on 2-byte boundaries.

4. **The sequential table** (field1/field2/field3 per entry) likely references external texture/rendering data. The values are too large to be byte offsets within the resource file itself, suggesting they reference external resources or virtual addresses.
