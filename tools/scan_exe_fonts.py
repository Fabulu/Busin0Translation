#!/usr/bin/env python3
"""
Scan the EXE data section for embedded PSMT4 font texture data.

Searches 0x200000-0x400000 for blocks that look like PSMT4 font textures:
- Values in 0-15 range when unpacked as nibbles
- Block sizes that are multiples of 128
- Tries both raw and deswizzled rendering
"""
import os
import sys
import struct
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4

try:
    from PIL import Image
except ImportError:
    print("ERROR: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
OUT_DIR = os.path.join(BASE, "dumps", "exe_font_candidates")
os.makedirs(OUT_DIR, exist_ok=True)

# Grayscale palette for 4-bit
def make_gray_palette():
    pal = bytearray(64)
    for i in range(16):
        v = i * 17
        pal[i*4] = v; pal[i*4+1] = v; pal[i*4+2] = v; pal[i*4+3] = 255
    return pal

GRAY_PAL = make_gray_palette()

def render_psmt4_raw(data, width, height, out_path):
    """Render raw bytes as PSMT4 (2 pixels per byte, no deswizzle)."""
    needed = width * height // 2
    if len(data) < needed:
        return
    img = Image.new('L', (width, height))
    pixels = []
    for i in range(needed):
        b = data[i]
        pixels.append((b & 0x0F) * 17)
        pixels.append(((b >> 4) & 0x0F) * 17)
    img.putdata(pixels[:width*height])
    img.save(out_path)

def render_psmt4_deswizzled(data, width, height, dbw_ct32, out_path):
    """Deswizzle and render as PSMT4."""
    needed = width * height // 2
    if len(data) < needed:
        return
    try:
        pixels_lin = deswizzle_psmt4(data[:needed], width, height,
                                      bw_psmt4=width, dbw_ct32=dbw_ct32)
        img = Image.new('L', (width, height))
        img.putdata([p * 17 for p in pixels_lin])
        img.save(out_path)
    except Exception as e:
        print(f"  Deswizzle error: {e}")

def analyze_block(data, offset, size):
    """Analyze a block of data for PSMT4 font-like characteristics."""
    block = data[offset:offset+size]
    if len(block) < size:
        return None

    # Check if all zeros or all same value
    unique = set(block[:1024])
    if len(unique) <= 1:
        return None

    # Unpack as nibbles and check distribution
    nibble_counts = [0] * 16
    total_nibbles = 0
    for b in block:
        nibble_counts[b & 0x0F] += 1
        nibble_counts[(b >> 4) & 0x0F] += 1
        total_nibbles += 2

    # Font textures typically have:
    # - Lots of 0s (background)
    # - Some mid-range values (anti-aliased edges)
    # - Some high values (glyph body)
    zero_ratio = nibble_counts[0] / total_nibbles

    # Calculate entropy
    entropy = 0
    for c in nibble_counts:
        if c > 0:
            p = c / total_nibbles
            entropy -= p * math.log2(p)

    # Count how many unique nibble values are used
    used_values = sum(1 for c in nibble_counts if c > 0)

    return {
        'zero_ratio': zero_ratio,
        'entropy': entropy,
        'used_values': used_values,
        'nibble_counts': nibble_counts,
    }

def has_glyph_patterns(data, width):
    """Check if data has repeating vertical/horizontal patterns typical of glyphs.
    Looks for grid-like structure where glyphs would be arranged in cells."""
    bytes_per_row = width // 2
    nrows = len(data) // bytes_per_row
    if nrows < 16:
        return False

    # Check for periodic blank rows (gaps between glyph rows)
    blank_rows = 0
    for row in range(min(nrows, 256)):
        row_data = data[row*bytes_per_row:(row+1)*bytes_per_row]
        if all(b == 0 for b in row_data):
            blank_rows += 1

    # Font atlases typically have some blank rows but not all
    blank_ratio = blank_rows / min(nrows, 256)
    return 0.05 < blank_ratio < 0.7

def scan_region(exe_data, start, end, label):
    """Scan a region for font-like PSMT4 data."""
    print(f"\n{'='*60}")
    print(f"Scanning {label}: 0x{start:06X} - 0x{end:06X} ({(end-start)//1024} KB)")
    print(f"{'='*60}")

    candidates = []

    # Target block sizes for font textures
    sizes = [
        (32768,  256, 256,  "256x256"),
        (65536,  256, 512,  "256x512"),
        (131072, 512, 512,  "512x512"),
        (16384,  128, 256,  "128x256"),
        (16384,  256, 128,  "256x128"),
        (8192,   128, 128,  "128x128"),
        (4096,   128, 64,   "128x64"),
        (4096,   64,  128,  "64x128"),
    ]

    # Slide through the region with 256-byte alignment
    step = 256
    for off in range(start, end - 4096, step):
        for size, w, h, desc in sizes:
            if off + size > end:
                continue

            stats = analyze_block(exe_data, off, size)
            if stats is None:
                continue

            # Font texture heuristics:
            # - Background (0) should be 20-80% of pixels
            # - Entropy should be moderate (not too random, not too uniform)
            # - Should use at least 4-5 different nibble values
            if (0.20 < stats['zero_ratio'] < 0.85 and
                1.5 < stats['entropy'] < 3.8 and
                stats['used_values'] >= 4):

                block = exe_data[off:off+size]
                if has_glyph_patterns(block, w):
                    score = stats['entropy'] * (1 - abs(stats['zero_ratio'] - 0.5))
                    candidates.append((off, size, w, h, desc, stats, score))

    # Also do a coarser scan without the glyph pattern check, just reporting stats
    # for the specific requested regions
    return candidates

def main():
    print("Loading EXE...")
    exe_data = open(EXE_PATH, 'rb').read()
    print(f"EXE size: {len(exe_data)} bytes (0x{len(exe_data):X})")

    all_candidates = []

    # Scan the full data section
    # But first, let's do a broad nibble analysis to find promising regions
    print("\n" + "="*60)
    print("PHASE 1: Broad nibble analysis (0x200000 - 0x400000)")
    print("="*60)

    # Analyze in 4KB chunks
    chunk_size = 4096
    promising_regions = []
    for off in range(0x200000, min(0x400000, len(exe_data)), chunk_size):
        end = min(off + chunk_size, len(exe_data))
        chunk = exe_data[off:end]
        if len(chunk) < chunk_size:
            break

        # Quick nibble check
        nibble_counts = [0]*16
        for b in chunk:
            nibble_counts[b & 0x0F] += 1
            nibble_counts[(b >> 4) & 0x0F] += 1
        total = sum(nibble_counts)
        zero_ratio = nibble_counts[0] / total
        used = sum(1 for c in nibble_counts if c > 0)
        entropy = 0
        for c in nibble_counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)

        # Mark as promising if it looks like font data
        if (0.20 < zero_ratio < 0.85 and 1.5 < entropy < 3.8 and used >= 4):
            promising_regions.append((off, zero_ratio, entropy, used))

    print(f"Found {len(promising_regions)} promising 4KB chunks")

    # Group contiguous promising regions
    if promising_regions:
        groups = []
        current_start = promising_regions[0][0]
        current_end = current_start + chunk_size
        for off, zr, ent, used in promising_regions[1:]:
            if off <= current_end:
                current_end = off + chunk_size
            else:
                groups.append((current_start, current_end))
                current_start = off
                current_end = off + chunk_size
        groups.append((current_start, current_end))

        print(f"\nContiguous promising regions:")
        for gs, ge in groups:
            size = ge - gs
            print(f"  0x{gs:06X} - 0x{ge:06X}  ({size//1024} KB)")

    # Now scan specific regions of interest
    regions = [
        (0x200000, 0x280000, "Low data section"),
        (0x280000, 0x300000, "Mid data section (0x28-0x30)"),
        (0x300000, 0x380000, "High data section (0x30-0x38)"),
        (0x380000, min(0x3D0000, len(exe_data)), "Upper section (before bitmap)"),
    ]

    for rstart, rend, label in regions:
        if rstart >= len(exe_data):
            continue
        rend = min(rend, len(exe_data))
        cands = scan_region(exe_data, rstart, rend, label)
        all_candidates.extend(cands)

    # Sort by score
    all_candidates.sort(key=lambda x: x[6], reverse=True)

    # Report and render top candidates
    print(f"\n{'='*60}")
    print(f"TOP CANDIDATES (found {len(all_candidates)} total)")
    print(f"{'='*60}")

    rendered = set()  # avoid rendering overlapping blocks
    count = 0
    for off, size, w, h, desc, stats, score in all_candidates[:50]:
        # Skip if too close to an already rendered candidate
        skip = False
        for roff in rendered:
            if abs(off - roff) < 4096:
                skip = True
                break
        if skip:
            continue

        print(f"\n  Offset 0x{off:06X}, {desc}, size={size}, "
              f"zero={stats['zero_ratio']:.2f}, entropy={stats['entropy']:.2f}, "
              f"vals={stats['used_values']}, score={score:.3f}")

        block = exe_data[off:off+size]
        base_name = f"0x{off:06X}_{desc.replace('x','x')}"

        # Render raw
        raw_path = os.path.join(OUT_DIR, f"{base_name}_raw.png")
        render_psmt4_raw(block, w, h, raw_path)
        print(f"    Raw: {raw_path}")

        # Render deswizzled with various dbw values
        for dbw in [w, w//2, w*2]:
            if dbw < 64 or dbw > 1024:
                continue
            desw_path = os.path.join(OUT_DIR, f"{base_name}_desw_dbw{dbw}.png")
            render_psmt4_deswizzled(block, w, h, dbw, desw_path)
            print(f"    Deswizzled (dbw={dbw}): {desw_path}")

        rendered.add(off)
        count += 1
        if count >= 30:
            break

    # PHASE 2: Also render EVERY 32KB and 64KB block at 4KB alignment
    # in the priority regions, even without heuristic match
    print(f"\n{'='*60}")
    print("PHASE 2: Exhaustive rendering of priority regions")
    print("="*60)

    priority_ranges = [
        (0x2A0000, 0x2C0000),
        (0x380000, 0x3A0000),
        # Also check around any promising contiguous regions
    ]
    if promising_regions:
        for gs, ge in groups:
            if ge - gs >= 32768:
                priority_ranges.append((gs, ge))

    # Deduplicate priority ranges
    seen_ranges = set()
    for pr_start, pr_end in priority_ranges:
        pr_end = min(pr_end, len(exe_data))
        if pr_start >= len(exe_data):
            continue

        # Try 32KB blocks (256x256)
        for off in range(pr_start, pr_end - 32768, 4096):
            if off in rendered:
                continue
            key = (off, 32768)
            if key in seen_ranges:
                continue
            seen_ranges.add(key)

            block = exe_data[off:off+32768]
            # Quick check - not all zeros, not all same
            if len(set(block[:256])) <= 2:
                continue

            base_name = f"0x{off:06X}_256x256"
            raw_path = os.path.join(OUT_DIR, f"{base_name}_raw.png")
            render_psmt4_raw(block, 256, 256, raw_path)

            # Also deswizzle
            for dbw in [256, 128]:
                desw_path = os.path.join(OUT_DIR, f"{base_name}_desw_dbw{dbw}.png")
                render_psmt4_deswizzled(block, 256, 256, dbw, desw_path)

        # Try 64KB blocks (256x512)
        for off in range(pr_start, pr_end - 65536, 4096):
            if off in rendered:
                continue
            key = (off, 65536)
            if key in seen_ranges:
                continue
            seen_ranges.add(key)

            block = exe_data[off:off+65536]
            if len(set(block[:256])) <= 2:
                continue

            base_name = f"0x{off:06X}_256x512"
            raw_path = os.path.join(OUT_DIR, f"{base_name}_raw.png")
            render_psmt4_raw(block, 256, 512, raw_path)

            for dbw in [256, 128]:
                desw_path = os.path.join(OUT_DIR, f"{base_name}_desw_dbw{dbw}.png")
                render_psmt4_deswizzled(block, 256, 512, dbw, desw_path)

    # PHASE 3: Look for small repeated glyph patterns
    # Font data might not be a full atlas but individual glyph bitmaps
    print(f"\n{'='*60}")
    print("PHASE 3: Search for individual glyph bitmaps")
    print("="*60)

    # Japanese stat labels are small - maybe 16x16 or 24x24 glyphs
    # Search for sequences of small bitmap-like data
    glyph_sizes = [(16, 16), (24, 24), (12, 12), (20, 20)]

    for gw, gh in glyph_sizes:
        glyph_bytes = gw * gh // 2  # PSMT4
        print(f"\n  Searching for {gw}x{gh} glyph patterns ({glyph_bytes} bytes each)...")

        found_runs = []
        for off in range(0x200000, min(0x400000, len(exe_data)) - glyph_bytes, glyph_bytes):
            block = exe_data[off:off+glyph_bytes]
            # Check nibble distribution
            nibbles = []
            for b in block:
                nibbles.append(b & 0x0F)
                nibbles.append((b >> 4) & 0x0F)

            zero_count = nibbles.count(0)
            zero_ratio = zero_count / len(nibbles)
            unique = len(set(nibbles))

            if 0.3 < zero_ratio < 0.85 and unique >= 3:
                found_runs.append(off)

        # Find runs of consecutive glyph-like blocks
        if found_runs:
            runs = []
            run_start = found_runs[0]
            run_count = 1
            for i in range(1, len(found_runs)):
                if found_runs[i] == found_runs[i-1] + glyph_bytes:
                    run_count += 1
                else:
                    if run_count >= 4:
                        runs.append((run_start, run_count))
                    run_start = found_runs[i]
                    run_count = 1
            if run_count >= 4:
                runs.append((run_start, run_count))

            for run_start, run_count in runs[:5]:
                print(f"    Run of {run_count} glyphs at 0x{run_start:06X}")
                # Render as a strip
                strip_w = gw
                strip_h = gh * min(run_count, 32)
                strip_bytes = strip_w * strip_h // 2
                block = exe_data[run_start:run_start + strip_bytes]
                out_name = f"glyphs_{gw}x{gh}_0x{run_start:06X}_n{run_count}"
                raw_path = os.path.join(OUT_DIR, f"{out_name}_raw.png")
                render_psmt4_raw(block, strip_w, strip_h, raw_path)
                print(f"      Saved: {raw_path}")

    # PHASE 4: Dump a hex overview of the data section
    print(f"\n{'='*60}")
    print("PHASE 4: Data section overview")
    print("="*60)

    for off in range(0x200000, min(0x400000, len(exe_data)), 0x10000):
        end = min(off + 0x10000, len(exe_data))
        block = exe_data[off:end]
        zero_bytes = block.count(0)
        zero_pct = zero_bytes / len(block) * 100
        unique_bytes = len(set(block))

        # Also check for text strings
        ascii_count = sum(1 for b in block if 0x20 <= b <= 0x7E)
        ascii_pct = ascii_count / len(block) * 100

        marker = ""
        if zero_pct > 90:
            marker = " [MOSTLY ZEROS]"
        elif ascii_pct > 30:
            marker = " [TEXT/STRINGS]"
        elif unique_bytes < 20 and zero_pct < 50:
            marker = " [LOW VARIETY]"
        elif 20 < zero_pct < 80 and unique_bytes > 50:
            marker = " [POSSIBLE TEXTURE]"

        print(f"  0x{off:06X}: zero={zero_pct:5.1f}%, unique_bytes={unique_bytes:3d}, "
              f"ascii={ascii_pct:5.1f}%{marker}")

    print(f"\nDone! Output in: {OUT_DIR}")

if __name__ == "__main__":
    main()
