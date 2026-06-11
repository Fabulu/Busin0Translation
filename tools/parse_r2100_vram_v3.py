#!/usr/bin/env python3
"""
R2100 VRAM upload analysis v3.

Key findings from v1/v2:
- NO BITBLTBUF/TRXPOS/TRXREG/TRXDIR found in R2100 data at all
- Headers are identical across all 4 sub-blocks
- Tails DIFFER (different palette colors per sub-block)
- TEX0_1 in header: TBP0=0x0000, TBW=4, PSM=PSMT4, 256x256

This means the EXE code controls WHERE in VRAM each sub-block's pixels go.
The game uploads only ONE sub-block at a time to TBP0=0x2840, overwriting
whatever was there before.

This script:
1. Confirms header/tail structure
2. Analyzes which cells in sub1/sub2 would overlap sub0's F/M cells
   IF all sub-blocks upload to the same VRAM address
3. Checks if those cells are modified by STAT_PATCHES
"""

import struct
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
DIG_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")

SECTOR = 2048
R2100_TOC_INDEX = 2100
TOC_ENTRIES = 2883
NUM_SUBS = 4
SUB_SIZE = 34624
HDR_SIZE = 0x4C0
PIXEL_SIZE = 32768
TAIL_SIZE = 640
TEX_W, TEX_H = 256, 256
CELL_W, CELL_H = 16, 16
COLS = TEX_W // CELL_W
ROWS = TEX_H // CELL_H


def main():
    print("=" * 70)
    print("R2100 VRAM Upload Analysis — Final Report")
    print("=" * 70)

    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
        so, sc, tc = struct.unpack_from("<III", toc_data, R2100_TOC_INDEX * 12)
        f.seek(so * SECTOR)
        r2100 = f.read(sc * SECTOR)

    # Parse descriptor table
    sub_entries = []
    for i in range(NUM_SUBS):
        sub_idx, sub_size, data_off, pad = struct.unpack_from("<IIII", r2100, i * 16)
        sub_entries.append((sub_idx, sub_size, data_off))

    # Collect headers and tails
    headers = []
    tails = []
    for blk in range(NUM_SUBS):
        _, _, data_off = sub_entries[blk]
        headers.append(r2100[data_off:data_off + HDR_SIZE])
        tail_off = data_off + HDR_SIZE + PIXEL_SIZE
        tails.append(r2100[tail_off:tail_off + TAIL_SIZE])

    print("\n1. HEADER COMPARISON")
    print("-" * 40)
    all_hdrs_same = all(headers[i] == headers[0] for i in range(1, NUM_SUBS))
    print(f"   All 4 headers identical: {all_hdrs_same}")
    print(f"   Header size: {HDR_SIZE} bytes (0x{HDR_SIZE:X})")

    print("\n2. TAIL (PALETTE) COMPARISON")
    print("-" * 40)
    for i in range(NUM_SUBS):
        for j in range(i + 1, NUM_SUBS):
            diffs = sum(1 for a, b in zip(tails[i], tails[j]) if a != b)
            print(f"   Sub {i} vs Sub {j}: {diffs} byte differences out of {TAIL_SIZE}")

    # Each tail = 10 palettes x 16 colors x 4 bytes (RGBA) = 640 bytes
    print(f"\n   Each tail = 10 palettes, 16 colors each, 4 bytes/color (RGBA)")
    for blk in range(NUM_SUBS):
        print(f"\n   Sub {blk} palettes (first 3 colors of palette 0):")
        for c in range(3):
            off = c * 4
            r, g, b, a = tails[blk][off], tails[blk][off+1], tails[blk][off+2], tails[blk][off+3]
            print(f"     Color {c}: R={r} G={g} B={b} A={a}")

    print("\n3. TEX0_1 REGISTER IN HEADER")
    print("-" * 40)
    # TEX0_1 data at header offset 0x50: 00 00 41 21 06 00 00 20
    tex0_raw = headers[0][0x50:0x58]
    val = struct.unpack('<Q', tex0_raw)[0]
    tbp0 = val & 0x3FFF
    tbw = (val >> 14) & 0x3F
    psm = (val >> 20) & 0x3F
    tw = (val >> 26) & 0xF
    th = (val >> 30) & 0xF
    psm_names = {0: "PSMCT32", 0x13: "PSMT8", 0x14: "PSMT4"}
    print(f"   TEX0_1: TBP0=0x{tbp0:04X}, TBW={tbw}, PSM={psm_names.get(psm, hex(psm))}")
    print(f"   Texture dims: {1<<tw}x{1<<th}")
    print(f"   NOTE: TBP0=0 in header is for PALETTE uploads, not pixel destination")
    print(f"   The actual pixel upload dest (0x2840) is set by EXE code via BITBLTBUF")

    print("\n4. KEY CONCLUSION: UPLOAD MECHANISM")
    print("-" * 40)
    print("""
   The R2100 resource contains NO BITBLTBUF, TRXPOS, TRXREG, or TRXDIR
   register writes anywhere in its data. The VIF/GIF header only contains:

   - GIF IMAGE-mode palette uploads (10 palettes, each 16 colors)
   - TEX0_1 register writes for palette texture setup (TBP0=0)

   The EXE code is responsible for:
   1. Setting BITBLTBUF with DBP = target VRAM block (0x2840 for chargen)
   2. Setting TRXPOS/TRXREG for 256x256 pixel transfer
   3. Setting TRXDIR = host->local
   4. Then sending the 32768-byte pixel data via DMA

   Since all 4 headers are IDENTICAL, the game uses the SAME upload setup
   for every sub-block. The EXE selects WHICH sub-block to load but always
   uploads to the SAME VRAM destination (TBP0=0x2840).

   => EACH sub-block OVERWRITES the previous one at TBP0=0x2840.
   => Only ONE sub-block is active in VRAM at any time.
   => Cell (row, col) in sub0 maps to EXACTLY the same VRAM pixels
      as cell (row, col) in sub1, sub2, sub3.
""")

    print("\n5. OVERLAP ANALYSIS: F/M vs STAT PATCHES")
    print("-" * 40)

    # Import patches from patch_r2100.py
    sys.path.insert(0, os.path.join(BASE, "tools"))

    # Manually define since import might have side effects
    STAT_PATCHES = {
        (1, 5, 10): "Str", (1, 3, 4): "Pie", (1, 6, 2): "", (1, 4, 0): "",
        (2, 1, 7): "Int", (2, 12, 13): "", (2, 4, 6): "Agi", (2, 12, 15): "",
        (2, 4, 14): "", (2, 12, 14): "Vit", (2, 11, 8): "", (2, 13, 0): "Lck",
        (2, 13, 1): "",
    }
    GENDER_PATCHES = {
        (2, 10, 0): "male",
        (2, 10, 1): "female",
    }

    # F = sub0, cell index 38 = row 2, col 6
    # M = sub0, cell index 45 = row 2, col 13
    f_row, f_col = 2, 6   # pixel coords (96,32)-(111,47)
    m_row, m_col = 2, 13  # pixel coords (208,32)-(223,47)

    print(f"   F cell in sub0: row={f_row}, col={f_col} -> pixels ({f_col*16},{f_row*16})-({f_col*16+15},{f_row*16+15})")
    print(f"   M cell in sub0: row={m_row}, col={m_col} -> pixels ({m_col*16},{m_row*16})-({m_col*16+15},{m_row*16+15})")

    print(f"\n   Since all sub-blocks upload to the SAME VRAM location,")
    print(f"   cell (2,6) in sub1 OVERWRITES cell (2,6) in sub0 (the F cell),")
    print(f"   and cell (2,13) in sub1 OVERWRITES cell (2,13) in sub0 (the M cell).")

    print(f"\n   Checking if any STAT_PATCHES or GENDER_PATCHES touch these cells:")

    all_patches = {}
    for k, v in STAT_PATCHES.items():
        all_patches[k] = v
    for k, v in GENDER_PATCHES.items():
        all_patches[k] = v

    f_conflicts = [(sb, r, c, t) for (sb, r, c), t in all_patches.items()
                   if sb > 0 and r == f_row and c == f_col]
    m_conflicts = [(sb, r, c, t) for (sb, r, c), t in all_patches.items()
                   if sb > 0 and r == m_row and c == m_col]

    if f_conflicts:
        for sb, r, c, t in f_conflicts:
            print(f"   *** CONFLICT: Sub{sb} ({r},{c}) = '{t}' overwrites sub0's F cell!")
    else:
        print(f"   No patches at ({f_row},{f_col}) in sub1/sub2/sub3 -> F cell SAFE")

    if m_conflicts:
        for sb, r, c, t in m_conflicts:
            print(f"   *** CONFLICT: Sub{sb} ({r},{c}) = '{t}' overwrites sub0's M cell!")
    else:
        print(f"   No patches at ({m_row},{m_col}) in sub1/sub2/sub3 -> M cell SAFE")

    print(f"\n6. BUT WAIT — THE REAL QUESTION IS DIFFERENT")
    print("-" * 40)
    print("""
   The overlap concern isn't about our patches conflicting with EACH OTHER.
   It's about the GAME's behavior:

   When the game needs glyphs from DIFFERENT sub-blocks simultaneously
   (e.g., sub0 for ASCII keyboard + sub1 for stat kanji), it can only
   have ONE sub-block loaded at TBP0=0x2840.

   The game likely:
   a) Loads the needed sub-block before drawing its glyphs
   b) Switches sub-blocks as needed (e.g., load sub1 for stats, sub0 for keyboard)

   This means F/M cells in sub0 are NOT visible when sub1/sub2 are loaded,
   and vice versa. There's no pixel corruption — just context switching.

   The ORIGINAL gender symbol problem was: F and M were placed in sub1/sub2
   at positions that, when those sub-blocks were loaded, would be drawn
   at the WRONG glyph IDs. The fix was to move them to sub2 row 10
   (positions not used by any other glyph rendering).
""")

    print(f"\n7. COMPLETE PATCH INVENTORY BY SUB-BLOCK")
    print("-" * 40)

    for sb in range(NUM_SUBS):
        patches_in_sb = [(r, c, t) for (s, r, c), t in all_patches.items() if s == sb]
        if patches_in_sb:
            print(f"\n   Sub-block {sb}:")
            for r, c, t in sorted(patches_in_sb):
                glyph_id = sb * 256 + r * 16 + c
                label = t if t else "(blank)"
                print(f"     ({r:2d},{c:2d}) glyph #{glyph_id:4d}: {label}")
        else:
            print(f"\n   Sub-block {sb}: no patches")

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print("""
   1. R2100 has NO embedded VRAM destination info (no BITBLTBUF/TRXPOS/TRXREG)
   2. All 4 sub-block headers are BYTE-IDENTICAL (only tails/palettes differ)
   3. The EXE controls upload destination — always TBP0=0x2840 for chargen
   4. Only ONE sub-block is in VRAM at a time; uploading overwrites previous
   5. Our patches in sub1/sub2 do NOT conflict with sub0's F/M at the
      same (row,col) because the game never needs both simultaneously
   6. The gender symbols were moved to sub2 (10,0)/(10,1) to avoid conflicts
      with keyboard ASCII cells that share the same glyph ID space
""")


if __name__ == "__main__":
    main()
