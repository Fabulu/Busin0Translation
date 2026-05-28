#!/usr/bin/env python3
"""Render text textures from EE RAM intro savestate using PSMT4/PSMT8 deswizzle."""
import zipfile, struct, sys, os
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation'
OUT = f'{BASE}/dumps/textevent'

z = zipfile.ZipFile(f'{BASE}/RAMdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

def psmt4_deswizzle(raw_data, tex_w, tex_h):
    """PSMT4 deswizzle: pages 128x128, linear within pages."""
    PAGE_W = 128
    PAGE_H = 128
    pages_x = max(1, tex_w // PAGE_W)
    pages_y = max(1, tex_h // PAGE_H)
    page_size = (PAGE_W * PAGE_H) // 2  # 8192 bytes

    out = np.zeros((tex_h, tex_w), dtype=np.uint8)

    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * page_size

            for y in range(PAGE_H):
                for x in range(PAGE_W):
                    pidx = y * PAGE_W + x
                    bi = page_off + pidx // 2
                    nib = pidx & 1

                    if bi < len(raw_data):
                        bv = raw_data[bi]
                        pv = (bv & 0x0F) if nib == 0 else ((bv >> 4) & 0x0F)
                    else:
                        pv = 0

                    ox = px * PAGE_W + x
                    oy = py * PAGE_H + y
                    if ox < tex_w and oy < tex_h:
                        out[oy, ox] = pv * 17

    return out


def psmt8_deswizzle(raw_data, tex_w, tex_h):
    """PSMT8 deswizzle: pages 128x64, linear within pages."""
    PAGE_W = 128
    PAGE_H = 64
    pages_x = max(1, tex_w // PAGE_W)
    pages_y = max(1, tex_h // PAGE_H)
    page_size = PAGE_W * PAGE_H  # 8192 bytes

    out = np.zeros((tex_h, tex_w), dtype=np.uint8)

    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * page_size

            for y in range(PAGE_H):
                for x in range(PAGE_W):
                    bi = page_off + y * PAGE_W + x

                    if bi < len(raw_data):
                        pv = raw_data[bi]
                    else:
                        pv = 0

                    ox = px * PAGE_W + x
                    oy = py * PAGE_H + y
                    if ox < tex_w and oy < tex_h:
                        out[oy, ox] = pv

    return out


# Regions in EE RAM where text textures live
regions = [
    ('E30000', 0x00E30000, 0x20000),
    ('E40000', 0x00E40000, 0x10000),
    ('E50000', 0x00E50000, 0x10000),
    ('E60000', 0x00E60000, 0x10000),
]

for name, start, size in regions:
    region = ram[start:start+size]
    nonzero = sum(1 for b in region if b != 0)
    if nonzero < 50:
        continue
    print(f'\n=== {name}: {nonzero}/{size} nonzero ===')

    # Try PSMT4 deswizzle at various widths
    for tex_w in [256, 384, 512, 128]:
        npix = size * 2  # 4bpp: 2 pixels per byte
        tex_h = npix // tex_w
        # Ensure multiple of page height (128)
        tex_h = min(tex_h, (tex_h // 128) * 128)
        if tex_h < 128:
            tex_h = 128
        if tex_h > 2048:
            tex_h = 2048

        pixels = psmt4_deswizzle(region, tex_w, tex_h)
        img = Image.fromarray(255 - pixels, 'L')
        fname = f'{OUT}/ram_{name}_psmt4_{tex_w}x{tex_h}.png'
        img.save(fname)
        print(f'  PSMT4 {tex_w}x{tex_h}')

    # Try PSMT8 deswizzle
    for tex_w in [256, 384, 512, 128]:
        tex_h = size // tex_w
        tex_h = min(tex_h, (tex_h // 64) * 64)
        if tex_h < 64:
            tex_h = 64
        if tex_h > 2048:
            tex_h = 2048

        pixels = psmt8_deswizzle(region, tex_w, tex_h)
        img = Image.fromarray(255 - pixels, 'L')
        fname = f'{OUT}/ram_{name}_psmt8_{tex_w}x{tex_h}.png'
        img.save(fname)
        print(f'  PSMT8 {tex_w}x{tex_h}')

# Also look at the framebuffer region to find the rendered text
# The PS2 framebuffer is typically at VRAM address 0
# In EE RAM, the DMA chain would upload the text to VRAM
# Let's search a wider area for text-like bitmaps

print('\n=== Broader RAM scan for text texture bitmaps ===')
candidates = []
for addr in range(0x00C00000, 0x01800000, 0x1000):
    region = ram[addr:addr+0x1000]
    nonzero = sum(1 for b in region if b != 0)
    ratio = nonzero / len(region)
    if 0.01 < ratio < 0.35:
        unique = len(set(region))
        if unique < 80:
            candidates.append((addr, nonzero, unique))

print(f'Found {len(candidates)} candidate 4KB blocks')
# Group consecutive candidates
groups = []
current_group = None
for addr, nz, uniq in candidates:
    if current_group is None or addr > current_group[1] + 0x2000:
        if current_group:
            groups.append(current_group)
        current_group = [addr, addr + 0x1000, [(addr, nz, uniq)]]
    else:
        current_group[1] = addr + 0x1000
        current_group[2].append((addr, nz, uniq))
if current_group:
    groups.append(current_group)

print(f'Grouped into {len(groups)} regions:')
for g in groups:
    start, end, blocks = g
    total_nz = sum(b[1] for b in blocks)
    region_size = end - start
    print(f'  0x{start:08X}-0x{end:08X}: {region_size} bytes, {total_nz} nonzero ({total_nz/region_size:.1%})')

    # Render the top 3 largest regions
    if region_size >= 0x4000:
        region = ram[start:end]
        for width in [384, 512, 256]:
            height = region_size // width
            if height > 2048: height = 2048
            arr = np.frombuffer(region[:width*height], dtype=np.uint8).reshape(height, width)
            img = Image.fromarray(255 - arr, 'L')
            fname = f'{OUT}/scan_{start:08X}_{width}x{height}.png'
            img.save(fname)
            # Only save one per region
            break

print('\nDone')
