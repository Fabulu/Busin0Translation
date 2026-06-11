#!/usr/bin/env python3
"""
Diagnostic ISO A: R2100 with ONLY gender patches (sub2 row10 col0/col1).
All other sub1/sub2 cells are ORIGINAL (unpatched).
Sub0 retains original ASCII keyboard data (no F/M ASCII patches either).

Start from latest translated build, then REPLACE R2100 in the ISO header
with a version that has only gender symbols patched.

If F/M disappear: the gender patches in sub2 row10 ARE the cause.
If F/M appear:    something else in the full patch set destroys them.
"""

import os, sys, struct, shutil, math

BASE = r"C:\Programmieren\wizardrytranslation"
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

SRC_ISO = os.path.join(BASE, "build", "BUSIN0_EN_v55.iso")
DST_ISO = os.path.join(BASE, "build", "BUSIN0_DIAG_r2100_gender_only.iso")
DIG_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")

SECTOR = 2048
PACKDATA_SECTOR = 16029
R2100_HEADER_OFFSET = 17  # sectors into PACKDATA header
R2100_ISO_OFFSET = (PACKDATA_SECTOR + R2100_HEADER_OFFSET) * SECTOR

# R2100 structure
TOC_ENTRIES = 2883
R2100_TOC_INDEX = 2100
NUM_SUBS = 4
SUB_SIZE = 34624      # 0x8740
HDR_SIZE = 0x4C0
PIXEL_SIZE = 32768
TAIL_SIZE = 640
TEX_W, TEX_H = 256, 256
CELL_W, CELL_H = 16, 16
DBW_CT32 = 128
BW_PSMT4 = 256

def render_gender_symbol(symbol_name):
    """Same as patch_r2100.py — render male/female symbol."""
    pixels = [15] * (CELL_W * CELL_H)
    def put(x, y):
        if 0 <= x < CELL_W and 0 <= y < CELL_H:
            pixels[y * CELL_W + x] = 0
    if symbol_name == "male":
        cx, cy, r = 6, 9, 4
        for angle_step in range(360):
            rad = math.radians(angle_step)
            rx = round(cx + r * math.cos(rad))
            ry = round(cy + r * math.sin(rad))
            put(rx, ry)
        for i in range(9):
            t = i / 8
            ax = round(9 + (13 - 9) * t)
            ay = round(6 + (2 - 6) * t)
            put(ax, ay)
        put(13, 2); put(12, 2); put(11, 2)
        put(13, 3); put(13, 4)
    elif symbol_name == "female":
        cx, cy, r = 7, 5, 4
        for angle_step in range(360):
            rad = math.radians(angle_step)
            rx = round(cx + r * math.cos(rad))
            ry = round(cy + r * math.sin(rad))
            put(rx, ry)
        for y in range(9, 15):
            put(7, y)
        for x in range(5, 10):
            put(x, 12)
    return pixels

def patch_cell(linear_pixels, row, col, cell_data):
    x0 = col * CELL_W
    y0 = row * CELL_H
    for dy in range(CELL_H):
        for dx in range(CELL_W):
            idx = (y0 + dy) * TEX_W + (x0 + dx)
            linear_pixels[idx] = cell_data[dy * CELL_W + dx]

def main():
    print("=== Diagnostic ISO A: R2100 Gender-Only Patches ===\n")

    # 1. Read ORIGINAL R2100 from extracted PACKDATA.DIG
    print(f"Reading original R2100 from {DIG_PATH}...")
    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
        so, sc, tc = struct.unpack_from("<III", toc_data, R2100_TOC_INDEX * 12)
        byte_off = so * SECTOR
        byte_size = sc * SECTOR
        print(f"  TOC: sector_offset=0x{so:X}, count={sc}, type={tc}")
        f.seek(byte_off)
        r2100_orig = bytearray(f.read(byte_size))

    # 2. Parse descriptor table
    sub_entries = []
    for i in range(NUM_SUBS):
        sub_idx, sub_sz, data_off, pad = struct.unpack_from("<IIII", r2100_orig, i * 16)
        sub_entries.append((sub_idx, sub_sz, data_off))
        print(f"  Sub {i}: size=0x{sub_sz:X}, offset=0x{data_off:X}")

    # 3. Apply ONLY gender patches to sub-block 2
    GENDER_PATCHES = {
        (10, 0): "male",
        (10, 1): "female",
    }

    blk = 2
    sub_idx, sub_sz, data_off = sub_entries[blk]
    sub_data = r2100_orig[data_off:data_off + sub_sz]
    header = sub_data[:HDR_SIZE]
    pixel_raw = sub_data[HDR_SIZE:HDR_SIZE + PIXEL_SIZE]
    tail = sub_data[HDR_SIZE + PIXEL_SIZE:]

    linear = bytearray(deswizzle_psmt4(bytes(pixel_raw), TEX_W, TEX_H,
                                        bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))

    for (row, col), sym_name in GENDER_PATCHES.items():
        cell_data = render_gender_symbol(sym_name)
        sym_char = "♂" if sym_name == "male" else "♀"
        print(f"  Patching sub2 ({row},{col}): {sym_char}")
        patch_cell(linear, row, col, cell_data)

    reswizzled = swizzle_psmt4(linear, TEX_W, TEX_H,
                               bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    new_sub = bytes(header) + bytes(reswizzled) + bytes(tail)
    assert len(new_sub) == SUB_SIZE
    r2100_orig[data_off:data_off + SUB_SIZE] = new_sub

    # Sub0 and sub1 are UNTOUCHED (original Japanese data)
    # Sub3 is also untouched

    # 4. Copy the latest translated ISO
    print(f"\nCopying {SRC_ISO}...")
    shutil.copy2(SRC_ISO, DST_ISO)

    # 5. Overwrite R2100 in the ISO with our gender-only version
    r2100_padded = bytes(r2100_orig) + b'\x00' * (68 * SECTOR - len(r2100_orig))
    with open(DST_ISO, "r+b") as f:
        f.seek(R2100_ISO_OFFSET)
        f.write(r2100_padded)
        print(f"  Wrote gender-only R2100 at ISO offset 0x{R2100_ISO_OFFSET:X} ({len(r2100_padded)} bytes)")

    print(f"\nOutput: {DST_ISO}")
    print(f"Size: {os.path.getsize(DST_ISO):,} bytes")
    print("\nR2100 patches: ONLY ♂/♀ in sub2 row10. Sub0/Sub1/Sub3 = ORIGINAL.")
    print("All other translations (R37/R38/R1272/dialogue/EXE) remain from v55.")
    print("DONE!")

if __name__ == "__main__":
    main()
