#!/usr/bin/env python3
"""
Fast EXE font texture scanner - Phase 1: identify candidates without deswizzle.
Phase 2: render only the best candidates with deswizzle.
"""
import os, sys, math, struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image
except ImportError:
    print("ERROR: pip install Pillow"); sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
OUT_DIR = os.path.join(BASE, "dumps", "exe_font_candidates")
os.makedirs(OUT_DIR, exist_ok=True)

def render_raw_psmt4(data, w, h, path):
    """Render bytes as raw PSMT4 (2 pixels/byte), no deswizzle."""
    img = Image.new('L', (w, h))
    px = []
    for i in range(w*h//2):
        b = data[i]
        px.append((b & 0x0F) * 17)
        px.append(((b >> 4) & 0x0F) * 17)
    img.putdata(px[:w*h])
    img.save(path)

def nibble_stats(data):
    """Get nibble distribution stats for a block."""
    counts = [0]*16
    for b in data:
        counts[b & 0x0F] += 1
        counts[(b >> 4) & 0x0F] += 1
    total = sum(counts)
    if total == 0:
        return 0, 0, 0
    zero_ratio = counts[0] / total
    entropy = 0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    used = sum(1 for c in counts if c > 0)
    return zero_ratio, entropy, used

def main():
    print("Loading EXE...")
    exe = open(EXE_PATH, 'rb').read()
    print(f"EXE size: {len(exe)} bytes (0x{len(exe):X})")

    # ========================================
    # PHASE 0: Overview of 0x200000-0x400000
    # ========================================
    print("\n" + "="*70)
    print("DATA SECTION OVERVIEW (64KB blocks)")
    print("="*70)
    for off in range(0x200000, min(0x400000, len(exe)), 0x10000):
        end = min(off + 0x10000, len(exe))
        block = exe[off:end]
        zero_bytes = block.count(0)
        zero_pct = zero_bytes / len(block) * 100
        unique = len(set(block))
        ascii_c = sum(1 for b in block if 0x20 <= b <= 0x7E)
        ascii_pct = ascii_c / len(block) * 100

        tag = ""
        if zero_pct > 90: tag = " ZEROS"
        elif ascii_pct > 30: tag = " TEXT"
        elif unique > 100 and 10 < zero_pct < 70: tag = " <-- TEXTURE?"
        elif unique > 50 and 10 < zero_pct < 80: tag = " data"

        print(f"  0x{off:06X}: zeros={zero_pct:5.1f}% unique={unique:3d} ascii={ascii_pct:4.1f}%{tag}")

    # ========================================
    # PHASE 1: Find promising 4KB chunks
    # ========================================
    print("\n" + "="*70)
    print("PHASE 1: Scanning 4KB chunks for PSMT4-like data")
    print("="*70)

    chunk_sz = 4096
    promising = []
    for off in range(0x200000, min(0x400000, len(exe)) - chunk_sz, chunk_sz):
        block = exe[off:off+chunk_sz]
        if len(set(block[:256])) <= 2:
            continue
        zr, ent, used = nibble_stats(block)
        if 0.15 < zr < 0.88 and 1.2 < ent < 3.9 and used >= 4:
            promising.append((off, zr, ent, used))

    print(f"Found {len(promising)} promising chunks")

    # Group contiguous
    groups = []
    if promising:
        gs = promising[0][0]
        ge = gs + chunk_sz
        for off, zr, ent, used in promising[1:]:
            if off <= ge:
                ge = off + chunk_sz
            else:
                groups.append((gs, ge))
                gs = off
                ge = off + chunk_sz
        groups.append((gs, ge))

    print(f"\nContiguous regions ({len(groups)}):")
    for gs, ge in groups:
        sz = ge - gs
        # Get average stats
        avg_zr = avg_ent = 0
        cnt = 0
        for off, zr, ent, used in promising:
            if gs <= off < ge:
                avg_zr += zr; avg_ent += ent; cnt += 1
        if cnt:
            avg_zr /= cnt; avg_ent /= cnt
        print(f"  0x{gs:06X}-0x{ge:06X} ({sz:6d} bytes = {sz//1024:3d} KB) "
              f"avg_zero={avg_zr:.2f} avg_ent={avg_ent:.2f}")

    # ========================================
    # PHASE 2: Render raw PSMT4 for all promising contiguous regions
    # ========================================
    print("\n" + "="*70)
    print("PHASE 2: Rendering raw PSMT4 for promising regions")
    print("="*70)

    # Render each contiguous region >= 4KB as 256-wide raw PSMT4
    for gs, ge in groups:
        sz = ge - gs
        if sz < 4096:
            continue

        block = exe[gs:ge]
        h = sz * 2 // 256  # 2 pixels per byte, 256 wide
        if h < 1:
            continue

        out_path = os.path.join(OUT_DIR, f"region_0x{gs:06X}_{sz//1024}KB_256w_raw.png")
        render_raw_psmt4(block, 256, h, out_path)
        print(f"  Rendered: {out_path}")

        # Also try 128 wide
        h2 = sz * 2 // 128
        out_path2 = os.path.join(OUT_DIR, f"region_0x{gs:06X}_{sz//1024}KB_128w_raw.png")
        render_raw_psmt4(block, 128, h2, out_path2)

    # ========================================
    # PHASE 3: Priority regions - render every 32KB at 4KB steps
    # ========================================
    print("\n" + "="*70)
    print("PHASE 3: Priority regions exhaustive render")
    print("="*70)

    priority = [
        (0x2A0000, 0x2C0000),
        (0x380000, 0x3A0000),
    ]
    # Add any large contiguous groups
    for gs, ge in groups:
        if ge - gs >= 16384:
            priority.append((gs, ge))

    # Deduplicate
    done_offsets = set()
    for pr_s, pr_e in priority:
        pr_e = min(pr_e, len(exe))
        if pr_s >= len(exe):
            continue
        print(f"\n  Region 0x{pr_s:06X}-0x{pr_e:06X}:")

        for off in range(pr_s, pr_e - 8192, 4096):
            if off in done_offsets:
                continue
            done_offsets.add(off)

            # 256x256 = 32KB
            if off + 32768 <= len(exe):
                block = exe[off:off+32768]
                if len(set(block[:512])) > 3:
                    p = os.path.join(OUT_DIR, f"pri_0x{off:06X}_256x256_raw.png")
                    render_raw_psmt4(block, 256, 256, p)

    # ========================================
    # PHASE 4: Deswizzle only the BEST candidates
    # ========================================
    print("\n" + "="*70)
    print("PHASE 4: Deswizzling best candidates")
    print("="*70)

    from psmt4_deswizzle import deswizzle_psmt4

    # Pick regions that are exactly font-atlas sized and have best stats
    best = []
    for gs, ge in groups:
        sz = ge - gs
        if sz >= 32768:  # At least 256x256
            block = exe[gs:ge]
            zr, ent, used = nibble_stats(block[:32768])
            best.append((gs, sz, zr, ent, used))

    best.sort(key=lambda x: x[3] * (1 - abs(x[2] - 0.45)), reverse=True)

    for gs, sz, zr, ent, used in best[:10]:
        print(f"\n  Deswizzling 0x{gs:06X} (size={sz}, zero={zr:.2f}, ent={ent:.2f})")

        # Try 256x256
        if sz >= 32768:
            block = exe[gs:gs+32768]
            for dbw in [256, 128, 64]:
                try:
                    px = deswizzle_psmt4(block, 256, 256, bw_psmt4=256, dbw_ct32=dbw)
                    img = Image.new('L', (256, 256))
                    img.putdata([p * 17 for p in px])
                    p = os.path.join(OUT_DIR, f"desw_0x{gs:06X}_256x256_dbw{dbw}.png")
                    img.save(p)
                    print(f"    Saved: {p}")
                except Exception as e:
                    print(f"    Error dbw={dbw}: {e}")

        # Try 256x512
        if sz >= 65536:
            block = exe[gs:gs+65536]
            for dbw in [256, 128]:
                try:
                    px = deswizzle_psmt4(block, 256, 512, bw_psmt4=256, dbw_ct32=dbw)
                    img = Image.new('L', (256, 512))
                    img.putdata([p * 17 for p in px])
                    p = os.path.join(OUT_DIR, f"desw_0x{gs:06X}_256x512_dbw{dbw}.png")
                    img.save(p)
                    print(f"    Saved: {p}")
                except Exception as e:
                    print(f"    Error dbw={dbw}: {e}")

    # ========================================
    # PHASE 5: Specifically scan around known structures
    # ========================================
    print("\n" + "="*70)
    print("PHASE 5: Known structure neighborhoods")
    print("="*70)

    # Menu structs at 0x3C3000-0x3C5300 - font data could be nearby
    # 8KB bitmap at 0x3D6C10 - SKIP that area
    # Search 0x3C5400 - 0x3D6000 (between menu structs and bitmap)
    check_ranges = [
        (0x3C5400, 0x3D6000, "Between menu structs and bitmap"),
        (0x200000, 0x220000, "Start of data section"),
        (0x3E0000, min(0x400000, len(exe)), "After bitmap area"),
    ]

    for cs, ce, label in check_ranges:
        ce = min(ce, len(exe))
        if cs >= len(exe):
            continue
        block = exe[cs:ce]
        zr, ent, used = nibble_stats(block)
        print(f"\n  {label} (0x{cs:06X}-0x{ce:06X}):")
        print(f"    zero={zr:.2f} entropy={ent:.2f} used_vals={used}")

        if len(block) >= 4096:
            # Render as 256-wide raw
            h = len(block) * 2 // 256
            if h > 0:
                p = os.path.join(OUT_DIR, f"check_0x{cs:06X}_{label.replace(' ','_')}_raw.png")
                render_raw_psmt4(block, 256, min(h, 2048), p)
                print(f"    Rendered: {p}")

    print(f"\n{'='*70}")
    print(f"DONE! All images saved to: {OUT_DIR}")
    print(f"{'='*70}")

    # List all generated files
    files = sorted(os.listdir(OUT_DIR))
    print(f"\nGenerated {len(files)} files:")
    for f in files:
        sz = os.path.getsize(os.path.join(OUT_DIR, f))
        print(f"  {f} ({sz} bytes)")

if __name__ == "__main__":
    main()
