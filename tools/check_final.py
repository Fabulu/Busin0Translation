#!/usr/bin/env python3
"""Final check: render linear with proper quality and zoom."""
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
    # R2119 linear at full resolution
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    pixel_count = w * h
    pal_size = 1024

    pixel_data = tex[192:192 + pixel_count]
    pal_data = tex[192 + pixel_count:192 + pixel_count + pal_size]
    palette = unswizzle_clut_psmt8(pal_data)

    img = Image.new('RGBA', (w, h))
    pix_out = [palette[pixel_data[i]] for i in range(pixel_count)]
    img.putdata(pix_out)

    # Save full resolution
    img.save(os.path.join(TEX_DIR, 'R2119_check_full.png'))

    # Zoom 4x a specific area with text
    crop = img.crop((80, 18, 400, 50))
    zoomed = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
    zoomed.save(os.path.join(TEX_DIR, 'R2119_check_zoom.png'))
    print("Saved R2119 zoom")

    # R2118 linear
    data2 = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex2 = data2[16:]
    w2, h2 = 512, 512
    pixel_count2 = w2 * h2

    pixel_data2 = tex2[192:192 + pixel_count2]
    pal_data2 = tex2[192 + pixel_count2:192 + pixel_count2 + pal_size]
    palette2 = unswizzle_clut_psmt8(pal_data2)

    img2 = Image.new('RGBA', (w2, h2))
    pix_out2 = [palette2[pixel_data2[i]] for i in range(pixel_count2)]
    img2.putdata(pix_out2)
    img2.save(os.path.join(TEX_DIR, 'R2118_check_full.png'))

    # Zoom 2x on content area
    crop2 = img2.crop((0, 90, 512, 280))
    zoomed2 = crop2.resize((crop2.width * 2, crop2.height * 2), Image.NEAREST)
    zoomed2.save(os.path.join(TEX_DIR, 'R2118_check_zoom.png'))
    print("Saved R2118 zoom")

    # Also check: are adjacent rows' pixel values consistent?
    # If the image is correct, pixels at the same x should be similar between rows
    print("\nR2119 pixel consistency check:")
    for y in range(24, 30):
        row = pixel_data[y * w:(y + 1) * w]
        # Show pixels at x=200-210
        segment = row[200:210]
        print(f"  Row {y}, x=200..209: {[hex(b) for b in segment]}")

    # Check if there's a clear horizontal shift between even/odd rows
    print("\nR2119 row-pair alignment check:")
    for y in range(24, 30, 2):
        row_even = pixel_data[y * w:(y + 1) * w]
        row_odd = pixel_data[(y+1) * w:(y + 2) * w]

        # Find first significant non-FF pixel in each row
        for x in range(w):
            if row_even[x] < 0xF0:
                print(f"  Row {y} (even): first significant pixel at x={x}, val=0x{row_even[x]:02x}")
                break

        for x in range(w):
            if row_odd[x] < 0xF0:
                print(f"  Row {y+1} (odd): first significant pixel at x={x}, val=0x{row_odd[x]:02x}")
                break


if __name__ == '__main__':
    main()
