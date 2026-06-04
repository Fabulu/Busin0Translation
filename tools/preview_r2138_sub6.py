#!/usr/bin/env python3
"""
Generate preview images for R2138 sub6 (guild roster) — both PATCHED and ORIGINAL.
Compares banner region to check for clear zone artifacts and residual JP strokes.
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image

DUMP_DIR = os.path.join(BASE, "dumps")
os.makedirs(DUMP_DIR, exist_ok=True)

# Sub6 parameters (from patch_r2138.py)
SUB6_OFFSET = 0x6C910
PIXEL_OFF = 0x800
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
BW_PSMT4 = 256
DBW_CT32 = 128
BG_IDX = 15
INK_IDX = 0

# Banner label region: (16, 145, 88, 23) = "New Character"
BANNER_X, BANNER_Y, BANNER_W, BANNER_H = 16, 145, 88, 23


def extract_and_deswizzle(filepath, label):
    """Extract sub6 pixel data and deswizzle."""
    with open(filepath, "rb") as f:
        r2138 = f.read()
    print(f"{label}: {len(r2138)} bytes total")

    abs_off = SUB6_OFFSET + PIXEL_OFF
    pixel_data = r2138[abs_off:abs_off + PIXEL_SIZE]
    assert len(pixel_data) == PIXEL_SIZE, f"Pixel data size: {len(pixel_data)}"

    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    print(f"  Deswizzled: {len(linear)} pixels ({TEX_W}x{TEX_H})")
    return linear


def render_atlas(linear, path, zoom=4, invert=True):
    """Render full atlas with zoom, optionally inverted."""
    w, h = TEX_W * zoom, TEX_H * zoom
    img = Image.new("L", (w, h))
    for y in range(TEX_H):
        for x in range(TEX_W):
            val = linear[y * TEX_W + x]
            if invert:
                brightness = (BG_IDX - val) * 255 // BG_IDX if BG_IDX > 0 else 0
            else:
                brightness = val * 255 // BG_IDX if BG_IDX > 0 else 0
            brightness = max(0, min(255, brightness))
            for dy in range(zoom):
                for dx in range(zoom):
                    img.putpixel((x * zoom + dx, y * zoom + dy), brightness)
    img.save(path)
    print(f"  Saved: {path} ({w}x{h})")


def render_crop(linear, path, cx, cy, cw, ch, zoom=8, invert=True):
    """Render a cropped region with zoom."""
    w, h = cw * zoom, ch * zoom
    img = Image.new("L", (w, h))
    for y in range(ch):
        for x in range(cw):
            sx, sy = cx + x, cy + y
            if 0 <= sx < TEX_W and 0 <= sy < TEX_H:
                val = linear[sy * TEX_W + sx]
            else:
                val = BG_IDX
            if invert:
                brightness = (BG_IDX - val) * 255 // BG_IDX if BG_IDX > 0 else 0
            else:
                brightness = val * 255 // BG_IDX if BG_IDX > 0 else 0
            brightness = max(0, min(255, brightness))
            for dy in range(zoom):
                for dx in range(zoom):
                    img.putpixel((x * zoom + dx, y * zoom + dy), brightness)
    img.save(path)
    print(f"  Saved: {path} ({w}x{h})")


def analyze_region(linear, label, rx, ry, rw, rh):
    """Analyze pixel statistics in a region."""
    print(f"\n  --- {label} region ({rx},{ry} {rw}x{rh}) ---")
    counts = {}
    for y in range(ry, ry + rh):
        for x in range(rx, rx + rw):
            if 0 <= x < TEX_W and 0 <= y < TEX_H:
                val = linear[y * TEX_W + x]
                counts[val] = counts.get(val, 0) + 1
    total = sum(counts.values())
    print(f"  Total pixels: {total}")
    for idx in sorted(counts.keys()):
        pct = counts[idx] * 100.0 / total
        print(f"    idx {idx:2d}: {counts[idx]:5d} ({pct:5.1f}%)")
    return counts


def compare_clear_zone(orig, patched, rx, ry, rw, rh):
    """Check if patched has a rectangular clear zone the original doesn't."""
    print(f"\n  --- Clear zone comparison ({rx},{ry} {rw}x{rh}) ---")

    # Count background pixels in each
    orig_bg = 0
    patched_bg = 0
    diff_pixels = 0
    for y in range(ry, ry + rh):
        for x in range(rx, rx + rw):
            if 0 <= x < TEX_W and 0 <= y < TEX_H:
                ov = orig[y * TEX_W + x]
                pv = patched[y * TEX_W + x]
                if ov == BG_IDX:
                    orig_bg += 1
                if pv == BG_IDX:
                    patched_bg += 1
                if ov != pv:
                    diff_pixels += 1

    total = rw * rh
    print(f"  Original  bg (idx {BG_IDX}): {orig_bg}/{total} ({orig_bg*100.0/total:.1f}%)")
    print(f"  Patched   bg (idx {BG_IDX}): {patched_bg}/{total} ({patched_bg*100.0/total:.1f}%)")
    print(f"  Changed pixels: {diff_pixels}/{total} ({diff_pixels*100.0/total:.1f}%)")

    # Check for a clear rectangular border (edges all bg in patched but not in original)
    edge_cleared = 0
    edge_total = 0
    for y in [ry, ry + rh - 1]:
        for x in range(rx, rx + rw):
            if 0 <= x < TEX_W and 0 <= y < TEX_H:
                edge_total += 1
                ov = orig[y * TEX_W + x]
                pv = patched[y * TEX_W + x]
                if ov != BG_IDX and pv == BG_IDX:
                    edge_cleared += 1
    for x in [rx, rx + rw - 1]:
        for y in range(ry + 1, ry + rh - 1):
            if 0 <= x < TEX_W and 0 <= y < TEX_H:
                edge_total += 1
                ov = orig[y * TEX_W + x]
                pv = patched[y * TEX_W + x]
                if ov != BG_IDX and pv == BG_IDX:
                    edge_cleared += 1

    print(f"  Edge pixels cleared by patch: {edge_cleared}/{edge_total}")
    if edge_cleared > edge_total * 0.3:
        print(f"  >> YES: visible rectangular clear zone detected")
    else:
        print(f"  >> No obvious rectangular clear zone on edges")


def check_residual_jp(orig, patched, rx, ry, rw, rh):
    """Check for residual Japanese strokes alongside English text."""
    print(f"\n  --- Residual JP check ({rx},{ry} {rw}x{rh}) ---")

    # Find columns with ink in both original and patched
    # Original ink = where original has non-bg pixels (Japanese)
    # Patched ink = where patched has non-bg pixels (should be English only)
    orig_ink_cols = set()
    patched_ink_cols = set()
    shared_ink_pixels = 0

    for y in range(ry, ry + rh):
        for x in range(rx, rx + rw):
            if 0 <= x < TEX_W and 0 <= y < TEX_H:
                ov = orig[y * TEX_W + x]
                pv = patched[y * TEX_W + x]
                if ov != BG_IDX:
                    orig_ink_cols.add(x)
                if pv != BG_IDX:
                    patched_ink_cols.add(x)
                # Pixel has ink in BOTH = potential residual JP
                if ov != BG_IDX and pv != BG_IDX and ov == pv:
                    shared_ink_pixels += 1

    only_orig = orig_ink_cols - patched_ink_cols
    only_patched = patched_ink_cols - orig_ink_cols
    both = orig_ink_cols & patched_ink_cols

    total_ink = len(patched_ink_cols) if patched_ink_cols else 1
    print(f"  Original ink columns: {len(orig_ink_cols)}")
    print(f"  Patched ink columns:  {len(patched_ink_cols)}")
    print(f"  Columns with ink in BOTH: {len(both)}")
    print(f"  Pixels identical (non-bg) in both: {shared_ink_pixels}")

    if shared_ink_pixels > 10:
        print(f"  >> WARNING: {shared_ink_pixels} pixels preserved from original — possible residual JP strokes")
    else:
        print(f"  >> Clean: no significant residual JP strokes detected")


def main():
    original_path = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
    patched_path = os.path.join(BASE, "build", "packdata_resources", "2138_type29.raw")

    print("=" * 60)
    print("  R2138 Sub6 Preview Generator")
    print("=" * 60)

    # 1. Deswizzle both
    print("\n[1] Deswizzle PATCHED sub6")
    patched_lin = extract_and_deswizzle(patched_path, "PATCHED")

    print("\n[2] Deswizzle ORIGINAL sub6")
    orig_lin = extract_and_deswizzle(original_path, "ORIGINAL")

    # 2. Full atlas patched at 4x
    print("\n[3] Render full PATCHED atlas at 4x")
    render_atlas(patched_lin,
                 os.path.join(DUMP_DIR, "r2138_sub6_PATCHED_4x.png"),
                 zoom=4, invert=True)

    # 3. Banner crops at 8x
    # Expand banner region slightly for context
    bx, by, bw, bh = BANNER_X - 2, BANNER_Y - 2, BANNER_W + 4, BANNER_H + 4

    print("\n[4] Render PATCHED banner at 8x")
    render_crop(patched_lin,
                os.path.join(DUMP_DIR, "r2138_sub6_banner_PATCHED_8x.png"),
                bx, by, bw, bh, zoom=8, invert=True)

    print("\n[5] Render ORIGINAL banner at 8x")
    render_crop(orig_lin,
                os.path.join(DUMP_DIR, "r2138_sub6_banner_ORIGINAL_8x.png"),
                bx, by, bw, bh, zoom=8, invert=True)

    # 4. Pixel analysis
    print("\n[6] Analyze banner region")
    print("\n  ORIGINAL:")
    analyze_region(orig_lin, "original banner", BANNER_X, BANNER_Y, BANNER_W, BANNER_H)
    print("\n  PATCHED:")
    analyze_region(patched_lin, "patched banner", BANNER_X, BANNER_Y, BANNER_W, BANNER_H)

    # 5. Clear zone comparison
    print("\n[7] Clear zone comparison")
    compare_clear_zone(orig_lin, patched_lin, BANNER_X, BANNER_Y, BANNER_W, BANNER_H)

    # 6. Residual JP check
    print("\n[8] Residual JP strokes check")
    check_residual_jp(orig_lin, patched_lin, BANNER_X, BANNER_Y, BANNER_W, BANNER_H)

    # Also check the wider clear zone that patch_r2138 creates
    # The patcher clears from y=145 down to next label at y=170 (25px)
    print("\n[9] Extended clear zone check (y=145..170, full clear height)")
    compare_clear_zone(orig_lin, patched_lin, BANNER_X, BANNER_Y, BANNER_W, 25)

    # Row-by-row ink density for the banner
    print("\n[10] Row-by-row ink density in banner region")
    print(f"  {'Row':>4s}  {'Orig ink':>9s}  {'Patched ink':>11s}  {'Match':>6s}")
    for y in range(BANNER_Y, BANNER_Y + BANNER_H):
        orig_ink = sum(1 for x in range(BANNER_X, BANNER_X + BANNER_W)
                       if orig_lin[y * TEX_W + x] != BG_IDX)
        patch_ink = sum(1 for x in range(BANNER_X, BANNER_X + BANNER_W)
                        if patched_lin[y * TEX_W + x] != BG_IDX)
        match = "SAME" if orig_ink == patch_ink else "DIFF"
        print(f"  {y:4d}  {orig_ink:9d}  {patch_ink:11d}  {match:>6s}")

    print("\n" + "=" * 60)
    print("  DONE — check dumps/ for preview images")
    print("=" * 60)


if __name__ == "__main__":
    main()
