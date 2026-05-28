#!/usr/bin/env python3
"""Render R1192 TextEventImage data with PS2 PSMT4/PSMT8 deswizzle."""
import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

BASE = 'C:/Programmieren/wizardrytranslation'
OUT = f'{BASE}/dumps/textevent'
os.makedirs(OUT, exist_ok=True)

def deswizzle_psmt4(raw_data, tex_w, tex_h):
    """Deswizzle PSMT4 texture (128x128 page layout)."""
    PAGE_W = 128
    PAGE_H = 128
    PAGE_BYTES = PAGE_W * PAGE_H // 2
    pages_x = tex_w // PAGE_W
    pages_y = tex_h // PAGE_H
    out = bytearray(tex_w * tex_h)
    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * PAGE_BYTES
            for ly in range(PAGE_H):
                for lx in range(PAGE_W):
                    pidx = ly * PAGE_W + lx
                    bi = page_off + pidx // 2
                    np_flag = pidx & 1
                    if bi < len(raw_data):
                        bv = raw_data[bi]
                        pv = (bv & 0x0F) if np_flag == 0 else ((bv >> 4) & 0x0F)
                    else:
                        pv = 0
                    ox = px * PAGE_W + lx
                    oy = py * PAGE_H + ly
                    if ox < tex_w and oy < tex_h:
                        out[oy * tex_w + ox] = pv * 17  # Scale 0-15 to 0-255
    return out

def deswizzle_psmt8(raw_data, tex_w, tex_h):
    """Deswizzle PSMT8 texture (128x64 page layout)."""
    PAGE_W = 128
    PAGE_H = 64
    PAGE_BYTES = PAGE_W * PAGE_H  # 8192
    pages_x = max(1, tex_w // PAGE_W)
    pages_y = max(1, tex_h // PAGE_H)
    out = bytearray(tex_w * tex_h)
    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * PAGE_BYTES
            for ly in range(PAGE_H):
                for lx in range(PAGE_W):
                    bi = page_off + ly * PAGE_W + lx
                    if bi < len(raw_data):
                        pv = raw_data[bi]
                    else:
                        pv = 0
                    ox = px * PAGE_W + lx
                    oy = py * PAGE_H + ly
                    if ox < tex_w and oy < tex_h:
                        out[oy * tex_w + ox] = pv
    return out

for idx in [1192, 2361]:
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type02.raw"
    data = open(rawfile, 'rb').read()
    s2o = struct.unpack_from('<I', data, 24)[0]
    s2t = struct.unpack_from('<I', data, 20)[0]
    s2 = data[s2o:s2o+s2t]
    count = struct.unpack_from('<H', s2, 6)[0]

    print(f"\n=== R{idx}: {count} entries, S2 = {s2t} bytes ===")

    # The GS register entries for R1192:
    # At +0x10: 18 00 00 00 = 0x18 = 24
    # At +0x14: 00 F0 18 00 = texture setup
    # At +0x18: 7C FB 00 00 = VRAM address 0xFB7C
    #
    # The value 0x0018F000 could encode:
    #   Bits [5:0] = 0x00 (SBP low)
    #   Bits [13:6] = 0xC0 -> SBP = 0xC0 * 256 = VRAM page
    #   Bits [19:14] = 0x06 -> SBW = 6 * 64 = 384 pixels wide!
    #   Bits [25:20] = 0x00 -> PSM = PSMCT32

    # Actually, PS2 GS TEX0 register format:
    #   TBP0 [13:0] = texture base pointer (in 256-byte units)
    #   TBW  [19:14] = texture buffer width / 64
    #   PSM  [25:20] = pixel storage mode
    #   TW   [29:26] = texture width (log2)
    #   TH   [33:30] = texture height (log2)

    # But the data at +0x14 is: F0 00 18 00 (reading differently)
    # In raw bytes: 00 F0 18 00
    # This seems like a different format. Let me try different register interpretations.

    # For R2361: 00 30 0B 00 at +0x14
    # 0x000B3000

    # Let me try: the 12-byte entries are actually GIF tag + register data pairs
    # GIF tag format:
    #   NLOOP[14:0], EOP[15], id[30:16], PRE[46], PRIM[57:47], FLG[59:58], NREG[62:60], REGS[127:64]

    # Actually I think the 12-byte entries might be:
    #   u32 NLOOP_etc (GIF tag low 32 bits)
    #   u64 register_data

    # But 12 bytes is too small for a proper GIF tag (16 bytes).
    # These might be custom game engine DMA transfer descriptors.

    # Let me just focus on the data. The high-entropy pixel region:
    # For R1192 it starts at ~0xFC80 (which is the start of actual pixel/texture data)
    # There are about 48KB of pixel data.
    # 48000 bytes / 199 entries = ~241 bytes per entry

    # If 4bpp: 241 bytes = 482 pixels
    # If each entry is a text line that's 384 wide: 482/384 = 1.25 rows... still doesn't fit

    # Wait -- maybe the entries aren't individual textures.
    # Maybe the 199 entries are animation FRAMES, and the actual texture is a single large image
    # that contains all the pre-rendered text lines.

    # The intro narration has about 10-15 lines of text, each fading in/out
    # 199 entries / ~15 lines = ~13 frames per line (for fade animation)

    # So the textures might be:
    # - A set of text-line textures (one per narration line)
    # - The 199 entries are animation frames that reference which texture to display at what time

    # The actual textures are in the pixel data region.
    # For R1192: ~48KB of pixel data
    # If the text is 384 wide, 4bpp: 48000 * 2 / 384 = 250 rows
    # Could be ~15 text lines of 16px height each = 240 rows -- very close!

    # Let's try deswizzled PSMT4 at 384 wide
    # Find the pixel data start
    pixel_start = None
    for i in range(0x100, len(s2) - 64, 16):
        block = s2[i:i+64]
        unique = len(set(block))
        if unique > 40:
            pixel_start = i
            break

    if pixel_start is None:
        pixel_start = 0x100

    pixel_data = s2[pixel_start:]
    print(f"  Pixel data from +{pixel_start:04X}, {len(pixel_data)} bytes")

    # Try PSMT4 deswizzle at various widths
    for tex_w in [128, 256, 384, 512]:
        for tex_h_mult in [1, 2, 4]:
            # Calculate height from data
            bytes_needed_per_row = tex_w // 2  # 4bpp
            raw_height = len(pixel_data) * 2 // tex_w
            # Round to nearest page boundary (128 for PSMT4)
            tex_h = (raw_height // 128) * 128
            if tex_h < 128:
                tex_h = 128
            if tex_h > 2048:
                tex_h = 2048

            pixels = deswizzle_psmt4(pixel_data, tex_w, tex_h)
            img = Image.new('L', (tex_w, tex_h))
            for y in range(tex_h):
                for x in range(tex_w):
                    img.putpixel((x, y), pixels[y * tex_w + x])
            fname = f'{OUT}/R{idx}_psmt4_{tex_w}x{tex_h}.png'
            img.save(fname)
            print(f"  Saved {fname}")
            break  # only one height per width

    # Also try raw (no deswizzle) 4bpp at key widths
    for width in [384, 512, 256]:
        npix = len(pixel_data) * 2
        height = min(npix // width, 1024)
        arr = np.zeros(width * height, dtype=np.uint8)
        for bi in range(min(len(pixel_data), width * height // 2)):
            b = pixel_data[bi]
            arr[bi*2] = (b & 0x0F) * 17
            arr[bi*2+1] = ((b >> 4) & 0x0F) * 17
        arr = arr[:width*height].reshape(height, width)
        # Also try inverted
        img = Image.fromarray(255 - arr, 'L')
        fname = f'{OUT}/R{idx}_4bpp_inv_{width}x{height}.png'
        img.save(fname)
        print(f"  Saved {fname}")

print("\nDone!")
