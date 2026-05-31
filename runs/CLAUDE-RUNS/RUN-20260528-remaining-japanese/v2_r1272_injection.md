# R1272 Font Atlas Injection Analysis (build_full_english_v2.py)

## Location
`build/build_full_english_v2.py`, lines 174-194 (STEP 3)

## What the injection code does

The code is extremely simple -- NO format conversion of any kind:

```python
font_data = open('build/english_font_atlas.bin', 'rb').read()
orig_1272 = open(raw_1272, 'rb').read()

# Reads original 16-byte sub-header, keeps h0/h2/h3, updates h1 to new size
new_sub = struct.pack('<IIII', h0, len(font_data), h2, h3)
new_1272 = new_sub + font_data   # concatenate header + raw atlas
# sector-pad with zeros
```

### Answers to specific questions

| Question | Answer |
|----------|--------|
| Just concatenates sub-header + font_data? | **YES** -- raw concatenation, no conversion |
| Applies any swizzle? | **NO** |
| Does any byte reordering? | **NO** |
| Modifies TEX0 register in header? | **NO** -- TEX0 lives inside the GS packet within the payload, not the sub-header. The sub-header has no TEX0 field. |

## Sub-header comparison

The sub-header is 16 bytes, 4x uint32 LE:

| Field | Offset | Original | New | Changed? |
|-------|--------|----------|-----|----------|
| h0 | 0x00 | 0x00000000 | 0x00000000 | No (preserved) |
| h1 (payload_size) | 0x04 | 0x00010100 (65,792) | 0x00014100 (82,176) | **YES** -- updated to new atlas size |
| h2 | 0x08 | 0x00000010 (16) | 0x00000010 (16) | No (preserved) |
| h3 | 0x0C | 0x00000000 | 0x00000000 | No (preserved) |

Only h1 (payload_size) changes. The meaning of h2=16 is unclear (possibly GS buffer width or stride); it is blindly preserved from the original.

## Extra data beyond payload in original

- Original total size: 67,584 bytes
- Sub-header: 16 bytes
- Payload (h1): 65,792 bytes
- Extra beyond payload: **1,776 bytes -- ALL ZEROS**
- Build script discards this extra data (not copied to new resource)
- Since it's all zeros, this is harmless -- it was just sector padding

## Atlas .bin internal format

The atlas .bin already contains the full GS packet structure (GIF tags, register writes, pixel data). The first 64 bytes of the original R1272 payload and the new atlas .bin are **byte-identical**, confirming `generate_font_atlas.py` produces the complete GS-format payload.

## New resource size

- New R1272 before padding: 82,192 bytes (16 header + 82,176 atlas)
- Sectors needed: 41
- New R1272 after sector padding: 83,968 bytes

## Conclusion

The injection is a clean pass-through: the sub-header payload_size is updated, and the raw atlas binary (which already contains correct GS packet formatting from `generate_font_atlas.py`) is concatenated directly. No format conversion, swizzle, or TEX0 modification occurs in the build script. All GS register setup (including TEX0) is handled inside `generate_font_atlas.py` when creating the .bin file.
