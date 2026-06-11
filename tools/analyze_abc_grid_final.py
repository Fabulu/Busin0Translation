#!/usr/bin/env python3
"""Final analysis: ABC grid layout with precise spacing to show F/M gaps."""

import struct
from pathlib import Path
import zstandard as zstd

SNAPS_DIR = Path(r"C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps")
ABC_FILE = "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605185644.gs.zst"


def parse_tex0(val):
    return {
        'tbp0': val & 0x3FFF, 'tbw': (val >> 14) & 0x3F,
        'psm': (val >> 20) & 0x3F,
        'tw': 1 << ((val >> 26) & 0xF), 'th': 1 << ((val >> 30) & 0xF),
        'cbp': (val >> 37) & 0x3FFF, 'cpsm': (val >> 51) & 0xF,
        'csa': (val >> 56) & 0x1F, 'cld': (val >> 61) & 7,
    }


def load_and_parse(path):
    dctx = zstd.ZstdDecompressor()
    with open(path, 'rb') as f:
        data = dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)

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
            pos += 1  # path_idx
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
                                ra = phi & 0xFF
                                if ra in (0x06, 0x07): cur_tex0 = parse_tex0(plo)
                                elif ra == 0x18: cur_xyoffset = (plo & 0xFFFF, (plo >> 32) & 0xFFFF)
                                elif ra in (0x04, 0x05, 0x0C, 0x0D):
                                    verts.append((plo & 0xFFFF, (plo >> 16) & 0xFFFF))
                                elif ra == 0x03:
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
            pos += 4
        elif tag == 3:
            if pos + 0x2000 > len(data): break
            pos += 0x2000
        else: break
    return all_draws


def cell_to_char(c):
    if 33 <= c <= 58: return chr(ord('A') + c - 33)
    if 65 <= c <= 90: return chr(ord('a') + c - 65)
    if 16 <= c <= 25: return str((c - 16 + 1) % 10)
    if c == 0: return '_'
    if c == 14: return 'BS'
    if c == 110: return '[]'
    if c == 242: return '>>'
    return f'#{c}'


def main():
    path = SNAPS_DIR / ABC_FILE
    all_draws = load_and_parse(path)
    kbd_draws = [d for d in all_draws if d['tex0']['tbp0'] == 0x2840]

    # Collect unique grid entries
    seen = set()
    entries = []
    for d in kbd_draws:
        ox, oy = d['xyoff']
        if len(d['uvs']) >= 1 and len(d['verts']) >= 1:
            sx = (d['verts'][0][0] - ox) / 16.0
            sy = (d['verts'][0][1] - oy) / 16.0
            u0 = d['uvs'][0][0] / 16.0
            v0 = d['uvs'][0][1] / 16.0
            cell_col = int(round(u0)) // 16
            cell_row = int(round(v0)) // 16
            cell_idx = cell_row * 16 + cell_col
            key = (round(sx*2), round(sy*2), cell_idx)  # sub-pixel dedup
            if key not in seen:
                seen.add(key)
                entries.append((sx, sy, cell_idx))

    # Sort by Y then X
    entries.sort(key=lambda e: (round(e[1]/10)*10, e[0]))

    print("=" * 90)
    print("ABC KEYBOARD PAGE - COMPLETE GRID LAYOUT")
    print("=" * 90)
    print()
    print("Y~38: Header text \"Enter your name.\" (drawn from R2840 atlas cells)")
    print()

    # Grid area (Y >= 140)
    grid = [e for e in entries if e[1] >= 140]

    print("KEYBOARD GRID (Y >= 140):")
    print(f"{'X':>8} {'Y':>8} {'Cell':>5} {'Char':>5}")
    print("-" * 35)

    current_row = -1
    for sx, sy, cell_idx in grid:
        row = round(sy / 10) * 10
        if row != current_row:
            if current_row >= 0:
                print()
            current_row = row
        ch = cell_to_char(cell_idx)
        marker = ""
        # Mark the gaps
        if cell_idx in (37,) and row == 150:
            marker = "  <-- next should be F(38) but..."
        if cell_idx == 65 and row == 150:
            marker = "  <-- gap! jumps to lowercase (F=38 SKIPPED)"
        if cell_idx == 44 and row == 190:
            marker = "  <-- next should be M(45) but..."
        if cell_idx == 46 and row == 190:
            marker = "  <-- gap! (M=45 SKIPPED)"

        print(f"{sx:8.1f} {sy:8.1f} {cell_idx:5d} {ch:>5s}{marker}")

    # Show the visual grid
    print()
    print("=" * 90)
    print("VISUAL GRID LAYOUT (as seen on screen):")
    print("=" * 90)

    current_row = -1
    row_entries = []
    all_rows = []
    for sx, sy, cell_idx in grid:
        row = round(sy / 10) * 10
        if row != current_row:
            if row_entries:
                all_rows.append((current_row, row_entries))
            current_row = row
            row_entries = []
        row_entries.append((sx, cell_idx))
    if row_entries:
        all_rows.append((current_row, row_entries))

    for row_y, cells in all_rows:
        cells.sort(key=lambda c: c[0])
        line_upper = f"Y~{row_y:3.0f}: "
        line_lower = "       "
        prev_x = None
        for sx, ci in cells:
            ch = cell_to_char(ci)
            if prev_x is not None:
                gap = sx - prev_x
                if gap > 30:  # gap bigger than normal
                    spaces = int((gap - 24) / 24)
                    line_upper += "  . " * spaces
                    line_lower += "    " * spaces
            line_upper += f" {ch:>3s}"
            line_lower += f" {ci:3d}"
            prev_x = sx
        print(line_upper)
        print(line_lower)
        print()

    # Summary
    print("=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)
    print()
    print("1. ALL 4 dumps are from the PATCHED build (English UI confirmed by screenshots)")
    print("   R2840 VRAM hash is IDENTICAL across all 4 -> same keyboard atlas data")
    print()
    print("2. The \"Enter your name.\" header is drawn using R2840 cells:")
    print("   E(37) n(78) t(84) e(69) r(82) SPC(0) y(89) o(79) u(85) r(82) SPC(0)")
    print("   n(78) a(65) m(77) e(69) BS(14)")
    print()
    print("3. On the ABC page, the keyboard grid draws cells 33-58 (A-Z) and 65-90 (a-z)")
    print("   EXCEPT cells 38(F) and 45(M) which are SKIPPED")
    print()
    print("4. The gap at F: After E(37) at X=196, next is lowercase 'a'(65) at X=228")
    print("   Gap = 32px (normal = 24px), meaning F's slot is empty but only 8px wider")
    print()
    print("5. The gap at M: After L(44) at X=124, next is N(46) at X=172")
    print("   Gap = 48px (normal = 24px), meaning M's slot is completely empty")
    print()
    print("6. Cannot determine original Japanese behavior from these dumps alone.")
    print("   Need a GS dump from the ORIGINAL Japanese ISO on the ABC keyboard page.")
    print()
    print("7. The R2840 keyboard atlas VRAM data is identical across all 4 dumps,")
    print("   confirming the texture data is the same regardless of which page is shown.")
    print("   The page switching is done by changing which cells are DRAWN, not by")
    print("   swapping the atlas texture.")


if __name__ == '__main__':
    main()
