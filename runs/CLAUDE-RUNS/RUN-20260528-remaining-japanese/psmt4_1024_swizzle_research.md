# PSMT4 1024x1024 Swizzle Research

## Summary

The VRAM simulation approach (PSMCT32 write -> PSMT4 read) that works for R1272
(256x512) does NOT produce readable glyphs for R1188 (1024x1024), regardless of
the dbw_ct32 value used. Multiple approaches were tested (dbw=64 through 1024,
native PSMT4 deswizzle, raw linear). None produced recognizable characters.
The root cause is likely that R1188's data is NOT organized for PSMCT32 upload,
or uses a game-specific DMA chain layout that requires additional analysis.

## Key Technical Findings from PCSX2 Source Code

### 1. Buffer Width Formula (from GSLocalMemory.h)

The critical code in PCSX2's GSOffset constructor:

```cpp
m_bwPg = bw >> (m_pageShiftX - 6)
```

Where:
- `bw` = GS register buffer width value (TBW field * 64, in pixels, or equivalently
  just TBW since PCSX2 stores it pre-multiplied)
- `m_pageShiftX` = log2(page width in pixels)

Format-specific values:
- PSMCT32: pageWidth=64, pageShiftX=6 -> m_bwPg = bw >> 0 = bw (pages_per_row = TBW)
- PSMT4:   pageWidth=128, pageShiftX=7 -> m_bwPg = bw >> 1 = bw/2 (pages_per_row = TBW/2)

### 2. Page/Block/Column Dimensions (confirmed from PCSX2 GSTables.cpp)

| Format  | Page (px) | Block (px) | Blocks/page | Page bytes |
|---------|-----------|------------|-------------|------------|
| PSMCT32 | 64x32     | 8x8        | 8x4=32      | 8192       |
| PSMT4   | 128x128   | 32x16      | 4x8=32      | 8192       |

Both formats use 8KB per page. Each page has 32 blocks of 256 bytes each.

### 3. TBW Register (from GS documentation + PCSX2)

- TBW is stored in the TEX0 register as a 6-bit field
- Represents buffer width in units of 64 pixels
- For R1188: TBW=16, meaning buffer width = 1024 pixels
- For R1272: TBW=4, meaning buffer width = 256 pixels
- DBW in BITBLTBUF uses the same units (width/64)

### 4. PSMT4-to-PSMCT32 Conversion Factors (from ezswizzle documentation)

When pre-swizzling PSMT4 data for PSMCT32 upload:
- Width factor: divide by 2 (or 8 for bytes: 0.5bpp -> 4bpp = 8x)
- Height factor: multiply by 4

So a 1024x1024 PSMT4 texture would need a PSMCT32 upload of:
- Option A: 128x4096 (width/8, height*4) - but 4096 exceeds GS limits
- Option B: 256x2048 (width/4, height*2) - also exceeds limits
- Option C: 512x1024 (width/2, height)
- Option D: 1024x512 (width, height/2)

### 5. CLUT Format Discovery

R1188 uses CPSM=2 (PSMCT16), not PSMCT32. Each palette entry is 16-bit R5G5B5A1.
The palette in the file contains multiple 16-entry palettes (32 bytes each),
stored as 32-bit words with upper 16 bits zero. The first palette is a
grayscale ramp from 0 to ~247.

## Block and Column Tables Verification

Our tables in tools/psmt4_deswizzle.py are EXACT matches to PCSX2's GSTables.cpp:
- blockTable4: 8x4 array (8 rows, 4 cols) - matches _blockTable4 in PCSX2
- columnTable4: 16x32 array (16 rows, 32 cols) - matches columnTable4 in PCSX2
- blockTable32: 4x8 array - matches _blockTable32 in PCSX2
- columnTable32: 8x8 array - matches columnTable32 in PCSX2

## What Was Tested

### dbw_ct32 values tested:
64, 128, 192, 256, 320, 384, 448, 512, 640, 768, 1024

All produced noise/scrambled patterns, NOT readable glyphs.

### Alternative approaches tested:
1. Raw linear 4bpp (no swizzle) - shows block-pattern noise
2. Native PSMT4 deswizzle (no PSMCT32 phase) - scrambled
3. Simplified block-only unswizzle (no column tables) - scrambled

### Round-trip verification:
The deswizzle->reswizzle round-trip with dbw_ct32=1024 produces an EXACT match
to the original data. This means our swizzle implementation is self-consistent
but the parameters may be wrong.

## Possible Explanations for Failure

### Theory 1: Data is NOT in PSMCT32 upload format
The file may store data in a game-specific format that doesn't correspond to
any standard PS2 GS transfer mode. The game's DMA chain might:
- Use a non-standard buffer width
- Upload in strips/tiles rather than one big rectangle
- Use interleaved transfers across multiple VRAM regions

### Theory 2: The texture is assembled from multiple smaller pieces
The 1024x1024 texture might actually be composed of many smaller sub-textures
(e.g., individual character glyphs) that are separately uploaded to different
VRAM positions. The file stores them contiguously but the game's upload code
places them in a specific VRAM layout.

### Theory 3: The data might need to be interpreted as raw VRAM
If the data represents a raw VRAM dump rather than host upload data, then
no PSMCT32 write phase is needed - we should only apply the PSMT4 read swizzle.
However, this was tested (native PSMT4 deswizzle) and also produced noise.

### Theory 4: Different header/data boundaries
The actual pixel data might not start at offset 0x800. The header analysis shows
repeating GIF A+D blocks every 0x50 bytes, and the header might be larger than
2048 bytes. Also, the trailing palette/metadata might extend further into the
pixel region.

## Answer to the Key Question

**What dbw_ct32 should we use for 1024x1024 PSMT4 with TBW=16?**

Based on PCSX2 source analysis, if the game uploads as PSMCT32 with the same
TBW register value:
- TBW = 16 (register value)
- DBW = 16 (same register units = 16 * 64 = 1024 pixels)
- dbw_ct32 = 1024 pixels

This is what we already use. The formula is: **dbw_ct32 = TBW * 64**.

The formula dbw_ct32 = tex_w / 4 (= 256) does NOT apply here. That formula
would only apply if the game explicitly uses a different DBW for the upload
than the TBW for texture sampling.

For PSMT8, dbw_ct32 = tex_w / 2 works because PSMT8 has page width 128
(vs PSMCT32's 64), so the game naturally uses half the pixel width for the
PSMCT32 upload. But for PSMT4, the page width is also 128, so the same
tex_w / 2 formula should theoretically apply if matching page layouts.

However, since neither formula produces correct results for R1188,
**the problem is not the dbw_ct32 value** -- it's something more fundamental
about how R1188's data is organized.

## Recommended Next Steps

1. **Capture the actual DMA chain** from PCSX2 during R1188 upload to see
   the exact BITBLTBUF.DBW and TRXREG values used by the game
2. **Use PCSX2's texture dump** feature to get the correctly decoded texture,
   then compare with our deswizzle output to identify the mismatch
3. **Check if R1188 data is tiled** - the game might upload individual
   character cells to specific VRAM positions rather than one big transfer
4. **Try EXE disassembly** around the code that loads resource 1188 to find
   the actual GIF packet construction

## Sources

- PCSX2 source: GSLocalMemory.h, GSTables.cpp, GSLocalMemoryMultiISA.cpp
  (https://github.com/PCSX2/pcsx2)
- ezswizzle documentation: TextureSwizzling.pdf
  (http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf)
- PS2 GS register reference: PSDevWiki
  (https://www.psdevwiki.com/ps2/Graphics_Synthesizer)
- Maister's PS2 GS emulation blog
  (https://themaister.net/blog/2024/07/03/playstation-2-gs-emulation-the-final-frontier-of-vulkan-compute-emulation/)
- Fireboyd78's PSMT4 unswizzle gist
  (https://gist.github.com/Fireboyd78/1546f5c86ebce52ce05e7837c697dc72)
- TellowKrinkle's GS memory swizzle visualizer
  (https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9)
- ResHax: C code to swizzle 4bpp PS2 textures
  (https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/)
