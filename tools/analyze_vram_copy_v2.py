#!/usr/bin/env python3
"""
Analyze the local-to-local VRAM copy: SBP=0x1800 -> DBP=0x3000
Uses the correct PS2 GS deswizzle from psmt4_deswizzle.py / deswizzle_gs_vram.py
"""

import os
import sys
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from deswizzle_gs_vram import (
    extract_gs_vram,
    read_psmct32_from_vram,
    read_psmt4_from_vram,
    save_psmct32_rgba,
    save_grayscale_psmt4,
)

from PIL import Image
import struct

OUT_DIR = os.path.join(BASE, "dumps", "vram_copy_analysis")

# VRAM copy parameters
SBP = 0x1800
DBP = 0x3000
BLOCK_COUNT = 0x380
BYTES_PER_BLOCK = 256
COPY_SIZE = BLOCK_COUNT * BYTES_PER_BLOCK


def analyze_state(p2s_path, name):
    print(f"\n{'='*70}")
    print(f"Analyzing: {name}")
    print(f"{'='*70}")

    vram = extract_gs_vram(p2s_path)

    # Step 1: Raw byte comparison
    src_off = SBP * BYTES_PER_BLOCK
    dst_off = DBP * BYTES_PER_BLOCK
    src_raw = vram[src_off:src_off + COPY_SIZE]
    dst_raw = vram[dst_off:dst_off + COPY_SIZE]

    if src_raw == dst_raw:
        print(f"\n  RAW COMPARISON: SRC and DST are IDENTICAL ({len(src_raw)} bytes)")
    else:
        diff = sum(1 for a, b in zip(src_raw, dst_raw) if a != b)
        print(f"\n  RAW COMPARISON: DIFFER in {diff}/{len(src_raw)} bytes ({100*diff/len(src_raw):.1f}%)")

    # Step 2: Render SBP=0x1800 as PSMCT32 framebuffer
    # If this is framebuffer data, the game's framebuffer setup determines width.
    # Standard PS2 NTSC: 640x448 or 512x448
    # FBP=0x1800 suggests this is a second framebuffer (double buffering)
    # FBW=10 for 640-wide, FBW=8 for 512-wide

    # Try 640 wide (tbw=10)
    for tbw, label in [(10, "640"), (8, "512")]:
        fw = tbw * 64
        # How many rows can we render with 0x380 blocks?
        # Each page row is tbw pages wide, each page = 32 blocks
        blocks_per_page_row = tbw * 32
        page_rows = BLOCK_COUNT // blocks_per_page_row
        fh = page_rows * 32  # each page row = 32 pixels tall

        if fh == 0:
            continue

        print(f"\n  SBP=0x1800 as PSMCT32 {fw}x{fh} (tbw={tbw})...")
        pixels = read_psmct32_from_vram(vram, SBP, fw, fh, tbw)
        save_psmct32_rgba(pixels, fw, fh,
                          os.path.join(OUT_DIR, f"{name}_src1800_ct32_{label}x{fh}.png"))

    # Step 3: Render DBP=0x3000 as PSMCT32
    for tbw, label in [(8, "512")]:
        fw = tbw * 64
        blocks_per_page_row = tbw * 32
        page_rows = BLOCK_COUNT // blocks_per_page_row
        fh = page_rows * 32

        print(f"\n  DBP=0x3000 as PSMCT32 {fw}x{fh} (tbw={tbw})...")
        pixels = read_psmct32_from_vram(vram, DBP, fw, fh, tbw)
        save_psmct32_rgba(pixels, fw, fh,
                          os.path.join(OUT_DIR, f"{name}_dst3000_ct32_{label}x{fh}.png"))

    # Step 4: Render DBP=0x3000 as PSMT4 (R1272 format: 256x512, tbw=4)
    # R1272 is TBP0=0x3000, PSMT4, 256x512, TBW=4 (bw_psmt4=256)
    print(f"\n  DBP=0x3000 as PSMT4 256x512 (R1272 format)...")
    pixels_psmt4 = read_psmt4_from_vram(vram, DBP, 256, 512, 256)
    save_grayscale_psmt4(pixels_psmt4, 256, 512,
                          os.path.join(OUT_DIR, f"{name}_dst3000_psmt4_256x512.png"))

    # Step 5: Render the MAIN framebuffer for context (FBP=0x0000, FBW=10, 640x448)
    print(f"\n  Main framebuffer at 0x0000 (640x448)...")
    fb_pixels = read_psmct32_from_vram(vram, 0x0000, 640, 448, 10)
    save_psmct32_rgba(fb_pixels, 640, 448,
                      os.path.join(OUT_DIR, f"{name}_fb0_ct32_640x448.png"))

    # Step 6: Also check what's at 0x0C00 (typical second framebuffer for 640x448 double buffering)
    # 640x448 PSMCT32: pages = 10 * 14 = 140 pages = 140*32 = 4480 blocks = 0x1180
    # So second FB at 0x0000 + 0x1180 = 0x1180
    # Or if FB is 640x224 (interlaced): 10*7 = 70 pages = 2240 blocks = 0x8C0
    # 0x1800 - 0x0000 = 0x1800 blocks = 6144 blocks
    # 6144 blocks / (10 pages/row * 32 blocks/page) = 19.2 page rows = not aligned
    # Maybe the second FB starts at 0x0C00? Let's try
    for fb2_start in [0x0C00, 0x1180, 0x1200]:
        fb2_label = f"0x{fb2_start:04X}"
        print(f"\n  Framebuffer at {fb2_label} (640x448)...")
        try:
            fb2 = read_psmct32_from_vram(vram, fb2_start, 640, 448, 10)
            save_psmct32_rgba(fb2, 640, 448,
                              os.path.join(OUT_DIR, f"{name}_fb_{fb2_label}_ct32_640x448.png"))
        except:
            pass

    # Step 7: R1272 font atlas at 0x3000 as PSMT4 with palette
    # Read palette from VRAM if we know where it is
    # R1272 CLUT is typically at a separate TBP0. Let's check common palette locations.
    # For now just save as grayscale indices.

    # Step 8: Also render SBP=0x1800 as PSMT4 to see if that makes sense
    print(f"\n  SBP=0x1800 as PSMT4 256x512...")
    src_psmt4 = read_psmt4_from_vram(vram, SBP, 256, 512, 256)
    save_grayscale_psmt4(src_psmt4, 256, 512,
                          os.path.join(OUT_DIR, f"{name}_src1800_psmt4_256x512.png"))

    # Extract screenshot
    try:
        with zipfile.ZipFile(p2s_path, 'r') as z:
            ss = z.read('Screenshot.png')
            ss_path = os.path.join(OUT_DIR, f"{name}_screenshot.png")
            with open(ss_path, 'wb') as f:
                f.write(ss)
            print(f"\n  Screenshot: {ss_path}")
    except:
        pass

    print(f"\n  Copy block range: SBP=0x{SBP:04X} to SBP+0x{BLOCK_COUNT:04X}=0x{SBP+BLOCK_COUNT:04X}")
    print(f"  Dest block range: DBP=0x{DBP:04X} to DBP+0x{BLOCK_COUNT:04X}=0x{DBP+BLOCK_COUNT:04X}")
    print(f"  R1272 at TBP0=0x3000: 256x512 PSMT4 = 0x100 blocks")
    print(f"  Copy covers 0x{BLOCK_COUNT:X} blocks = {COPY_SIZE} bytes = {COPY_SIZE/65536:.1f}x R1272 size")
    print(f"  Copy covers blocks 0x3000-0x{0x3000+BLOCK_COUNT:04X}, so it covers R1272 AND {BLOCK_COUNT - 0x100} blocks beyond")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    states = [
        (os.path.join(BASE, "RAMdumps", "charscreenv5.p2s"), "charscreenv5"),
        (os.path.join(BASE, "RAMdumps", "fundamental.p2s"), "fundamental"),
    ]

    for path, name in states:
        if os.path.exists(path):
            analyze_state(path, name)


if __name__ == '__main__':
    main()
