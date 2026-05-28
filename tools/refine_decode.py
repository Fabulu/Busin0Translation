#!/usr/bin/env python3
"""Refine the byte-interleave decode for PS2 PSMT8 textures."""
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


def try_pattern(raw, w, h, palette, name, fn):
    """Try a specific deswizzle pattern function.

    fn(src_idx, w, h) -> (dst_x, dst_y) for each source byte index.
    """
    img = Image.new('RGBA', (w, h))
    pixels = [(0, 0, 0, 0)] * (w * h)
    for i in range(min(len(raw), w * h)):
        x, y = fn(i, w, h)
        if 0 <= x < w and 0 <= y < h:
            pixels[y * w + x] = palette[raw[i]]
    img.putdata(pixels)
    out_path = os.path.join(TEX_DIR, name)
    img.save(out_path)

    # Save zoomed
    crop = img.crop((60, 15, 400, 50))
    zoomed = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
    zoomed.save(out_path.replace('.png', '_zoom.png'))
    print(f"Saved: {name}")


def main():
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    header = 192

    raw = tex[header:header + w * h]
    pal_data = tex[header + w * h:header + w * h + 1024]
    palette = unswizzle_clut_psmt8(pal_data)

    # The byte2 interleave was close. Let me refine.
    # The stippled effect suggests within each column, pixels alternate
    # between two different patterns.

    # PSMT8 GS column: 16 pixels wide, 2 pixels tall
    # Within a column (32 bytes), the bytes map to:
    # Row 0: bytes 0,2,4,...,30 -> pixels 0,1,2,...,15
    # Row 1: bytes 1,3,5,...,31 -> pixels 0,1,2,...,15
    #
    # But then the columns are 2 rows tall. For 64 rows, there are 32 column pairs.
    # And within each page (128x64), columns are arranged differently.

    # Let me try: the PCSX2 column table applied AFTER the byte2 interleave
    # No wait, let me just try the simplest fix first:
    # The byte2 interleave but with the x-coordinate column table

    # Pattern A: byte-pair interleave with 32-byte column width
    # Every 32 bytes forms a 16x2 column
    def pattern_col32(i, w, h):
        # 32-byte columns: 16 pixels wide x 2 rows
        col_size = 32  # 16 px * 2 rows
        col_idx = i // col_size
        pos_in_col = i % col_size

        # Within column: even bytes = row 0, odd bytes = row 1
        px = pos_in_col // 2  # 0..15
        py_in_col = pos_in_col % 2  # 0 or 1

        # Column position on screen
        cols_per_row = w // 16  # 512/16 = 32
        col_row = col_idx // cols_per_row
        col_col = col_idx % cols_per_row

        x = col_col * 16 + px
        y = col_row * 2 + py_in_col
        return x, y

    try_pattern(raw, w, h, palette, 'R2119_col32.png', pattern_col32)

    # Pattern B: 64-byte columns (16x4)
    def pattern_col64(i, w, h):
        col_size = 64  # 16 px * 4 rows
        col_idx = i // col_size
        pos_in_col = i % col_size

        # Within 16x4 column:
        # Maybe: every 4 consecutive bytes -> same x, rows 0-3?
        # Or: alternating bytes between 4 rows?

        # Try: 16 bytes per row within column, 4 rows
        px = pos_in_col % 16
        py_in_col = pos_in_col // 16  # 0..3

        cols_per_row = w // 16
        col_row = col_idx // cols_per_row
        col_col = col_idx % cols_per_row

        x = col_col * 16 + px
        y = col_row * 4 + py_in_col
        return x, y

    try_pattern(raw, w, h, palette, 'R2119_col64.png', pattern_col64)

    # Pattern C: 64-byte columns but with 2-row interleave within
    def pattern_col64_interlv(i, w, h):
        col_size = 64
        col_idx = i // col_size
        pos_in_col = i % col_size

        # Within column: bytes alternate between 2 sub-rows
        # bytes 0,1 -> row 0 pixels 0,1
        # bytes 2,3 -> row 1 pixels 0,1
        # bytes 4,5 -> row 0 pixels 2,3
        # etc.

        pair_in_col = pos_in_col // 2
        byte_in_pair = pos_in_col % 2

        # pair_in_col: 0..31
        # Each pair contributes 1 pixel to each of 2 rows
        # Row: even pair -> rows 0,1; odd pair -> rows 2,3?

        # Actually for 16x4:
        # 32 pairs for 16 columns x 2 row-groups
        # pair 0..15: row group 0 (rows 0-1)
        # pair 16..31: row group 1 (rows 2-3)

        row_group = pair_in_col // 16  # 0 or 1
        col_in_group = pair_in_col % 16  # 0..15

        px = col_in_group
        py_in_col = row_group * 2 + byte_in_pair

        cols_per_row = w // 16
        col_row = col_idx // cols_per_row
        col_col = col_idx % cols_per_row

        x = col_col * 16 + px
        y = col_row * 4 + py_in_col
        return x, y

    try_pattern(raw, w, h, palette, 'R2119_col64i.png', pattern_col64_interlv)

    # Pattern D: just swap even/odd pixels within each 32-byte segment
    # on top of the byte2 interleave
    def pattern_byte2_swap4(i, w, h):
        # First apply byte2 interleave
        linear_idx = i // 2
        row_in_pair = i % 2

        x = linear_idx % w
        y_pair = linear_idx // w
        y = y_pair * 2 + row_in_pair

        # Then swap within 4-pixel groups on certain rows
        # if y % 2 == 1:
        #     x = (x ^ 2)  # Swap pairs

        return x, y

    # Actually let's try: for even src bytes, pixels go at x*2
    # for odd src bytes, pixels go at x*2+1
    # This would mean the horizontal resolution is halved

    # Let me think about this differently based on the observed data:
    # R2119 row 24 (even): first_non_ff=131
    # R2119 row 25 (odd): first_non_ff=0
    # Difference: 131 pixels

    # With byte2 interleave: byte 0 -> (0,0), byte 1 -> (0,1)
    # byte 2 -> (1,0), byte 3 -> (1,1)
    # So in the raw data, bytes at even positions go to even rows, odd to odd
    # Raw byte 0 (0xFF) -> (0, 0)
    # Raw byte 1 (0xFF) -> (0, 1)
    # ...
    # Raw byte 2*131 = 262 -> (131, 0) - first non-FF in even row!
    # Raw byte 262 is at offset 192+262 = 454 in tex

    # Check: what value is at raw byte 262?
    print(f"\nDiagnostic:")
    print(f"  Raw byte 262 = 0x{raw[262]:02x}")
    print(f"  Raw byte 263 = 0x{raw[263]:02x}")
    print(f"  Raw byte 0 = 0x{raw[0]:02x}")
    print(f"  Raw byte 1 = 0x{raw[1]:02x}")

    # With byte2: raw[262] goes to pixel (131, 0) and raw[263] goes to (131, 1)
    # But in the linear layout, raw[131] goes to (131, 0) and raw[512+131] = raw[643] goes to (131, 1)

    # Let me check: does the byte2 interleave actually match the observed data?
    # In linear: row 0 = raw[0..511], row 1 = raw[512..1023]
    # Non-FF starts at: row 0 x=131 -> raw[131], row 1 x=0 -> raw[512]
    # But wait, in the linear decode, the issue was that content on even rows
    # starts at ~131 and on odd rows at 0.

    # If the data were byte-interleaved:
    # Even row data: raw[0,2,4,6,...] = raw[0], raw[2], raw[4], ...
    # Odd row data: raw[1,3,5,7,...] = raw[1], raw[3], raw[5], ...
    # Even row pixel 0 = raw[0] = 0xFF
    # Even row pixel 131 = raw[262] - is this non-FF?
    print(f"  Even row (from raw[even]): pixel 131 = raw[262] = 0x{raw[262]:02x}")
    print(f"  Odd row (from raw[odd]): pixel 0 = raw[1] = 0x{raw[1]:02x}")

    # Both are 0xFF. So the byte2 interleave doesn't match the observed pattern.
    # The content starts at raw byte ~131 for the linear even rows
    # and at raw byte ~512 for the linear odd rows.

    # Let me look at this from the data side:
    # Where does the first non-FF byte appear?
    for idx in range(len(raw)):
        if raw[idx] != 0xFF:
            print(f"  First non-FF: raw[{idx}] = 0x{raw[idx]:02x}")
            break

    # And the distribution of non-FF in the first 2048 bytes
    chunks = []
    for start in range(0, min(2048, len(raw)), 128):
        non_ff = sum(1 for b in raw[start:start+128] if b != 0xFF)
        if non_ff > 0:
            chunks.append((start, non_ff))
    print(f"  Non-FF distribution (first 2048 bytes):")
    for start, count in chunks:
        print(f"    offset {start}-{start+127}: {count} non-FF bytes")


if __name__ == '__main__':
    main()
