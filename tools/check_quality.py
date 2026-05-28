#!/usr/bin/env python3
"""Check image quality by zooming in on specific regions."""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def zoom_and_save(img_path, crop_box, zoom, out_path):
    """Crop and zoom an image."""
    img = Image.open(img_path)
    cropped = img.crop(crop_box)
    zoomed = cropped.resize((cropped.width * zoom, cropped.height * zoom), Image.NEAREST)
    zoomed.save(out_path)
    print(f"Saved: {out_path}")


def check_pixel_patterns():
    """Check for specific pixel patterns that indicate swizzle issues."""
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]

    w, h = 512, 64
    pixel_data = tex[192:192 + w * h]

    # Look at adjacent rows to see if there's a horizontal displacement
    for y in range(10, 20):
        row = pixel_data[y * w:(y + 1) * w]
        # Show first 32 pixels as hex
        print(f"Row {y:3d}: {row[:32].hex()}")


def main():
    # Zoom into R2119 noswizzle - look at the text area
    zoom_and_save(
        os.path.join(TEX_DIR, 'R2119_noswizzle.png'),
        (100, 10, 350, 50),  # x1, y1, x2, y2
        4,
        os.path.join(TEX_DIR, 'R2119_zoom_noswizzle.png')
    )

    # Compare with R2119_v0 (block swizzled)
    zoom_and_save(
        os.path.join(TEX_DIR, 'R2119_v0.png'),
        (100, 10, 350, 50),
        4,
        os.path.join(TEX_DIR, 'R2119_zoom_v0.png')
    )

    # Check pixel patterns
    print("\nPixel patterns in R2119:")
    check_pixel_patterns()

    # Also zoom R2118 linear
    zoom_and_save(
        os.path.join(TEX_DIR, 'R2118_tavern_background_linear.png'),
        (0, 100, 512, 300),
        2,
        os.path.join(TEX_DIR, 'R2118_zoom_linear.png')
    )


if __name__ == '__main__':
    main()
