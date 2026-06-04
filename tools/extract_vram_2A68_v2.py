#!/usr/bin/env python3
"""
Extract TBP0=0x2A68 from VRAM and compare with R1188 sub-regions.

Key insight from gs_vram_analysis.md:
- R1188 is a 1024x1024 PSMT4 atlas uploaded as multiple 256x256 tiles
- TBP0=0x2840 = first tile (confirmed R1188 content)
- TBP0=0x2A68 = "additional kanji tile (page 339)" = R1188 page 2
- Each tile: 256x256 PSMT4, TBW=4, CLUT at TBP0+0x80

The tiles from gs_vram_analysis.md (different save state but same game):
  0x2840, 0x28CA, 0x2954, 0x29DE, 0x2A68(?), 0x2B08, 0x2BA4, 0x2C34, 0x2CC4, 0x2D56

Strategy: Since R1188 is deswizzled by writing to VRAM via PSMCT32 then reading as PSMT4,
the data in the GS.bin VRAM dump is ALREADY in the GS's native storage format.
To read it correctly, we need _psmt4_nibble_addr which gives us the nibble
offset in the native VRAM word array.

But wait - the PCSX2 GS.bin dump stores VRAM as a flat array of bytes.
The question is: does it store bytes in linear order (byte 0, byte 1, ...),
or in PSMCT32 word order?

From PCSX2 source: GS VRAM is stored as a flat 4MB byte array indexed by
byte address. When the GS renders, it uses the swizzle tables to map
(page, block, column, pixel) to byte addresses. So GS.bin IS just the
raw byte array.

So _psmt4_nibble_addr(x, y, bw) gives us nibble index in this flat array.
For a texture at TBP0, the base nibble is TBP0 * 256 * 2 = TBP0 * 512.
"""
import os
import sys
import struct

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import _psmt4_nibble_addr, deswizzle_psmt4

from PIL import Image

GS_HEADER = 509


def read_psmt4_from_vram(vram, tbp0, w, h, bw):
    """Read PSMT4 texture from GS VRAM flat byte array."""
    base_nibble = tbp0 * 512  # TBP0 * 256 bytes * 2 nibbles/byte
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            nib_off = _psmt4_nibble_addr(x, y, bw)
            nib = base_nibble + nib_off
            byte_addr = nib // 2
            if byte_addr < len(vram):
                bv = vram[byte_addr]
                if nib & 1:
                    out[y * w + x] = (bv >> 4) & 0xF
                else:
                    out[y * w + x] = bv & 0xF
    return out


def save_img(pixels, w, h, path, invert=False):
    img = Image.new('L', (w, h))
    data = []
    for p in pixels[:w*h]:
        v = p * 17
        if invert:
            v = 255 - v
        data.append(v)
    img.putdata(data)
    img.save(path)
    return img


def main():
    out_dir = os.path.join(BASE, "debug_vram")
    os.makedirs(out_dir, exist_ok=True)

    # Load VRAM
    with open(os.path.join(BASE, "RAMdumps", "GS.bin"), 'rb') as f:
        data = f.read()
    vram = data[GS_HEADER:]
    print(f"VRAM: {len(vram)} bytes")

    # ====================================================
    # Part 1: Extract all known R1188 tiles from VRAM
    # ====================================================
    # From gs_vram_analysis.md tile list
    tile_tbp0s = [0x2840, 0x28CA, 0x2954, 0x29DE, 0x2A68, 0x2B08, 0x2BA4, 0x2C34, 0x2CC4, 0x2D56]

    print("\n=== Extracting all R1188 tiles from VRAM ===")
    tile_pixels = {}
    for tbp0 in tile_tbp0s:
        pix = read_psmt4_from_vram(vram, tbp0, 256, 256, 256)
        nz = sum(1 for p in pix if p != 0)
        path = os.path.join(out_dir, f"r1188_tile_{tbp0:04X}.png")
        save_img(pix, 256, 256, path, invert=True)
        tile_pixels[tbp0] = pix
        print(f"  TBP0=0x{tbp0:04X}: {nz} non-zero pixels -> {path}")

    # ====================================================
    # Part 2: Deswizzle R1188 from disc and compare sub-regions
    # ====================================================
    print("\n=== Deswizzling R1188 from disc ===")
    r1188_path = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
    r1188_data = open(r1188_path, 'rb').read()
    print(f"R1188 file: {len(r1188_data)} bytes")

    # R1188: 1024x1024 PSMT4, header=0xC00, dbw_ct32=512
    hdr = 0xC00
    pixel_bytes = 1024 * 1024 // 2  # 524288
    pixel_data = r1188_data[hdr:hdr + pixel_bytes]
    print(f"Pixel data: {len(pixel_data)} bytes from offset 0x{hdr:X}")

    r1188_full = deswizzle_psmt4(pixel_data, 1024, 1024, bw_psmt4=1024, dbw_ct32=512)
    print(f"Deswizzled R1188: {len(r1188_full)} pixels")

    # Save full R1188 for reference
    save_img(r1188_full, 1024, 1024, os.path.join(out_dir, "r1188_full_disc.png"), invert=True)

    # ====================================================
    # Part 3: Compare each VRAM tile with R1188 sub-regions
    # ====================================================
    print("\n=== Comparing VRAM tiles with R1188 sub-regions ===")

    # R1188 is 1024x1024 = 4x4 grid of 256x256 tiles
    # Tile positions: (col*256, row*256) for col,row in 0..3
    disc_tiles = {}
    for row in range(4):
        for col in range(4):
            sx, sy = col * 256, row * 256
            tile = bytearray(256 * 256)
            for y in range(256):
                for x in range(256):
                    tile[y * 256 + x] = r1188_full[(sy + y) * 1024 + (sx + x)]
            disc_tiles[(col, row)] = tile

    for tbp0, vpix in tile_pixels.items():
        best_pct = 0
        best_pos = None
        for (col, row), dpix in disc_tiles.items():
            total = 256 * 256
            matches = sum(1 for i in range(total) if vpix[i] == dpix[i])
            pct = matches / total * 100
            if pct > best_pct:
                best_pct = pct
                best_pos = (col, row)
        print(f"  TBP0=0x{tbp0:04X}: best match = R1188 tile ({best_pos[0]},{best_pos[1]}) at {best_pct:.1f}%")

    # ====================================================
    # Part 4: Focus on TBP0=0x2A68 - detailed analysis
    # ====================================================
    print("\n=== Detailed analysis of TBP0=0x2A68 ===")
    target = tile_pixels[0x2A68]
    nz = sum(1 for p in target if p != 0)
    print(f"Non-zero pixels: {nz}/{256*256}")
    print(f"Used indices: {sorted(set(target))}")

    # Check ALL disc tiles with more detail
    print("\nDetailed comparison with all R1188 sub-regions:")
    for row in range(4):
        for col in range(4):
            dpix = disc_tiles[(col, row)]
            total = 256 * 256
            matches = sum(1 for i in range(total) if target[i] == dpix[i])
            nz_disc = sum(1 for p in dpix if p != 0)
            pct = matches / total * 100
            print(f"  R1188[{col},{row}] ({col*256},{row*256}): {matches}/{total} = {pct:.1f}%  (disc nz={nz_disc})")

    # ====================================================
    # Part 5: Check if it's a DIFFERENT resource entirely
    # ====================================================
    print("\n=== Searching ALL packdata resources ===")
    res_dir = os.path.join(BASE, "extracted", "packdata_resources")

    # Get the raw VRAM bytes at TBP0=0x2A68 for byte-level search
    vram_offset = 0x2A68 * 256
    raw_vram = vram[vram_offset:vram_offset + 32768]  # 256x256 PSMT4 = 32KB

    # Try to find these exact bytes in any resource
    # Use 128-byte signature from the start
    sig128 = raw_vram[:128]
    sig32 = raw_vram[:32]

    print(f"Searching for 128-byte VRAM signature starting at 0x{vram_offset:X}")
    print(f"Sig: {sig128[:16].hex()}...")

    files = sorted(os.listdir(res_dir))
    found_128 = []
    found_32 = []

    for fname in files:
        fpath = os.path.join(res_dir, fname)
        try:
            fdata = open(fpath, 'rb').read()
        except:
            continue
        if len(fdata) < 128:
            continue

        idx128 = fdata.find(sig128)
        if idx128 >= 0:
            found_128.append((fname, idx128))
            continue

        idx32 = fdata.find(sig32)
        if idx32 >= 0:
            found_32.append((fname, idx32))

    if found_128:
        print(f"\n128-byte signature matches:")
        for fname, idx in found_128:
            print(f"  {fname} at offset 0x{idx:X}")
            # Check how much of the 32KB matches
            fdata = open(os.path.join(res_dir, fname), 'rb').read()
            match_bytes = sum(1 for i in range(min(len(raw_vram), len(fdata) - idx))
                            if raw_vram[i] == fdata[idx + i])
            print(f"    Total match: {match_bytes}/{len(raw_vram)} bytes ({match_bytes/len(raw_vram)*100:.1f}%)")
    else:
        print("\nNo 128-byte signature matches found.")

    if found_32:
        print(f"\n32-byte signature matches:")
        for fname, idx in found_32[:20]:
            print(f"  {fname} at offset 0x{idx:X}")

    # ====================================================
    # Part 6: Check EE RAM (EXE region and beyond)
    # ====================================================
    print("\n=== Searching EE RAM ===")
    ee_path = os.path.join(BASE, "RAMdumps", "eeMemory.bin")
    ee_data = open(ee_path, 'rb').read()

    # Search for 128-byte signature
    idx = ee_data.find(sig128)
    if idx >= 0:
        print(f"128-byte VRAM sig found at EE 0x{idx:X}")
        match_bytes = sum(1 for i in range(min(len(raw_vram), len(ee_data) - idx))
                        if raw_vram[i] == ee_data[idx + i])
        print(f"  Total match: {match_bytes}/{len(raw_vram)} bytes ({match_bytes/len(raw_vram)*100:.1f}%)")
    else:
        print("128-byte sig NOT found in EE RAM")

    # Search for 32-byte sig
    idx = ee_data.find(sig32)
    if idx >= 0:
        print(f"32-byte VRAM sig found at EE 0x{idx:X}")
    else:
        print("32-byte sig NOT found in EE RAM")

    # Search for 16-byte sig
    sig16 = raw_vram[:16]
    idx = ee_data.find(sig16)
    if idx >= 0:
        print(f"16-byte VRAM sig found at EE 0x{idx:X}")
        # Check how far the match extends
        match_len = 0
        while idx + match_len < len(ee_data) and match_len < len(raw_vram):
            if raw_vram[match_len] == ee_data[idx + match_len]:
                match_len += 1
            else:
                break
        print(f"  Continuous match: {match_len} bytes")
    else:
        print("16-byte sig NOT found in EE RAM")

    # ====================================================
    # Part 7: Is the data at 0x2A68 part of a PSMCT32 upload?
    # ====================================================
    # The raw VRAM bytes are in the GS's native format.
    # When data is uploaded via GIF IMAGE transfer, the host sends
    # pixels in raster order and the GS writes them using PSMCT32 swizzle.
    # So the stored bytes are PSMCT32-swizzled.
    #
    # To find the original upload data, we need to UN-swizzle from PSMCT32 format.
    # Then search for THAT data in resources.

    from psmt4_deswizzle import _psmct32_word_addr

    # Read the 32KB at TBP0=0x2A68 and un-swizzle as PSMCT32
    # For PSMCT32: each page is 64x32 pixels (each pixel = 4 bytes = 1 word)
    # TBW for the upload... we need to figure this out.
    # For R1188: dbw_ct32=512 pixels (TBW=8 in PSMCT32 terms)

    print("\n=== Reverse PSMCT32 unswizzle of VRAM at 0x2A68 ===")

    # The PSMT4 256x256 texture occupies 32768 bytes in VRAM.
    # In PSMCT32 terms, 32768 bytes = 8192 words = 128x64 or 256x32 etc.
    # For R1188 upload with dbw_ct32=512: 32768 bytes = 512 * (32768/(512*4)) = 512*16 pixels

    # Actually, let's try a different approach:
    # Read PSMT4 from VRAM -> get linear pixels -> re-swizzle to PSMCT32 upload format
    # Then search for THAT in resources

    from psmt4_deswizzle import swizzle_psmt4

    # We already have the deswizzled pixels (target = tile_pixels[0x2A68])
    # Re-swizzle back to PSMCT32 upload format
    for dbw in [128, 256, 512]:
        upload_data = swizzle_psmt4(target, 256, 256, bw_psmt4=256, dbw_ct32=dbw)
        print(f"\n  dbw_ct32={dbw}: upload data = {len(upload_data)} bytes")

        # Search for first 128 bytes of upload data in R1188
        up_sig = upload_data[:128]
        idx = r1188_data.find(up_sig)
        if idx >= 0:
            print(f"  *** FOUND in R1188 at offset 0x{idx:X}!")
            match_bytes = sum(1 for i in range(min(len(upload_data), len(r1188_data) - idx))
                            if upload_data[i] == r1188_data[idx + i])
            print(f"  Match: {match_bytes}/{len(upload_data)} bytes ({match_bytes/len(upload_data)*100:.1f}%)")
        else:
            # Try in EE RAM
            idx = ee_data.find(up_sig)
            if idx >= 0:
                print(f"  Found in EE RAM at 0x{idx:X}")
                match_bytes = sum(1 for i in range(min(len(upload_data), len(ee_data) - idx))
                                if upload_data[i] == ee_data[idx + i])
                print(f"  Match: {match_bytes}/{len(upload_data)} bytes ({match_bytes/len(upload_data)*100:.1f}%)")
            else:
                print(f"  NOT found in R1188 or EE RAM")

        # Also search all resources
        up_sig32 = upload_data[:32]
        for fname in files:
            fpath = os.path.join(res_dir, fname)
            try:
                fdata = open(fpath, 'rb').read()
            except:
                continue
            idx = fdata.find(up_sig)
            if idx >= 0:
                match_bytes = sum(1 for i in range(min(len(upload_data), len(fdata) - idx))
                                if upload_data[i] == fdata[idx + i])
                pct = match_bytes / len(upload_data) * 100
                if pct > 50:
                    print(f"  *** FOUND in {fname} at 0x{idx:X}: {match_bytes}/{len(upload_data)} = {pct:.1f}%")


    print("\nDone!")


if __name__ == '__main__':
    main()
