#!/usr/bin/env python3
"""
Extract and deswizzle PSMT4 textures from GS VRAM in a PCSX2 save state.

The GS.bin in the save state has a 509-byte header, then 4MB of VRAM data
stored in PSMCT32 linear order (word address = offset from start).

To read PSMT4 textures, we use _psmt4_nibble_addr() to map texel (x,y)
to a nibble address in VRAM.
"""
import os
import sys
import zipfile
import io

# Note: don't wrap sys.stdout here, it causes issues on some platforms

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import (
    _psmt4_nibble_addr, _psmct32_word_addr,
    BLOCK_TABLE_4, COLUMN_TABLE_4, BLOCK_TABLE_32, COLUMN_TABLE_32,
    deswizzle_psmt4, make_rgba_image_4bit
)

GS_HEADER_SIZE = 509
VRAM_SIZE = 4 * 1024 * 1024  # 4MB


def extract_gs_vram(save_state_path):
    """Extract the 4MB VRAM data from GS.bin in a save state."""
    with zipfile.ZipFile(save_state_path, 'r') as z:
        gs_data = z.read('GS.bin')
    print(f"GS.bin: {len(gs_data)} bytes total")
    print(f"  Header: {GS_HEADER_SIZE} bytes")
    vram = gs_data[GS_HEADER_SIZE:GS_HEADER_SIZE + VRAM_SIZE]
    print(f"  VRAM: {len(vram)} bytes ({len(vram) / 1024 / 1024:.1f} MB)")
    return vram


def read_psmt4_from_vram(vram, tbp0, tex_w, tex_h, bw_psmt4):
    """Read a PSMT4 texture from GS VRAM at a given TBP0.

    Args:
        vram: The full 4MB VRAM buffer (PSMCT32 word-addressable)
        tbp0: Texture Base Pointer (in 256-byte blocks)
        tex_w: Texture width in pixels
        tex_h: Texture height in pixels
        bw_psmt4: PSMT4 buffer width in pixels (TBW * 64 for PSMT4)

    Returns:
        bytearray of pixel indices (one byte per pixel, 0-15)
    """
    base_byte = tbp0 * 256  # TBP0 is in 256-byte blocks
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
            # else: stays 0

    return out


def read_psmct32_from_vram(vram, tbp0, tex_w, tex_h, tbw):
    """Read a PSMCT32 texture from GS VRAM.

    Args:
        vram: Full 4MB VRAM buffer
        tbp0: Texture Base Pointer (256-byte blocks)
        tex_w, tex_h: Texture dimensions
        tbw: Buffer width in 64-pixel units

    Returns:
        bytearray of RGBA pixels (4 bytes per pixel)
    """
    base_word = tbp0 * 64  # 256 bytes / 4 bytes per word = 64 words per block
    bw_ct32 = tbw * 64  # buffer width in pixels

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


def save_grayscale_psmt4(pixels, tex_w, tex_h, out_path):
    """Save PSMT4 pixels as grayscale PNG (intensity = nibble * 17)."""
    img = Image.new('L', (tex_w, tex_h))
    img_data = [min(p, 15) * 17 for p in pixels[:tex_w * tex_h]]
    img.putdata(img_data)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    print(f"  Saved: {out_path}")
    return img


def save_psmct32_rgba(pixels, tex_w, tex_h, out_path):
    """Save PSMCT32 pixels as RGBA PNG."""
    img = Image.new('RGBA', (tex_w, tex_h))
    data = []
    for i in range(tex_w * tex_h):
        off = i * 4
        r, g, b, a = pixels[off], pixels[off+1], pixels[off+2], pixels[off+3]
        a = min(a * 2, 255)  # PS2 alpha 0-128
        data.append((r, g, b, a))
    img.putdata(data)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    print(f"  Saved: {out_path}")
    return img


def deswizzle_disc_resource(path, tex_w, tex_h, dbw_ct32, header_size, clut_size=0):
    """Deswizzle a disc resource for comparison."""
    data = open(path, 'rb').read()
    pixel_bytes = tex_w * tex_h // 2
    pixels_raw = data[header_size:header_size + pixel_bytes]
    pixels_lin = deswizzle_psmt4(pixels_raw, tex_w, tex_h,
                                  bw_psmt4=tex_w, dbw_ct32=dbw_ct32)
    return pixels_lin


def compare_textures(name, vram_pixels, disc_pixels, tex_w, tex_h):
    """Compare VRAM texture with disc texture."""
    total = tex_w * tex_h
    matches = sum(1 for a, b in zip(vram_pixels[:total], disc_pixels[:total]) if a == b)
    pct = matches / total * 100
    diff = total - matches
    print(f"  {name}: {matches}/{total} pixels match ({pct:.1f}%), {diff} differ")

    # Check if all zeros
    vram_nonzero = sum(1 for p in vram_pixels[:total] if p != 0)
    disc_nonzero = sum(1 for p in disc_pixels[:total] if p != 0)
    print(f"    VRAM non-zero pixels: {vram_nonzero}, Disc non-zero: {disc_nonzero}")

    return pct


def main():
    save_state = os.path.join(BASE, "RAMdumps", "SearchForTheResourcesInEXE.p2s")
    out_dir = os.path.join(BASE, "debug_vram")
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 70)
    print("GS VRAM PSMT4 Deswizzle from Save State")
    print("=" * 70)

    # Step 1: Extract VRAM
    print("\n--- Step 1: Extract GS VRAM ---")
    vram = extract_gs_vram(save_state)

    # Also save raw VRAM for reference
    vram_path = os.path.join(out_dir, "gs_vram.bin")
    with open(vram_path, 'wb') as f:
        f.write(vram)
    print(f"  Saved raw VRAM: {vram_path}")

    # Step 2: Read PSMT4 textures at known TBP0 addresses
    # TBW for PSMT4: TBW register value * 64 gives pixel width
    # TBW=4 means bw_psmt4 = 4 * 64 = 256

    # --- TBP0=0x2840 (R1188/R2100 range) ---
    print("\n--- TBP0=0x2840 (R1188/R2100 range, 256x256 PSMT4, bw=256) ---")
    tbp0_2840 = 0x2840
    pixels_2840 = read_psmt4_from_vram(vram, tbp0_2840, 256, 256, 256)
    save_grayscale_psmt4(pixels_2840, 256, 256,
                          os.path.join(out_dir, "vram_tbp0_2840_psmt4_256x256.png"))

    # Also try larger area
    print("\n--- TBP0=0x2840, 256x512 (full R1188 might span more) ---")
    pixels_2840_big = read_psmt4_from_vram(vram, tbp0_2840, 256, 512, 256)
    save_grayscale_psmt4(pixels_2840_big, 256, 512,
                          os.path.join(out_dir, "vram_tbp0_2840_psmt4_256x512.png"))

    # --- TBP0=0x3000 (R1272 area) ---
    print("\n--- TBP0=0x3000 (R1272 area, 256x256 PSMT4, bw=256) ---")
    tbp0_3000 = 0x3000
    pixels_3000 = read_psmt4_from_vram(vram, tbp0_3000, 256, 256, 256)
    save_grayscale_psmt4(pixels_3000, 256, 256,
                          os.path.join(out_dir, "vram_tbp0_3000_psmt4_256x256.png"))

    # Also try 256x512 (R1272 is 256x512)
    print("\n--- TBP0=0x3000, 256x512 (R1272 full size) ---")
    pixels_3000_full = read_psmt4_from_vram(vram, tbp0_3000, 256, 512, 256)
    save_grayscale_psmt4(pixels_3000_full, 256, 512,
                          os.path.join(out_dir, "vram_tbp0_3000_psmt4_256x512.png"))

    # Also try reading as PSMCT32 (since status says stat labels drawn as PSMCT32 64x32 strips)
    print("\n--- TBP0=0x3000 as PSMCT32, 256x128 (render target?) ---")
    pixels_3000_ct32 = read_psmct32_from_vram(vram, tbp0_3000, 256, 128, 4)
    save_psmct32_rgba(pixels_3000_ct32, 256, 128,
                       os.path.join(out_dir, "vram_tbp0_3000_psmct32_256x128.png"))

    # --- TBP0=0x319F ---
    print("\n--- TBP0=0x319F (HP labels, 256x256 PSMT4, bw=256) ---")
    tbp0_319f = 0x319F
    pixels_319f = read_psmt4_from_vram(vram, tbp0_319f, 256, 256, 256)
    save_grayscale_psmt4(pixels_319f, 256, 256,
                          os.path.join(out_dir, "vram_tbp0_319f_psmt4_256x256.png"))

    # Also as PSMCT32 for 319F (64x16 and 48x20 strips)
    print("\n--- TBP0=0x319F as PSMCT32, 128x64 ---")
    pixels_319f_ct32 = read_psmct32_from_vram(vram, tbp0_319f, 128, 64, 2)
    save_psmct32_rgba(pixels_319f_ct32, 128, 64,
                       os.path.join(out_dir, "vram_tbp0_319f_psmct32_128x64.png"))

    # Step 3: Compare with disc resources
    print("\n" + "=" * 70)
    print("COMPARISON WITH DISC RESOURCES")
    print("=" * 70)

    # Original R1272 from extracted/
    orig_r1272_path = os.path.join(BASE, "extracted", "packdata_resources", "1272_type01.bin")
    # Build R1272
    build_r1272_path = os.path.join(BASE, "build", "packdata_resources", "1272_type01.raw")

    if os.path.exists(orig_r1272_path):
        print("\n--- Original R1272 (extracted) ---")
        orig_data = open(orig_r1272_path, 'rb').read()
        print(f"  File size: {len(orig_data)} bytes")
        # R1272: 256x512 PSMT4, header varies. Try finding pixel data.
        # type01 bin: usually has sub-header + offset table
        # Let's check the header
        print(f"  First 32 bytes: {orig_data[:32].hex()}")
        # Typical R1272: 1024 header + 65536 pixels + 1024 CLUT = 67584 or similar
        # Try 0x400 header
        orig_pixels = deswizzle_psmt4(orig_data[0x400:0x400 + 65536], 256, 512,
                                       bw_psmt4=256, dbw_ct32=256)
        save_grayscale_psmt4(orig_pixels, 256, 512,
                              os.path.join(out_dir, "disc_orig_r1272_256x512.png"))
        # Compare first 256x256 region with VRAM at 0x3000
        compare_textures("VRAM@0x3000 vs OrigR1272 (256x256)",
                         pixels_3000, orig_pixels, 256, 256)
        compare_textures("VRAM@0x3000 vs OrigR1272 (256x512)",
                         pixels_3000_full, orig_pixels, 256, 512)

    if os.path.exists(build_r1272_path):
        print("\n--- Build R1272 (our English version) ---")
        build_data = open(build_r1272_path, 'rb').read()
        print(f"  File size: {len(build_data)} bytes")
        print(f"  First 32 bytes: {build_data[:32].hex()}")
        # .raw format: 16 byte outer + inner data
        # Try several header sizes
        for hdr in [0x400, 0x410, 0x000]:
            remain = len(build_data) - hdr
            if remain >= 65536:
                build_pixels = deswizzle_psmt4(build_data[hdr:hdr + 65536], 256, 512,
                                                bw_psmt4=256, dbw_ct32=256)
                nz = sum(1 for p in build_pixels if p != 0)
                print(f"  Header=0x{hdr:x}: {nz} non-zero pixels")
                if nz > 1000:
                    save_grayscale_psmt4(build_pixels, 256, 512,
                                          os.path.join(out_dir, f"disc_build_r1272_hdr{hdr:x}_256x512.png"))
                    compare_textures(f"VRAM@0x3000 vs BuildR1272 (hdr=0x{hdr:x}, 256x512)",
                                     pixels_3000_full, build_pixels, 256, 512)
                    break

    # Also try R2100 comparisons
    # R2100 sub-block 0 at offset 0x500 in the resource
    orig_r2100_path = os.path.join(BASE, "extracted", "packdata_resources", "2100_type04.bin")
    build_r2100_path = os.path.join(BASE, "build", "packdata_resources", "2100_type04.raw")

    for label, path in [("Original R2100", orig_r2100_path), ("Build R2100", build_r2100_path)]:
        if os.path.exists(path):
            print(f"\n--- {label} sub0 (256x256 PSMT4) ---")
            data = open(path, 'rb').read()
            print(f"  File size: {len(data)} bytes")
            # Sub 0 pixels at 0x500, 256x256 PSMT4, dbw_ct32=128
            if len(data) > 0x500 + 32768:
                sub0_pixels = deswizzle_psmt4(data[0x500:0x500 + 32768], 256, 256,
                                               bw_psmt4=256, dbw_ct32=128)
                save_grayscale_psmt4(sub0_pixels, 256, 256,
                                      os.path.join(out_dir, f"disc_{label.lower().replace(' ','_')}_sub0.png"))
                compare_textures(f"VRAM@0x2840 vs {label} sub0",
                                 pixels_2840, sub0_pixels, 256, 256)

    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY: Non-zero pixel counts in VRAM textures")
    print("=" * 70)
    for name, pix, w, h in [
        ("TBP0=0x2840 256x256", pixels_2840, 256, 256),
        ("TBP0=0x3000 256x256", pixels_3000, 256, 256),
        ("TBP0=0x3000 256x512", pixels_3000_full, 256, 512),
        ("TBP0=0x319F 256x256", pixels_319f, 256, 256),
    ]:
        nz = sum(1 for p in pix[:w*h] if p != 0)
        total = w * h
        print(f"  {name}: {nz}/{total} non-zero ({nz/total*100:.1f}%)")

    print("\nDone! Check debug_vram/ for PNG outputs.")


if __name__ == "__main__":
    main()
