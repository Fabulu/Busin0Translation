#!/usr/bin/env python3
"""Decode PS2 textures using row-pair byte interleave pattern.

The pixel data is stored with rows interleaved in pairs:
  bytes 0..511: row 0, pixels 0-511
  bytes 512..1023: row 1, pixels 0-511
But within each row, the columns might also be interleaved.

Let me investigate the exact interleave pattern.
"""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def unswizzle_clut_psmt8(palette_data):
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


def decode_interleaved(pixel_data, width, height, palette, name, interleave_fn):
    """Decode with a specific interleave function."""
    img = Image.new('RGBA', (width, height))
    for i in range(width * height):
        if i < len(pixel_data):
            x, y = interleave_fn(i, width, height)
            if 0 <= x < width and 0 <= y < height:
                img.putpixel((x, y), palette[pixel_data[i]])

    out_path = os.path.join(TEX_DIR, name)
    img.save(out_path)
    print(f"Saved: {out_path}")
    return img


def main():
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    header = 192
    pal_size = 1024

    raw = tex[header:header + w * h]
    pal_data = tex[header + w * h:header + w * h + pal_size]
    palette = unswizzle_clut_psmt8(pal_data)

    # The byte_interleave that worked was:
    # pixel_x = (i // 2) % w
    # pixel_y = ((i // 2) // w) * 2 + (i % 2)
    # This maps: byte 0 -> (0,0), byte 1 -> (0,1), byte 2 -> (1,0), byte 3 -> (1,1)
    # So pairs of bytes alternate between even/odd rows

    # But looking at the zoomed image, the text was still slightly distorted
    # Let me try more interleave patterns

    # Pattern 1: byte-level 2-row interleave (as confirmed working)
    def interleave_byte2(i, w, h):
        x = (i // 2) % w
        y = ((i // 2) // w) * 2 + (i % 2)
        return x, y

    decode_interleaved(raw, w, h, palette, 'R2119_byte2.png', interleave_byte2)

    # Pattern 2: 128-byte segment interleave (2 rows per segment pair)
    # Each 128 bytes is a segment. Segments alternate between even/odd rows.
    def interleave_seg128(i, w, h):
        seg_size = 128
        seg_idx = i // seg_size  # Which segment
        pos_in_seg = i % seg_size  # Position within segment

        # Segments within a row pair
        segs_per_row = w // seg_size  # 512/128 = 4
        row_pair = seg_idx // (segs_per_row * 2)
        seg_in_pair = seg_idx % (segs_per_row * 2)

        # Which row in the pair and which column segment
        row_in_pair = seg_in_pair % 2  # 0 or 1
        col_seg = seg_in_pair // 2  # 0..3

        x = col_seg * seg_size + pos_in_seg
        y = row_pair * 2 + row_in_pair
        return x, y

    decode_interleaved(raw, w, h, palette, 'R2119_seg128.png', interleave_seg128)

    # Pattern 3: 64-byte segment interleave
    def interleave_seg64(i, w, h):
        seg_size = 64
        seg_idx = i // seg_size
        pos_in_seg = i % seg_size

        segs_per_row = w // seg_size  # 512/64 = 8
        row_pair = seg_idx // (segs_per_row * 2)
        seg_in_pair = seg_idx % (segs_per_row * 2)

        row_in_pair = seg_in_pair % 2
        col_seg = seg_in_pair // 2

        x = col_seg * seg_size + pos_in_seg
        y = row_pair * 2 + row_in_pair
        return x, y

    decode_interleaved(raw, w, h, palette, 'R2119_seg64.png', interleave_seg64)

    # Pattern 4: 256-byte segment interleave
    def interleave_seg256(i, w, h):
        seg_size = 256
        seg_idx = i // seg_size
        pos_in_seg = i % seg_size

        segs_per_row = w // seg_size  # 512/256 = 2
        row_pair = seg_idx // (segs_per_row * 2)
        seg_in_pair = seg_idx % (segs_per_row * 2)

        row_in_pair = seg_in_pair % 2
        col_seg = seg_in_pair // 2

        x = col_seg * seg_size + pos_in_seg
        y = row_pair * 2 + row_in_pair
        return x, y

    decode_interleaved(raw, w, h, palette, 'R2119_seg256.png', interleave_seg256)

    # Pattern 5: 512-byte segment = full row interleave
    def interleave_row(i, w, h):
        row_idx = i // w
        col = i % w
        # Interleave rows: row 0, row 32, row 1, row 33, row 2, row 34, ...
        # i.e., first 32 rows are even, next 32 are odd
        if row_idx < h // 2:
            y = row_idx * 2
        else:
            y = (row_idx - h // 2) * 2 + 1
        return col, y

    decode_interleaved(raw, w, h, palette, 'R2119_row_interleave.png', interleave_row)

    # Zoom the best candidates
    for name in ['R2119_byte2.png', 'R2119_seg128.png', 'R2119_seg256.png', 'R2119_row_interleave.png']:
        try:
            img = Image.open(os.path.join(TEX_DIR, name))
            crop = img.crop((60, 15, 400, 50))
            zoomed = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
            zoomed.save(os.path.join(TEX_DIR, name.replace('.png', '_zoom.png')))
            print(f"Zoomed: {name}")
        except Exception as e:
            print(f"Error zooming {name}: {e}")


if __name__ == '__main__':
    main()
