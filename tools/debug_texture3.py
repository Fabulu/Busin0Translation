#!/usr/bin/env python3
"""Try decoding R2119 as raw PSMT8 data starting at various offsets."""
import struct
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def unswizzle_clut_psmt8(palette_data):
    """Unswizzle PS2 CLUT for PSMT8."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            a = min(a * 2, 255)
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))
    unswizzled = list(colors)
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            unswizzled[base + 8 + j], unswizzled[base + 16 + j] = \
                unswizzled[base + 16 + j], unswizzled[base + 8 + j]
    return unswizzled


def try_decode(data, offset, width, height, pal_after_pixels, name, out_suffix):
    """Try decoding PSMT8 from given offset."""
    pixel_count = width * height
    pal_size = 1024

    pixels = data[offset:offset + pixel_count]
    if len(pixels) < pixel_count:
        print(f"  {out_suffix}: Not enough pixels at offset {offset}: {len(pixels)}/{pixel_count}")
        return

    if pal_after_pixels:
        pal_raw = data[offset + pixel_count:offset + pixel_count + pal_size]
    else:
        pal_raw = data[offset - pal_size:offset]

    if len(pal_raw) < pal_size:
        print(f"  {out_suffix}: Not enough palette data")
        return

    palette = unswizzle_clut_psmt8(pal_raw)

    img = Image.new('RGBA', (width, height))
    pix_out = []
    for i in range(pixel_count):
        pix_out.append(palette[pixels[i]])
    img.putdata(pix_out)

    out_path = os.path.join(TEX_DIR, f"{name}_{out_suffix}.png")
    img.save(out_path)
    print(f"  Saved: {out_path}")


def main():
    # ========== R2119 ==========
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]  # skip sub-header

    print(f"R2119: tex = {len(tex)} bytes")
    print(f"TEX0 says: PSMT8 512x64 -> need {512*64} pixels + 1024 palette = {512*64+1024}")

    # The header is 192 bytes (12 QWs of registers + padding)
    # After that: pixel data + palette

    # But wait: QW[7] has data 0x0000000000400200 with reg 0x4c
    # And QW[8] has data 0x0000000000000080 with reg 0x3c
    # These look like: TRXREG-like value 0x00400200 -> width=512(0x200), height=64(0x40)
    # And BITBLTBUF-like 0x80 -> maybe buffer width in 64-pixel units = 128*64 = 8192?

    # Let me check: reg 0x4c = TEXFLUSH, reg 0x3c = MIPTBP2_1
    # Actually these might not be real register writes. Let me re-examine.
    # QW[7]: lo=0x0000000000400200, hi=0x002001000000004c
    # If this is A+D: reg = hi & 0xFF = 0x4c (TEXFLUSH), data = 0x0000000000400200
    # But TEXFLUSH doesn't take data...
    # The hi byte also has 0x00200100 which could be part of a different structure

    # Actually maybe QW[7] and [8] are TRXREG and BITBLTBUF in VIF-wrapped format?

    # Let me check: maybe the register layout is:
    # QW[7]: TRXREG equivalent with width=0x200=512, height=0x40=64
    # QW[8]: Could be PSMT8-specific: buffer width = 0x80 = 128 QWs = 2048 bytes

    # Let me also check if R2119's data after QW[11] (offset 192) is:
    # - Pure pixel data for 512x64 = 32768 bytes
    # - Followed by palette 1024 bytes
    # - Total = 33792
    # - Available = 34800 - 192 = 34608 bytes
    # - Difference = 816 bytes

    # Maybe there's a GIF tag + register writes before the IMAGE data?
    # Or maybe the "header" ends at a different QW

    # Try different pixel data start offsets
    w, h = 512, 64
    pixel_count = w * h  # 32768

    # Option 1: pixels at offset 192, palette at 192+32768=32960
    try_decode(tex, 192, w, h, True, 'R2119', 'off192_palafter')

    # Option 2: palette first at 192, pixels at 192+1024=1216
    try_decode(tex, 1216, w, h, False, 'R2119', 'off1216_palbefore')

    # Option 3: maybe there's a GIF tag at offset 192 (QW[12])
    # The data at QW[12] is all 0xFF - that's actual pixel data (white/FF index)
    # Try pixels starting after some header
    for off in [192, 208, 224, 240, 256, 272, 288]:
        try_decode(tex, off, w, h, True, 'R2119', f'off{off}')

    # Check what's at offset 192+32768 = 32960
    pal_start = 192 + 32768
    print(f"\nData at potential palette start (offset {pal_start}):")
    print(f"  Hex: {tex[pal_start:pal_start+64].hex()}")

    # Also check end of file
    print(f"\nLast 128 bytes of tex:")
    print(f"  {tex[-128:-64].hex()}")
    print(f"  {tex[-64:].hex()}")

    # ========== R2118 ==========
    print("\n" + "="*60)
    data2 = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex2 = data2[16:]
    print(f"R2118: tex = {len(tex2)} bytes")

    # For R2118 we know the IMAGE transfers work.
    # Let's concatenate all IMAGE data properly.
    # IMAGE blocks found: 26 blocks
    # But wait - the gap at QW 5044-5047 contains what looks like pixel data
    # not real GIF tags.

    # Let me concatenate ALL IMAGE data blocks (already found 26 of them)
    # and also include the "gap" data

    # Actually the simplest approach: after the 192-byte header (QW 0-16 = 17 QWs),
    # the rest is all pixel+palette data WITH embedded GIF tags for IMAGE transfers.
    # Each IMAGE transfer has a 16-byte GIF tag followed by data.

    # For R2118: header = 17 QWs = 272 bytes
    # Then interleaved GIF tags and data
    # Total file data after header: 264176 - 272 = 263904 bytes
    # Each IMAGE block has 1 QW (16 byte) GIF tag overhead
    # With 26 IMAGE blocks: 26 * 16 = 416 bytes overhead
    # Plus the "gap" QWs 5044-5046 (3 QWs = 48 bytes)
    # Total overhead: 416 + 48 = 464 bytes
    # Actual data: 263904 - 464 = 263440
    # But we need: 512*512 + 1024 = 263168
    # Difference: 263440 - 263168 = 272 extra bytes... hmm

    # Let me just collect IMAGE data the same way the debug script found it
    image_blocks = []
    i = 17  # skip header
    total_qw = len(tex2) // 16
    while i < total_qw:
        lo = struct.unpack_from('<Q', tex2, i * 16)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3
        eop = (lo >> 15) & 1

        if flg == 2 and nloop > 0:
            data_start = (i + 1) * 16
            data_size = nloop * 16
            # Make sure we don't read past end
            data_size = min(data_size, len(tex2) - data_start)
            if data_size > 0:
                image_blocks.append((data_start, data_size))
            i += 1 + nloop
        else:
            # Check if this could be a valid IMAGE tag at i+1, i+2, i+3
            found = False
            for j in range(i, min(i + 5, total_qw)):
                lo2 = struct.unpack_from('<Q', tex2, j * 16)[0]
                flg2 = (lo2 >> 46) & 3
                nloop2 = lo2 & 0x7FFF
                if flg2 == 2 and nloop2 > 0 and j + 1 + nloop2 <= total_qw + 5:
                    # Found next IMAGE tag - skip to it
                    # But treat the bytes between as raw data too? No, they're GIF headers
                    i = j
                    found = True
                    break
            if not found:
                # Treat remaining as raw data
                remaining = len(tex2) - i * 16
                if remaining > 0:
                    image_blocks.append((i * 16, remaining))
                break

    all_pixel_data = bytearray()
    for offset, size in image_blocks:
        all_pixel_data.extend(tex2[offset:offset + size])

    print(f"Total IMAGE data: {len(all_pixel_data)} bytes")
    print(f"Need: 512*512 + 1024 = {512*512 + 1024}")

    # Split into pixels and palette
    pixel_count = 512 * 512
    pal_size = 1024

    if len(all_pixel_data) >= pixel_count + pal_size:
        pixels = all_pixel_data[:pixel_count]
        pal_raw = all_pixel_data[pixel_count:pixel_count + pal_size]
        palette = unswizzle_clut_psmt8(pal_raw)

        img = Image.new('RGBA', (512, 512))
        pix_out = []
        for idx in pixels:
            pix_out.append(palette[idx])
        img.putdata(pix_out)
        out_path = os.path.join(TEX_DIR, 'R2118_tavern_background.png')
        img.save(out_path)
        print(f"Saved: {out_path}")
    else:
        print(f"Not enough data: have {len(all_pixel_data)}")
        # Try without palette
        if len(all_pixel_data) >= pixel_count:
            pixels = all_pixel_data[:pixel_count]
            palette = [(i, i, i, 255) for i in range(256)]
            img = Image.new('RGBA', (512, 512))
            pix_out = [palette[p] for p in pixels]
            img.putdata(pix_out)
            out_path = os.path.join(TEX_DIR, 'R2118_tavern_background_gray.png')
            img.save(out_path)
            print(f"Saved (grayscale): {out_path}")


if __name__ == '__main__':
    main()
