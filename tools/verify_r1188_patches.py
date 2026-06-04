#!/usr/bin/env python3
"""
Verify R1188 pixel patches: compare original vs patched atlas,
find all changed regions, cross-reference with STAT_GLYPHS, and
produce diff-map + per-region PNG visualizations.
"""
import sys
import os
import io

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed.  Run:  pip install Pillow")
    sys.exit(1)

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, _psmt4_nibble_addr

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
ORIG_PATH   = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
PATCH_PATH  = os.path.join(BASE, "build", "packdata_resources", "1188_type01.raw")
OUT_DIR     = os.path.join(BASE, "build", "textures_to_edit")

HEADER_RAW  = 0xC00 + 0x10   # 16-byte outer container + 3072-byte header
TEX_W       = 1024
TEX_H       = 1024
DBW_CT32    = 512
BW_PSMT4    = 1024
BASE_VRAM   = 0xA140

# ---------------------------------------------------------------------------
# STAT_GLYPHS from patch_r1188_comprehensive.py
# ---------------------------------------------------------------------------
STAT_GLYPHS = [
    ("STR",   "T",  1, 60, 0xA450),
    ("INT-1", "I",  0, 67, 0xA1F0),
    ("INT-2", "Q",  3, 88, 0xA700),
    ("PIE-1", "P",  0, 76, 0xA238),
    ("PIE-2", "I",  0, 66, 0xA390),
    ("PIE-3", "E",  0, 62, 0xA290),
    ("VIT-1", "V",  4, 60, 0xA708),
    ("VIT-2", "I",  3, 67, 0xA658),
    ("AGI-1", "A",  0, 60, 0xA2E0),
    ("AGI-2", "G",  4, 61, 0xA710),
    ("AGI-3", "I",  0, 60, 0xA318),
    ("LCK-1", "L",  4, 62, 0xA718),
    ("LCK-2", "C",  4, 63, 0xA720),
]
STAT_GLYPH_W = 20
STAT_GLYPH_H = 20


def load_and_deswizzle(path):
    """Load a .raw R1188 file and deswizzle to linear pixels."""
    data = open(path, "rb").read()
    pixel_data = data[HEADER_RAW:HEADER_RAW + TEX_W * TEX_H // 2]
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    return bytearray(linear)


def find_diff_pixels(orig, patched):
    """Return list of (x, y) where pixels differ."""
    diffs = []
    for i in range(TEX_W * TEX_H):
        if orig[i] != patched[i]:
            x = i % TEX_W
            y = i // TEX_W
            diffs.append((x, y))
    return diffs


def cluster_into_bboxes(points, gap=3):
    """Cluster nearby points into bounding-box regions.

    Uses a simple row-column merging: expand each bbox by *gap* pixels
    and merge overlapping boxes.
    """
    if not points:
        return []

    # Start with each point as a 1x1 bbox
    boxes = []
    for x, y in points:
        boxes.append([x, y, x, y])  # x0, y0, x1, y1

    # Iteratively merge overlapping boxes (with gap padding)
    changed = True
    while changed:
        changed = False
        merged = []
        used = [False] * len(boxes)
        for i in range(len(boxes)):
            if used[i]:
                continue
            bx = list(boxes[i])
            for j in range(i + 1, len(boxes)):
                if used[j]:
                    continue
                bj = boxes[j]
                # Check overlap with gap
                if (bx[0] - gap <= bj[2] and bj[0] - gap <= bx[2] and
                    bx[1] - gap <= bj[3] and bj[1] - gap <= bx[3]):
                    bx[0] = min(bx[0], bj[0])
                    bx[1] = min(bx[1], bj[1])
                    bx[2] = max(bx[2], bj[2])
                    bx[3] = max(bx[3], bj[3])
                    used[j] = True
                    changed = True
            merged.append(bx)
        boxes = merged

    # Sort by y then x
    boxes.sort(key=lambda b: (b[1], b[0]))
    return boxes


def pixels_to_grayscale(linear, x0, y0, x1, y1, scale=17):
    """Extract a region from the linear pixel array as a grayscale PIL Image."""
    w = x1 - x0 + 1
    h = y1 - y0 + 1
    img = Image.new("L", (w, h), 0)
    for dy in range(h):
        for dx in range(w):
            px = x0 + dx
            py = y0 + dy
            if 0 <= px < TEX_W and 0 <= py < TEX_H:
                v = linear[py * TEX_W + px]
                img.putpixel((dx, dy), v * scale)
    return img


def build_reverse_nibble_map():
    """Build VRAM nibble -> (atlas_x, atlas_y) reverse map."""
    reverse = {}
    for y in range(TEX_H):
        for x in range(TEX_W):
            nib = _psmt4_nibble_addr(x, y, BW_PSMT4)
            reverse[nib] = (x, y)
    return reverse


def stat_glyph_expected_regions(reverse_map):
    """Compute the expected atlas bounding boxes for each STAT_GLYPH entry."""
    regions = []
    for label, eng_char, u, v, vram in STAT_GLYPHS:
        xs, ys = [], []
        for dy in range(STAT_GLYPH_H):
            for dx in range(STAT_GLYPH_W):
                local_nib = _psmt4_nibble_addr(u + dx, v + dy, 256)
                global_nib = (vram - BASE_VRAM) * 512 + local_nib
                pos = reverse_map.get(global_nib)
                if pos:
                    xs.append(pos[0])
                    ys.append(pos[1])
        if xs:
            regions.append({
                "label": label,
                "char": eng_char,
                "vram": vram,
                "bbox": (min(xs), min(ys), max(xs), max(ys)),
            })
        else:
            regions.append({
                "label": label,
                "char": eng_char,
                "vram": vram,
                "bbox": None,
            })
    return regions


def bbox_overlaps(a, b, margin=2):
    """Check if two bboxes overlap (with margin)."""
    return (a[0] - margin <= b[2] and b[0] - margin <= a[2] and
            a[1] - margin <= b[3] and b[1] - margin <= a[3])


def main():
    print("=" * 70)
    print("  R1188 Patch Verification Tool")
    print("=" * 70)

    # --- Step 1-2: Load and deswizzle both versions ---
    print(f"\n  Loading ORIGINAL: {ORIG_PATH}")
    orig = load_and_deswizzle(ORIG_PATH)
    print(f"  Loading PATCHED:  {PATCH_PATH}")
    patched = load_and_deswizzle(PATCH_PATH)
    print(f"  Both deswizzled to {TEX_W}x{TEX_H} linear pixels.")

    # --- Step 4: Find all pixel differences ---
    print("\n  Finding pixel differences ...")
    diff_pixels = find_diff_pixels(orig, patched)
    total_changed = len(diff_pixels)
    print(f"  Total pixels changed: {total_changed}")

    if total_changed == 0:
        print("\n  WARNING: No differences found! Files may be identical.")
        return

    # --- Step 5: Cluster into bounding boxes ---
    print("\n  Clustering changed pixels into regions (gap=5) ...")
    bboxes = cluster_into_bboxes(diff_pixels, gap=5)
    print(f"  Found {len(bboxes)} distinct changed regions:\n")

    for i, bb in enumerate(bboxes):
        x0, y0, x1, y1 = bb
        w = x1 - x0 + 1
        h = y1 - y0 + 1
        n_changed = sum(1 for (px, py) in diff_pixels
                        if x0 <= px <= x1 and y0 <= py <= y1)
        print(f"    Region {i:3d}: ({x0:4d},{y0:4d})-({x1:4d},{y1:4d})  "
              f"size={w:4d}x{h:<4d}  changed_px={n_changed}")

    # --- Step 6: Save per-region PNGs ---
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"\n  Saving per-region comparison PNGs to {OUT_DIR} ...")

    zoom = 4  # scale factor for visibility
    for i, bb in enumerate(bboxes):
        x0, y0, x1, y1 = bb
        # Add 2px padding
        x0p = max(0, x0 - 2)
        y0p = max(0, y0 - 2)
        x1p = min(TEX_W - 1, x1 + 2)
        y1p = min(TEX_H - 1, y1 + 2)

        orig_img = pixels_to_grayscale(orig, x0p, y0p, x1p, y1p)
        patch_img = pixels_to_grayscale(patched, x0p, y0p, x1p, y1p)

        w = x1p - x0p + 1
        h = y1p - y0p + 1

        # Side-by-side: ORIGINAL | PATCHED
        combined = Image.new("L", (w * 2 + 4, h + 16), 0)
        combined.paste(orig_img, (0, 16))
        combined.paste(patch_img, (w + 4, 16))

        # Add labels
        draw = ImageDraw.Draw(combined)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 10)
        except Exception:
            font = ImageFont.load_default()
        draw.text((1, 1), "ORIG", fill=200, font=font)
        draw.text((w + 5, 1), "PATCH", fill=200, font=font)

        # Zoom up
        combined = combined.resize(
            (combined.width * zoom, combined.height * zoom), Image.NEAREST)

        path = os.path.join(OUT_DIR, f"R1188_diff_region_{i:03d}.png")
        combined.save(path)

    print(f"  Saved {len(bboxes)} region comparison PNGs.")

    # --- Step 7: Generate diff map ---
    print("\n  Generating diff map (1024x1024) ...")
    diff_set = set(diff_pixels)
    diff_map = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 255))
    dm_pixels = diff_map.load()
    for x, y in diff_set:
        # Red for changed pixels, intensity based on magnitude of change
        orig_v = orig[y * TEX_W + x]
        patch_v = patched[y * TEX_W + x]
        intensity = min(255, abs(patch_v - orig_v) * 40 + 80)
        dm_pixels[x, y] = (intensity, 0, 0, 255)

    diff_map_path = os.path.join(OUT_DIR, "R1188_diff_map.png")
    diff_map.save(diff_map_path)
    print(f"  Saved: {diff_map_path}")

    # Also save a zoomed-in version of interesting rows
    # Top 150 rows (kana area) + bottom 20 rows (label area)
    for label, yrange in [("kana_0-150", (0, 150)), ("bottom_1000-1024", (1000, 1024))]:
        y0r, y1r = yrange
        crop = diff_map.crop((0, y0r, TEX_W, y1r))
        crop = crop.resize((TEX_W * 2, (y1r - y0r) * 4), Image.NEAREST)
        zpath = os.path.join(OUT_DIR, f"R1188_diff_map_{label}.png")
        crop.save(zpath)
        print(f"  Saved: {zpath}")

    # --- Step 8: Cross-reference with STAT_GLYPHS ---
    print("\n  Building VRAM reverse map for STAT_GLYPH cross-reference ...")
    reverse_map = build_reverse_nibble_map()
    expected = stat_glyph_expected_regions(reverse_map)

    print(f"\n  STAT_GLYPH Cross-Reference ({len(expected)} glyphs):")
    print(f"  {'Label':8s} {'Char':5s} {'VRAM':8s} {'Expected BBox':28s} {'Matches Region?'}")
    print(f"  {'-'*8} {'-'*5} {'-'*8} {'-'*28} {'-'*20}")

    matched_count = 0
    for sg in expected:
        label = sg["label"]
        char = sg["char"]
        vram = sg["vram"]
        ebb = sg["bbox"]

        if ebb is None:
            print(f"  {label:8s} '{char}'   0x{vram:04X}  NO MAPPING FOUND            ---")
            continue

        eb_str = f"({ebb[0]:4d},{ebb[1]:4d})-({ebb[2]:4d},{ebb[3]:4d})"

        # Check if any diff region overlaps this expected bbox
        match_regions = []
        for ri, bb in enumerate(bboxes):
            if bbox_overlaps(ebb, bb):
                match_regions.append(ri)

        if match_regions:
            matched_count += 1
            region_str = ", ".join(f"R{r}" for r in match_regions)
            print(f"  {label:8s} '{char}'   0x{vram:04X}  {eb_str}  YES -> {region_str}")
        else:
            print(f"  {label:8s} '{char}'   0x{vram:04X}  {eb_str}  NO MATCH")

    print(f"\n  STAT_GLYPH match rate: {matched_count}/{len(expected)} "
          f"({100*matched_count/len(expected):.0f}%)")

    # --- Summary of region types ---
    print(f"\n  Region Classification Summary:")

    # Check which regions are in the kana area (y < 200)
    kana_regions = [i for i, bb in enumerate(bboxes)
                    if bb[1] < 200]
    # Check which are in the bottom label area (y >= 1000)
    bottom_regions = [i for i, bb in enumerate(bboxes)
                      if bb[1] >= 1000]
    # Check which overlap stat glyph expected areas
    stat_regions = set()
    for sg in expected:
        if sg["bbox"]:
            for ri, bb in enumerate(bboxes):
                if bbox_overlaps(sg["bbox"], bb):
                    stat_regions.add(ri)
    stat_regions = sorted(stat_regions)

    # Everything else
    all_classified = set(kana_regions) | set(bottom_regions) | set(stat_regions)
    other_regions = [i for i in range(len(bboxes)) if i not in all_classified]

    print(f"    Kana cell regions (y<200):           {len(kana_regions)}")
    print(f"    Bottom label regions (y>=1000):       {len(bottom_regions)}")
    print(f"    Stat glyph regions (VRAM-mapped):     {len(stat_regions)}")
    print(f"    Unclassified regions:                 {len(other_regions)}")

    if other_regions:
        print(f"\n    Unclassified region details:")
        for ri in other_regions:
            bb = bboxes[ri]
            print(f"      Region {ri:3d}: ({bb[0]:4d},{bb[1]:4d})-({bb[2]:4d},{bb[3]:4d})  "
                  f"size={bb[2]-bb[0]+1}x{bb[3]-bb[1]+1}")

    # --- Final verdict ---
    print(f"\n{'=' * 70}")
    if matched_count == len(expected):
        print("  VERDICT: ALL stat glyph patches land on expected VRAM positions.")
    elif matched_count > 0:
        print(f"  VERDICT: {matched_count}/{len(expected)} stat glyphs match expected positions.")
        print("           Some glyphs may have missed their target cells.")
    else:
        print("  VERDICT: NO stat glyphs match expected positions!")
        print("           The VRAM mapping may be incorrect.")

    if other_regions:
        print(f"  NOTE: {len(other_regions)} region(s) do not match any known patch category.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
