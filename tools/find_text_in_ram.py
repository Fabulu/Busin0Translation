#!/usr/bin/env python3
"""Search EE RAM for R1192's TextEventImage data and find the text textures."""
import zipfile, struct, sys, os
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation'
OUT = f'{BASE}/dumps/textevent'

z = zipfile.ZipFile(f'{BASE}/RAMdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')
print(f'EE RAM: {len(ram)} bytes')

# Search for R1192's magic header 13131313 followed by 0100C700
needle = bytes.fromhex('131313130100c700')
print(f'\nSearching for R1192 header (13131313 0100C700)...')
positions = []
for i in range(0, len(ram) - len(needle)):
    if ram[i:i+len(needle)] == needle:
        positions.append(i)
        print(f'  Found at 0x{i:08X}')

# Also search for R2361's header (13131313 01004C00) - 76 = 0x4C
needle2 = bytes.fromhex('1313131301004c00')
print(f'\nSearching for R2361 header (13131313 01004C00)...')
for i in range(0, len(ram) - len(needle2)):
    if ram[i:i+len(needle2)] == needle2:
        print(f'  Found at 0x{i:08X}')
        positions.append(i)

# For each found position, dump a large region and try to render it
for pos in positions:
    print(f'\n=== TextEventImage data at RAM 0x{pos:08X} ===')
    # Read the count
    count = struct.unpack_from('<H', ram, pos+6)[0]
    print(f'  Count: {count}')

    # Try to find the extent of the data
    # The R1192 section2 was 113032 bytes
    # The R2361 section2 was 23480 bytes
    data_size = 113032 if count == 199 else 23480

    # Dump the pixel data region
    # Skip the header area (first ~0xB0 bytes for R1192, ~0x90 for R2361)
    header_skip = 0xB0 if count == 199 else 0x90
    pixel_data = ram[pos+header_skip:pos+data_size]

    # Render as 8bpp at various widths
    for width in [256, 384, 512, 128]:
        height = len(pixel_data) // width
        if height < 16 or height > 2048:
            continue
        arr = np.frombuffer(pixel_data[:width*height], dtype=np.uint8).reshape(height, width)
        img = Image.fromarray(255 - arr, 'L')
        fname = f'{OUT}/ram_{pos:08X}_8bpp_inv_{width}x{height}.png'
        img.save(fname)
        print(f'  Saved {fname}')

    # Also look for the actual rendered text texture in nearby RAM
    # The game engine creates rendered text bitmaps and uploads them to VRAM
    # Let's search for recognizable text patterns nearby

    # The GS register FB7C might mean the texture is at a specific location
    # Let's look at the area around 0xE30000 (mentioned in extract_intro_texture.py)
    print(f'\n  Dumping known texture regions from RAM...')

# Check specific RAM regions mentioned in existing tools
for region_name, start, size in [
    ('text_E30000', 0x00E30000, 0x20000),
    ('text_E40000', 0x00E40000, 0x10000),
    ('text_E50000', 0x00E50000, 0x10000),
    ('text_E00000', 0x00E00000, 0x30000),
    ('text_D00000', 0x00D00000, 0x20000),
]:
    if start + size <= len(ram):
        region = ram[start:start+size]
        nonzero = sum(1 for b in region if b != 0)
        if nonzero > 100:
            print(f'\n{region_name}: {nonzero}/{size} nonzero bytes')
            for width in [384, 512, 256]:
                height = size // width
                if height > 2048: height = 2048
                arr = np.frombuffer(region[:width*height], dtype=np.uint8).reshape(height, width)
                img = Image.fromarray(arr, 'L')
                fname = f'{OUT}/{region_name}_{width}x{height}.png'
                img.save(fname)
                print(f'  Saved {fname}')

# Search for blocks of memory that look like text textures
# (mostly zero/low values with some moderate values = anti-aliased text)
print('\n=== Scanning RAM for text-like texture regions ===')
for addr in range(0x00C00000, 0x01800000, 0x10000):
    region = ram[addr:addr+0x10000]
    nonzero = sum(1 for b in region if b != 0)
    # Text texture: mostly zeros (background), some non-zero (text)
    # About 5-20% nonzero for sparse text
    ratio = nonzero / len(region)
    if 0.02 < ratio < 0.25:
        # Check if values are clustered (anti-aliased edges)
        unique = len(set(region))
        if unique < 64:
            print(f'  0x{addr:08X}: {nonzero}/{len(region)} nonzero ({ratio:.1%}), {unique} unique values')

print('\nDone')
