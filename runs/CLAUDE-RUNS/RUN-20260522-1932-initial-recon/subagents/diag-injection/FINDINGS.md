# MSG Resource Injection Diagnostic -- FINDINGS

Date: 2026-05-22

## Summary

**TWO CRITICAL BUGS found in `build/full_patch_pipeline.py` STEP 2 (MSG injection).**

Both bugs stem from the `find_ss()` stream-start detection heuristic, which scans
for the first `0xFFFF` or `0xFFFE` big-endian word after the 16-byte sub-header.
This heuristic is WRONG for most type01 MSG resources.

---

## Bug 1: Stream Start Misidentification (2-byte offset table truncation)

### What happens

The offset table in type01 MSG resources uses 4-byte entries:

    [BE u16 message_offset] [BE u16 flags]

The LAST entry in many resources has `flags = 0xFFFF`. The `find_ss()` function
hits this `0xFFFF` at byte position `ss` and treats it as the start of the
glyph stream. This is 2 bytes too early -- the actual glyph stream starts at
`ss + 2`.

### Consequence

`pre = raw[16:ss]` captures the offset table minus its last 2 bytes. The new
glyph stream is placed 2 bytes before where the offset table says messages
should be. **Every message pointer in the offset table is now wrong by at
least 2 bytes.**

### Affected resources (13 of 21 modified)

| Resource | find_ss | Correct ss | Last offset |
|----------|---------|------------|-------------|
| 36       | 0x28A   | 0x28C      | 0x0D30      |
| 37       | 0x20A   | 0x20C      | 0x0B56      |
| 38       | 0x302   | 0x304      | 0x1D44      |
| 40       | 0x0F6   | 0x0F8      | 0x07AA      |
| 41       | 0x05A   | 0x05C      | 0x03CE      |
| 42       | 0x04A   | 0x04C      | 0x0252      |
| 43       | 0x0AE   | 0x0B0      | 0x0570      |
| 44       | 0x0FA   | 0x0FC      | 0x08F0      |
| 45       | 0x326   | 0x328      | 0x1B10      |
| 48       | 0x1BE   | 0x1C0      | 0x0874      |
| 49       | 0x1CE   | 0x1D0      | 0x0D6A      |
| 1272     | 0x072   | 0x074      | 0x0000      |
| 2124     | 0x202   | 0x204      | 0x0000      |

---

## Bug 2: Offset Table Not Rebuilt After Message Replacement

### What happens

The pipeline replaces individual messages with English translations of
different byte lengths, but does NOT update the offset table entries to
reflect the new message positions.

### Consequence for Resource 49

Offset table has 111 message entries (entry[0] = count = 111, entries[1..111]
are byte offsets from payload start to each message).

After injection:

| Message | Table says    | Actual position | Delta  |
|---------|--------------|-----------------|--------|
| 0       | 0x01C0 (448) | 0x01BE (446)    | -2     |
| 1       | 0x01DC (476) | 0x01E4 (484)    | +8     |
| 2       | 0x01FA (506) | 0x021E (542)    | +36    |
| 3       | 0x0216 (534) | 0x0258 (600)    | +66    |
| 4       | 0x0250 (592) | 0x02B2 (690)    | +98    |

The drift grows with each message because English translations are typically
longer than the original Japanese glyph sequences. **ALL 111 message offsets
are wrong.** The game would read garbage from the middle of other messages.

---

## What IS Correct

Despite the offset table bugs, several things are done correctly:

1. **Sub-header payload_size** -- correctly updated (3458 -> 6120 for r49)
2. **PACKDATA.DIG TOC** -- sector offset and sector count updated correctly
3. **PACKDATA.DIG contains the modified data** -- verified byte-for-byte match
   between `build/packdata_resources/0049_type01.raw` and the data at the TOC
   offset in `build/PACKDATA.DIG`
4. **Glyph encoding** -- English text is correctly encoded using the glyph table
   (e.g., message 1 decodes to "Can't open from [NL] this side.")
5. **Sector padding** -- files correctly padded to 2048-byte boundaries

---

## Offset Table Format (Type01 MSG Resources)

```
File layout:
  [0x00..0x0F]  16-byte sub-header (LE):
                  u32 zero, u32 payload_size, u32 stride(=16), u32 zero
  [0x10..0x13]  Entry 0: BE u16 message_count, BE u16 0x0000
  [0x14..0x17]  Entry 1: BE u16 offset_to_msg0, BE u16 0x0000
  [0x18..0x1B]  Entry 2: BE u16 offset_to_msg1, BE u16 0x0000
  ...
  [last entry]  Entry N: BE u16 offset_to_msgN-1, BE u16 0xFFFF (terminator flag)
  [after table] Glyph stream: BE u16 glyph words, 0xFFFF between messages
```

- Entry[0] value = number of messages (e.g., 111 = 0x006F for resource 49)
- Entry[1..N] values = byte offset from payload start (byte 16) to each message
- The flags field of the last entry is 0xFFFF (NOT a stream terminator)
- All other entries have flags = 0x0000

---

## Recommended Fix

In `build/full_patch_pipeline.py`, the injection loop needs two changes:

### Fix 1: Correct stream start detection

Instead of scanning for `0xFFFF`, parse the offset table properly:

```python
# Read entry[0] as message count
msg_count = struct.unpack_from(">H", raw, 0x10)[0]
# Offset table = (msg_count + 1) entries * 4 bytes, starting at byte 16
table_size = (msg_count + 1) * 4
ss = 16 + table_size  # correct stream start
```

### Fix 2: Rebuild offset table after message replacement

After rebuilding the glyph stream with new message lengths, recompute
all offset table entries:

```python
# After building ns (new stream), compute new offsets
new_offsets = []
pos = table_size  # first message starts right after offset table in payload
for mi in range(msg_count):
    new_offsets.append(pos)
    # scan ns to find end of message mi...
    pos += msg_length[mi] + 2  # +2 for 0xFFFF terminator

# Rebuild offset table
pre = bytearray()
pre += struct.pack(">HH", msg_count, 0x0000)
for i, off in enumerate(new_offsets):
    flags = 0xFFFF if i == len(new_offsets) - 1 else 0x0000
    pre += struct.pack(">HH", off, flags)
```

---

## Files Examined

- `C:/Programmieren/wizardrytranslation/extracted/packdata_raw/0049_type01.raw` (original, 4096 bytes)
- `C:/Programmieren/wizardrytranslation/build/packdata_resources/0049_type01.raw` (modified, 6144 bytes)
- `C:/Programmieren/wizardrytranslation/build/PACKDATA.DIG` (rebuilt, 839,661,568 bytes)
- `C:/Programmieren/wizardrytranslation/build/full_patch_pipeline.py` (injection script, lines 40-78)
- `C:/Programmieren/wizardrytranslation/data/english_glyph_table.json` (glyph index mapping)
