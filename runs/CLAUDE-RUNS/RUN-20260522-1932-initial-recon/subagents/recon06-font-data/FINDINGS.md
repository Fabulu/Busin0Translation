# Recon 06: Font/Glyph Data and Character Encoding Tables

## Summary

Font and text rendering analysis for Busin 0: Wizardry Alternative Neo (PS2, 2003).
The game does NOT use standard TIM2 font textures. Font glyph data is almost certainly
stored inside PACKDATA.DIG as compressed entries, making it harder to locate without
first understanding the pack file's compression scheme.

## Key Findings

### 1. No TIM2 Font Textures Found

A full scan of the entire 800MB PACKDATA.DIG found **zero TIM2 headers**. The game
uses a custom compressed data format for all assets. Each PACKDATA entry has a 16-byte
internal header: `00 00 00 00 [compressed_size:4] [header_flag:4] 00 00 00 00`.
The header_flag values observed: 0x20 (type 2), 0x30 (type 3), 0x40 (type 4),
0xA0 (type 10), 0x140 (type 20), 0xF0 (type 15).

Font textures are therefore inside compressed PACKDATA entries and cannot be located
until the compression format is reverse-engineered.

### 2. No Explicit SJIS Mapping Tables in EXE

No continuous Shift-JIS character mapping tables were found in the EXE. The game
likely either:
- Uses standard SJIS encoding directly (computing glyph positions from SJIS codepoints
  algorithmically rather than via lookup table)
- Stores the mapping table inside PACKDATA.DIG alongside the font texture

### 3. Log2 Tables Misidentified as Font Width Tables

The 4 identical 256-byte tables at 0x3DDC40-0x3DE040 (detected as "width tables" by
the initial scan) are actually **floor(log2(n))** lookup tables from the C standard
library (pattern: 0,1,2,2,3,3,3,3,4*8,5*16,6*32,7*64,8*128). The adjacent data at
0x3DE040 is a standard **ctype classification table** (character type flags for
ASCII 0-255). These are part of the Metrowerks CodeWarrior C runtime library.

### 4. PS2 SDK Libraries Present

The EXE contains Metrowerks CodeWarrior compiler output ("MW MIPS C Compiler (2.4.1.01)")
with standard PS2 SDK libraries:
- `PsIIlibipu 2500` -- IPU (Image Processing Unit) library
- `PsIIlibkernl2540` -- Kernel library
- Standard IOP modules: SIO2MAN, PADMAN, MCMAN, MCSERV, LIBSD, MODMIDI, MODHSYN,
  MODMSIN, MUS

### 5. Debug Strings Confirm SJIS Text System

464 Shift-JIS text strings found in the EXE data section (0x3EC910-0x3FC7F0).
Notable examples:
- `0x3EC910`: "Debug check!!!" (in Japanese)
- `0x3F0B00`: "Monster magic use : magic_no=%d : magic_id=%d" (mixed SJIS + ASCII format string)
- `0x3F3636`: "Wall event data creation error" (in Japanese)
- `0x3F9370`: "BUSIN 0 pause data" (full-width chars)
- `0x3FC7F0`: "Matsuno game boot!!" (in Japanese -- likely a developer reference)

These debug strings prove the game uses Shift-JIS encoding and processes format strings
with mixed SJIS/ASCII content.

### 6. ELF Structure

- Format: MIPS ELF, entry point 0x00100008
- Text segment: vaddr 0x00100000, file offset 0x80, file size 0x3FDC80 (4.0MB), mem size 0x479800 (4.5MB)
- Load base for VA calculation: file_offset + 0x000FFF80 = VA

### 7. PACKDATA.DIG Structure (Partial)

The pack file uses a sector-based TOC (sector size = 2048 bytes):
- First 4 bytes: not a simple entry count (value 125 = number of sectors before data)
- TOC entries: 12 bytes each (sector_offset, sector_count, type)
- 500+ entries parsed before running out of TOC space
- Entry types observed: 1, 2, 3, 4, 10, 15, 20
- Entries contain sub-headers with nested sub-entries (16 bytes each: index, csz, offset, 0)

**Potential font entries** (based on size and type):
- Entry 34 (type=20, 68KB, 16 sub-entries) -- unusual type, multi-resource container
- Entry 26 (type=10, 326KB) -- large, unusual type
- Entry 30 (type=2, 806KB) -- largest type-2 entry

### 8. No SJIS Range-Check Code Identified

Despite searching for canonical MIPS SJIS detection patterns (sltiu with 0x80, 0x81,
0x9F, 0xA0, 0xE0, 0xF0), no clear SJIS lead-byte parsing function was identified.
The few `slti $r,$r,0x80` instructions found were used for color/brightness clamping,
not character encoding. This suggests the text system may use a simpler custom encoding
rather than raw SJIS, or the SJIS parsing is in an IOP overlay module.

## Recommendations for Next Steps

1. **Reverse-engineer PACKDATA.DIG compression** -- This is the critical blocker.
   The compressed_size vs sector allocation ratio suggests a standard algorithm
   (likely LZSS or similar). Once decompressed, font textures should be identifiable
   by their characteristic dimensions.

2. **Trace text rendering from debug strings** -- The debug strings at 0x3EC910+
   have known VA addresses. Use a PS2 debugger (PCSX2 debugger) to set breakpoints
   on string references and trace into the text rendering call chain.

3. **Examine Entry 34 (type=20)** -- This 68KB multi-resource container with 16
   sub-entries is the most likely font data location. After decompression, look for
   glyph bitmap data and character width tables.

4. **Check if font is generated at runtime via IPU** -- The presence of PsIIlibipu
   (Image Processing Unit library) could indicate the game generates font textures
   from compressed data using the PS2's hardware IPU decoder.

## Files Produced

- `C:/Programmieren/wizardrytranslation/tools/find_font_data.py` -- Analysis script
- `C:/Programmieren/wizardrytranslation/dumps/font_analysis.txt` -- Script output
- `C:/Programmieren/wizardrytranslation/dumps/sjis_strings_in_exe.txt` -- All SJIS strings found in EXE
