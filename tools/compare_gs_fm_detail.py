#!/usr/bin/env python3
"""Detailed comparison of GS dumps that have vs miss F/M.

Key finding from previous analysis:
- June 2 dumps (6 of them): ALL have cell 38 (F) and 45 (M) PRESENT
  But they have different screen positions (Y~150 X=408-472) and only ~35 unique cells
- June 3 dump: Cell indices >100 — this is Japanese hiragana keyboard
- June 5 dump: 58 unique cells, proper English keyboard layout, but F/M MISSING

This script does a detailed draw-by-draw comparison of a "working" (June 2) dump
vs the "broken" (June 5) dump to understand:
1. Are the June 2 dumps actually on the same screen?
2. What are the complete grid layouts in each?
3. Where exactly are F/M drawn in the working dump?
"""

import struct
from collections import defaultdict
from pathlib import Path

import zstandard as zstd

SNAPS_DIR = Path(r"C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps")

PSM_NAMES = {
    0x00: "PSMCT32", 0x14: "PSMT4", 0x13: "PSMT8",
}


def parse_tex0(val):
    return {
        'tbp0': val & 0x3FFF, 'tbw': (val >> 14) & 0x3F,
        'psm': (val >> 20) & 0x3F,
        'tw': 1 << ((val >> 26) & 0xF), 'th': 1 << ((val >> 30) & 0xF),
        'cbp': (val >> 37) & 0x3FFF, 'cpsm': (val >> 51) & 0xF,
        'csa': (val >> 56) & 0x1F, 'cld': (val >> 61) & 7,
    }


def parse_gs_data(data):
    """Parse GS dump, return draws."""
    pos = 0
    pos += 4  # fake_crc
    header_total_size = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    hdr = struct.unpack_from("<9I", data, pos)
    state_version, state_size = hdr[0], hdr[1]
    data_start = 8 + header_total_size
    packets_start = data_start + state_size + 0x2000

    cur_tex0 = None
    cur_xyoffset = (0, 0)
    all_draws = []
    draw_seq = 0
    pos = packets_start
    vsync_count = 0

    while pos < len(data) and vsync_count < 1:  # Only FIRST vsync
        if pos >= len(data): break
        tag = data[pos]; pos += 1

        if tag == 0:
            if pos + 5 > len(data): break
            path_idx = data[pos]; pos += 1
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            if pos + size > len(data): break
            gif_data = data[pos:pos + size]
            pos += size

            gpos = 0
            while gpos + 16 <= len(gif_data):
                lo = struct.unpack_from("<Q", gif_data, gpos)[0]
                hi = struct.unpack_from("<Q", gif_data, gpos + 8)[0]
                nloop = lo & 0x7FFF
                eop = (lo >> 15) & 1
                pre = (lo >> 46) & 1
                prim_data = (lo >> 47) & 0x7FF
                flg = (lo >> 58) & 3
                nreg = (lo >> 60) & 0xF
                if nreg == 0: nreg = 16
                gpos += 16
                reg_ids = [(hi >> (r * 4)) & 0xF for r in range(nreg)]

                if flg == 0:
                    verts = []; uvs = []; tme = 0; prim_type = 6
                    if pre:
                        prim_type = prim_data & 0x7
                        tme = (prim_data >> 4) & 1
                    for loop in range(nloop):
                        for ri, reg_id in enumerate(reg_ids):
                            if gpos + 16 > len(gif_data): break
                            plo = struct.unpack_from("<Q", gif_data, gpos)[0]
                            phi = struct.unpack_from("<Q", gif_data, gpos + 8)[0]
                            if reg_id == 0x0E:
                                reg_addr = phi & 0xFF
                                if reg_addr in (0x06, 0x07): cur_tex0 = parse_tex0(plo)
                                elif reg_addr == 0x00: prim_type = plo & 0x7; tme = (plo >> 4) & 1
                                elif reg_addr == 0x18: cur_xyoffset = (plo & 0xFFFF, (plo >> 32) & 0xFFFF)
                                elif reg_addr in (0x04, 0x05, 0x0C, 0x0D):
                                    verts.append((plo & 0xFFFF, (plo >> 16) & 0xFFFF))
                                elif reg_addr == 0x03:
                                    uvs.append((plo & 0x3FFF, (plo >> 16) & 0x3FFF))
                            elif reg_id == 0x05: verts.append((plo & 0xFFFF, (plo >> 32) & 0xFFFF))
                            elif reg_id == 0x04: verts.append((plo & 0xFFFF, (plo >> 32) & 0xFFFF))
                            elif reg_id == 0x03: uvs.append((plo & 0x3FFF, (plo >> 32) & 0x3FFF))
                            elif reg_id == 0x00: prim_type = plo & 0x7; tme = (plo >> 4) & 1
                            gpos += 16
                    if verts and cur_tex0:
                        all_draws.append({'seq': draw_seq, 'tex0': dict(cur_tex0),
                            'prim': prim_type, 'tme': tme, 'verts': verts, 'uvs': uvs,
                            'xyoff': cur_xyoffset, 'flg': 'PACKED'})
                        draw_seq += 1

                elif flg == 1:
                    verts = []; uvs = []; tme = 0; prim_type = 6
                    if pre:
                        prim_type = prim_data & 0x7; tme = (prim_data >> 4) & 1
                    total_regs = nloop * nreg
                    for i in range(total_regs):
                        if gpos + 8 > len(gif_data): break
                        reg_id = reg_ids[i % nreg]
                        rd = struct.unpack_from("<Q", gif_data, gpos)[0]
                        if reg_id == 0x00: prim_type = rd & 0x7; tme = (rd >> 4) & 1
                        elif reg_id == 0x05: verts.append((rd & 0xFFFF, (rd >> 16) & 0xFFFF))
                        elif reg_id == 0x04: verts.append((rd & 0xFFFF, (rd >> 16) & 0xFFFF))
                        elif reg_id == 0x0D: verts.append((rd & 0xFFFF, (rd >> 16) & 0xFFFF))
                        elif reg_id == 0x03: uvs.append((rd & 0x3FFF, (rd >> 16) & 0x3FFF))
                        gpos += 8
                    if (total_regs % 2) == 1: gpos += 8
                    if verts and cur_tex0:
                        all_draws.append({'seq': draw_seq, 'tex0': dict(cur_tex0),
                            'prim': prim_type, 'tme': tme, 'verts': verts, 'uvs': uvs,
                            'xyoff': cur_xyoffset, 'flg': 'REGLIST'})
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
        else:
            break

    return all_draws


def extract_kbd_grid(all_draws):
    """Extract keyboard grid positions from TBP0=0x2840 draws."""
    kbd_draws = [d for d in all_draws if d['tex0']['tbp0'] == 0x2840]
    positions = []
    for d in kbd_draws:
        ox, oy = d['xyoff']
        if len(d['verts']) >= 2 and len(d['uvs']) >= 2:
            x0 = (d['verts'][0][0] - ox) / 16.0
            y0 = (d['verts'][0][1] - oy) / 16.0
            u0 = d['uvs'][0][0] / 16.0
            v0 = d['uvs'][0][1] / 16.0
            u1 = d['uvs'][1][0] / 16.0 if len(d['uvs']) > 1 else u0
            v1 = d['uvs'][1][1] / 16.0 if len(d['uvs']) > 1 else v0
            cell_col = int(round(u0)) // 16
            cell_row = int(round(v0)) // 16
            cell_idx = cell_row * 16 + cell_col
            positions.append({
                'seq': d['seq'], 'sx': x0, 'sy': y0,
                'u0': u0, 'v0': v0, 'u1': u1, 'v1': v1,
                'cell_col': cell_col, 'cell_row': cell_row, 'cell_idx': cell_idx,
                'tex0': d['tex0'],
            })
    return positions


def main():
    # Load the "working" dump (June 2, first one) and "broken" dump (June 5)
    working_file = SNAPS_DIR / "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602192618.gs.zst"
    broken_file = SNAPS_DIR / "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605055713.gs.zst"

    # Also load 20260602200606 for additional reference
    working2_file = SNAPS_DIR / "Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602200606.gs.zst"

    dctx = zstd.ZstdDecompressor()

    print("Loading dumps...")
    with open(working_file, 'rb') as f:
        working_data = dctx.decompress(f.read(), max_output_size=512*1024*1024)
    with open(broken_file, 'rb') as f:
        broken_data = dctx.decompress(f.read(), max_output_size=512*1024*1024)
    with open(working2_file, 'rb') as f:
        working2_data = dctx.decompress(f.read(), max_output_size=512*1024*1024)

    print("\nParsing...")
    working_draws = parse_gs_data(working_data)
    broken_draws = parse_gs_data(broken_data)
    working2_draws = parse_gs_data(working2_data)

    working_grid = extract_kbd_grid(working_draws)
    broken_grid = extract_kbd_grid(broken_draws)
    working2_grid = extract_kbd_grid(working2_draws)

    # ===== DETAILED: "working" dump (June 2, 192618) =====
    print("\n" + "=" * 90)
    print("DUMP 1 ('WORKING' - June 2, 19:26): TBP0=0x2840 draws")
    print("=" * 90)

    rows_w = defaultdict(list)
    for gp in working_grid:
        row = round(gp['sy'] / 20) * 20
        rows_w[row].append(gp)

    for row_y in sorted(rows_w.keys()):
        items = sorted(rows_w[row_y], key=lambda x: x['sx'])
        print(f"\n  Screen Y~{row_y}: {len(items)} draws")
        for gp in items:
            ci = gp['cell_idx']
            letter = chr(ord('A') + ci - 33) if 33 <= ci <= 58 else (chr(ord('a') + ci - 65) if 65 <= ci <= 90 else f"#{ci}")
            print(f"    X={gp['sx']:6.1f} Y={gp['sy']:6.1f}  UV=({gp['u0']:.1f},{gp['v0']:.1f})-({gp['u1']:.1f},{gp['v1']:.1f})  "
                  f"cell=({gp['cell_col']},{gp['cell_row']})={ci:3d} [{letter}]")

    # ===== DETAILED: "broken" dump (June 5) =====
    print("\n" + "=" * 90)
    print("DUMP 2 ('BROKEN' - June 5, 05:57): TBP0=0x2840 draws")
    print("=" * 90)

    rows_b = defaultdict(list)
    for gp in broken_grid:
        row = round(gp['sy'] / 20) * 20
        rows_b[row].append(gp)

    for row_y in sorted(rows_b.keys()):
        items = sorted(rows_b[row_y], key=lambda x: x['sx'])
        print(f"\n  Screen Y~{row_y}: {len(items)} draws")
        for gp in items:
            ci = gp['cell_idx']
            letter = chr(ord('A') + ci - 33) if 33 <= ci <= 58 else (chr(ord('a') + ci - 65) if 65 <= ci <= 90 else f"#{ci}")
            print(f"    X={gp['sx']:6.1f} Y={gp['sy']:6.1f}  UV=({gp['u0']:.1f},{gp['v0']:.1f})-({gp['u1']:.1f},{gp['v1']:.1f})  "
                  f"cell=({gp['cell_col']},{gp['cell_row']})={ci:3d} [{letter}]")

    # ===== KEY QUESTION: Where do cells 38 and 45 appear in the working dump? =====
    print("\n" + "=" * 90)
    print("CELL 38 (F) and CELL 45 (M) LOCATIONS IN WORKING DUMP")
    print("=" * 90)

    for gp in working_grid:
        if gp['cell_idx'] in (38, 45):
            ci = gp['cell_idx']
            letter = 'F' if ci == 38 else 'M'
            print(f"  Cell {ci} ({letter}): X={gp['sx']:.1f} Y={gp['sy']:.1f} "
                  f"UV=({gp['u0']:.1f},{gp['v0']:.1f})-({gp['u1']:.1f},{gp['v1']:.1f}) "
                  f"cell=({gp['cell_col']},{gp['cell_row']})")

    # ===== COMPARE: What's at those same screen positions in the broken dump? =====
    print("\n" + "=" * 90)
    print("WHAT'S AT F/M SCREEN POSITIONS IN BROKEN DUMP?")
    print("=" * 90)

    # Find F/M positions from working dump
    for gp in working_grid:
        if gp['cell_idx'] in (38, 45):
            target_x, target_y = gp['sx'], gp['sy']
            letter = 'F' if gp['cell_idx'] == 38 else 'M'
            print(f"\n  Looking for draws near X={target_x:.1f} Y={target_y:.1f} ({letter} position):")

            # Find nearest draws in broken dump
            for bp in broken_grid:
                dist = abs(bp['sx'] - target_x) + abs(bp['sy'] - target_y)
                if dist < 50:  # within 50 pixels
                    ci = bp['cell_idx']
                    bl = chr(ord('A') + ci - 33) if 33 <= ci <= 58 else (chr(ord('a') + ci - 65) if 65 <= ci <= 90 else f"#{ci}")
                    print(f"    Broken dump: X={bp['sx']:.1f} Y={bp['sy']:.1f} cell={ci} [{bl}] dist={dist:.1f}")

    # ===== TEX0 comparison =====
    print("\n" + "=" * 90)
    print("TEX0 CONFIG COMPARISON (TBP0=0x2840)")
    print("=" * 90)

    w_tex0 = set()
    for gp in working_grid:
        t = gp['tex0']
        w_tex0.add((t['tbp0'], t['tbw'], t['psm'], t['tw'], t['th'], t['cbp'], t['cpsm'], t['csa'], t['cld']))

    b_tex0 = set()
    for gp in broken_grid:
        t = gp['tex0']
        b_tex0.add((t['tbp0'], t['tbw'], t['psm'], t['tw'], t['th'], t['cbp'], t['cpsm'], t['csa'], t['cld']))

    print(f"\n  Working dump TEX0 configs:")
    for t in sorted(w_tex0):
        print(f"    TBP0=0x{t[0]:04X} TBW={t[1]} PSM=0x{t[2]:02X} {t[3]}x{t[4]} CBP=0x{t[5]:04X} CPSM={t[6]} CSA={t[7]} CLD={t[8]}")

    print(f"\n  Broken dump TEX0 configs:")
    for t in sorted(b_tex0):
        print(f"    TBP0=0x{t[0]:04X} TBW={t[1]} PSM=0x{t[2]:02X} {t[3]}x{t[4]} CBP=0x{t[5]:04X} CPSM={t[6]} CSA={t[7]} CLD={t[8]}")

    # ===== What screen is the working dump actually showing? =====
    print("\n" + "=" * 90)
    print("SCREEN IDENTIFICATION: ALL TEXTURE CONFIGS IN EACH DUMP")
    print("=" * 90)

    for name, draws in [("Working (June 2)", working_draws), ("Broken (June 5)", broken_draws)]:
        print(f"\n  {name}:")
        tex0_counts = defaultdict(int)
        for d in draws:
            t = d['tex0']
            key = (t['tbp0'], t['tbw'], t['psm'], t['tw'], t['th'], t['cbp'])
            tex0_counts[key] += 1
        for key in sorted(tex0_counts.keys()):
            tbp0, tbw, psm, tw, th, cbp = key
            psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
            print(f"    TBP0=0x{tbp0:04X} TBW={tbw} {psm_name:>10} {tw}x{th} CBP=0x{cbp:04X}: {tex0_counts[key]} draws")

    # ===== Check if the "working" dump is actually a DIFFERENT screen =====
    # The working dump has screen Y~30 to Y~380 which is unusual
    # The broken dump has Y~40 to Y~250 which is the keyboard area
    print("\n" + "=" * 90)
    print("SCREEN RANGE COMPARISON")
    print("=" * 90)

    w_ys = sorted(set(round(gp['sy']) for gp in working_grid))
    b_ys = sorted(set(round(gp['sy']) for gp in broken_grid))
    w_xs = sorted(set(round(gp['sx']) for gp in working_grid))
    b_xs = sorted(set(round(gp['sx']) for gp in broken_grid))

    print(f"\n  Working dump:")
    print(f"    Y range: {min(w_ys)} to {max(w_ys)}")
    print(f"    X range: {min(w_xs)} to {max(w_xs)}")
    print(f"    Unique Y positions: {w_ys}")
    print(f"    Unique X positions: {w_xs}")

    print(f"\n  Broken dump:")
    print(f"    Y range: {min(b_ys)} to {max(b_ys)}")
    print(f"    X range: {min(b_xs)} to {max(b_xs)}")
    print(f"    Unique Y positions: {b_ys}")
    print(f"    Unique X positions: {b_xs}")

    # ===== Check working dump #2 =====
    print("\n" + "=" * 90)
    print("DUMP 3 ('WORKING 2' - June 2, 20:06): TBP0=0x2840 draws")
    print("=" * 90)

    rows_w2 = defaultdict(list)
    for gp in working2_grid:
        row = round(gp['sy'] / 20) * 20
        rows_w2[row].append(gp)

    for row_y in sorted(rows_w2.keys()):
        items = sorted(rows_w2[row_y], key=lambda x: x['sx'])
        print(f"\n  Screen Y~{row_y}: {len(items)} draws")
        for gp in items:
            ci = gp['cell_idx']
            letter = chr(ord('A') + ci - 33) if 33 <= ci <= 58 else (chr(ord('a') + ci - 65) if 65 <= ci <= 90 else f"#{ci}")
            print(f"    X={gp['sx']:6.1f} Y={gp['sy']:6.1f}  cell=({gp['cell_col']},{gp['cell_row']})={ci:3d} [{letter}]")

    # Cell 38/45 in working2
    for gp in working2_grid:
        if gp['cell_idx'] in (38, 45):
            ci = gp['cell_idx']
            letter = 'F' if ci == 38 else 'M'
            print(f"\n  ** Cell {ci} ({letter}) in Working2: X={gp['sx']:.1f} Y={gp['sy']:.1f}")


if __name__ == '__main__':
    main()
