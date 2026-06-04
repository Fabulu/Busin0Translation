#!/usr/bin/env python3
"""
Scan the deswizzled R1188 atlas for high-density 64x16 blocks that could be
pre-composed stat label sprites (力, 知恵, 信仰心, etc.).

Uses integral images (numpy) for fast density scanning, then analyzes only
top candidates. Outputs candidate PNGs and annotated atlas.

PCSX2 texture dump hashes (64x16 stat label sprites):
  f2013a64642252e3: Strength (力)       bb20512b10c3128b: IQ (知恵)
  aa43f966ad69195e: Piety (信仰心)      5d0c6327e20384e7: Vitality (生命力)
  4841ef9a2dc4981:  Agility (敏捷度)    280ea82c1c476a98: Luck (幸運度)
  d455234204274c43: 7th stat label
"""

import os, sys
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from PIL import Image, ImageDraw, ImageOps

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DESWIZZLED_PNGS = [
    os.path.join(BASE, "build", "textures_to_edit", "R1188_full_deswizzled.png"),
    os.path.join(BASE, "build", "R1188_deswizzled_full.png"),
]
OUT_DIR = os.path.join(BASE, "dumps", "r1188_label_scan")
TEX_W, TEX_H = 1024, 1024


def load_atlas():
    """Load deswizzled R1188 as numpy uint8 array (grayscale 0-255)."""
    for p in DESWIZZLED_PNGS:
        if os.path.exists(p):
            print(f"Loading: {p}")
            img = Image.open(p).convert('L')
            return np.array(img, dtype=np.uint8), img
    # Fallback: deswizzle
    print("No deswizzled PNG found, running deswizzle...")
    sys.path.insert(0, os.path.join(BASE, "tools"))
    from psmt4_deswizzle import deswizzle_psmt4
    data = open(os.path.join(BASE, "extracted", "packdata_resources",
                              "1188_type01.bin"), 'rb').read()
    px = deswizzle_psmt4(data[0xC00:0xC00+524288], 1024, 1024,
                          bw_psmt4=1024, dbw_ct32=512)
    arr = np.clip(np.array(px, dtype=np.uint8).reshape(1024, 1024) * 17,
                  0, 255).astype(np.uint8)
    img = Image.fromarray(arr, mode='L')
    return arr, img


def integral_density_scan(arr, bw, bh, step_x, step_y, threshold):
    """Fast sliding-window density scan using integral image.

    Returns list of (x, y, density) tuples above threshold.
    """
    binary = (arr > 0).astype(np.float64)
    integral = np.cumsum(np.cumsum(binary, axis=0), axis=1)
    h, w = arr.shape
    area = bw * bh

    # Build coordinate grids
    ys = np.arange(0, h - bh + 1, step_y)
    xs = np.arange(0, w - bw + 1, step_x)

    results = []
    # Vectorize over x for each y
    for y in ys:
        y2 = y + bh - 1
        # Bottom-right corners
        br = integral[y2, xs + bw - 1]
        # Top strip
        top = integral[y - 1, xs + bw - 1] if y > 0 else np.zeros(len(xs))
        # Left strip
        left = np.zeros(len(xs))
        mask = xs > 0
        left[mask] = integral[y2, xs[mask] - 1]
        # Top-left corner
        tl = np.zeros(len(xs))
        if y > 0:
            tl[mask] = integral[y - 1, xs[mask] - 1]
        sums = br - top - left + tl
        densities = sums / area
        above = densities >= threshold
        for x_idx in np.where(above)[0]:
            results.append((int(xs[x_idx]), int(y), float(densities[x_idx])))

    return results


def nms_grid(hits, bw, bh, grid_size=None):
    """Fast NMS by keeping only the best hit per grid cell."""
    if grid_size is None:
        grid_size = (bw // 2, bh // 2)
    grid = {}
    for x, y, density in hits:
        key = (x // grid_size[0], y // grid_size[1])
        if key not in grid or density > grid[key][2]:
            grid[key] = (x, y, density)
    return sorted(grid.values(), key=lambda t: t[2], reverse=True)


def analyze_block_np(arr, x, y, bw, bh):
    """Detailed analysis of a candidate block using numpy."""
    block = arr[y:y+bh, x:x+bw]
    nz_mask = block > 0
    density = nz_mask.sum() / block.size
    nz_vals = block[nz_mask]
    mean_int = float(nz_vals.mean()) if len(nz_vals) > 0 else 0.0

    # Edge emptiness
    edges = np.concatenate([block[0,:], block[-1,:], block[1:-1,0], block[1:-1,-1]])
    edge_empty = float((edges == 0).sum()) / len(edges) if len(edges) > 0 else 0

    # Vertical strokes (columns with >= 6 consecutive non-zero rows)
    has_vstroke = False
    col_nz = nz_mask.astype(np.int8)
    for c in range(bw):
        col = col_nz[:, c]
        # Find max consecutive run
        runs = np.diff(np.where(np.concatenate(([0], col, [0])) == 0)[0]) - 1
        if len(runs) > 0 and runs.max() >= 6:
            has_vstroke = True
            break

    # Horizontal strokes
    has_hstroke = False
    for r in range(bh):
        row = col_nz[r, :]
        runs = np.diff(np.where(np.concatenate(([0], row, [0])) == 0)[0]) - 1
        if len(runs) > 0 and runs.max() >= 6:
            has_hstroke = True
            break

    score = density
    if edge_empty > 0.4:
        score *= 1.3
    if has_vstroke and has_hstroke:
        score *= 1.5
    if density > 0.85:
        score *= 0.5

    return {
        'x': x, 'y': y, 'bw': bw, 'bh': bh,
        'density': density, 'edge_empty': edge_empty,
        'mean_intensity': mean_int,
        'has_vstroke': has_vstroke, 'has_hstroke': has_hstroke,
        'score': score,
    }


def save_candidates(arr, candidates, out_dir, prefix, scale=4):
    """Save candidate blocks as scaled PNGs."""
    os.makedirs(out_dir, exist_ok=True)
    for i, c in enumerate(candidates):
        block = arr[c['y']:c['y']+c['bh'], c['x']:c['x']+c['bw']]
        img = Image.fromarray(block, mode='L')
        img = img.resize((c['bw']*scale, c['bh']*scale), Image.NEAREST)
        fname = (f"{prefix}_{i:03d}_x{c['x']}_y{c['y']}"
                 f"_d{c['density']:.2f}_s{c['score']:.2f}.png")
        img.save(os.path.join(out_dir, fname))


def save_annotated(gray_img, candidates, out_path, n=80):
    """Save atlas with candidate rectangles."""
    rgb = gray_img.convert('RGB')
    draw = ImageDraw.Draw(rgb)
    for i, c in enumerate(candidates[:n]):
        x, y, bw, bh = c['x'], c['y'], c['bw'], c['bh']
        color = (255, 0, 0) if c['score'] > 0.5 else (255, 255, 0)
        draw.rectangle([x, y, x+bw-1, y+bh-1], outline=color)
        draw.text((x+1, y+1), str(i), fill=color)
    rgb.save(out_path)
    print(f"  Saved: {out_path}")


def scan_size(arr, gray_img, bw, bh, step_x, step_y, threshold, label,
              top_n=80, grid_nms_div=2):
    """Run full scan pipeline for one block size."""
    print(f"\n{'='*60}")
    print(f"Scanning {bw}x{bh} blocks (step={step_x}x{step_y}, "
          f"threshold={threshold})")
    print(f"{'='*60}")

    # Fast integral-image scan
    hits = integral_density_scan(arr, bw, bh, step_x, step_y, threshold)
    print(f"  Raw hits: {len(hits)}")

    # Grid-based NMS (fast)
    grid_size = (max(1, bw // grid_nms_div), max(1, bh // grid_nms_div))
    nms_hits = nms_grid(hits, bw, bh, grid_size)
    print(f"  After grid NMS ({grid_size}): {len(nms_hits)}")

    # Detailed analysis of top candidates
    n_analyze = min(500, len(nms_hits))
    candidates = []
    for x, y, density in nms_hits[:n_analyze]:
        c = analyze_block_np(arr, x, y, bw, bh)
        candidates.append(c)

    # Sort by score
    candidates.sort(key=lambda c: c['score'], reverse=True)

    # Print top
    n_show = min(top_n, len(candidates))
    print(f"\n  Top {n_show} candidates:")
    for i, c in enumerate(candidates[:n_show]):
        print(f"    #{i:3d}: ({c['x']:4d},{c['y']:4d}) "
              f"d={c['density']:.3f} edge={c['edge_empty']:.3f} "
              f"int={c['mean_intensity']:.0f} "
              f"v={c['has_vstroke']} h={c['has_hstroke']} "
              f"s={c['score']:.3f}")

    # Save PNGs
    cand_dir = os.path.join(OUT_DIR, f"candidates_{bw}x{bh}")
    save_candidates(arr, candidates[:top_n], cand_dir, f"cand{bw}x{bh}")
    print(f"  Saved {min(top_n, len(candidates))} PNGs to {cand_dir}")

    # Annotated atlas
    ann_path = os.path.join(OUT_DIR, f"r1188_annotated_{bw}x{bh}.png")
    save_annotated(gray_img, candidates, ann_path, top_n)

    # Y histogram
    if candidates:
        print(f"\n  Y-histogram (top {n_show}, {bh}px buckets):")
        y_hist = {}
        for c in candidates[:n_show]:
            bucket = c['y'] // bh
            y_hist[bucket] = y_hist.get(bucket, 0) + 1
        for b in sorted(y_hist.keys()):
            cnt = y_hist[b]
            print(f"    y={b*bh:4d}-{b*bh+bh-1:4d}: {cnt:3d} {'#'*cnt}")

    return candidates


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    arr, gray_img = load_atlas()
    nz = np.count_nonzero(arr)
    print(f"Atlas: {arr.shape}, non-zero: {nz}/{arr.size} ({nz/arr.size*100:.1f}%)")

    # Save copies
    gray_img.save(os.path.join(OUT_DIR, "r1188_full_deswizzled.png"))
    ImageOps.invert(gray_img).save(
        os.path.join(OUT_DIR, "r1188_full_deswizzled_inverted.png"))

    # Validate with known glyphs
    print("\n=== Validation ===")
    for label, cx, cy in [("digit_5", 96, 0), ("A", 288, 0),
                           ("a", 24, 24), ("space", 264, 0)]:
        block = arr[cy:cy+24, cx:cx+24]
        d = np.count_nonzero(block) / block.size
        print(f"  {label:8s} ({cx:3d},{cy:3d}) 24x24: density={d:.3f}")

    # Scan 1: 64x16 (stat label size from PCSX2 dumps)
    cands_64 = scan_size(arr, gray_img, 64, 16, 4, 2, 0.20, "stat_labels",
                         top_n=80, grid_nms_div=2)

    # Scan 2: 48x20 (tab label size)
    cands_48 = scan_size(arr, gray_img, 48, 20, 4, 4, 0.20, "tab_labels",
                         top_n=40, grid_nms_div=2)

    # Scan 3: 24x24 grid-aligned cells (atlas layout analysis)
    print(f"\n{'='*60}")
    print("24x24 grid-aligned cell occupancy")
    print(f"{'='*60}")
    cell_rows = {}
    for cy in range(0, TEX_H - 23, 24):
        for cx in range(0, TEX_W - 23, 24):
            block = arr[cy:cy+24, cx:cx+24]
            d = np.count_nonzero(block) / block.size
            if d >= 0.10:
                r = cy // 24
                if r not in cell_rows:
                    cell_rows[r] = []
                cell_rows[r].append((cx // 24, d))

    total_cells = sum(len(v) for v in cell_rows.values())
    print(f"  Occupied cells: {total_cells}")
    last_occupied_row = 0
    for r in sorted(cell_rows.keys()):
        cells = cell_rows[r]
        cols = sorted([c[0] for c in cells])
        max_d = max(c[1] for c in cells)
        n = len(cells)
        last_occupied_row = r
        print(f"  Row {r:3d} (y={r*24:4d}-{r*24+23:4d}): "
              f"{n:3d} cells, max_d={max_d:.3f}, "
              f"cols={cols[:10]}{'...' if n > 10 else ''}")

    print(f"\n  Last occupied row: {last_occupied_row} "
          f"(y={last_occupied_row*24}-{last_occupied_row*24+23})")
    print(f"  Empty rows below: {TEX_H//24 - last_occupied_row - 1}")

    # Final analysis
    print(f"\n{'='*60}")
    print("CONCLUSION")
    print(f"{'='*60}")
    high_64 = [c for c in cands_64 if c['score'] > 0.4 and
               c['has_vstroke'] and c['has_hstroke']]
    print(f"\n64x16 candidates with strokes AND score>0.4: {len(high_64)}")
    if high_64:
        print("These may be pre-composed stat labels. Check PNGs visually:")
        for i, c in enumerate(high_64[:10]):
            print(f"  ({c['x']},{c['y']}) d={c['density']:.3f} s={c['score']:.3f}")
    else:
        print("No strong 64x16 composite candidates found.")

    # Check if atlas is densely packed (kanji region)
    # If every 24x24 cell is a single glyph, then composites don't exist
    print(f"\nAtlas is a grid of individual glyph cells.")
    print(f"If 64x16 composites exist, they'd overlap cell boundaries.")
    print(f"If NOT found: game composites stat labels at RUNTIME from")
    print(f"individual cells -> VRAM scratch buffer -> PCSX2 captures that.")

    print(f"\nAll output: {OUT_DIR}")


if __name__ == "__main__":
    main()
