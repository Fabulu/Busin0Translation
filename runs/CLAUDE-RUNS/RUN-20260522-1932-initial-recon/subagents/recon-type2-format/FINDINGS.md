# Type-2 Resource Format: Section 2 Dialogue Extraction

## DEFINITIVE FORMAT SPECIFICATION

### Overall Resource Layout

Every type-2 resource in PACKDATA.DIG has this layout:

```
Offset   Size   Field              Endian
------   ----   -----              ------
0x00     4      zero               LE uint32  (always 0)
0x04     4      payload_size       LE uint32  (Section 1 data size in bytes)
0x08     4      stride             LE uint32  (record stride for Section 1, always 32)
0x0C     4      zero               LE uint32  (always 0)
--- 16-byte "PACKDATA header" ends here ---
0x10     4      section_count      LE uint32  (always 1 = "1 additional section")
0x14     4      sec2_size          LE uint32  (Section 2 total byte length)
0x18     4      sec2_offset        LE uint32  (byte offset from 0x10 to Section 2 start)
0x1C     4      zero               LE uint32  (always 0)
--- 16-byte "payload header" ends here ---
0x20     ...    Section 1 data     (payload_size - 16 bytes of structured records)
...      ...    zero-padding       (gap between end of Section 1 and Section 2 start)
sec2_off ...    Section 2 data     (sec2_size bytes of dialogue or binary data)
```

### Key Offset Relationships

- **Section 1 data** runs from byte 0x20 to byte 0x10 + payload_size
- **Section 2 data** starts at byte 0x10 + sec2_offset
- **Gap** (zero-padding) between Section 1 end and Section 2 start = sec2_offset - payload_size (typically 32-47 bytes, alignment padding to nearest 16-byte boundary with variable extra padding)
- **Total resource data** = 16 (PACKDATA hdr) + sec2_offset + sec2_size + sector-alignment padding
- sec2_offset is relative to byte 0x10 (start of the payload header), NOT relative to byte 0x00
- **IMPORTANT**: sec2_offset is always 16-byte aligned. It is explicitly stored in the header; do NOT try to compute it from payload_size (the relationship is not a simple formula)

### Reading Section 2 from PACKDATA.DIG

```
resource_abs_offset = sector_offset_from_TOC * 2048
section2_abs_offset = resource_abs_offset + 16 + sec2_offset
section2_data = read(section2_abs_offset, sec2_size)
```

## SECTION 2 SUB-FORMATS

Section 2 has several distinct sub-formats, identified by the first 2 bytes:

### Category A: Direct Glyph Stream (REAL DIALOGUE)

**Identifying feature:** First BE uint16 value is a valid glyph index (< 0x0600) or a control code (FFFF/FFFE/FFxx).

**Count:** ~196 resources, ~22,872 messages, ~23,402 line breaks

**Sub-variants:**

#### A1: "Preamble" format (signature `00e2 00f9`)

- 20 resources: R1196-R1213, R1348, R1353
- Section 2 starts with a fixed 28-byte (14-glyph) preamble message:
  ```
  00E2 00F9 00E9 0089 FFFE 044C 012C 0085 052A 0078 0410 00BF 007F 003F
  ```
  Decoded: "メダルはい|[1100]階の兵[1322]に問えばわかる？"
  (Roughly: "Ask the soldier on floor [1100] about medals?")
- First FFFF message delimiter appears at byte offset 28
- After that, continuous FFFF-delimited glyph stream

#### A2: Pointer table + glyph stream (e.g., R35)

- Signature: first LE uint32 values are increasing offsets (e.g., `00B8 0000 00C2 0000 ...`)
- Section 2 starts with a table of LE uint32 byte offsets (padded to 8 bytes each)
- Each offset points to a message within the same Section 2
- The glyph stream follows after the pointer table
- R35 has 37 messages (save/load system text)

#### A3: Other direct glyph streams

- Various resources (R1347, R1351-R1355, etc.) start directly with glyph data
- No consistent preamble; first bytes are simply the first character(s) of the first message
- Example: R1354 starts with `FFFE FFF0` (line break + color code), then dialogue
- FFFF delimiters may or may not be present at position 0

### Category B: Complex Nested Structure (NOT direct dialogue)

**Identifying feature:** First BE uint16 is a structure header magic: `4001`, `5001`, `3801`, `5801`, `6001`, `4801`, `7001`, `2001`, or `0480`.

**Count:** ~314 resources, but with very sparse actual text (154K false-positive FFFF, only 6K FFFE)

#### B1: Offset-table format (signatures `40 01`, `50 01`, etc.)

- First LE uint32 = total header size (e.g., 0x140 = 320 bytes)
- Second LE uint32 = unknown (e.g., 0x1000 = 4096)
- Followed by (header_size - 8) / 8 entries, each: (offset LE uint32, size LE uint32)
- These entries point to binary sub-blocks (3D data, scripts, etc.)
- Any FFFF/FFFE in these blocks is coincidental binary data, NOT dialogue
- Line density: ~0.0 lines/KB (essentially zero real text)

#### B2: PS2 display list format (signature `04 80 00 00`)

- 201 resources
- Contains `0480 0000 0000 0010 0E00 0000 ...` header pattern
- PS2 GIF/VIF display list or model data
- Any FFFF/FFFE occurrences are binary data artifacts
- Line density: ~2.0 lines/KB but decoded text is garbage (indices > 60000)

## RELIABLE EXTRACTION ALGORITHM

```python
def extract_dialogue(packdata_file, resource_index):
    """Extract dialogue from a type-2 resource's Section 2."""
    
    # 1. Read TOC entry
    sector_offset, sector_count, type_code = read_toc(resource_index)
    assert type_code == 2
    
    # 2. Read PACKDATA header (16 bytes)
    abs_off = sector_offset * 2048
    zero1, payload_size, stride, zero2 = read_le_u32x4(abs_off)
    
    # 3. Read payload header (next 16 bytes)
    section_count, sec2_size, sec2_offset, zero3 = read_le_u32x4(abs_off + 16)
    assert section_count == 1  # Always 1 additional section
    
    # 4. Read Section 2 data
    sec2_abs = abs_off + 16 + sec2_offset
    sec2_data = read_bytes(sec2_abs, sec2_size)
    
    # 5. Check if this is a direct glyph stream (Category A)
    first_be_u16 = struct.unpack('>H', sec2_data[0:2])[0]
    COMPLEX_HEADERS = {0x4001, 0x5001, 0x3801, 0x5801, 0x6001, 
                       0x4801, 0x7001, 0x2001, 0x0480}
    
    if first_be_u16 in COMPLEX_HEADERS:
        return None  # Complex structure, skip for now
    
    # 6. Parse as BE uint16 glyph stream
    messages = []
    current_msg = []
    i = 0
    while i < len(sec2_data) - 1:
        glyph = struct.unpack('>H', sec2_data[i:i+2])[0]
        if glyph == 0xFFFF:
            if current_msg:
                messages.append(current_msg)
            current_msg = []
        elif glyph == 0xFFFE:
            current_msg.append(('linebreak',))
        elif glyph >= 0xFF00:
            current_msg.append(('control', glyph))
        else:
            current_msg.append(('glyph', glyph))
        i += 2
    if current_msg:
        messages.append(current_msg)
    
    return messages
```

## VERIFIED EXAMPLES

### R1203 (Ingo's dialogue)

- PACKDATA header: payload_size=69445, stride=32
- Payload header: section_count=1, sec2_size=100462, sec2_offset=69488
- Section 2 starts with the 28-byte preamble, then FFFF at byte 28
- Ingo's famous line at sec2-relative offset 0xFC08:
  "難攻不落の城であろうと、鉄壁をほこる法王庁の宝物殿の中であろうとなんのそ..."
  ("Whether it be an impregnable castle, or within the treasure hall of the Papal Court...")
- Total: 1633 FFFF message delimiters, 2185 FFFE line breaks

### R35 (save/load system text)

- sec2_size=2410, 37 messages with pointer table
- Decoded: "セーブしますか？" (Save?), "はい" (Yes), "いいえ" (No), etc.

### R1354 (NPC dialogue)

- sec2_size=19166, 312 messages, 376 line breaks
- Starts with FFFE/FFF0 (line break + formatting code)
- Content: "ウェブスター絆に除上えられた..." (Webster...)

## STATISTICS

| Category | Resources | Messages | Line Breaks | Avg Density |
|----------|-----------|----------|-------------|-------------|
| A: Direct glyph stream | 196 | 22,872 | 23,402 | 21.7 lines/KB |
| B: Complex nested | 314 | 154,214* | 5,996* | 0.0-2.0 lines/KB |

*Complex resources have mostly false-positive FFFF/FFFE counts from binary data

## KEY RESOURCES FOR TRANSLATION

The 20 resources in the "A1 preamble" format (R1196-R1213, R1348, R1353) contain the bulk of translatable NPC dialogue:

| Resource | Messages | Lines | Sec2 Size |
|----------|----------|-------|-----------|
| R1196 | 953 | 1,290 | 61,028 |
| R1197 | 1,099 | 1,460 | 69,212 |
| R1198 | 88 | 129 | 5,874 |
| R1199 | 254 | 345 | 15,834 |
| R1200 | 252 | 640 | 24,358 |
| R1201 | 171 | 217 | 11,032 |
| R1202 | 300 | 436 | 18,634 |
| R1203 | 1,633 | 2,185 | 100,462 |
| R1204 | 999 | 1,307 | 59,372 |
| R1205 | 906 | 1,174 | 55,388 |
| R1206 | 914 | 1,264 | 57,110 |
| R1207 | 912 | 1,176 | 54,398 |
| R1208 | 907 | 1,213 | 54,700 |
| R1209 | 634 | 813 | 37,956 |
| R1210 | 785 | 1,017 | 47,238 |
| R1211 | 635 | 790 | 37,364 |
| R1212 | 723 | 904 | 42,798 |
| R1213 | 49 | 47 | 3,238 |
| R1348 | 10 | 5 | 292 |
| R1353 | 652 | 832 | 38,788 |

**Total: 12,876 messages across 20 resources (~740 KB of glyph data)**

Additional dialogue exists in:
- R35 (37 msgs, save/load UI text with pointer table)
- R1347, R1351-R1352, R1354-R1355 (various direct glyph streams)

## OPEN QUESTIONS

1. **Complex B-type resources**: Do R675-R739, R1911+ contain any translatable dialogue embedded within their nested sub-blocks? Initial evidence suggests no real dialogue (line density ~0.0/KB), but a deeper scan of specific sub-blocks may be needed.

2. **Pointer table format**: R35's pointer table suggests some resources index individual messages. The 20 "A1" resources don't use pointer tables - they rely on sequential FFFF scanning.

3. **Preamble purpose**: The 28-byte preamble in A1 resources ("メダルはい|[1100]階の兵[1322]に問えばわかる？") appears to be a default/fallback dialogue message. Its function is unknown.
