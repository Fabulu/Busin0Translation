#!/usr/bin/env python3
"""Identify what the common cells (appearing in all 4 dumps) actually are.
These are the persistent UI elements drawn from TBP0=0x2840."""

import struct
from pathlib import Path
import zstandard as zstd

SNAPS_DIR = Path(r"C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps")

DUMP_FILES = [
    ("Kana",  "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605185636.gs.zst"),
    ("Hira",  "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605185641.gs.zst"),
    ("ABC",   "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605185644.gs.zst"),
    ("Sym",   "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605185648.gs.zst"),
]

# Common cells across all 4 pages: [0, 14, 37, 65, 69, 77, 78, 79, 82, 84, 85, 89, 110, 242]
# Let's map these to characters using the keyboard atlas layout:
# Cell = row*16 + col
# 0  = (0,0)  -> space/empty
# 14 = (0,14) -> backspace icon?
# 37 = (2,5)  -> E (uppercase)
# 65 = (4,1)  -> a (lowercase)
# 69 = (4,5)  -> e
# 77 = (4,13) -> m
# 78 = (4,14) -> n
# 79 = (4,15) -> o
# 82 = (5,2)  -> r
# 84 = (5,4)  -> t
# 85 = (5,5)  -> u
# 89 = (5,9)  -> y
# 110 = (6,14) -> cursor highlight?
# 242 = (15,2) -> selection marker?

# Wait -- these spell out tab labels!
# "Kana" = K, a, n, a  but K=43 and that's NOT in common set
# Actually the tabs say: "Kana", "Hira", "ABC", "Sym", "OK"
# These use R1272 (main font), not R2840!
#
# Let me re-examine. The common cells drawn at specific screen positions
# will tell us what UI elements they represent.
# The tab/button labels might be drawn using the R2840 atlas too.

# Let's check the screen positions of these common cells

def parse_tex0(val):
    return {
        'tbp0': val & 0x3FFF, 'tbw': (val >> 14) & 0x3F,
        'psm': (val >> 20) & 0x3F,
        'tw': 1 << ((val >> 26) & 0xF), 'th': 1 << ((val >> 30) & 0xF),
        'cbp': (val >> 37) & 0x3FFF, 'cpsm': (val >> 51) & 0xF,
        'csa': (val >> 56) & 0x1F, 'cld': (val >> 61) & 7,
    }

def load_gs_dump(path):
    dctx = zstd.ZstdDecompressor()
    with open(path, 'rb') as f:
        return dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)

def parse_gs_draws(data):
    pos = 0; pos += 4
    header_total_size = struct.unpack_from("<I", data, pos)[0]; pos += 4
    hdr = struct.unpack_from("<9I", data, pos)
    state_size = hdr[1]
    data_start = 8 + header_total_size
    packets_start = data_start + state_size + 0x2000

    cur_tex0 = None
    cur_xyoffset = (0, 0)
    all_draws = []
    draw_seq = 0
    pos = packets_start
    vsync_count = 0

    while pos < len(data) and vsync_count < 2:
        if pos >= len(data): break
        tag = data[pos]; pos += 1
        if tag == 0:
            if pos + 5 > len(data): break
            path_idx = data[pos]; pos += 1
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            if pos + size > len(data): break
            gif_data = data[pos:pos + size]; pos += size
            gpos = 0
            while gpos + 16 <= len(gif_data):
                lo = struct.unpack_from("<Q", gif_data, gpos)[0]
                hi = struct.unpack_from("<Q", gif_data, gpos + 8)[0]
                nloop = lo & 0x7FFF; eop = (lo >> 15) & 1
                pre = (lo >> 46) & 1; prim_data = (lo >> 47) & 0x7FF
                flg = (lo >> 58) & 3; nreg = (lo >> 60) & 0xF
                if nreg == 0: nreg = 16
                gpos += 16
                reg_ids = [(hi >> (r * 4)) & 0xF for r in range(nreg)]
                if flg == 0:
                    verts, uvs = [], []
                    for loop in range(nloop):
                        for ri, reg_id in enumerate(reg_ids):
                            if gpos + 16 > len(gif_data): break
                            plo = struct.unpack_from("<Q", gif_data, gpos)[0]
                            phi = struct.unpack_from("<Q", gif_data, gpos + 8)[0]
                            if reg_id == 0x0E:
                                reg_addr = phi & 0xFF
                                if reg_addr in (0x06, 0x07): cur_tex0 = parse_tex0(plo)
                                elif reg_addr == 0x18: cur_xyoffset = (plo & 0xFFFF, (plo >> 32) & 0xFFFF)
                                elif reg_addr in (0x04, 0x05, 0x0C, 0x0D):
                                    verts.append((plo & 0xFFFF, (plo >> 16) & 0xFFFF))
                                elif reg_addr == 0x03:
                                    uvs.append((plo & 0x3FFF, (plo >> 16) & 0x3FFF))
                            elif reg_id in (0x04, 0x05):
                                verts.append((plo & 0xFFFF, (plo >> 32) & 0xFFFF))
                            elif reg_id == 0x03:
                                uvs.append((plo & 0x3FFF, (plo >> 32) & 0x3FFF))
                            gpos += 16
                    if verts and cur_tex0:
                        all_draws.append({'seq': draw_seq, 'tex0': dict(cur_tex0), 'verts': verts, 'uvs': uvs, 'xyoff': cur_xyoffset})
                        draw_seq += 1
                elif flg == 1:
                    verts, uvs = [], []
                    total_regs = nloop * nreg
                    for i in range(total_regs):
                        if gpos + 8 > len(gif_data): break
                        reg_id = reg_ids[i % nreg]
                        rd = struct.unpack_from("<Q", gif_data, gpos)[0]
                        if reg_id in (0x04, 0x05, 0x0D):
                            verts.append((rd & 0xFFFF, (rd >> 16) & 0xFFFF))
                        elif reg_id == 0x03:
                            uvs.append((rd & 0x3FFF, (rd >> 16) & 0x3FFF))
                        gpos += 8
                    if (total_regs % 2) == 1: gpos += 8
                    if verts and cur_tex0:
                        all_draws.append({'seq': draw_seq, 'tex0': dict(cur_tex0), 'verts': verts, 'uvs': uvs, 'xyoff': cur_xyoffset})
                        draw_seq += 1
                elif flg == 2:
                    gpos += nloop * 16
                if eop: break
        elif tag == 1:
            if pos + 1 > len(data): break
            pos += 1; vsync_count += 1
        elif tag == 2:
            if pos + 4 > len(data): break
            struct.unpack_from("<I", data, pos)[0]; pos += 4
        elif tag == 3:
            if pos + 0x2000 > len(data): break
            pos += 0x2000
        else: break
    return all_draws


COMMON_CELLS = {0, 14, 37, 65, 69, 77, 78, 79, 82, 84, 85, 89, 110, 242}

def main():
    print("=" * 90)
    print("COMMON CELLS ANALYSIS: What UI elements do the 14 common cells represent?")
    print("=" * 90)
    print(f"\nCommon cells: {sorted(COMMON_CELLS)}")

    # Map cell to potential character
    cell_chars = {}
    for c in COMMON_CELLS:
        if 33 <= c <= 58:
            cell_chars[c] = chr(ord('A') + c - 33)
        elif 65 <= c <= 90:
            cell_chars[c] = chr(ord('a') + c - 65)
        elif 16 <= c <= 25:
            cell_chars[c] = str((c - 16 + 1) % 10)
        elif c == 0:
            cell_chars[c] = "SPC"
        elif c == 14:
            cell_chars[c] = "BS?"
        elif c == 110:
            cell_chars[c] = "CUR?"
        elif c == 242:
            cell_chars[c] = "SEL?"
        else:
            cell_chars[c] = f"#{c}"

    print("\nCell -> Character mapping:")
    for c in sorted(COMMON_CELLS):
        row, col = c // 16, c % 16
        print(f"  Cell {c:3d} (row={row}, col={col:2d}) -> {cell_chars[c]}")

    # The letter cells in common: 37(E), 65(a), 69(e), 77(m), 78(n), 79(o), 82(r), 84(t), 85(u), 89(y)
    # These spell: E a e m n o r t u y
    # UI labels visible in screenshots: "Enter your name." "Kana" "Hira" "ABC" "Sym" "OK" "Name" "Level"
    # But those are drawn with R1272 (TBP0=0x3000), not R2840!
    #
    # Wait - these cells appear at Y~40 in the first dump's grid.
    # Looking at Dump 1 Kana page: Y~40 row has: 37(E) 84 89 79 85 82 78 65 77 69 14
    # That's: E t y o u r n a m e BS
    # = "Enter your name" backwards + backspace!
    #
    # NO WAIT. The name input field shows what you've typed.
    # Y~40 is the TOP of the screen. These cells at Y~40 spell out:
    # Cells: 37 84 89 79 85 82 78 65 77 69 = E t y o u r n a m e
    # That's "Entryouname" ... no, reading in screen X order:
    # From the ABC dump: Y~40 has just cell 14 (at X=416)
    # But in Dump 1: Y~40: 37(E) 84 89 79 85 82 78 65 77 69 14

    # Let me get the actual screen positions for each dump

    for page_name, fname in DUMP_FILES:
        print(f"\n{'='*70}")
        print(f"PAGE: {page_name}")
        print(f"{'='*70}")

        path = SNAPS_DIR / fname
        data = load_gs_dump(path)
        draws = parse_gs_draws(data)
        kbd = [d for d in draws if d['tex0']['tbp0'] == 0x2840]

        # Get unique draws with screen positions for common cells
        seen = set()
        common_positions = []
        all_positions = []

        for d in kbd:
            ox, oy = d['xyoff']
            if len(d['uvs']) >= 1 and len(d['verts']) >= 1:
                sx = (d['verts'][0][0] - ox) / 16.0
                sy = (d['verts'][0][1] - oy) / 16.0
                u0 = d['uvs'][0][0] / 16.0
                v0 = d['uvs'][0][1] / 16.0
                cell_col = int(round(u0)) // 16
                cell_row = int(round(v0)) // 16
                cell_idx = cell_row * 16 + cell_col

                key = (round(sx), round(sy), cell_idx)
                if key not in seen:
                    seen.add(key)
                    entry = {'sx': sx, 'sy': sy, 'cell': cell_idx, 'char': cell_chars.get(cell_idx, f"#{cell_idx}")}
                    all_positions.append(entry)
                    if cell_idx in COMMON_CELLS:
                        common_positions.append(entry)

        # Show common cells with positions
        print(f"\n  Common cells and their screen positions:")
        common_positions.sort(key=lambda e: (round(e['sy']/10)*10, e['sx']))

        current_row = -1
        for e in common_positions:
            row = round(e['sy'] / 10) * 10
            if row != current_row:
                print(f"\n    Y~{row:3.0f}:", end="")
                current_row = row
            print(f"  {e['char']}@{e['sx']:.0f}", end="")
        print()

        # Also show the top region (Y < 100) for ALL cells
        print(f"\n  ALL cells in top region (Y < 100):")
        top = [e for e in all_positions if e['sy'] < 100]
        top.sort(key=lambda e: (round(e['sy']/10)*10, e['sx']))
        for e in top:
            print(f"    X={e['sx']:6.1f} Y={e['sy']:6.1f} cell={e['cell']:3d} ({e['char']})")

    # CRITICAL INSIGHT
    print("\n\n" + "=" * 90)
    print("CRITICAL INSIGHT")
    print("=" * 90)
    print("""
The common cells [37, 65, 69, 77, 78, 79, 82, 84, 85, 89] spell:
  E, a, e, m, n, o, r, t, u, y

These appear at Y~40 (top of screen) - this is the NAME INPUT FIELD!
The user has typed "ゲ" (shown in screenshots) but the display also shows
previously-entered characters using the R2840 atlas cells.

Wait - looking at the Kana page screenshot, the name field shows "ゲ" followed
by dashes. The cells at Y~40 aren't the typed name - they must be something else.

Actually looking more carefully: In the Kana screenshot, Y~40 has cells:
  37(E) 84(t) 89(y) 79(o) 85(u) 82(r) 78(n) 65(a) 77(m) 69(e) 14(BS)
Reading left to right by X position:
  E-n-t-e-r-y-o-u-r-n-a-m-e  -> "Enter your name" !

So the "Enter your name." text at the top is ALSO drawn using R2840 cells!
Cell 37=E, and F(38) and M(45) are the adjacent cells that are NEVER drawn.

This is significant: the UI text "Enter your name" uses specific cells from
the R2840 atlas. The cells it uses (E, a, e, m, n, o, r, t, u, y) are the
exact letters needed for those UI strings, and they happen to NOT include
F or M (because "Enter your name" doesn't contain F or M).

The F and M are simply not present in ANY draw because:
1. The keyboard grid skips those positions
2. No UI text uses those letters
""")


if __name__ == '__main__':
    main()
