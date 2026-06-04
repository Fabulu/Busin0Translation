#!/usr/bin/env python3
"""
V2: Try different pixel formats and widths to find embedded fonts in EXE.
Tries: 1bpp, 2bpp, 4bpp (PSMT4 raw), 8bpp (PSMT8 raw)
Widths: 64, 128, 192, 256, 320, 384, 512
Also tries PSMT8 deswizzle.
"""
import os, sys, struct

try:
    from PIL import Image
except ImportError:
    print("ERROR: pip install Pillow"); sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
OUT_DIR = os.path.join(BASE, "dumps", "exe_font_candidates")
os.makedirs(OUT_DIR, exist_ok=True)

def render_1bpp(data, w, out_path):
    """1 bit per pixel bitmap."""
    h = len(data) * 8 // w
    if h < 1: return
    h = min(h, 2048)
    img = Image.new('L', (w, h))
    px = []
    for byte in data[:w*h//8]:
        for bit in range(8):
            px.append(255 if (byte >> (7 - bit)) & 1 else 0)
    img.putdata(px[:w*h])
    img.save(out_path)

def render_2bpp(data, w, out_path):
    """2 bits per pixel."""
    h = len(data) * 4 // w
    if h < 1: return
    h = min(h, 2048)
    img = Image.new('L', (w, h))
    px = []
    for byte in data[:w*h//4]:
        px.append(((byte >> 6) & 3) * 85)
        px.append(((byte >> 4) & 3) * 85)
        px.append(((byte >> 2) & 3) * 85)
        px.append((byte & 3) * 85)
    img.putdata(px[:w*h])
    img.save(out_path)

def render_4bpp(data, w, out_path):
    """4 bits per pixel (PSMT4 linear)."""
    h = len(data) * 2 // w
    if h < 1: return
    h = min(h, 2048)
    img = Image.new('L', (w, h))
    px = []
    for byte in data[:w*h//2]:
        px.append((byte & 0x0F) * 17)
        px.append(((byte >> 4) & 0x0F) * 17)
    img.putdata(px[:w*h])
    img.save(out_path)

def render_8bpp(data, w, out_path):
    """8 bits per pixel."""
    h = len(data) // w
    if h < 1: return
    h = min(h, 2048)
    img = Image.new('L', (w, h))
    img.putdata(list(data[:w*h]))
    img.save(out_path)

def main():
    exe = open(EXE_PATH, 'rb').read()
    print(f"EXE: {len(exe)} bytes")

    # Focus on the most interesting regions identified in v1:
    # 0x3B3000-0x3D7000 (menu structs area, 144KB)
    # 0x3D9000-0x3E1000 (32KB near bitmap)
    # 0x3E6000-0x3FD000 (92KB after bitmap)
    # Also check the large 0x200000 region with different widths

    regions = [
        (0x3B3000, 0x3D7000, "menu_area"),
        (0x3D9000, 0x3E1000, "near_bitmap"),
        (0x3E6000, 0x3FD000, "after_bitmap"),
        (0x3C3000, 0x3C5400, "menu_structs"),   # 56-byte menu records
        (0x3C5400, 0x3D6000, "between_structs_bitmap"),
        (0x200000, 0x210000, "data_start_64K"),
        (0x350000, 0x3B0000, "mid_upper"),
    ]

    widths_4bpp = [128, 192, 256, 320, 384, 512]
    widths_8bpp = [64, 96, 128, 160, 192, 256, 320]
    widths_1bpp = [128, 192, 256, 384, 512]

    for rstart, rend, label in regions:
        rend = min(rend, len(exe))
        if rstart >= len(exe):
            continue
        data = exe[rstart:rend]
        sz = len(data)
        print(f"\n{'='*60}")
        print(f"Region: {label} (0x{rstart:06X}-0x{rend:06X}, {sz//1024}KB)")
        print(f"{'='*60}")

        # 4bpp with various widths
        for w in widths_4bpp:
            p = os.path.join(OUT_DIR, f"v2_{label}_4bpp_w{w}.png")
            render_4bpp(data, w, p)
            print(f"  4bpp w={w}: {p}")

        # 8bpp with various widths
        for w in widths_8bpp:
            p = os.path.join(OUT_DIR, f"v2_{label}_8bpp_w{w}.png")
            render_8bpp(data, w, p)
            print(f"  8bpp w={w}: {p}")

        # 1bpp (monochrome bitmap)
        for w in widths_1bpp:
            p = os.path.join(OUT_DIR, f"v2_{label}_1bpp_w{w}.png")
            render_1bpp(data, w, p)
            print(f"  1bpp w={w}: {p}")

        # 2bpp
        for w in [128, 256]:
            p = os.path.join(OUT_DIR, f"v2_{label}_2bpp_w{w}.png")
            render_2bpp(data, w, p)
            print(f"  2bpp w={w}: {p}")

    # Also: try rendering 0x3C3000 menu struct region as 8bpp with record-aligned width
    # Each record is 56 bytes = could be 56-wide or 28-wide (2 pixels each)
    print(f"\n{'='*60}")
    print("Menu struct special renders")
    print(f"{'='*60}")
    data = exe[0x3C3000:0x3C5400]
    for w in [56, 28, 112]:
        p = os.path.join(OUT_DIR, f"v2_menu_structs_8bpp_w{w}.png")
        render_8bpp(data, w, p)
        p2 = os.path.join(OUT_DIR, f"v2_menu_structs_4bpp_w{w}.png")
        render_4bpp(data, w, p2)

    # Try PSMT8 (8bpp) tables for deswizzle of promising areas
    # PSMT8: 128x64 per page, 16x16 per block
    # Actually let's try a different approach: render the 0x3B3000 area
    # with width = number that aligns to visible glyph patterns

    # Check 0x3B3000 raw at special widths
    data = exe[0x3B3000:0x3D7000]
    for w in [160, 176, 208, 224, 240, 288, 304, 336, 352, 368, 416, 448, 480]:
        p = os.path.join(OUT_DIR, f"v2_menu_area_4bpp_w{w}.png")
        render_4bpp(data, w, p)

    print("\nDone!")

if __name__ == "__main__":
    main()
