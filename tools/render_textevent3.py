#!/usr/bin/env python3
"""Render TextEventImage with proper GS register decoding."""
import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

BASE = 'C:/Programmieren/wizardrytranslation'
OUT = f'{BASE}/dumps/textevent'
os.makedirs(OUT, exist_ok=True)

for idx in [1192, 2361]:
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type02.raw"
    data = open(rawfile, 'rb').read()
    s2o = struct.unpack_from('<I', data, 24)[0]
    s2t = struct.unpack_from('<I', data, 20)[0]
    s2 = data[s2o:s2o+s2t]
    count = struct.unpack_from('<H', s2, 6)[0]

    print(f"\n{'='*60}")
    print(f"=== R{idx}: {count} entries, S2 = {s2t} bytes ===")

    # Let's decode the GS setup more carefully
    # At offset 0x10: first 4 bytes = 0x00000018 = 24
    # This 24 might be the size of the GS setup in quadwords (24 * 16 = 384 bytes)
    # Or it's the number of GIF tags / DMA transfers

    # Actually, looking at the PS2 GIF tag format:
    # The value at +0x14 for R1192 is 0x0018F000
    # GS BITBLTBUF register (0x50):
    #   SBP[13:0] = source base pointer in 256-byte units
    #   SBW[21:16] = source buffer width / 64
    #   SPSM[29:24] = source pixel storage mode
    #   DBP[45:32] = dest base pointer
    #   DBW[53:48] = dest buffer width / 64
    #   DPSM[61:56] = dest pixel storage mode

    # But 0x34034000 is not 0x50. Let me look at this differently.
    # 0x34 is GS register TEX0_1: texture base pointer, buffer width, etc.
    # TEX0_1 (0x06): TBP0[13:0], TBW[19:14], PSM[25:20], TW[29:26], TH[33:30], ...

    # But these values are in the data section, not actual GS register writes.
    # The game engine interprets these as DMA chain entries.

    # Let me try a different approach: just look at the actual data
    # The header region (0x10 to ~0xAC for R1192) contains 13 groups of 12 bytes
    # Each group has a progressive VRAM offset pattern:
    #   FB7C, FB88, FB94, FBA0, FBAC, FBB8, FBC4, FBD0, FBDC, FBE8, FBF4, FC00, FC0C
    # These are VRAM addresses spaced 12 (0x0C) apart
    # 13 entries * something = VRAM tile uploads

    # The key insight: look at offset 0xAC for R1192
    # 60 02 8F 01 = two values: 0x0260 = 608, 0x018F = 399
    # This could be the texture dimensions: 608 x 399? Or 399 x 608?
    # That seems too odd. Let's try it anyway.

    # Actually wait -- 0x0260 = 608 and 0x018F = 399
    # But more likely: the data at 0xA8 is still part of the GS entries
    # The REAL data starts at 0xB0 or 0xB4

    # For R1192: after the header, the "animation table" from ~0xB8
    # has entries like: 00 01 20 00 02 20 00 02
    # These are 3-byte entries where each entry is (frame_byte, offset_high, offset_low)
    # With offset values: 0x0120, 0x0220, 0x0220, 0x0220, 0x0230, 0x0330...
    # These are byte offsets within the texture data

    # For R2361: the header ends around 0x88, then mostly zeros until 0x94
    # Data starts around 0x94

    # The GS address pattern for R2361:
    # 26F4, 2700, 270C, 2718, 2724, 2730, 273C, 2748, 2754, 2760
    # Spaced 12 (0x0C) apart, just like R1192

    # Each 12-byte-apart set = one 192x32 tile?
    # Or each set represents a texture page upload

    # Let me try rendering with width = 192 (common for PS2 event text)
    # Also try 384 (double) and 96 (half)

    # Skip header completely - find first non-header data
    # For R1192, the real pixel data likely starts after the offset table
    # which appears to end around offset 0x630 based on the data blocks analysis

    # Actually, let's re-examine. The "first data block" for R1192 was at
    # +0x100 to +0x630. But this block's content was:
    # 000dd0000ef0000ff00010100111100111100112200113400115500115500116...
    # That's still part of the offset/animation table (ascending values)

    # The actual pixel data starts after all the control tables
    # Let me find where the high-entropy pixel data begins

    # Scan for transition from low-entropy (table) to high-entropy (pixels)
    pixel_start = None
    for i in range(0x100, len(s2) - 64, 16):
        block = s2[i:i+64]
        unique = len(set(block))
        if unique > 40:  # high entropy = likely pixel data
            pixel_start = i
            break

    if pixel_start:
        print(f"  High-entropy data starts at +{pixel_start:04X}")
    else:
        pixel_start = 0x100
        print(f"  Using default pixel start +{pixel_start:04X}")

    pixel_data = s2[pixel_start:]
    print(f"  Pixel data region: {len(pixel_data)} bytes")

    # The R1192 intro narration shows text that appears as lines, fading in
    # Common PS2 text texture sizes for narration:
    # 512x32 per text line, or 256x64, or 384x32

    # Given R1192 has 199 "entries" and the total pixel data is ~108KB:
    # 108000 / 199 = ~543 bytes per entry
    # If 8bpp: 543 pixels = not a clean dimension
    # If 4bpp: 1086 pixels = not clean either
    # If each entry is a text line: maybe 384x1.4 pixels (8bpp)... not clean

    # Let me try: total pixel area / count
    # 112000 bytes, 199 entries
    # If texture is 384 wide: 112000 / 384 = 291 rows, 291/199 = ~1.5 rows per entry
    # Not helpful.

    # Let me look at the actual data differently. Each "data block" might be one
    # frame/text-line's texture. The blocks have varying sizes (670-4483 bytes).

    # Common PS2 text rendering:
    # 512x32 = 16384 bytes (8bpp) or 8192 (4bpp) -- way bigger than most blocks
    # 256x16 = 4096 (8bpp) or 2048 (4bpp) -- close to big blocks
    # 192x16 = 3072 (8bpp) -- also reasonable

    # These are likely NOT full bitmaps but rather compressed or run-length encoded
    # Or they might be much smaller texture strips

    # Let me just try every reasonable width with the raw data
    for width in [64, 96, 128, 192, 256, 320, 384, 512]:
        height = min(len(pixel_data) // width, 2048)
        if height < 16:
            continue
        arr = np.frombuffer(pixel_data[:width*height], dtype=np.uint8).reshape(height, width)
        img = Image.fromarray(arr, 'L')
        fname = f'{OUT}/R{idx}_pixels_{width}x{height}.png'
        img.save(fname)
        print(f"  Saved {fname}")

    # Also try 4bpp interpretation (each byte = 2 pixels)
    for width in [128, 256, 384, 512]:
        pixel_count = len(pixel_data) * 2
        height = min(pixel_count // width, 2048)
        if height < 16:
            continue
        arr = np.zeros(width * height, dtype=np.uint8)
        for bi in range(min(len(pixel_data), width * height // 2)):
            b = pixel_data[bi]
            arr[bi*2] = (b & 0x0F) * 17
            arr[bi*2+1] = ((b >> 4) & 0x0F) * 17
        arr = arr[:width*height].reshape(height, width)
        img = Image.fromarray(arr, 'L')
        fname = f'{OUT}/R{idx}_4bpp_{width}x{height}.png'
        img.save(fname)
        print(f"  Saved {fname}")

print("\nDone!")
