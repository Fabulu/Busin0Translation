#!/usr/bin/env python3
"""Try rendering entire R1192 section2 as a single large PSMT8 texture.
   The data might NOT be PSMT4 -- it could be 8bpp or even 32bpp RGBA."""
import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

BASE = 'C:/Programmieren/wizardrytranslation'
OUT = f'{BASE}/dumps/textevent'
os.makedirs(OUT, exist_ok=True)

def analyze_data_entropy(data, offset, length, block_size=256):
    """Analyze data entropy in blocks."""
    results = []
    for i in range(offset, min(offset + length, len(data)), block_size):
        block = data[i:i+block_size]
        nonzero = sum(1 for b in block if b != 0)
        unique = len(set(block))
        results.append((i, nonzero, unique))
    return results

for idx in [1192, 2361]:
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type02.raw"
    data = open(rawfile, 'rb').read()
    s2o = struct.unpack_from('<I', data, 24)[0]
    s2t = struct.unpack_from('<I', data, 20)[0]
    s2 = data[s2o:s2o+s2t]
    count = struct.unpack_from('<H', s2, 6)[0]

    print(f"\n{'='*60}")
    print(f"=== R{idx}: {count} entries, S2 = {s2t} bytes ===")

    # Analyze entropy profile of the entire section 2
    entropy = analyze_data_entropy(s2, 0, len(s2), 256)
    print(f"\nEntropy profile (blocks of 256 bytes):")
    for off, nz, uniq in entropy[:10]:
        print(f"  +{off:05X}: nonzero={nz:3d}/256, unique={uniq:3d}")
    print(f"  ...")
    # Find transitions
    prev_type = 'low'
    for off, nz, uniq in entropy:
        curr_type = 'high' if uniq > 30 else 'low'
        if curr_type != prev_type:
            print(f"  +{off:05X}: TRANSITION to {curr_type} (nonzero={nz}, unique={uniq})")
            prev_type = curr_type

    # Let me try a very different interpretation:
    # What if the data from 0xB8 is NOT a table but IS the actual pixel data?
    # The "table" entries (00 01 20 00 02...) could be pixel values!

    # For text rendered as white on black, most pixels are 0 (black)
    # with occasional non-zero values (anti-aliased text edges)
    # The pattern of mostly-zero bytes with occasional small values fits!

    # Let me try rendering from offset 0xB8 (after the 13131313 header + GS setup)
    header_end = 0xB8 if idx == 1192 else 0x94
    pixel_data = s2[header_end:]

    print(f"\n  Rendering from +{header_end:03X}, {len(pixel_data)} bytes")

    # R1192 intro narration:
    # - Text appears in the center of screen
    # - PS2 resolution 640x448 or 512x448
    # - Text likely occupies ~400px wide, ~32px tall per line
    # - With 199 frames and ~15 lines, might be a 512x256 or 384x256 texture atlas

    # The total data from 0xB8 = 113032 - 0xB8 = 112848 bytes
    # If 8bpp 512 wide: 112848/512 = 220 rows
    # If 8bpp 384 wide: 112848/384 = 293 rows
    # If 4bpp 512 wide: 112848*2/512 = 440 rows
    # If 4bpp 384 wide: 112848*2/384 = 587 rows

    # The GS value 0x0018F000 might encode TBW=6 (buffer width = 384)
    # TEX0: TBP0[13:0]=0x000, TBW[19:14]=0x06=384px, PSM[25:20]=0x00=PSMCT32
    # Wait, let me parse it differently:
    # 0x0018F000 as TEX0 bits:
    #   TBP0 = bits[13:0] = 0x0018F000 & 0x3FFF = 0x3000 = 12288
    #   TBW = bits[19:14] = (0x0018F000 >> 14) & 0x3F = 0x63C >> 14 = hmm...
    # This doesn't parse cleanly as TEX0.

    # Let me just try the most common PS2 text texture widths
    for width in [384, 512, 256, 448, 320, 640]:
        height = len(pixel_data) // width
        if height < 16: continue
        arr = np.frombuffer(pixel_data[:width*height], dtype=np.uint8).reshape(height, width)
        # Try both normal and inverted
        img = Image.fromarray(arr, 'L')
        fname = f'{OUT}/R{idx}_full8bpp_{width}x{height}.png'
        img.save(fname)

        img_inv = Image.fromarray(255 - arr, 'L')
        fname2 = f'{OUT}/R{idx}_full8bpp_inv_{width}x{height}.png'
        img_inv.save(fname2)
        print(f"  Saved {width}x{height}")

    # Try 4bpp full data
    for width in [384, 512, 768, 256]:
        npix = len(pixel_data) * 2
        height = npix // width
        if height < 16 or height > 2048: continue
        arr = np.zeros(width * height, dtype=np.uint8)
        for bi in range(min(len(pixel_data), width * height // 2)):
            b = pixel_data[bi]
            arr[bi*2] = (b & 0x0F) * 17
            arr[bi*2+1] = ((b >> 4) & 0x0F) * 17
        arr = arr[:width*height].reshape(height, width)
        img = Image.fromarray(255 - arr, 'L')
        fname = f'{OUT}/R{idx}_full4bpp_inv_{width}x{height}.png'
        img.save(fname)
        print(f"  Saved 4bpp {width}x{height}")

    # Also try: what if data is 32bpp RGBA? (4 bytes per pixel)
    for width in [128, 192, 256, 384]:
        npix = len(pixel_data) // 4
        height = npix // width
        if height < 16 or height > 2048: continue
        arr = np.frombuffer(pixel_data[:width*height*4], dtype=np.uint8).reshape(height, width, 4)
        img = Image.fromarray(arr[:,:,:3], 'RGB')
        fname = f'{OUT}/R{idx}_rgba_{width}x{height}.png'
        img.save(fname)
        print(f"  Saved RGBA {width}x{height}")

print("\nDone!")
