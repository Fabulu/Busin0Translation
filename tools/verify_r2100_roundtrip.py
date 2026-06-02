#!/usr/bin/env python3
"""
Verify deswizzle/reswizzle round-trip for R2100 sub-blocks.

R2100 structure in PACKDATA.DIG:
  - Starts at byte 34816 (0x8800)
  - 64-byte global header (0x40): 4 entries x 16 bytes each (sub-block index table)
  - 4 sub-blocks, each 0x8740 (34624) bytes
  - Each sub-block: GIF/VIF header (0x4C0 = 1216 bytes) + pixel data (0x8000 = 32768 bytes) + CLUT (0x280 = 640 bytes)
  - Texture format: 256x256 PSMT4 (4-bit indexed)
  - Pixel data per sub-block: 256*256/2 = 32768 bytes

Deswizzle params: dbw_ct32=128, bw_psmt4=256
"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

PACKDATA_DIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "build", "PACKDATA.DIG")

R2100_START = 34816          # byte offset of R2100 in PACKDATA.DIG
GLOBAL_HEADER_SIZE = 0x40    # 64 bytes
SUB_BLOCK_SIZE = 0x8740      # 34624 bytes per sub-block
PIXEL_OFFSET_IN_SUB = 0x4C0  # pixel data starts here within each sub-block
PIXEL_DATA_SIZE = 0x8000     # 32768 bytes = 256*256/2
CLUT_SIZE = 0x280            # 640 bytes of CLUT after pixel data

TEX_W = 256
TEX_H = 256
DBW_CT32 = 128
BW_PSMT4 = 256

# Sub-block offsets relative to R2100 start (from global header)
SUB_OFFSETS = [0x40, 0x8780, 0x10EC0, 0x19600]


def main():
    print("=" * 70)
    print("R2100 Deswizzle/Reswizzle Round-Trip Verification")
    print("=" * 70)
    print()

    with open(PACKDATA_DIG, "rb") as f:
        # Verify global header
        f.seek(R2100_START)
        ghdr = f.read(GLOBAL_HEADER_SIZE)
        print(f"R2100 start in PACKDATA.DIG: 0x{R2100_START:X} ({R2100_START})")
        print(f"Global header: {GLOBAL_HEADER_SIZE} bytes")
        print()

        # Parse and verify sub-block TOC
        print("Sub-block TOC (from global header):")
        for i in range(4):
            entry = struct.unpack("<IIII", ghdr[i*16:(i+1)*16])
            print(f"  Sub {i}: index={entry[0]}, size=0x{entry[1]:X} ({entry[1]}), "
                  f"offset=0x{entry[2]:X}, pad={entry[3]}")
        print()

        all_pass = True

        for sub_idx in range(4):
            sub_off = SUB_OFFSETS[sub_idx]
            abs_sub_off = R2100_START + sub_off
            abs_pixel_off = abs_sub_off + PIXEL_OFFSET_IN_SUB

            print(f"--- Sub-block {sub_idx} ---")
            print(f"  Sub-block offset in R2100:    0x{sub_off:X}")
            print(f"  Sub-block offset in DIG:      0x{abs_sub_off:X}")
            print(f"  Pixel offset in sub-block:    0x{PIXEL_OFFSET_IN_SUB:X}")
            print(f"  Pixel offset in R2100:        0x{sub_off + PIXEL_OFFSET_IN_SUB:X}")
            print(f"  Pixel offset in DIG:          0x{abs_pixel_off:X}")
            print(f"  Pixel data size:              0x{PIXEL_DATA_SIZE:X} ({PIXEL_DATA_SIZE} bytes)")
            print(f"  CLUT offset in sub-block:     0x{PIXEL_OFFSET_IN_SUB + PIXEL_DATA_SIZE:X}")
            print(f"  CLUT size:                    0x{CLUT_SIZE:X} ({CLUT_SIZE} bytes)")
            print(f"  Texture: {TEX_W}x{TEX_H} PSMT4")
            print(f"  dbw_ct32={DBW_CT32}, bw_psmt4={BW_PSMT4}")

            # Read pixel data
            f.seek(abs_pixel_off)
            pixel_data = f.read(PIXEL_DATA_SIZE)
            assert len(pixel_data) == PIXEL_DATA_SIZE, \
                f"Short read: got {len(pixel_data)}, expected {PIXEL_DATA_SIZE}"

            # Non-zero check
            nonzero = sum(1 for b in pixel_data if b != 0)
            print(f"  Non-zero bytes: {nonzero}/{PIXEL_DATA_SIZE} "
                  f"({100*nonzero/PIXEL_DATA_SIZE:.1f}%)")

            # Deswizzle
            linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                                     bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
            assert len(linear) == TEX_W * TEX_H

            # Reswizzle
            reswizzled = swizzle_psmt4(linear, TEX_W, TEX_H,
                                       bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

            # Compare
            orig = pixel_data[:len(reswizzled)]
            resw = reswizzled[:len(orig)]

            if resw == orig:
                print(f"  Round-trip: PASS (0 mismatches out of {len(orig)} bytes)")
            else:
                mismatches = sum(1 for a, b in zip(resw, orig) if a != b)
                print(f"  Round-trip: FAIL ({mismatches} mismatches out of {len(orig)} bytes)")
                all_pass = False
                # Show first 10 mismatches
                shown = 0
                for i, (a, b) in enumerate(zip(resw, orig)):
                    if a != b:
                        print(f"    offset 0x{i:04X}: reswizzled=0x{a:02X}, original=0x{b:02X}")
                        shown += 1
                        if shown >= 10:
                            print(f"    ... and {mismatches - shown} more")
                            break

            print()

    # Summary
    print("=" * 70)
    if all_pass:
        print("ALL 4 SUB-BLOCKS: ROUND-TRIP PASS")
        print("Safe to deswizzle, modify, and reswizzle R2100 textures.")
    else:
        print("SOME SUB-BLOCKS FAILED -- need different params!")
    print("=" * 70)

    # Print offset summary table
    print()
    print("Byte offset summary for R2100 pixel data:")
    print(f"{'Sub':>4}  {'In R2100':>12}  {'In DIG':>12}  {'Size':>10}")
    print("-" * 44)
    for sub_idx in range(4):
        sub_off = SUB_OFFSETS[sub_idx]
        pix_in_r2100 = sub_off + PIXEL_OFFSET_IN_SUB
        pix_in_dig = R2100_START + pix_in_r2100
        print(f"  {sub_idx:>2}  0x{pix_in_r2100:>08X}  0x{pix_in_dig:>08X}  {PIXEL_DATA_SIZE:>10}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
