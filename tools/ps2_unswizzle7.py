#!/usr/bin/env python3
"""Try page-level row interleave for PSMT8."""
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


def try_interleave(pixel_data, width, height, pattern_name, addr_fn):
    """Try a specific interleave pattern."""
    output = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            src_addr = addr_fn(x, y, width)
            if 0 <= src_addr < len(pixel_data):
                output[y * width + x] = pixel_data[src_addr]
    return bytes(output)


def decode_and_save(pixel_data, pal_data, width, height, out_name, addr_fn=None):
    """Decode and save."""
    palette = unswizzle_clut_psmt8(pal_data)
    pixel_count = width * height

    if addr_fn:
        pixels = try_interleave(pixel_data, width, height, out_name, addr_fn)
    else:
        pixels = pixel_data

    img = Image.new('RGBA', (width, height))
    pix_out = [palette[pixels[i]] for i in range(pixel_count)]
    img.putdata(pix_out)

    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"Saved: {out_path}")
    return img


def main():
    # R2119 first (faster)
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    pixel_count = w * h
    header = 192

    pixel_data = tex[header:header + pixel_count]
    pal_data = tex[header + pixel_count:header + pixel_count + 1024]

    # The pattern: even rows start at x~130, odd rows at x=0
    # This means: the raw data for even rows is stored starting at byte 130
    # within the row, while odd rows start at byte 0.

    # For PSMT8 with 128-pixel pages:
    # Within each page row (128 pixels wide, 64 rows tall),
    # even rows and odd rows interleave differently.

    # Theory: the data is stored in 128-byte segments, and for each pair of rows,
    # the segments are interleaved:
    # Raw bytes: [row0_seg0(128B)] [row1_seg0(128B)] [row0_seg1(128B)] [row1_seg1(128B)] ...

    # This would explain why even rows see data starting at x=128 - because
    # row1_seg0 comes before row0_seg1 in the byte stream.

    # For a 512-pixel wide image with 128-pixel segments:
    # Each row = 4 segments of 128 bytes
    # Stored as: row0_s0 row1_s0 row0_s1 row1_s1 row0_s2 row1_s2 row0_s3 row1_s3
    # Total for 2 rows = 8 * 128 = 1024 bytes

    # With 512 bytes per row, 2 rows = 1024 bytes either way.
    # But the interleaving means:
    # Byte 0..127: row 0, pixels 0..127
    # Byte 128..255: row 1, pixels 0..127
    # Byte 256..383: row 0, pixels 128..255
    # Byte 384..511: row 1, pixels 128..255
    # etc.

    def addr_2row_interleave(x, y, width):
        """2-row interleaved 128-byte segments."""
        seg = x // 128  # Which 128-pixel segment
        pos = x % 128   # Position within segment
        row_pair = y // 2
        row_in_pair = y % 2

        # Each row pair has segments interleaved:
        # seg0_row0 seg0_row1 seg1_row0 seg1_row1 ...
        n_segs = width // 128

        # Base offset for this row pair
        pair_base = row_pair * width * 2  # 2 rows of width bytes

        # Offset within the pair
        seg_offset = seg * 128 * 2 + row_in_pair * 128 + pos

        return pair_base + seg_offset

    decode_and_save(pixel_data, pal_data, w, h,
                    'R2119_2row_interleave.png', addr_2row_interleave)

    # Try 4-row interleave (within a column of 4 rows)
    def addr_4row_interleave(x, y, width):
        """4-row interleaved 128-byte segments."""
        seg = x // 128
        pos = x % 128
        row_group = y // 4
        row_in_group = y % 4

        n_segs = width // 128
        group_base = row_group * width * 4

        # Within group: seg0_row0 seg0_row1 seg0_row2 seg0_row3 seg1_row0 ...
        seg_offset = seg * 128 * 4 + row_in_group * 128 + pos

        return group_base + seg_offset

    decode_and_save(pixel_data, pal_data, w, h,
                    'R2119_4row_interleave.png', addr_4row_interleave)

    # Try: even rows read from offset, odd rows normal
    def addr_shift128_even(x, y, width):
        """Shift even rows by 128 pixels."""
        if y % 2 == 0:
            actual_x = (x + 128) % width
        else:
            actual_x = x
        return y * width + actual_x

    decode_and_save(pixel_data, pal_data, w, h,
                    'R2119_shift128_even.png', addr_shift128_even)

    # The data shows even rows start at ~130-131, not exactly 128
    # Maybe the offset is 130 or 132?
    for shift in [128, 130, 131, 132]:
        def make_shift_fn(s):
            def addr_fn(x, y, width):
                if y % 2 == 0:
                    return y * width + (x + s) % width
                return y * width + x
            return addr_fn

        decode_and_save(pixel_data, pal_data, w, h,
                        f'R2119_shift{shift}.png', make_shift_fn(shift))


if __name__ == '__main__':
    main()
