#!/usr/bin/env python3
"""
Extract the PSMT4 texture at TBP0=0x2A68 from VRAM and find its disc source.

Uses the proven PCSX2-sourced deswizzle tables from psmt4_deswizzle.py.
"""
import os
import sys
import struct
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import (
    _psmt4_nibble_addr, _psmct32_word_addr, deswizzle_psmt4,
    BLOCK_TABLE_4, COLUMN_TABLE_4
)

try:
    from PIL import Image
except ImportError:
    print("Need Pillow"); sys.exit(1)

GS_HEADER = 509
VRAM_SIZE = 4 * 1024 * 1024


def read_psmt4_from_vram(vram, tbp0, tex_w, tex_h, bw_psmt4):
    """Read PSMT4 texture from VRAM at TBP0 using correct addressing."""
    base_byte = tbp0 * 256
    base_nibble = base_byte * 2
    out = bytearray(tex_w * tex_h)
    for y in range(tex_h):
        for x in range(tex_w):
            nib_offset = _psmt4_nibble_addr(x, y, bw_psmt4)
            nib_addr = base_nibble + nib_offset
            byte_addr = nib_addr // 2
            if byte_addr < len(vram):
                bv = vram[byte_addr]
                if nib_addr & 1:
                    out[y * tex_w + x] = (bv >> 4) & 0xF
                else:
                    out[y * tex_w + x] = bv & 0xF
    return out


def read_clut_ct16(vram, cbp, n=16):
    """Read PSMCT16 CLUT from VRAM."""
    base = cbp * 256
    clut = []
    for i in range(n):
        off = base + i * 2
        if off + 1 < len(vram):
            val = struct.unpack_from('<H', vram, off)[0]
            r = (val & 0x1F) << 3
            g = ((val >> 5) & 0x1F) << 3
            b = ((val >> 10) & 0x1F) << 3
            a = 255 if (val >> 15) else 0
            clut.append((r, g, b, a))
        else:
            clut.append((0, 0, 0, 0))
    return clut


def save_grayscale(pixels, w, h, path, invert=False):
    img = Image.new('L', (w, h))
    for y in range(h):
        for x in range(w):
            v = pixels[y * w + x] * 17
            if invert:
                v = 255 - v
            img.putpixel((x, y), v)
    img.save(path)
    return img


def compare_raw_bytes(name, vram_raw, candidate, length):
    """Compare raw VRAM bytes with candidate data."""
    clen = min(length, len(candidate), len(vram_raw))
    matches = sum(1 for i in range(clen) if vram_raw[i] == candidate[i])
    pct = matches / clen * 100 if clen > 0 else 0
    if pct > 50:
        print(f"  {name}: {matches}/{clen} bytes match ({pct:.1f}%)")
    return pct


def compare_pixels(name, pix_a, pix_b, total):
    """Compare deswizzled pixel arrays."""
    clen = min(total, len(pix_a), len(pix_b))
    matches = sum(1 for i in range(clen) if pix_a[i] == pix_b[i])
    pct = matches / clen * 100 if clen > 0 else 0
    nz_a = sum(1 for p in pix_a[:clen] if p != 0)
    nz_b = sum(1 for p in pix_b[:clen] if p != 0)
    if pct > 30 or nz_a > 100:
        print(f"  {name}: {matches}/{clen} match ({pct:.1f}%), nz_a={nz_a} nz_b={nz_b}")
    return pct


def main():
    out_dir = os.path.join(BASE, "debug_vram")
    os.makedirs(out_dir, exist_ok=True)

    # Load VRAM
    gs_path = os.path.join(BASE, "RAMdumps", "GS.bin")
    if not os.path.exists(gs_path):
        save_state = os.path.join(BASE, "RAMdumps", "SearchForTheResourcesInEXE.p2s")
        with zipfile.ZipFile(save_state, 'r') as z:
            z.extract('GS.bin', os.path.join(BASE, "RAMdumps"))

    with open(gs_path, 'rb') as f:
        data = f.read()
    vram = data[GS_HEADER:]
    print(f"VRAM: {len(vram)} bytes")

    # ====== Extract TBP0=0x2A68 ======
    TBP0 = 0x2A68
    TBW = 4
    W, H = 256, 256
    CBP = 0x2AE9
    bw_psmt4 = TBW * 64  # 256

    print(f"\n=== Extracting PSMT4 at TBP0=0x{TBP0:X}, {W}x{H}, TBW={TBW} ===")
    print(f"VRAM byte range: 0x{TBP0*256:X} - 0x{(TBP0*256 + W*H//2):X}")

    pixels = read_psmt4_from_vram(vram, TBP0, W, H, bw_psmt4)
    nz = sum(1 for p in pixels if p != 0)
    print(f"Non-zero pixels: {nz}/{W*H} ({nz/W/H*100:.1f}%)")
    print(f"Used indices: {sorted(set(pixels))}")

    # Save images
    save_grayscale(pixels, W, H, os.path.join(out_dir, "vram_2A68_psmt4.png"))
    save_grayscale(pixels, W, H, os.path.join(out_dir, "vram_2A68_psmt4_inv.png"), invert=True)
    print(f"Saved: debug_vram/vram_2A68_psmt4.png and _inv.png")

    # Save raw VRAM bytes at this address for comparison
    vram_base = TBP0 * 256
    vram_raw = vram[vram_base:vram_base + W * H // 2]  # 32768 bytes for 256x256 PSMT4
    with open(os.path.join(out_dir, "vram_2A68_raw.bin"), 'wb') as f:
        f.write(vram_raw)
    print(f"Raw VRAM bytes: {len(vram_raw)} at offset 0x{vram_base:X}")

    # Also extract a wider view - try 256x512 in case it's part of a larger texture
    pixels_512 = read_psmt4_from_vram(vram, TBP0, W, 512, bw_psmt4)
    save_grayscale(pixels_512, W, 512, os.path.join(out_dir, "vram_2A68_psmt4_256x512.png"))

    # Read CLUT
    clut = read_clut_ct16(vram, CBP)
    print(f"\nCLUT at CBP=0x{CBP:X}:")
    for i, c in enumerate(clut):
        print(f"  [{i:2d}] {c}")

    # ====== Search PACKDATA resources ======
    print("\n" + "=" * 70)
    print("SEARCHING PACKDATA RESOURCES FOR MATCHING DATA")
    print("=" * 70)

    res_dir = os.path.join(BASE, "extracted", "packdata_resources")
    if not os.path.isdir(res_dir):
        print(f"Resource dir not found: {res_dir}")
        return

    # Strategy 1: Raw byte comparison with VRAM data
    # The texture data in VRAM is stored in PSMCT32-swizzled format since the GS
    # stores everything in its native page/block format.
    # But disc resources are also in PSMCT32-upload format!
    # So we should compare the raw VRAM bytes with resource pixel data directly.

    # Get first 256 bytes from VRAM as a search signature
    sig = vram_raw[:256]
    sig_64 = vram_raw[:64]

    best_matches = []

    files = sorted(os.listdir(res_dir))
    print(f"Scanning {len(files)} resources...")

    for fname in files:
        fpath = os.path.join(res_dir, fname)
        try:
            fdata = open(fpath, 'rb').read()
        except:
            continue

        if len(fdata) < 64:
            continue

        # Try to find the VRAM signature anywhere in the file
        idx = fdata.find(sig_64)
        if idx >= 0:
            # Check how much matches from this point
            match_len = 0
            for i in range(min(len(vram_raw), len(fdata) - idx)):
                if vram_raw[i] == fdata[idx + i]:
                    match_len += 1
            pct = match_len / len(vram_raw) * 100
            if pct > 10:
                print(f"  ** {fname}: sig found at offset 0x{idx:X}, {match_len}/{len(vram_raw)} bytes match ({pct:.1f}%)")
                best_matches.append((pct, fname, idx, match_len))

    # Strategy 2: Deswizzle known texture resources and compare pixels
    print("\n--- Pixel-level comparison with known textures ---")

    # R1272 (256x512 PSMT4, main font)
    r1272_path = os.path.join(res_dir, "1272_type01.bin")
    if os.path.exists(r1272_path):
        r1272_data = open(r1272_path, 'rb').read()
        # Header is typically 0x400 for type01 textures
        for hdr in [0x400, 0x000, 0x200, 0x800]:
            pixel_data = r1272_data[hdr:hdr + 65536]
            if len(pixel_data) >= 65536:
                r1272_pix = deswizzle_psmt4(pixel_data, 256, 512, bw_psmt4=256, dbw_ct32=256)
                # Compare first 256x256 with our VRAM texture
                pct = compare_pixels(f"R1272 (hdr=0x{hdr:X}, 256x256)", pixels, r1272_pix, W * H)
                if pct > 80:
                    print(f"    >>> MATCH! R1272 at header 0x{hdr:X}")

    # R1188 (1024x1024 PSMT4, name entry)
    r1188_path = os.path.join(res_dir, "1188_type01.bin")
    if os.path.exists(r1188_path):
        r1188_data = open(r1188_path, 'rb').read()
        for hdr in [0xC00, 0x400, 0x000]:
            pixel_data = r1188_data[hdr:hdr + 524288]
            if len(pixel_data) >= 32768:  # at least 256x256
                r1188_pix = deswizzle_psmt4(pixel_data[:524288], 1024, 1024,
                                             bw_psmt4=1024, dbw_ct32=512)
                # Compare 256x256 sub-regions
                for sy in range(0, 1024, 256):
                    for sx in range(0, 1024, 256):
                        sub = bytearray(W * H)
                        for y in range(H):
                            for x in range(W):
                                sub[y * W + x] = r1188_pix[(sy + y) * 1024 + (sx + x)]
                        nz_sub = sum(1 for p in sub if p != 0)
                        if nz_sub > 100:
                            pct = compare_pixels(
                                f"R1188 (hdr=0x{hdr:X}) region ({sx},{sy})",
                                pixels, sub, W * H)
                            if pct > 80:
                                print(f"    >>> MATCH! R1188 at ({sx},{sy})")

    # R2100 sub-blocks
    r2100_path = os.path.join(res_dir, "2100_type04.bin")
    if os.path.exists(r2100_path):
        r2100_data = open(r2100_path, 'rb').read()
        # R2100 has multiple sub-blocks, try each one as 256x256 PSMT4
        for hdr_name, hdr, dbw in [("sub0", 0x500, 128), ("sub0", 0x500, 256),
                                     ("raw@0", 0, 128), ("raw@0", 0, 256)]:
            pixel_data = r2100_data[hdr:hdr + 32768]
            if len(pixel_data) >= 32768:
                r2100_pix = deswizzle_psmt4(pixel_data, 256, 256,
                                             bw_psmt4=256, dbw_ct32=dbw)
                compare_pixels(f"R2100 {hdr_name} dbw={dbw}", pixels, r2100_pix, W * H)

    # Strategy 3: Search EE memory (the EXE)
    print("\n--- Searching EE memory (EXE) ---")
    ee_path = os.path.join(BASE, "RAMdumps", "eeMemory.bin")
    if os.path.exists(ee_path):
        ee_data = open(ee_path, 'rb').read()
        print(f"EE memory: {len(ee_data)} bytes")

        # Search for the first 64 bytes of VRAM data in EE memory
        idx = ee_data.find(sig_64)
        if idx >= 0:
            match_len = sum(1 for i in range(min(len(vram_raw), len(ee_data) - idx))
                          if vram_raw[i] == ee_data[idx + i])
            print(f"  ** Found sig at EE offset 0x{idx:X}, {match_len} bytes match")
        else:
            print("  First 64 bytes of VRAM not found in EE memory")

        # Also try smaller signatures
        for sig_len in [32, 16, 8]:
            small_sig = vram_raw[:sig_len]
            idx = ee_data.find(small_sig)
            if idx >= 0:
                print(f"  {sig_len}-byte sig found at EE offset 0x{idx:X}")

    # Strategy 4: Brute-force compare raw VRAM bytes with ALL resources
    # (looking for the PSMCT32-upload-format data that produces this VRAM state)
    print("\n--- Brute-force raw byte search in all resources ---")
    # Try various 32-byte chunks from VRAM at different offsets
    for chunk_off in [0, 256, 512, 1024, 4096]:
        chunk = vram_raw[chunk_off:chunk_off + 32]
        if len(chunk) < 32:
            continue
        for fname in files:
            fpath = os.path.join(res_dir, fname)
            try:
                fdata = open(fpath, 'rb').read()
            except:
                continue
            idx = fdata.find(chunk)
            if idx >= 0:
                print(f"  VRAM[0x{chunk_off:X}:+32] found in {fname} at offset 0x{idx:X}")

    # Summary
    print("\n" + "=" * 70)
    print("BEST RAW MATCHES:")
    print("=" * 70)
    best_matches.sort(reverse=True)
    for pct, fname, idx, match_len in best_matches[:10]:
        print(f"  {pct:.1f}% - {fname} at offset 0x{idx:X} ({match_len} bytes)")

    if not best_matches:
        print("  No significant raw byte matches found in PACKDATA resources.")
        print("  This suggests the texture may be:")
        print("    1. Dynamically generated/composed at runtime")
        print("    2. Stored in the EXE and DMA'd to VRAM")
        print("    3. Computed from multiple source resources")

    print("\nDone!")


if __name__ == '__main__':
    main()
