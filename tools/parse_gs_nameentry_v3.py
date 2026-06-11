#!/usr/bin/env python3
"""Parse PCSX2 GS dump from NAME ENTRY screen - v3.

Debug version: dump raw GIF tag info and register state to understand
why no textured draws are being captured.
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

REG_NAMES_4BIT = {
    0x00: "PRIM", 0x01: "RGBAQ", 0x02: "ST", 0x03: "UV",
    0x04: "XYZF2", 0x05: "XYZ2", 0x06: "TEX0_1", 0x07: "TEX0_2",
    0x08: "CLAMP_1", 0x09: "CLAMP_2", 0x0A: "FOG",
    0x0C: "XYZF3", 0x0D: "XYZ3", 0x0E: "A+D", 0x0F: "NOP",
}

REG_NAMES_8BIT = {
    0x00: "PRIM", 0x01: "RGBAQ", 0x02: "ST", 0x03: "UV",
    0x04: "XYZF2", 0x05: "XYZ2", 0x06: "TEX0_1", 0x07: "TEX0_2",
    0x08: "CLAMP_1", 0x09: "CLAMP_2", 0x0A: "FOG",
    0x0C: "XYZF3", 0x0D: "XYZ3", 0x0E: "A+D", 0x0F: "NOP",
    0x14: "TEX1_1", 0x18: "XYOFFSET_1", 0x1A: "PRMODECONT",
    0x3F: "TEXA", 0x40: "FOGCOL", 0x42: "TEXFLUSH",
    0x43: "SCISSOR_1", 0x45: "ALPHA_1",
    0x47: "DIMX", 0x48: "DTHE", 0x49: "COLCLAMP",
    0x4A: "TEST_1", 0x4C: "FRAME_1", 0x4E: "ZBUF_1",
    0x50: "BITBLTBUF", 0x51: "TRXPOS", 0x52: "TRXREG", 0x53: "TRXDIR",
}


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
    fake_crc = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    header_total_size = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    hdr = struct.unpack_from("<9I", data, pos)
    state_version, state_size, serial_offset, serial_size, crc, \
        ss_width, ss_height, ss_offset, ss_size = hdr

    serial_abs = 8 + serial_offset
    serial = data[serial_abs:serial_abs + serial_size].decode("ascii", errors="replace")
    print(f"Serial: {serial}, CRC: 0x{crc:08X}")

    data_start = 8 + header_total_size
    packets_start = data_start + state_size + 0x2000

    # Render state
    cur_tex0 = None
    cur_prim_type = 6
    cur_tme = 0
    cur_frame_fbp = 0
    cur_xyoffset = (0, 0)

    # Results
    draw_calls = []
    draw_seq = 0

    # Parse packets
    pos = packets_start
    vsync_count = 0
    packet_idx = 0

    # Only analyze first 2 vsyncs (one frame)
    while pos < len(data) and vsync_count < 2:
        tag = data[pos]
        pos += 1

        if tag == 0:  # Transfer
            if pos + 5 > len(data): break
            path_idx = data[pos]; pos += 1
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            if pos + size > len(data): break
            gif_data = data[pos:pos + size]
            pos += size

            # Parse GIF tags
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

                # Extract reg descriptor names
                reg_ids = [(hi >> (r * 4)) & 0xF for r in range(nreg)]
                reg_names = [REG_NAMES_4BIT.get(r, f"0x{r:X}") for r in reg_ids]

                flg_names = {0: "PACKED", 1: "REGLIST", 2: "IMAGE", 3: "DISABLED"}

                if flg == 0:  # PACKED
                    # Handle PRE bit
                    if pre:
                        cur_prim_type = prim_data & 0x7
                        cur_tme = (prim_data >> 4) & 1

                    verts = []
                    uvs = []
                    sts = []

                    for loop in range(nloop):
                        for ri, reg_id in enumerate(reg_ids):
                            if gpos + 16 > len(gif_data): break
                            plo = struct.unpack_from("<Q", gif_data, gpos)[0]
                            phi = struct.unpack_from("<Q", gif_data, gpos + 8)[0]

                            if reg_id == 0x0E:  # A+D
                                reg_addr = phi & 0xFF
                                if reg_addr in (0x06, 0x07):
                                    cur_tex0 = parse_tex0(plo)
                                elif reg_addr == 0x00:  # PRIM
                                    cur_prim_type = plo & 0x7
                                    cur_tme = (plo >> 4) & 1
                                elif reg_addr in (0x4C, 0x4D):
                                    cur_frame_fbp = plo & 0x1FF
                                elif reg_addr == 0x18:
                                    cur_xyoffset = (plo & 0xFFFF, (plo >> 32) & 0xFFFF)
                                elif reg_addr in (0x04, 0x0C):
                                    x = plo & 0xFFFF; y = (plo >> 16) & 0xFFFF
                                    verts.append((x, y, 0))
                                elif reg_addr in (0x05, 0x0D):
                                    x = plo & 0xFFFF; y = (plo >> 16) & 0xFFFF
                                    verts.append((x, y, 0))
                                elif reg_addr == 0x03:
                                    u = plo & 0x3FFF; v = (plo >> 16) & 0x3FFF
                                    uvs.append((u, v))

                            elif reg_id == 0x05:  # XYZ2 packed
                                x = plo & 0xFFFF; y = (plo >> 32) & 0xFFFF
                                verts.append((x, y, phi & 0xFFFFFFFF))

                            elif reg_id == 0x04:  # XYZF2 packed
                                x = plo & 0xFFFF; y = (plo >> 32) & 0xFFFF
                                verts.append((x, y, 0))

                            elif reg_id == 0x03:  # UV packed
                                u = plo & 0x3FFF; v = (plo >> 32) & 0x3FFF
                                uvs.append((u, v))

                            elif reg_id == 0x02:  # ST packed
                                s = struct.unpack('<f', struct.pack('<I', plo & 0xFFFFFFFF))[0]
                                t = struct.unpack('<f', struct.pack('<I', (plo >> 32) & 0xFFFFFFFF))[0]
                                sts.append((s, t))

                            elif reg_id == 0x01:  # RGBAQ packed
                                pass  # skip

                            elif reg_id == 0x00:  # PRIM packed
                                cur_prim_type = plo & 0x7
                                cur_tme = (plo >> 4) & 1

                            gpos += 16

                    if verts:
                        draw_calls.append({
                            'seq': draw_seq,
                            'tex0': dict(cur_tex0) if cur_tex0 else None,
                            'prim': cur_prim_type,
                            'tme': cur_tme,
                            'verts': verts,
                            'uvs': uvs,
                            'sts': sts,
                            'xyoff': cur_xyoffset,
                            'fbp': cur_frame_fbp,
                            'vsync': vsync_count,
                            'pkt': packet_idx,
                            'nloop': nloop,
                            'regs': reg_names,
                            'flg': 'PACKED',
                        })
                        draw_seq += 1

                elif flg == 1:  # REGLIST
                    # Handle PRE bit
                    if pre:
                        cur_prim_type = prim_data & 0x7
                        cur_tme = (prim_data >> 4) & 1

                    verts = []
                    uvs = []
                    sts = []

                    total_regs = nloop * nreg
                    for i in range(total_regs):
                        if gpos + 8 > len(gif_data): break
                        reg_id = reg_ids[i % nreg]
                        rd = struct.unpack_from("<Q", gif_data, gpos)[0]

                        if reg_id == 0x05:  # XYZ2
                            x = rd & 0xFFFF; y = (rd >> 16) & 0xFFFF
                            verts.append((x, y, (rd >> 32) & 0xFFFFFFFF))
                        elif reg_id == 0x04:  # XYZF2
                            x = rd & 0xFFFF; y = (rd >> 16) & 0xFFFF
                            verts.append((x, y, 0))
                        elif reg_id == 0x03:  # UV
                            u = rd & 0x3FFF; v = (rd >> 16) & 0x3FFF
                            uvs.append((u, v))
                        elif reg_id == 0x02:  # ST
                            s = struct.unpack('<f', struct.pack('<I', rd & 0xFFFFFFFF))[0]
                            t = struct.unpack('<f', struct.pack('<I', (rd >> 32) & 0xFFFFFFFF))[0]
                            sts.append((s, t))

                        gpos += 8

                    if (total_regs % 2) == 1:
                        gpos += 8  # pad to 16 bytes

                    if verts:
                        draw_calls.append({
                            'seq': draw_seq,
                            'tex0': dict(cur_tex0) if cur_tex0 else None,
                            'prim': cur_prim_type,
                            'tme': cur_tme,
                            'verts': verts,
                            'uvs': uvs,
                            'sts': sts,
                            'xyoff': cur_xyoffset,
                            'fbp': cur_frame_fbp,
                            'vsync': vsync_count,
                            'pkt': packet_idx,
                            'nloop': nloop,
                            'regs': reg_names,
                            'flg': 'REGLIST',
                        })
                        draw_seq += 1

                elif flg == 2:  # IMAGE
                    gpos += nloop * 16

                if eop:
                    break

        elif tag == 1:
            if pos + 1 > len(data): break
            pos += 1
            vsync_count += 1
        elif tag == 2:
            if pos + 4 > len(data): break
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
        elif tag == 3:
            if pos + 0x2000 > len(data): break
            pos += 0x2000
        else:
            break

        packet_idx += 1

    print(f"\nParsed: {vsync_count} vsyncs, {len(draw_calls)} draw calls (with vertices)")

    # ===== DUMP ALL DRAW CALLS =====
    print("\n" + "=" * 100)
    print("ALL DRAW CALLS (first frame)")
    print("=" * 100)

    textured_count = 0
    untextured_count = 0

    for dc in draw_calls:
        tex0 = dc['tex0']
        tme = dc['tme']
        ox, oy = dc['xyoff']
        verts = dc['verts']

        coords = [((vx - ox) / 16.0, (vy - oy) / 16.0) for vx, vy, vz in verts]
        min_x = min(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_x = max(c[0] for c in coords)
        max_y = max(c[1] for c in coords)

        prim_name = PRIM_TYPES.get(dc['prim'], str(dc['prim']))

        tex_str = "NO_TEX0"
        if tex0:
            psm_name = PSM_NAMES.get(tex0['psm'], f"0x{tex0['psm']:02X}")
            tex_str = f"TBP0=0x{tex0['tbp0']:04X} TBW={tex0['tbw']} {psm_name} {tex0['tw']}x{tex0['th']} CBP=0x{tex0['cbp']:04X} CSA={tex0['csa']}"

        uv_str = ""
        if dc['uvs']:
            uv_coords = [(u/16.0, v/16.0) for u, v in dc['uvs']]
            uv_str = f" UV=({min(u for u,v in uv_coords):.1f},{min(v for u,v in uv_coords):.1f})-({max(u for u,v in uv_coords):.1f},{max(v for u,v in uv_coords):.1f})"
        elif dc['sts']:
            uv_str = f" ST=({min(s for s,t in dc['sts']):.4f},{min(t for s,t in dc['sts']):.4f})-({max(s for s,t in dc['sts']):.4f},{max(t for s,t in dc['sts']):.4f})"

        tme_mark = "TME=1" if tme else "TME=0"
        if tme:
            textured_count += 1
        else:
            untextured_count += 1

        print(f"  [{dc['seq']:4d}] {dc['flg']:>8} {prim_name:>8} {tme_mark} v={len(verts):3d} "
              f"scr=({min_x:6.1f},{min_y:6.1f})-({max_x:6.1f},{max_y:6.1f}) "
              f"FBP=0x{dc['fbp']:03X} "
              f"regs={','.join(dc['regs'])} "
              f"{tex_str}{uv_str}")

    print(f"\nSummary: {textured_count} textured, {untextured_count} untextured")

    # ===== TEXTURED DRAWS ONLY =====
    textured = [dc for dc in draw_calls if dc['tme']]
    print(f"\n{'=' * 100}")
    print(f"TEXTURED DRAWS ONLY ({len(textured)})")
    print(f"{'=' * 100}")

    for dc in textured:
        tex0 = dc['tex0']
        ox, oy = dc['xyoff']
        verts = dc['verts']
        coords = [((vx - ox) / 16.0, (vy - oy) / 16.0) for vx, vy, vz in verts]
        min_x = min(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_x = max(c[0] for c in coords)
        max_y = max(c[1] for c in coords)

        psm_name = PSM_NAMES.get(tex0['psm'], f"0x{tex0['psm']:02X}") if tex0 else "?"
        tbp0 = tex0['tbp0'] if tex0 else 0
        prim_name = PRIM_TYPES.get(dc['prim'], str(dc['prim']))

        uv_str = ""
        if dc['uvs']:
            uv_coords = [(u/16.0, v/16.0) for u, v in dc['uvs']]
            uv_str = f" UV=({min(u for u,v in uv_coords):.1f},{min(v for u,v in uv_coords):.1f})-({max(u for u,v in uv_coords):.1f},{max(v for u,v in uv_coords):.1f})"
        elif dc['sts']:
            uv_str = f" ST=({min(s for s,t in dc['sts']):.4f},{min(t for s,t in dc['sts']):.4f})-({max(s for s,t in dc['sts']):.4f},{max(t for s,t in dc['sts']):.4f})"

        print(f"  [{dc['seq']:4d}] {prim_name:>8} scr=({min_x:6.1f},{min_y:6.1f})-({max_x:6.1f},{max_y:6.1f}) "
              f"TBP0=0x{tbp0:04X} {psm_name} "
              f"{tex0['tw']}x{tex0['th']} CBP=0x{tex0['cbp']:04X} CSA={tex0['csa']}"
              f"{uv_str}")

    # ===== PSMT4 TEXTURED ANALYSIS =====
    psmt4_textured = [dc for dc in textured if dc['tex0'] and dc['tex0']['psm'] == 0x14]
    print(f"\n{'=' * 100}")
    print(f"PSMT4 TEXTURED DRAWS ({len(psmt4_textured)})")
    print(f"{'=' * 100}")

    if psmt4_textured:
        # Group by position row
        by_y = defaultdict(list)
        for dc in psmt4_textured:
            ox, oy = dc['xyoff']
            coords = [((vx - ox) / 16.0, (vy - oy) / 16.0) for vx, vy, vz in dc['verts']]
            min_x = min(c[0] for c in coords)
            min_y = min(c[1] for c in coords)
            max_x = max(c[0] for c in coords)
            max_y = max(c[1] for c in coords)
            row = round(min_y / 4) * 4
            by_y[row].append((dc, min_x, min_y, max_x, max_y))

        for row in sorted(by_y.keys()):
            items = sorted(by_y[row], key=lambda x: x[1])
            print(f"\n  Row Y~{row} ({len(items)} draws):")
            for dc, min_x, min_y, max_x, max_y in items:
                tex0 = dc['tex0']
                uv_str = ""
                if dc['uvs']:
                    uv_coords = [(u/16.0, v/16.0) for u, v in dc['uvs']]
                    uv_str = f" UV({min(u for u,v in uv_coords):.0f},{min(v for u,v in uv_coords):.0f})-({max(u for u,v in uv_coords):.0f},{max(v for u,v in uv_coords):.0f})"
                print(f"    X={min_x:6.1f}-{max_x:6.1f} TBP0=0x{tex0['tbp0']:04X} TBW={tex0['tbw']} "
                      f"CBP=0x{tex0['cbp']:04X} CSA={tex0['csa']}{uv_str}")
    else:
        print("  NONE - no PSMT4 textured draws!")
        print("\n  All textured PSM types:")
        psm_counts = defaultdict(int)
        for dc in textured:
            if dc['tex0']:
                psm_counts[dc['tex0']['psm']] += 1
        for psm, cnt in sorted(psm_counts.items()):
            print(f"    {PSM_NAMES.get(psm, f'0x{psm:02X}')}: {cnt} draws")


if __name__ == '__main__':
    main()
