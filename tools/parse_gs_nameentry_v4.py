#!/usr/bin/env python3
"""Parse PCSX2 GS dump from NAME ENTRY screen - v4.

Focused analysis: extract TBP0=0x2840 keyboard draws,
map UV coordinates to character cells, identify F and M positions.

PRIM in REGLIST mode: parse the PRIM data from first reg in REGLIST.
"""

import struct
from collections import defaultdict
from pathlib import Path

import zstandard as zstd

GS_DUMP = Path(r"C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps/Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605055713.gs.zst")

PSM_NAMES = {
    0x00: "PSMCT32", 0x01: "PSMCT24", 0x02: "PSMCT16", 0x0A: "PSMCT16S",
    0x13: "PSMT8", 0x14: "PSMT4", 0x1B: "PSMT8H",
    0x24: "PSMT4HL", 0x2C: "PSMT4HH",
    0x30: "PSMZ32", 0x31: "PSMZ24", 0x32: "PSMZ16", 0x3A: "PSMZ16S",
}

PRIM_TYPES = {0: "POINT", 1: "LINE", 2: "LINE_STRIP", 3: "TRI",
              4: "TRI_STRIP", 5: "TRI_FAN", 6: "SPRITE"}


def parse_tex0(val):
    return {
        'tbp0': val & 0x3FFF, 'tbw': (val >> 14) & 0x3F,
        'psm': (val >> 20) & 0x3F,
        'tw': 1 << ((val >> 26) & 0xF), 'th': 1 << ((val >> 30) & 0xF),
        'cbp': (val >> 37) & 0x3FFF, 'cpsm': (val >> 51) & 0xF,
        'csa': (val >> 56) & 0x1F, 'cld': (val >> 61) & 7,
    }


def main():
    print(f"Reading: {GS_DUMP}")
    dctx = zstd.ZstdDecompressor()
    with open(GS_DUMP, 'rb') as f:
        data = dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)
    print(f"Decompressed: {len(data):,} bytes")

    # Parse header
    pos = 0
    pos += 4  # fake_crc
    header_total_size = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    hdr = struct.unpack_from("<9I", data, pos)
    state_version, state_size = hdr[0], hdr[1]

    data_start = 8 + header_total_size
    packets_start = data_start + state_size + 0x2000

    # Render state
    cur_tex0 = None
    cur_xyoffset = (0, 0)
    cur_frame_fbp = 0

    # Results
    all_draws = []
    bitblt_writes = []
    draw_seq = 0

    pos = packets_start
    vsync_count = 0
    packet_idx = 0

    # Only first 2 vsyncs
    while pos < len(data) and vsync_count < 2:
        tag = data[pos]; pos += 1

        if tag == 0:  # Transfer
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

                if flg == 0:  # PACKED
                    verts = []
                    uvs = []
                    tme = 0
                    prim_type = 6

                    if pre:
                        prim_type = prim_data & 0x7
                        tme = (prim_data >> 4) & 1

                    for loop in range(nloop):
                        for ri, reg_id in enumerate(reg_ids):
                            if gpos + 16 > len(gif_data): break
                            plo = struct.unpack_from("<Q", gif_data, gpos)[0]
                            phi = struct.unpack_from("<Q", gif_data, gpos + 8)[0]

                            if reg_id == 0x0E:  # A+D
                                reg_addr = phi & 0xFF
                                if reg_addr in (0x06, 0x07):
                                    cur_tex0 = parse_tex0(plo)
                                elif reg_addr == 0x00:
                                    prim_type = plo & 0x7
                                    tme = (plo >> 4) & 1
                                elif reg_addr in (0x4C, 0x4D):
                                    cur_frame_fbp = plo & 0x1FF
                                elif reg_addr == 0x18:
                                    cur_xyoffset = (plo & 0xFFFF, (plo >> 32) & 0xFFFF)
                                elif reg_addr in (0x04, 0x05, 0x0C, 0x0D):
                                    x = plo & 0xFFFF; y = (plo >> 16) & 0xFFFF
                                    verts.append((x, y))
                                elif reg_addr == 0x03:
                                    u = plo & 0x3FFF; v = (plo >> 16) & 0x3FFF
                                    uvs.append((u, v))
                                elif reg_addr == 0x50:
                                    sbp = plo & 0x3FFF; dbp = (plo >> 32) & 0x3FFF
                                    spsm = (plo >> 24) & 0x3F; dpsm = (plo >> 56) & 0x3F
                                    sbw = (plo >> 16) & 0x3F; dbw = (plo >> 48) & 0x3F
                                    bitblt_writes.append({'sbp': sbp, 'dbp': dbp,
                                        'spsm': spsm, 'dpsm': dpsm, 'sbw': sbw, 'dbw': dbw})
                            elif reg_id == 0x05:  # XYZ2 packed
                                x = plo & 0xFFFF; y = (plo >> 32) & 0xFFFF
                                verts.append((x, y))
                            elif reg_id == 0x04:  # XYZF2 packed
                                x = plo & 0xFFFF; y = (plo >> 32) & 0xFFFF
                                verts.append((x, y))
                            elif reg_id == 0x03:  # UV packed
                                u = plo & 0x3FFF; v = (plo >> 32) & 0x3FFF
                                uvs.append((u, v))
                            elif reg_id == 0x00:  # PRIM packed
                                prim_type = plo & 0x7
                                tme = (plo >> 4) & 1
                            gpos += 16

                    if verts and cur_tex0:
                        all_draws.append({
                            'seq': draw_seq, 'tex0': dict(cur_tex0),
                            'prim': prim_type, 'tme': tme,
                            'verts': verts, 'uvs': uvs,
                            'xyoff': cur_xyoffset, 'fbp': cur_frame_fbp,
                            'flg': 'PACKED',
                        })
                        draw_seq += 1

                elif flg == 1:  # REGLIST
                    verts = []
                    uvs = []
                    tme = 0
                    prim_type = 6

                    if pre:
                        prim_type = prim_data & 0x7
                        tme = (prim_data >> 4) & 1

                    total_regs = nloop * nreg
                    for i in range(total_regs):
                        if gpos + 8 > len(gif_data): break
                        reg_id = reg_ids[i % nreg]
                        rd = struct.unpack_from("<Q", gif_data, gpos)[0]

                        if reg_id == 0x00:  # PRIM
                            prim_type = rd & 0x7
                            tme = (rd >> 4) & 1
                        elif reg_id == 0x05:  # XYZ2
                            x = rd & 0xFFFF; y = (rd >> 16) & 0xFFFF
                            verts.append((x, y))
                        elif reg_id == 0x04:  # XYZF2
                            x = rd & 0xFFFF; y = (rd >> 16) & 0xFFFF
                            verts.append((x, y))
                        elif reg_id == 0x0D:  # XYZ3
                            x = rd & 0xFFFF; y = (rd >> 16) & 0xFFFF
                            verts.append((x, y))
                        elif reg_id == 0x03:  # UV
                            u = rd & 0x3FFF; v = (rd >> 16) & 0x3FFF
                            uvs.append((u, v))
                        gpos += 8

                    if (total_regs % 2) == 1:
                        gpos += 8

                    if verts and cur_tex0:
                        all_draws.append({
                            'seq': draw_seq, 'tex0': dict(cur_tex0),
                            'prim': prim_type, 'tme': tme,
                            'verts': verts, 'uvs': uvs,
                            'xyoff': cur_xyoffset, 'fbp': cur_frame_fbp,
                            'flg': 'REGLIST',
                        })
                        draw_seq += 1

                elif flg == 2:  # IMAGE
                    gpos += nloop * 16

                if eop: break

        elif tag == 1:
            if pos + 1 > len(data): break
            pos += 1; vsync_count += 1
        elif tag == 2:
            if pos + 4 > len(data): break
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
        elif tag == 3:
            if pos + 0x2000 > len(data): break
            pos += 0x2000
        else:
            break
        packet_idx += 1

    print(f"\nTotal draws (first frame): {len(all_draws)}")
    textured = [d for d in all_draws if d['tme']]
    print(f"Textured draws (TME=1): {len(textured)}")
    print(f"Non-textured (TME=0): {len(all_draws) - len(textured)}")

    # ===== TME STATISTICS =====
    # The TME=0 with tex0 draws are the keyboard chars - REGLIST PRIM parsing
    # In REGLIST: PRIM,RGBAQ,UV,XYZ3,UV,XYZ2
    # PRIM value sets TME. Let's check what the actual PRIM values are.
    print("\n" + "=" * 90)
    print("REGLIST PRIM VALUE ANALYSIS")
    print("=" * 90)
    prim_tme_counts = defaultdict(int)
    for d in all_draws:
        prim_tme_counts[(d['prim'], d['tme'], d['flg'])] += 1
    for (p, t, f), cnt in sorted(prim_tme_counts.items()):
        pn = PRIM_TYPES.get(p, str(p))
        print(f"  PRIM={pn} TME={t} mode={f}: {cnt} draws")

    # ===== ALL draws that use TBP0=0x2840 (keyboard font) =====
    print("\n" + "=" * 90)
    print("TBP0=0x2840 DRAWS -- KEYBOARD FONT ATLAS")
    print("=" * 90)
    kbd_draws = [d for d in all_draws if d['tex0']['tbp0'] == 0x2840]
    print(f"Total: {len(kbd_draws)} draws")
    print(f"Texture: PSMT4 256x256 TBW=4 CBP=0x{kbd_draws[0]['tex0']['cbp']:04X}")
    print(f"Cell size: 16x16 (UV range 16 per cell)")

    # The UV coords tell us which 16x16 cell is being sampled
    # UV values are in 12.4 fixed point, so divide by 16
    # The .5 offset is GS half-pixel sampling
    print(f"\n{'Seq':>4} {'Screen X':>9} {'Screen Y':>9} {'UV_U0':>6} {'UV_V0':>6} {'UV_U1':>6} {'UV_V1':>6} {'Cell':>10} {'CellIdx':>8}")
    print("-" * 80)

    grid_positions = []
    for d in kbd_draws:
        ox, oy = d['xyoff']
        if len(d['verts']) >= 2 and len(d['uvs']) >= 2:
            # XYZ3 is kick-without-draw, XYZ2 is kick-with-draw
            # For SPRITE: first vertex = top-left, second = bottom-right
            x0 = (d['verts'][0][0] - ox) / 16.0
            y0 = (d['verts'][0][1] - oy) / 16.0
            x1 = (d['verts'][1][0] - ox) / 16.0
            y1 = (d['verts'][1][1] - oy) / 16.0
            u0 = d['uvs'][0][0] / 16.0
            v0 = d['uvs'][0][1] / 16.0
            u1 = d['uvs'][1][0] / 16.0
            v1 = d['uvs'][1][1] / 16.0

            # Cell index in the 256x256 PSMT4 atlas (16x16 cells = 16 columns x 16 rows)
            cell_col = int(round(u0)) // 16
            cell_row = int(round(v0)) // 16
            cell_idx = cell_row * 16 + cell_col

            grid_positions.append({
                'seq': d['seq'],
                'sx': x0, 'sy': y0,
                'sx1': x1, 'sy1': y1,
                'u0': u0, 'v0': v0, 'u1': u1, 'v1': v1,
                'cell_col': cell_col, 'cell_row': cell_row,
                'cell_idx': cell_idx,
            })

            print(f"{d['seq']:4d} {x0:9.1f} {y0:9.1f} {u0:6.1f} {v0:6.1f} {u1:6.1f} {v1:6.1f} "
                  f"({cell_col:2d},{cell_row:2d}) {cell_idx:8d}")

    # ===== GROUP BY SCREEN ROW =====
    print("\n" + "=" * 90)
    print("KEYBOARD GRID BY SCREEN ROW")
    print("=" * 90)

    rows = defaultdict(list)
    for gp in grid_positions:
        row = round(gp['sy'] / 10) * 10
        rows[row].append(gp)

    for row_y in sorted(rows.keys()):
        items = sorted(rows[row_y], key=lambda x: x['sx'])
        x_positions = [gp['sx'] for gp in items]
        cells = [(gp['cell_col'], gp['cell_row'], gp['cell_idx']) for gp in items]
        print(f"\n  Screen Y~{row_y}: {len(items)} chars")
        print(f"    X positions: {[f'{x:.0f}' for x in x_positions]}")
        print(f"    Cell indices: {[f'({c},{r})={idx}' for c,r,idx in cells]}")

        # Check for gaps in X spacing
        if len(x_positions) >= 2:
            spacings = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
            median_spacing = sorted(spacings)[len(spacings)//2] if spacings else 0
            print(f"    X spacings: {[f'{s:.0f}' for s in spacings]} (median: {median_spacing:.0f})")

            # Look for missing positions (gaps > 1.5x median)
            if median_spacing > 0:
                for i, sp in enumerate(spacings):
                    if sp > median_spacing * 1.5:
                        expected_x = x_positions[i] + median_spacing
                        print(f"    *** GAP at X~{expected_x:.0f} (spacing {sp:.0f} > {median_spacing:.0f})")

    # ===== ATLAS CELL MAP =====
    print("\n" + "=" * 90)
    print("ATLAS CELL USAGE MAP (256x256 PSMT4, 16x16 cells)")
    print("Cells used in this frame:")
    print("=" * 90)

    cell_usage = defaultdict(int)
    for gp in grid_positions:
        cell_usage[(gp['cell_col'], gp['cell_row'])] += 1

    # Print as grid
    print("     ", end="")
    for c in range(16):
        print(f"{c:3d}", end="")
    print()
    for r in range(16):
        print(f"  {r:2d}:", end="")
        for c in range(16):
            cnt = cell_usage.get((c, r), 0)
            if cnt > 0:
                print(f"{cnt:3d}", end="")
            else:
                print("  .", end="")
        print()

    # ===== SUMMARY STATS =====
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"Total keyboard character draws: {len(kbd_draws)}")
    print(f"Unique cells used: {len(cell_usage)}")
    print(f"Screen rows with draws: {len(rows)}")

    # Keyboard grid expected layout (for reference)
    # Original Japanese name entry has rows of characters
    # English keyboard has: Row 1: A-M, Row 2: N-Z, Row 3: numbers etc
    # Each row spans X=116 to X=340, spacing ~24px

    # Count draws per grid column position
    print("\n  Grid columns (by X position):")
    col_counts = defaultdict(int)
    for gp in grid_positions:
        col_x = round(gp['sx'] / 24) * 24
        col_counts[col_x] += 1
    for cx in sorted(col_counts.keys()):
        print(f"    X~{cx:4d}: {col_counts[cx]} draws")

    # ===== Check for specific X positions where F and M should be =====
    # If grid starts at X=116, spacing=24, then:
    # Row with ABCDEFGHIJ: F is at position 5 (0-indexed), X = 116 + 5*24 = 236
    # Row with KLMNOPQRST: M is at position 2, X = 116 + 2*24 = 164
    # But we need to verify the actual layout
    print("\n  Looking for F and M positions:")
    print("  (Need to correlate cell indices with actual characters)")

    # ===== ALL UNIQUE TEX0 values =====
    print("\n" + "=" * 90)
    print("ALL UNIQUE TEX0 CONFIGURATIONS IN FRAME")
    print("=" * 90)
    tex0_counts = defaultdict(int)
    for d in all_draws:
        t = d['tex0']
        key = (t['tbp0'], t['tbw'], t['psm'], t['tw'], t['th'], t['cbp'])
        tex0_counts[key] += 1

    for key in sorted(tex0_counts.keys()):
        tbp0, tbw, psm, tw, th, cbp = key
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        cnt = tex0_counts[key]
        print(f"  TBP0=0x{tbp0:04X} TBW={tbw} {psm_name:>10} {tw}x{th} CBP=0x{cbp:04X}: {cnt} draws")

    # ===== DRAW 28 raw data (first TBP0=0x2840 draw) =====
    print("\n" + "=" * 90)
    print("FIRST TBP0=0x2840 DRAW DETAILS")
    print("=" * 90)
    d = kbd_draws[0]
    print(f"  TEX0: tbp0=0x{d['tex0']['tbp0']:04X} tbw={d['tex0']['tbw']} "
          f"psm=0x{d['tex0']['psm']:02X} {d['tex0']['tw']}x{d['tex0']['th']} "
          f"cbp=0x{d['tex0']['cbp']:04X} cpsm={d['tex0']['cpsm']} csa={d['tex0']['csa']} "
          f"cld={d['tex0']['cld']}")
    print(f"  PRIM type={d['prim']} TME={d['tme']}")
    print(f"  XYOFFSET: {d['xyoff']}")
    print(f"  FRAME FBP: 0x{d['fbp']:03X}")
    print(f"  Vertices: {d['verts']}")
    print(f"  UVs: {d['uvs']}")


if __name__ == '__main__':
    main()
