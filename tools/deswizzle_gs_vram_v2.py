#!/usr/bin/env python3
"""
Extract and deswizzle PSMT4 textures from GS VRAM in a PCSX2 save state.
v2: Corrected header offsets and tries multiple TBW values.
"""
import os
import sys
import zipfile

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed.")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import (
    _psmt4_nibble_addr, _psmct32_word_addr,
    deswizzle_psmt4, make_rgba_image_4bit
)

GS_HEADER_SIZE = 509
VRAM_SIZE = 4 * 1024 * 1024


def extract_gs_vram(save_state_path):
    with zipfile.ZipFile(save_state_path, 'r') as z:
        gs_data = z.read('GS.bin')
    vram = gs_data[GS_HEADER_SIZE:GS_HEADER_SIZE + VRAM_SIZE]
    print(f"Extracted VRAM: {len(vram)} bytes")
    return vram


def read_psmt4_from_vram(vram, tbp0, tex_w, tex_h, bw_psmt4):
    """Read PSMT4 texture from linear VRAM at TBP0."""
    base_byte = tbp0 * 256
    base_nibble = base_byte * 2
    out = bytearray(tex_w * tex_h)
    for y in range(tex_h):
        for x in range(tex_w):
            nib_offset = _psmt4_nibble_addr(x, y, bw_psmt4)
            nib_addr = base_nibble + nib_offset
            byte_addr = nib_addr // 2
            if byte_addr < len(vram):
                byte_val = vram[byte_addr]
                if nib_addr & 1:
                    out[y * tex_w + x] = (byte_val >> 4) & 0xF
                else:
                    out[y * tex_w + x] = byte_val & 0xF
    return out


def read_psmct32_from_vram(vram, tbp0, tex_w, tex_h, tbw):
    """Read PSMCT32 texture from linear VRAM."""
    base_word = tbp0 * 64
    bw_ct32 = tbw * 64
    out = bytearray(tex_w * tex_h * 4)
    for y in range(tex_h):
        for x in range(tex_w):
            word_offset = _psmct32_word_addr(x, y, bw_ct32)
            word_addr = base_word + word_offset
            byte_addr = word_addr * 4
            if byte_addr + 4 <= len(vram):
                off = (y * tex_w + x) * 4
                out[off:off + 4] = vram[byte_addr:byte_addr + 4]
    return out


def save_grayscale(pixels, w, h, path):
    img = Image.new('L', (w, h))
    img.putdata([min(p, 15) * 17 for p in pixels[:w * h]])
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    print(f"  Saved: {path}")


def save_rgba(pixels, w, h, path):
    img = Image.new('RGBA', (w, h))
    data = []
    for i in range(w * h):
        off = i * 4
        r, g, b, a = pixels[off], pixels[off+1], pixels[off+2], pixels[off+3]
        a = min(a * 2, 255)
        data.append((r, g, b, a))
    img.putdata(data)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    print(f"  Saved: {path}")


def compare(name, a, b, n):
    matches = sum(1 for i in range(n) if a[i] == b[i])
    pct = matches / n * 100
    print(f"  {name}: {matches}/{n} match ({pct:.1f}%)")
    return pct


def main():
    save_state = os.path.join(BASE, "RAMdumps", "SearchForTheResourcesInEXE.p2s")
    out_dir = os.path.join(BASE, "debug_vram")
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 70)
    print("GS VRAM Deswizzle v2")
    print("=" * 70)

    vram = extract_gs_vram(save_state)

    # ======================================================================
    # TBP0=0x2840: R2100/R1188 range
    # R2100 sub0 is 256x256 PSMT4, and was uploaded with dbw_ct32=128
    # But in VRAM it's read as PSMT4 with TBW=4 -> bw_psmt4=256
    # ======================================================================
    print("\n--- TBP0=0x2840: R2100 area ---")
    # Try bw=128 (TBW=2) and bw=256 (TBW=4)
    for bw in [128, 256]:
        px = read_psmt4_from_vram(vram, 0x2840, 256, 256, bw)
        nz = sum(1 for p in px if p != 0)
        save_grayscale(px, 256, 256,
                        os.path.join(out_dir, f"vram_2840_bw{bw}_256x256.png"))
        print(f"    bw={bw}: {nz} non-zero")

    # ======================================================================
    # TBP0=0x3000: R1272 area (256x512 PSMT4)
    # R1272 TEX0: TBW=4 -> bw_psmt4=256
    # But maybe TBW=2 (bw=128)?
    # ======================================================================
    print("\n--- TBP0=0x3000: R1272 area ---")
    for bw in [128, 256]:
        px = read_psmt4_from_vram(vram, 0x3000, 256, 512, bw)
        nz = sum(1 for p in px if p != 0)
        save_grayscale(px, 256, 512,
                        os.path.join(out_dir, f"vram_3000_bw{bw}_256x512.png"))
        print(f"    bw={bw}: {nz} non-zero")

    # Also try 256x256 at 0x3000
    for bw in [128, 256]:
        px = read_psmt4_from_vram(vram, 0x3000, 256, 256, bw)
        save_grayscale(px, 256, 256,
                        os.path.join(out_dir, f"vram_3000_bw{bw}_256x256.png"))

    # ======================================================================
    # TBP0=0x319F
    # ======================================================================
    print("\n--- TBP0=0x319F ---")
    for bw in [128, 256]:
        px = read_psmt4_from_vram(vram, 0x319F, 256, 256, bw)
        nz = sum(1 for p in px if p != 0)
        save_grayscale(px, 256, 256,
                        os.path.join(out_dir, f"vram_319f_bw{bw}_256x256.png"))
        print(f"    bw={bw}: {nz} non-zero")

    # Also try PSMCT32 at 0x3000 with various TBW
    print("\n--- TBP0=0x3000 as PSMCT32 ---")
    for tbw in [1, 2, 4, 8]:
        w = tbw * 64
        h = min(256, 65536 // w) if w > 0 else 64
        px = read_psmct32_from_vram(vram, 0x3000, w, h, tbw)
        nz = sum(1 for i in range(w * h) for c in range(3)
                 if px[i * 4 + c] != 0)
        save_rgba(px, w, h,
                   os.path.join(out_dir, f"vram_3000_ct32_tbw{tbw}_{w}x{h}.png"))
        print(f"    TBW={tbw} ({w}x{h}): {nz} non-zero color channels")

    # Also try PSMCT32 at 0x319F
    print("\n--- TBP0=0x319F as PSMCT32 ---")
    for tbw in [1, 2, 4]:
        w = tbw * 64
        h = min(128, 32768 // w) if w > 0 else 64
        px = read_psmct32_from_vram(vram, 0x319F, w, h, tbw)
        nz = sum(1 for i in range(w * h) for c in range(3)
                 if px[i * 4 + c] != 0)
        save_rgba(px, w, h,
                   os.path.join(out_dir, f"vram_319f_ct32_tbw{tbw}_{w}x{h}.png"))
        print(f"    TBW={tbw} ({w}x{h}): {nz} non-zero color channels")

    # ======================================================================
    # Disc resource comparison
    # ======================================================================
    print("\n" + "=" * 70)
    print("DISC RESOURCE COMPARISONS")
    print("=" * 70)

    # Original R1272: 256-byte header, 65536 pixel bytes, no CLUT
    orig_r1272 = open(os.path.join(BASE, "extracted", "packdata_resources",
                                    "1272_type01.bin"), 'rb').read()
    orig_r1272_pixels = deswizzle_psmt4(orig_r1272[256:256 + 65536], 256, 512,
                                         bw_psmt4=256, dbw_ct32=256)
    save_grayscale(orig_r1272_pixels, 256, 512,
                    os.path.join(out_dir, "disc_orig_r1272.png"))

    # Build R1272: 1024-byte header, 65536 pixel bytes, 1024 CLUT
    build_r1272 = open(os.path.join(BASE, "build", "packdata_resources",
                                     "1272_type01.raw"), 'rb').read()
    build_r1272_pixels = deswizzle_psmt4(build_r1272[1024:1024 + 65536], 256, 512,
                                          bw_psmt4=256, dbw_ct32=256)
    save_grayscale(build_r1272_pixels, 256, 512,
                    os.path.join(out_dir, "disc_build_r1272.png"))

    # R2100 sub0: offset 0x500, 256x256 PSMT4, dbw_ct32=128
    build_r2100 = open(os.path.join(BASE, "build", "packdata_resources",
                                     "2100_type04.raw"), 'rb').read()
    build_r2100_sub0 = deswizzle_psmt4(build_r2100[0x500:0x500 + 32768], 256, 256,
                                        bw_psmt4=256, dbw_ct32=128)
    save_grayscale(build_r2100_sub0, 256, 256,
                    os.path.join(out_dir, "disc_build_r2100_sub0.png"))

    # Compare VRAM textures with disc
    print("\n--- R1272 comparisons (256x512) ---")
    for bw in [128, 256]:
        vram_px = read_psmt4_from_vram(vram, 0x3000, 256, 512, bw)
        compare(f"VRAM@0x3000(bw={bw}) vs Orig R1272",
                vram_px, orig_r1272_pixels, 256 * 512)
        compare(f"VRAM@0x3000(bw={bw}) vs Build R1272",
                vram_px, build_r1272_pixels, 256 * 512)

    print("\n--- R2100 sub0 comparisons (256x256) ---")
    for bw in [128, 256]:
        vram_px = read_psmt4_from_vram(vram, 0x2840, 256, 256, bw)
        compare(f"VRAM@0x2840(bw={bw}) vs Build R2100 sub0",
                vram_px, build_r2100_sub0, 256 * 256)

    # Try to find where R1272 MIGHT be in VRAM by scanning TBP0 values
    print("\n--- Scanning for R1272 in VRAM (first 256 pixels match) ---")
    # Take first 1000 non-zero pixels of original R1272 as signature
    orig_sig = orig_r1272_pixels[:256*32]  # first 32 rows
    build_sig = build_r1272_pixels[:256*32]

    best_orig_tbp = None
    best_orig_pct = 0
    best_build_tbp = None
    best_build_pct = 0

    # Scan TBP0 from 0x2800 to 0x3400 in steps of 0x10
    for tbp0 in range(0x2800, 0x3500, 0x10):
        for bw in [128, 256]:
            vram_px = read_psmt4_from_vram(vram, tbp0, 256, 32, bw)
            n = 256 * 32
            orig_m = sum(1 for i in range(n) if vram_px[i] == orig_sig[i])
            build_m = sum(1 for i in range(n) if vram_px[i] == build_sig[i])
            orig_pct = orig_m / n * 100
            build_pct = build_m / n * 100
            if orig_pct > best_orig_pct:
                best_orig_pct = orig_pct
                best_orig_tbp = (tbp0, bw)
            if build_pct > best_build_pct:
                best_build_pct = build_pct
                best_build_tbp = (tbp0, bw)

    print(f"  Best match for ORIGINAL R1272: TBP0=0x{best_orig_tbp[0]:04X} bw={best_orig_tbp[1]}, {best_orig_pct:.1f}%")
    print(f"  Best match for BUILD R1272:    TBP0=0x{best_build_tbp[0]:04X} bw={best_build_tbp[1]}, {best_build_pct:.1f}%")

    # Dump the best matches as full images
    if best_orig_pct > 20:
        tbp0, bw = best_orig_tbp
        px = read_psmt4_from_vram(vram, tbp0, 256, 512, bw)
        save_grayscale(px, 256, 512,
                        os.path.join(out_dir, f"vram_best_orig_r1272_{tbp0:04x}_bw{bw}.png"))
    if best_build_pct > 20:
        tbp0, bw = best_build_tbp
        px = read_psmt4_from_vram(vram, tbp0, 256, 512, bw)
        save_grayscale(px, 256, 512,
                        os.path.join(out_dir, f"vram_best_build_r1272_{tbp0:04x}_bw{bw}.png"))

    print("\nDone!")


if __name__ == "__main__":
    main()
