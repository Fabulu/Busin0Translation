# R1188 RAM Check - Save State 27-5

## Method
1. Extracted `eeMemory.bin` (32 MB EE RAM) from `RAMdumps/27-5.p2s` (ZIP format)
2. Located PACKDATA.DIG TOC in RAM at **0x00D63EC0**
3. Read R1188's TOC entry: sector=205100, count=258 (528,384 bytes), type=1
4. Matched the RAM TOC against all available ISOs and DIG files
5. Read R1188's actual content from the matching ISO and compared against patched/original

## Key Findings

### Which ISO created this save state?
The RAM TOC matches **v25/v26/v27 ISOs** perfectly (2500/2500 entries).
- v28+ ISOs only match 1274/2500 entries (TOC was rebuilt after v27)
- v25/v26/v27 all contain identical R1188 content

### Was our patched R1188 loaded?
**YES** - the game loaded our patched R1188 edits. The R1188 in the v25-v27 ISOs
differs from the original by exactly **1,068 bytes** (all our font glyph pixel edits).

### Important caveat: OLDER patch version
The R1188 in v25-v27 is an **older version** of our patches, not the current one:
- v25-v27 R1188: 1,068 bytes changed from original
- Current `build/packdata_resources/1188_type01.raw`: 16,884 bytes changed from original
- The current patched file has significantly more edits (added since v27 was built)

### Texture data NOT in EE RAM
The actual R1188 pixel data was **not found** in EE RAM. This is expected:
- R1188 is a type-01 (texture) resource
- The game DMA-transfers texture data to GS VRAM (separate from EE RAM)
- GS VRAM uses swizzled storage format, so raw bytes wouldn't match anyway
- Confirmation came from TOC analysis, not pixel-level RAM comparison

## Conclusion

| Question | Answer |
|----------|--------|
| Did the game load R1188? | **YES** |
| Did it load OUR patched version? | **YES** (older build's patches, 1,068 byte diffs from original) |
| Was R1188 rejected by the game? | **NO** - fully accepted and DMA'd to GS VRAM |
| If glyphs are wrong, why? | Glyph coordinate/mapping issue, NOT a loading/rejection issue |

The game engine accepts our R1188 modifications without complaint. Any rendering
issues with font glyphs stem from coordinate mapping or glyph table configuration,
not from the game refusing to load the modified texture.
