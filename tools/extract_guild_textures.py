#!/usr/bin/env python3
"""Extract R2121 (guild background) and R2122 (guild buttons) CockpitImg textures as PNG.

These PS2 CockpitImg resources contain pre-rendered Japanese text for the guild/character
creation screen. The format is:
  - 16-byte sub-header (type, payload_size, offset, pad)
  - GS packet: first GIF tag sets TEX0 (PSMT8 format, dimensions)
  - Then pixel data + palette data

PSMT8 layout:
  - Pixel data: width * height bytes (8bpp indexed)
  - Palette: 256 * 4 bytes RGBA (PS2 CLUT with groups of 32 swizzled)
  - PS2 GS stores PSMT8 in 128x64 pixel pages (8192 bytes each)
  - Within each page, data is stored in 16x4 pixel columns/blocks
"""
import struct
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def unswizzle_clut_psmt8(palette_data):
    """Unswizzle PS2 CLUT for PSMT8 (256 colors).
    Within each group of 32 palette entries, entries 8-15 and 16-23 are swapped."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r = palette_data[off]
            g = palette_data[off + 1]
            b = palette_data[off + 2]
            a = palette_data[off + 3]
            a = min(a * 2, 255)  # PS2 alpha 0-128 -> 0-255
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


# PS2 PSMT8 column/block table
# PSMT8 stores data in 16x4 columns within 128x64 pages
# The column arrangement within a page follows the standard GS block layout

# Standard PSMT8 block table (maps linear block index -> (x, y) position in page)
# PSMT8 page: 128x64 pixels, 8 blocks wide (16px each) x 16 blocks tall (4px each) = 128 blocks
# Block order within a page:
PSMT8_BLOCK_TABLE = [
    (0,0), (1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0),   # row 0
    (0,1), (1,1), (2,1), (3,1), (4,1), (5,1), (6,1), (7,1),   # row 1
    (0,2), (1,2), (2,2), (3,2), (4,2), (5,2), (6,2), (7,2),
    (0,3), (1,3), (2,3), (3,3), (4,3), (5,3), (6,3), (7,3),
    (0,4), (1,4), (2,4), (3,4), (4,4), (5,4), (6,4), (7,4),
    (0,5), (1,5), (2,5), (3,5), (4,5), (5,5), (6,5), (7,5),
    (0,6), (1,6), (2,6), (3,6), (4,6), (5,6), (6,6), (7,6),
    (0,7), (1,7), (2,7), (3,7), (4,7), (5,7), (6,7), (7,7),
    (0,8), (1,8), (2,8), (3,8), (4,8), (5,8), (6,8), (7,8),
    (0,9), (1,9), (2,9), (3,9), (4,9), (5,9), (6,9), (7,9),
    (0,10),(1,10),(2,10),(3,10),(4,10),(5,10),(6,10),(7,10),
    (0,11),(1,11),(2,11),(3,11),(4,11),(5,11),(6,11),(7,11),
    (0,12),(1,12),(2,12),(3,12),(4,12),(5,12),(6,12),(7,12),
    (0,13),(1,13),(2,13),(3,13),(4,13),(5,13),(6,13),(7,13),
    (0,14),(1,14),(2,14),(3,14),(4,14),(5,14),(6,14),(7,14),
    (0,15),(1,15),(2,15),(3,15),(4,15),(5,15),(6,15),(7,15),
]


def deswizzle_psmt8_pages(raw_data, tex_w, tex_h):
    """Deswizzle PSMT8 texture using page layout (128x64 pages, linear within pages)."""
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
                    src_idx = page_off + ly * PAGE_W + lx
                    if src_idx < len(raw_data):
                        val = raw_data[src_idx]
                    else:
                        val = 0

                    ox = px * PAGE_W + lx
                    oy = py * PAGE_H + ly
                    if ox < tex_w and oy < tex_h:
                        out[oy * tex_w + ox] = val

    return bytes(out)


def parse_initial_tex0(tex):
    """Parse TEX0 from the first PACKED GIF tag."""
    lo = struct.unpack_from('<Q', tex, 0)[0]
    nloop = lo & 0x7FFF
    flg = (lo >> 46) & 3
    nreg = (lo >> 60) & 0xF
    if nreg == 0:
        nreg = 16

    if flg != 0 or nloop < 1:
        return None

    info = {}
    for i in range(nloop * nreg):
        qw_idx = 1 + i
        d_lo = struct.unpack_from('<Q', tex, qw_idx * 16)[0]
        d_hi = struct.unpack_from('<Q', tex, qw_idx * 16 + 8)[0]
        reg = d_hi & 0xFF

        if reg == 0x06:  # TEX0_1
            psm = (d_lo >> 20) & 0x3F
            tw = (d_lo >> 26) & 0xF
            th = (d_lo >> 30) & 0xF
            tbw = (d_lo >> 14) & 0x3F
            cbp = (d_lo >> 37) & 0x3FFF
            info['psm'] = psm
            info['tex_w'] = 1 << tw
            info['tex_h'] = 1 << th
            info['tbw'] = tbw
            info['cbp'] = cbp
            print(f"  TEX0: PSM=0x{psm:02x} {1 << tw}x{1 << th} TBW={tbw} CBP={cbp}")

    info['data_start'] = (1 + nloop * nreg) * 16
    return info


def decode_resource(filename):
    """Decode a CockpitImg resource to PNG."""
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    print(f"\n{'=' * 60}")
    print(f"Processing: {filename} ({len(data)} bytes)")
    print(f"{'=' * 60}")

    sub_hdr = struct.unpack_from('<IIII', data, 0)
    print(f"Sub-header: payload={sub_hdr[1]}")

    tex = data[16:]
    info = parse_initial_tex0(tex)
    if not info:
        print("ERROR: Could not parse TEX0")
        return

    psm = info['psm']
    width = info['tex_w']
    height = info['tex_h']
    data_start = info['data_start']

    if psm != 0x13:
        print(f"ERROR: Expected PSMT8 (0x13), got 0x{psm:02x}")
        return

    pixel_count = width * height
    pal_size = 256 * 4  # 1024 bytes
    raw = tex[data_start:]

    print(f"  {width}x{height} PSMT8, pixel data at offset {data_start}")
    print(f"  Available: {len(raw)} bytes, need: {pixel_count + pal_size}")

    # The raw data after the GIF tag setup might have additional GIF tags
    # or it might be directly pixel data. Let's check.

    # Check if the next 16 bytes look like a GIF tag or raw pixel data
    lo_next = struct.unpack_from('<Q', raw, 0)[0]
    flg_next = (lo_next >> 46) & 3
    nloop_next = lo_next & 0x7FFF
    nreg_next = (lo_next >> 60) & 0xF
    if nreg_next == 0:
        nreg_next = 16

    skip = 0
    if flg_next == 2 and nloop_next > 0 and nloop_next * 16 < len(raw):
        # IMAGE GIF tag found
        print(f"  IMAGE GIF tag: nloop={nloop_next}, data_size={nloop_next * 16}")
        # Collect all IMAGE transfers
        pixel_data = bytearray()
        pos = 0
        while pos < len(raw):
            lo_gif = struct.unpack_from('<Q', raw, pos)[0]
            flg_gif = (lo_gif >> 46) & 3
            nloop_gif = lo_gif & 0x7FFF

            if flg_gif == 2 and nloop_gif > 0:
                img_start = pos + 16
                img_size = nloop_gif * 16
                pixel_data.extend(raw[img_start:img_start + img_size])
                pos = img_start + img_size
            elif flg_gif == 0:
                nreg_gif = (lo_gif >> 60) & 0xF
                if nreg_gif == 0:
                    nreg_gif = 16
                ad_count = nloop_gif * nreg_gif
                pos += (1 + ad_count) * 16
            else:
                pos += 16

        raw = bytes(pixel_data)
        print(f"  Collected {len(raw)} bytes from IMAGE transfers")
    elif flg_next == 0 and nloop_next > 100:
        # Large PACKED block - might be wrapping pixel data as A+D writes
        # Or it could be misinterpreted pixel data
        # Check: would this PACKED block extend past the data?
        total_qw = nloop_next * nreg_next
        if (1 + total_qw) * 16 > len(raw):
            # Too large - this is probably raw pixel data being misinterpreted
            print(f"  First QW looks like pixel data (PACKED nloop={nloop_next} too large)")
            # Use raw data as-is
        else:
            # Skip this PACKED block
            skip = (1 + total_qw) * 16
            print(f"  Skipping PACKED block ({skip} bytes)")
            raw = raw[skip:]

    # Now raw should be pixel data followed by palette
    # Try layout: pixels (pixel_count bytes) then palette (1024 bytes)
    if len(raw) < pixel_count + pal_size:
        print(f"  WARNING: not enough data ({len(raw)} < {pixel_count + pal_size})")
        # Try with whatever we have
        if len(raw) < pixel_count:
            # Pad pixel data
            raw = raw + b'\x00' * (pixel_count + pal_size - len(raw))

    pixel_bytes = raw[:pixel_count]
    pal_bytes = raw[pixel_count:pixel_count + pal_size]

    # Decode palette with CLUT unswizzle
    palette_swiz = unswizzle_clut_psmt8(pal_bytes)
    # Also keep linear palette for comparison
    palette_lin = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(pal_bytes):
            r, g, b, a = pal_bytes[off], pal_bytes[off + 1], pal_bytes[off + 2], pal_bytes[off + 3]
            palette_lin.append((r, g, b, min(a * 2, 255)))
        else:
            palette_lin.append((0, 0, 0, 0))

    # Decode pixel data with different swizzle options
    px_linear = pixel_bytes
    px_pages = deswizzle_psmt8_pages(pixel_bytes, width, height)

    # Generate output images with different combinations
    results = []
    for px_label, px_data in [('linear', px_linear), ('pages', px_pages)]:
        for pal_label, palette in [('clutS', palette_swiz), ('clutL', palette_lin)]:
            img = Image.new('RGBA', (width, height))
            pixels_out = []
            for j in range(pixel_count):
                if j < len(px_data):
                    idx = px_data[j]
                    pixels_out.append(palette[idx])
                else:
                    pixels_out.append((0, 0, 0, 0))
            img.putdata(pixels_out)

            out_name = filename.replace('.raw', f'_{px_label}_{pal_label}.png')
            out_path = os.path.join(TEX_DIR, out_name)
            img.save(out_path)
            results.append(out_path)
            print(f"  Saved: {out_path}")

    # Also try: palette at end of file, pixel data right after GIF setup
    end_pal = tex[-(pal_size):]
    palette_end = unswizzle_clut_psmt8(end_pal)
    for px_label, px_data in [('linear', px_linear), ('pages', px_pages)]:
        img = Image.new('RGBA', (width, height))
        pixels_out = []
        for j in range(pixel_count):
            if j < len(px_data):
                idx = px_data[j]
                pixels_out.append(palette_end[idx])
            else:
                pixels_out.append((0, 0, 0, 0))
        img.putdata(pixels_out)

        out_name = filename.replace('.raw', f'_{px_label}_endpal.png')
        out_path = os.path.join(TEX_DIR, out_name)
        img.save(out_path)
        results.append(out_path)
        print(f"  Saved: {out_path}")

    return results


if __name__ == '__main__':
    for f in ['R2121_guild_background.raw', 'R2122_guild_buttons.raw']:
        decode_resource(f)
