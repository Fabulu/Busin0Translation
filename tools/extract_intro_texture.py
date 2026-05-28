#!/usr/bin/env python3
"""Extract potential text textures from RAM and save as images."""
import zipfile
import struct
import sys
from PIL import Image
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

output_dir = 'C:/Programmieren/wizardrytranslation/ramdumps'

# Extract regions that look like text textures
# Focus on 0x00E30000-0x00E50000
for region_name, start_addr, size in [
    ('text_E30000', 0x00E30000, 0x20000),  # 128KB
    ('text_E40000', 0x00E40000, 0x10000),  # 64KB
    ('text_E50000', 0x00E50000, 0x10000),  # 64KB
]:
    data = ram[start_addr:start_addr + size]

    # Try interpreting as 8bpp grayscale texture at various widths
    for width in [256, 512, 640, 320]:
        height = size // width
        if height < 16:
            continue
        # Create image from raw 8-bit data
        arr = np.frombuffer(data[:width*height], dtype=np.uint8).reshape(height, width)
        img = Image.fromarray(arr, 'L')
        fname = f'{output_dir}/{region_name}_8bpp_{width}x{height}.png'
        img.save(fname)
        print(f"Saved {fname}")

    # Try 4bpp (each byte = 2 pixels)
    for width in [256, 512]:
        pixel_count = size * 2  # 2 pixels per byte
        height = pixel_count // width
        if height < 16:
            continue
        # Unpack nibbles
        arr = np.zeros(pixel_count, dtype=np.uint8)
        for i, b in enumerate(data):
            arr[i*2] = (b & 0x0F) * 17  # Scale 0-15 to 0-255
            arr[i*2+1] = ((b >> 4) & 0x0F) * 17
        arr = arr[:width*height].reshape(height, width)
        img = Image.fromarray(arr, 'L')
        fname = f'{output_dir}/{region_name}_4bpp_{width}x{height}.png'
        img.save(fname)
        print(f"Saved {fname}")

# Also try the GS VRAM
print("\n=== Extracting GS VRAM ===")
gs = z.read('GS.bin')
# GS.bin starts with register state, then 4MB VRAM
# The register state size varies, but typically the VRAM is the last 4MB
vram_start = len(gs) - 4*1024*1024
if vram_start >= 0:
    vram = gs[vram_start:]
    print(f"VRAM from offset {vram_start} in GS.bin, size {len(vram)}")

    # PS2 VRAM is 4MB at 1024 pixels wide (32bpp) = 1024x1024
    # Or 2048 wide (16bpp) = 2048x1024
    # Try various interpretations
    for width in [1024, 2048, 640]:
        bpp = 32 if width <= 1024 else 16
        if bpp == 32:
            height = len(vram) // (width * 4)
            if height < 16:
                continue
            arr = np.frombuffer(vram[:width*height*4], dtype=np.uint8).reshape(height, width, 4)
            # RGBA -> RGB for display
            img = Image.fromarray(arr[:,:,:3], 'RGB')
        else:
            height = len(vram) // (width * 2)
            if height < 16:
                continue
            arr16 = np.frombuffer(vram[:width*height*2], dtype=np.uint16).reshape(height, width)
            # Convert RGB555 to RGB888
            r = ((arr16 >> 0) & 0x1F) * 8
            g = ((arr16 >> 5) & 0x1F) * 8
            b = ((arr16 >> 10) & 0x1F) * 8
            arr = np.stack([r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8)], axis=-1)
            img = Image.fromarray(arr, 'RGB')

        fname = f'{output_dir}/vram_{bpp}bpp_{width}x{height}.png'
        img.save(fname)
        print(f"Saved {fname}")

# Also check GS register state at the beginning
print(f"\nGS.bin first 128 bytes: {gs[:128].hex()}")
# The PCSX2 GS savestate typically starts with a magic/version
# then register state, then VRAM
# Let's look for the VRAM offset indicator
print(f"Bytes at offset 0: {gs[:4].hex()}")
print(f"Likely VRAM starts right after register state")
# PCSX2 2.x format: first word is version? then registers + paths
# Let's try reading VRAM from offset 813 (4194813 - 4194304 = 509... not 4MB aligned)
# 4194813 = 4*1024*1024 + 513
# So there are 513 bytes of header, then 4MB VRAM
header_size = len(gs) - 4*1024*1024
print(f"Header size: {header_size} bytes")

if header_size > 0 and header_size < 10000:
    vram = gs[header_size:]
    # Render VRAM at 1024x1024 RGBA
    width, height = 1024, 1024
    arr = np.frombuffer(vram[:width*height*4], dtype=np.uint8).reshape(height, width, 4)
    img = Image.fromarray(arr[:,:,:3], 'RGB')
    img.save(f'{output_dir}/vram_correct_1024x1024.png')
    print(f"Saved vram_correct_1024x1024.png")

    # Also try 64x32 blocks (PS2 VRAM layout for 32bpp)
    # Save as-is for now, we can reinterpret later

print("\n=== Done ===")
