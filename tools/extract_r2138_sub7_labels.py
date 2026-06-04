#!/usr/bin/env python3
"""
Extract stat label rectangles from R2138 sub7 atlas.

Deswizzles the PSMT4 256x256 texture, extracts each label by UV coordinates,
saves individual PNGs, and computes byte offsets in the swizzled (disc) data.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4, _psmt4_nibble_addr, _psmct32_word_addr

try:
    from PIL import Image
except ImportError:
    print("ERROR: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
OUT_DIR = os.path.join(BASE, "dumps", "r2138_sub7_labels")

# Sub7 layout in the raw file
SUB7_DATA_OFFSET = 0x075510   # start of sub7 container
SUB7_PIXEL_OFFSET = 0x0755D0  # pixel data within raw file
SUB7_PIXEL_SIZE = 32768       # 256*256/2

# Texture params
TEX_W, TEX_H = 256, 256
BW_PSMT4 = 256
DBW_CT32 = 128

# Labels from GS dump vertex analysis (UV coordinates)
STAT_LABELS = [
    {"name": "HP",    "u1": 192, "v1": 20,  "u2": 256, "v2": 36},
    {"name": "STR",   "u1": 192, "v1": 80,  "u2": 256, "v2": 96},
    {"name": "INT",   "u1": 192, "v1": 100, "u2": 256, "v2": 116},
    {"name": "PIE",   "u1": 192, "v1": 120, "u2": 256, "v2": 136},
    {"name": "VIT",   "u1": 192, "v1": 140, "u2": 256, "v2": 156},
    {"name": "AGI",   "u1": 192, "v1": 160, "u2": 256, "v2": 176},
    {"name": "LCK",   "u1": 192, "v1": 180, "u2": 256, "v2": 196},
]

# Sidebar labels at U=136-184, V=0-80 (48x20 each)
SIDEBAR_LABELS = [
    {"name": "sidebar_1", "u1": 136, "v1": 0,  "u2": 184, "v2": 20},
    {"name": "sidebar_2", "u1": 136, "v1": 20, "u2": 184, "v2": 40},
    {"name": "sidebar_3", "u1": 136, "v1": 40, "u2": 184, "v2": 60},
    {"name": "sidebar_4", "u1": 136, "v1": 60, "u2": 184, "v2": 80},
]

# Mystery label at U=88-128, V=88-112
OTHER_LABELS = [
    {"name": "mystery_88_88", "u1": 88, "v1": 88, "u2": 128, "v2": 112},
]

# Additional labels from the existing label map
EXTRA_LABELS = [
    {"name": "LEVEL",   "u1": 193, "v1": 1,   "u2": 233, "v2": 14},
    {"name": "EXP",     "u1": 193, "v1": 42,  "u2": 217, "v2": 54},
    {"name": "NEXT",    "u1": 193, "v1": 62,  "u2": 225, "v2": 74},
    {"name": "ATK",     "u1": 193, "v1": 200, "u2": 239, "v2": 216},
    {"name": "EVA",     "u1": 194, "v1": 221, "u2": 239, "v2": 236},
    {"name": "DEF",     "u1": 194, "v1": 241, "u2": 239, "v2": 256},
]

ALL_LABELS = STAT_LABELS + SIDEBAR_LABELS + OTHER_LABELS + EXTRA_LABELS


def extract_rect(pixels_lin, x1, y1, x2, y2, tex_w):
    """Extract a rectangle from linear pixel array."""
    w = x2 - x1
    h = y2 - y1
    rect = []
    for y in range(y1, min(y2, TEX_H)):
        for x in range(x1, min(x2, TEX_W)):
            rect.append(pixels_lin[y * tex_w + x])
    return rect, w, h


def make_label_image(pixels, w, h, invert=True):
    """Create a grayscale PNG from pixel data. Invert for visibility."""
    img = Image.new('L', (w, h))
    data = []
    for p in pixels:
        v = p * 17  # 0-15 -> 0-255
        if invert:
            v = 255 - v
        data.append(v)
    img.putdata(data)
    return img


def find_swizzled_byte_offsets(x1, y1, x2, y2):
    """
    For each pixel in the label rectangle, find its byte offset in the
    swizzled (PSMCT32 upload) data. Returns a set of unique byte offsets.

    The swizzled data is organized as PSMCT32 with upload width = DBW_CT32.
    Each PSMCT32 pixel = 4 bytes (32 bits).

    Pipeline: pixel (x,y) in PSMT4 space -> nibble in VRAM -> which PSMCT32
    word wrote that VRAM location -> byte offset in the upload stream.
    """
    # We need to find which bytes in the swizzled stream correspond to
    # each pixel in the deswizzled image. The approach:
    # 1. For each pixel (x,y), compute PSMT4 nibble address in VRAM
    # 2. Convert nibble address to byte address in VRAM
    # 3. Find which PSMCT32 upload word wrote to that VRAM byte

    # Build reverse map: VRAM word -> (upload_x, upload_y)
    upload_w = DBW_CT32
    upload_h = SUB7_PIXEL_SIZE // (upload_w * 4)

    # This is expensive but we only do it once
    vram_to_upload = {}
    for uy in range(upload_h):
        for ux in range(upload_w):
            vram_word = _psmct32_word_addr(ux, uy, upload_w)
            vram_to_upload[vram_word] = (ux, uy)

    offsets = set()
    pixel_map = []  # (px, py) -> upload byte offset

    for py in range(y1, min(y2, TEX_H)):
        for px in range(x1, min(x2, TEX_W)):
            nib_addr = _psmt4_nibble_addr(px, py, BW_PSMT4)
            vram_byte_addr = nib_addr // 2
            # Each PSMCT32 word = 4 bytes, so VRAM word = vram_byte_addr // 4
            vram_word = vram_byte_addr // 4
            byte_within_word = vram_byte_addr % 4

            if vram_word in vram_to_upload:
                ux, uy = vram_to_upload[vram_word]
                upload_byte_offset = (uy * upload_w + ux) * 4 + byte_within_word
                offsets.add(upload_byte_offset)
                pixel_map.append((px, py, upload_byte_offset))

    return offsets, pixel_map


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=== R2138 Sub7 Label Extraction ===\n")

    # Read raw file
    data = open(RAW_PATH, 'rb').read()
    pixel_data = data[SUB7_PIXEL_OFFSET:SUB7_PIXEL_OFFSET + SUB7_PIXEL_SIZE]
    print(f"Raw file: {len(data)} bytes")
    print(f"Pixel data: {len(pixel_data)} bytes from offset 0x{SUB7_PIXEL_OFFSET:x}")

    # Deswizzle
    print(f"Deswizzling {TEX_W}x{TEX_H} PSMT4 (bw={BW_PSMT4}, dbw_ct32={DBW_CT32})...")
    pixels_lin = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                                  bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # Save full deswizzled atlas
    full_img = make_label_image(pixels_lin, TEX_W, TEX_H, invert=True)
    full_path = os.path.join(OUT_DIR, "_full_atlas.png")
    # Scale up 2x for visibility
    full_img_2x = full_img.resize((TEX_W * 2, TEX_H * 2), Image.NEAREST)
    full_img_2x.save(full_path)
    print(f"Saved full atlas: {full_path}")

    # Build reverse VRAM map once (expensive)
    print("\nBuilding VRAM reverse map for swizzle offset calculation...")
    upload_w = DBW_CT32
    upload_h = SUB7_PIXEL_SIZE // (upload_w * 4)
    print(f"Upload dimensions: {upload_w}x{upload_h} PSMCT32 pixels")

    vram_to_upload = {}
    for uy in range(upload_h):
        for ux in range(upload_w):
            vram_word = _psmct32_word_addr(ux, uy, upload_w)
            vram_to_upload[vram_word] = (ux, uy)

    # Process each label
    results = []
    print(f"\n{'='*70}")
    print(f"{'Label':<15} {'UV rect':<25} {'Size':<10} {'Swizzle bytes':<15} {'Disc offset range'}")
    print(f"{'='*70}")

    for label in ALL_LABELS:
        name = label["name"]
        u1, v1, u2, v2 = label["u1"], label["v1"], label["u2"], label["v2"]
        w, h = u2 - u1, v2 - v1

        # Extract pixels
        rect_pixels, rw, rh = extract_rect(pixels_lin, u1, v1, u2, v2, TEX_W)

        # Save individual PNG (4x scale for visibility)
        img = make_label_image(rect_pixels, rw, rh, invert=True)
        img_4x = img.resize((rw * 4, rh * 4), Image.NEAREST)
        png_path = os.path.join(OUT_DIR, f"{name}.png")
        img_4x.save(png_path)

        # Calculate swizzled byte offsets
        swiz_offsets = set()
        for py in range(v1, min(v2, TEX_H)):
            for px in range(u1, min(u2, TEX_W)):
                nib_addr = _psmt4_nibble_addr(px, py, BW_PSMT4)
                vram_byte_addr = nib_addr // 2
                vram_word = vram_byte_addr // 4
                byte_within_word = vram_byte_addr % 4

                if vram_word in vram_to_upload:
                    ux, uy = vram_to_upload[vram_word]
                    upload_byte_offset = (uy * upload_w + ux) * 4 + byte_within_word
                    swiz_offsets.add(upload_byte_offset)

        min_off = min(swiz_offsets) if swiz_offsets else 0
        max_off = max(swiz_offsets) if swiz_offsets else 0

        # Disc offset = SUB7_PIXEL_OFFSET + swizzled byte offset
        disc_min = SUB7_PIXEL_OFFSET + min_off
        disc_max = SUB7_PIXEL_OFFSET + max_off

        # Check if pixels are non-empty (not all background=15)
        non_bg = sum(1 for p in rect_pixels if p != 15)

        result = {
            "name": name,
            "uv": f"({u1},{v1})-({u2},{v2})",
            "size": f"{rw}x{rh}",
            "pixel_count": rw * rh,
            "non_background_pixels": non_bg,
            "swizzled_byte_range": f"0x{min_off:05x}-0x{max_off:05x}",
            "swizzled_byte_count": len(swiz_offsets),
            "disc_offset_range": f"0x{disc_min:06x}-0x{disc_max:06x}",
            "disc_pixel_offset": f"0x{SUB7_PIXEL_OFFSET:06x}",
        }
        results.append(result)

        has_content = "YES" if non_bg > 0 else "empty"
        print(f"{name:<15} ({u1:3d},{v1:3d})-({u2:3d},{v2:3d})  {rw:3d}x{rh:<3d}  {len(swiz_offsets):5d} bytes   0x{disc_min:06x}-0x{disc_max:06x}  [{has_content}]")

    # Save results JSON
    json_path = os.path.join(OUT_DIR, "label_offsets.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved offset data: {json_path}")

    # Detailed per-label swizzled offset breakdown
    print(f"\n{'='*70}")
    print("DETAILED SWIZZLED BYTE RANGES PER LABEL")
    print(f"{'='*70}")
    print(f"(Offsets relative to pixel data start at 0x{SUB7_PIXEL_OFFSET:06x} in raw file)")
    print()

    for label in ALL_LABELS:
        name = label["name"]
        u1, v1, u2, v2 = label["u1"], label["v1"], label["u2"], label["v2"]

        # Collect offsets per row for detailed view
        row_ranges = []
        for py in range(v1, min(v2, TEX_H)):
            row_offsets = set()
            for px in range(u1, min(u2, TEX_W)):
                nib_addr = _psmt4_nibble_addr(px, py, BW_PSMT4)
                vram_byte_addr = nib_addr // 2
                vram_word = vram_byte_addr // 4
                byte_within_word = vram_byte_addr % 4
                if vram_word in vram_to_upload:
                    ux, uy = vram_to_upload[vram_word]
                    upload_byte_offset = (uy * upload_w + ux) * 4 + byte_within_word
                    row_offsets.add(upload_byte_offset)
            if row_offsets:
                row_ranges.append((py, min(row_offsets), max(row_offsets)))

        print(f"{name}:")
        # Group contiguous swizzled ranges
        all_offsets = set()
        for _, rmin, rmax in row_ranges:
            all_offsets.update(range(rmin, rmax + 1))

        if row_ranges:
            # Show first and last row's swizzled ranges
            for py, rmin, rmax in row_ranges[:2]:
                print(f"  row {py:3d}: swiz 0x{rmin:05x}-0x{rmax:05x} (disc 0x{SUB7_PIXEL_OFFSET+rmin:06x}-0x{SUB7_PIXEL_OFFSET+rmax:06x})")
            if len(row_ranges) > 4:
                print(f"  ...")
            for py, rmin, rmax in row_ranges[-2:]:
                print(f"  row {py:3d}: swiz 0x{rmin:05x}-0x{rmax:05x} (disc 0x{SUB7_PIXEL_OFFSET+rmin:06x}-0x{SUB7_PIXEL_OFFSET+rmax:06x})")
        print()

    print("Done! Check dumps/r2138_sub7_labels/ for individual label PNGs.")


if __name__ == "__main__":
    main()
