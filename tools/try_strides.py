#!/usr/bin/env python3
"""Try different data strides for R2119."""
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


def main():
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]

    # Try rendering with different strides
    # The display is 512x64, but the data might be stored with a wider stride
    # If stride=1024, then every other "row" in our 512-wide view would be
    # from the SECOND half of the wider row

    w_display = 512
    h_display = 64
    header = 192
    pal_size = 1024

    # Available data: 33792 bytes (after header)
    # For 512x64: 32768 pixels + 1024 palette

    # Get palette at end
    pal_data = tex[header + 32768:header + 32768 + pal_size]
    palette = unswizzle_clut_psmt8(pal_data)

    raw_pixels = tex[header:header + 32768]

    # Theory: the data is stored as 1024 pixels wide x 32 rows
    # and the display shows the left 512 pixels of each row
    # plus the right 512 pixels as the next row
    # So display row 0 = data[0..511], display row 1 = data[512..1023] (right half of data row 0)
    # This would mean the data stride is 1024 and height is 32

    for stride in [256, 384, 512, 640, 768, 1024]:
        # Calculate actual height from stride
        actual_h = 32768 // stride
        if actual_h * stride != 32768:
            continue

        # Render with this stride
        img = Image.new('RGBA', (stride, actual_h))
        for y in range(actual_h):
            for x in range(stride):
                off = y * stride + x
                if off < len(raw_pixels):
                    img.putpixel((x, y), palette[raw_pixels[off]])

        out_path = os.path.join(TEX_DIR, f'R2119_stride{stride}x{actual_h}.png')
        img.save(out_path)
        print(f"Saved: {out_path}")

    # Also try: 2-plane interleave where even and odd bytes go to different rows
    # Maybe the data is byte-interleaved: byte 0 -> row 0 px 0, byte 1 -> row 1 px 0
    img_interleave = Image.new('RGBA', (w_display, h_display))
    for i in range(32768):
        # Each pair of bytes: first to even row, second to odd row
        pixel_x = (i // 2) % w_display
        pixel_y = ((i // 2) // w_display) * 2 + (i % 2)
        if pixel_y < h_display:
            img_interleave.putpixel((pixel_x, pixel_y), palette[raw_pixels[i]])

    out_path = os.path.join(TEX_DIR, 'R2119_byte_interleave.png')
    img_interleave.save(out_path)
    print(f"Saved: {out_path}")


if __name__ == '__main__':
    main()
