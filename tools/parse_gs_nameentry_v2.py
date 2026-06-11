#!/usr/bin/env python3
"""Parse PCSX2 GS dump from NAME ENTRY screen - v2.

Better GIF parsing: handle PACKED mode with inline PRIM/UV/XYZ2 registers
(not just A+D blocks).
"""

import struct
import sys
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

REG_NAMES = {
    0x00: "PRIM", 0x01: "RGBAQ", 0x02: "ST", 0x03: "UV",
    0x04: "XYZF2", 0x05: "XYZ2", 0x06: "TEX0_1", 0x07: "TEX0_2",
    0x08: "CLAMP_1", 0x09: "CLAMP_2", 0x0A: "FOG",
    0x0C: "XYZF3", 0x0D: "XYZ3", 0x0E: "A+D", 0x0F: "NOP",
}


def parse_tex0(val):
    return {
        'tbp0': val & 0x3FFF,
        'tbw': (val >> 14) & 0x3F,
        'psm': (val >> 20) & 0x3F,
        'tw': 1 << ((val >> 26) & 0xF),
        'th': 1 << ((val >> 30) & 0xF),
        'tcc': (val >> 34) & 1,
        'tfx': (val >> 35) & 3,
        'cbp': (val >> 37) & 0x3FFF,
        'cpsm': (val >> 51) & 0xF,
        'csm': (val >> 55) & 1,
        'csa': (val >> 56) & 0x1F,
        'cld': (val >> 61) & 7,
    }


class RenderState:
    def __init__(self):
        self.tex0 = None  # parsed dict
        self.tex0_raw = 0
        self.prim_type = 6
        self.tme = 0
        self.abe = 0
        self.frame_fbp = 0
        self.frame_fbw = 0
        self.xyoffset = (0, 0)


class DrawCall:
    def __init__(self, state, vertices, uvs, sts, vsync, pkt, seq):
        self.tex0 = state.tex0 if state.tex0 else {}
        self.tbp0 = self.tex0.get('tbp0', 0)
        self.tbw = self.tex0.get('tbw', 0)
        self.psm = self.tex0.get('psm', 0)
        self.tw = self.tex0.get('tw', 0)
        self.th = self.tex0.get('th', 0)
        self.cbp = self.tex0.get('cbp', 0)
        self.cpsm = self.tex0.get('cpsm', 0)
        self.csa = self.tex0.get('csa', 0)
        self.prim_type = state.prim_type
        self.tme = state.tme
        self.vertices = vertices  # list of (x, y, z) raw GS fixed-point
        self.uvs = uvs
        self.sts = sts
        self.frame_fbp = state.frame_fbp
        self.xyoffset = state.xyoffset
        self.vsync = vsync
        self.packet_idx = pkt
        self.seq = seq


def parse_dump(path):
    print(f"Reading: {path}")
    dctx = zstd.ZstdDecompressor()
    with open(path, 'rb') as f:
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
    pos += 36

    serial_abs = 8 + serial_offset
    serial = data[serial_abs:serial_abs + serial_size].decode("ascii", errors="replace")
    print(f"Serial: {serial}, CRC: 0x{crc:08X}")

    data_start = 8 + header_total_size
    packets_start = data_start + state_size + 0x2000
    print(f"Packets start: 0x{packets_start:X}, remaining: {len(data) - packets_start} bytes")

    # Parse packets
    pos = packets_start
    vsync_count = 0
    packet_idx = 0

    state = RenderState()
    draw_calls = []
    bitblt_writes = []
    draw_seq = 0

    # Debug counters
    gif_tag_count = 0
    packed_vertex_count = 0
    reglist_vertex_count = 0
    ad_vertex_count = 0
    prim_inline_count = 0

    while pos < len(data):
        tag = data[pos]
        pos += 1

        if tag == 0:  # Transfer
            if pos + 5 > len(data):
                break
            path_idx = data[pos]
            pos += 1
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            if pos + size > len(data):
                break
            gif_data = data[pos:pos + size]
            pos += size

            # Parse GIF packets
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
                if nreg == 0:
                    nreg = 16
                gpos += 16
                gif_tag_count += 1

                # PRE bit: if set, PRIM field contains PRIM register value
                if pre and flg != 2:  # not IMAGE mode
                    state.prim_type = prim_data & 0x7
                    state.tme = (prim_data >> 4) & 1
                    state.abe = (prim_data >> 6) & 1
                    prim_inline_count += 1

                regs = []
                for r in range(nreg):
                    regs.append((hi >> (r * 4)) & 0xF)

                if flg == 0:  # PACKED mode
                    current_verts = []
                    current_uvs = []
                    current_sts = []

                    for loop in range(nloop):
                        for ri, reg_id in enumerate(regs):
                            if gpos + 16 > len(gif_data):
                                break
                            plo = struct.unpack_from("<Q", gif_data, gpos)[0]
                            phi = struct.unpack_from("<Q", gif_data, gpos + 8)[0]

                            if reg_id == 0x0E:  # A+D
                                reg_data = plo
                                reg_addr = phi & 0xFF
                                # Process A+D register
                                if reg_addr in (0x06, 0x07):  # TEX0
                                    state.tex0 = parse_tex0(reg_data)
                                    state.tex0_raw = reg_data
                                elif reg_addr == 0x00:  # PRIM via A+D
                                    state.prim_type = reg_data & 0x7
                                    state.tme = (reg_data >> 4) & 1
                                    state.abe = (reg_data >> 6) & 1
                                elif reg_addr in (0x4C, 0x4D):  # FRAME
                                    state.frame_fbp = reg_data & 0x1FF
                                    state.frame_fbw = (reg_data >> 16) & 0x3F
                                elif reg_addr == 0x18:  # XYOFFSET_1
                                    ox = reg_data & 0xFFFF
                                    oy = (reg_data >> 32) & 0xFFFF
                                    state.xyoffset = (ox, oy)
                                elif reg_addr == 0x50:  # BITBLTBUF
                                    sbp = reg_data & 0x3FFF
                                    sbw = (reg_data >> 16) & 0x3F
                                    spsm = (reg_data >> 24) & 0x3F
                                    dbp = (reg_data >> 32) & 0x3FFF
                                    dbw = (reg_data >> 48) & 0x3F
                                    dpsm = (reg_data >> 56) & 0x3F
                                    bitblt_writes.append({
                                        'sbp': sbp, 'sbw': sbw, 'spsm': spsm,
                                        'dbp': dbp, 'dbw': dbw, 'dpsm': dpsm,
                                        'vsync': vsync_count, 'packet': packet_idx,
                                    })
                                elif reg_addr in (0x04, 0x0C):  # XYZF2/XYZF3 via A+D
                                    x = reg_data & 0xFFFF
                                    y = (reg_data >> 16) & 0xFFFF
                                    z = (reg_data >> 32) & 0xFFFFFF
                                    current_verts.append((x, y, z))
                                    ad_vertex_count += 1
                                elif reg_addr in (0x05, 0x0D):  # XYZ2/XYZ3 via A+D
                                    x = reg_data & 0xFFFF
                                    y = (reg_data >> 16) & 0xFFFF
                                    z = (reg_data >> 32) & 0xFFFFFFFF
                                    current_verts.append((x, y, z))
                                    ad_vertex_count += 1
                                elif reg_addr == 0x03:  # UV via A+D
                                    u = reg_data & 0x3FFF
                                    v = (reg_data >> 16) & 0x3FFF
                                    current_uvs.append((u, v))

                            elif reg_id == 0x05:  # XYZ2 packed
                                # Packed XYZ2: X=[15:0] in lo, Y=[47:32] (i.e. bits 32-47 of 128-bit)
                                # Actually in PACKED format:
                                # DATA[31:0] = X (unsigned, sub-pixel 12.4)
                                # DATA[63:32] = Y (unsigned, sub-pixel 12.4)
                                # DATA[95:64] = Z
                                # DATA[111:96] = unused
                                # DATA[112] = ADC bit (drawing kick)
                                # lo has bits 0-63, phi has bits 64-127
                                x = plo & 0xFFFF  # lower 16 bits of X
                                y = (plo >> 32) & 0xFFFF  # lower 16 bits of Y
                                z = phi & 0xFFFFFFFF  # Z
                                adc = (phi >> 47) & 1  # ADC bit (bit 111 from start = bit 47 of hi)
                                current_verts.append((x, y, z))
                                packed_vertex_count += 1

                            elif reg_id == 0x04:  # XYZF2 packed
                                x = plo & 0xFFFF
                                y = (plo >> 32) & 0xFFFF
                                z = (phi >> 4) & 0xFFFFFF  # Z in bits [75:48] -> bits [27:4] of phi
                                current_verts.append((x, y, z))
                                packed_vertex_count += 1

                            elif reg_id == 0x0D:  # XYZ3 packed
                                x = plo & 0xFFFF
                                y = (plo >> 32) & 0xFFFF
                                z = phi & 0xFFFFFFFF
                                current_verts.append((x, y, z))
                                packed_vertex_count += 1

                            elif reg_id == 0x03:  # UV packed
                                # Packed UV: U=[13:0] in bits[13:0], V=[13:0] in bits[45:32]
                                u = plo & 0x3FFF
                                v = (plo >> 32) & 0x3FFF
                                current_uvs.append((u, v))

                            elif reg_id == 0x02:  # ST packed
                                s = struct.unpack('<f', struct.pack('<I', plo & 0xFFFFFFFF))[0]
                                t = struct.unpack('<f', struct.pack('<I', (plo >> 32) & 0xFFFFFFFF))[0]
                                current_sts.append((s, t))

                            elif reg_id == 0x00:  # PRIM packed
                                state.prim_type = plo & 0x7
                                state.tme = (plo >> 4) & 1
                                state.abe = (plo >> 6) & 1

                            gpos += 16

                    # After processing all loops, if we have vertices, create a draw call
                    if current_verts and state.tme and state.tex0:
                        dc = DrawCall(state, current_verts, current_uvs, current_sts,
                                      vsync_count, packet_idx, draw_seq)
                        draw_calls.append(dc)
                        draw_seq += 1

                elif flg == 1:  # REGLIST mode
                    current_verts = []
                    current_uvs = []
                    current_sts = []

                    total_regs = nloop * nreg
                    for i in range(total_regs):
                        if gpos + 8 > len(gif_data):
                            break
                        reg_id = regs[i % nreg]
                        rd = struct.unpack_from("<Q", gif_data, gpos)[0]

                        if reg_id == 0x05:  # XYZ2
                            x = rd & 0xFFFF
                            y = (rd >> 16) & 0xFFFF
                            z = (rd >> 32) & 0xFFFFFFFF
                            current_verts.append((x, y, z))
                            reglist_vertex_count += 1
                        elif reg_id == 0x04:  # XYZF2
                            x = rd & 0xFFFF
                            y = (rd >> 16) & 0xFFFF
                            z = (rd >> 32) & 0xFFFFFF
                            current_verts.append((x, y, z))
                            reglist_vertex_count += 1
                        elif reg_id == 0x03:  # UV
                            u = rd & 0x3FFF
                            v = (rd >> 16) & 0x3FFF
                            current_uvs.append((u, v))
                        elif reg_id == 0x02:  # ST
                            s = struct.unpack('<f', struct.pack('<I', rd & 0xFFFFFFFF))[0]
                            t = struct.unpack('<f', struct.pack('<I', (rd >> 32) & 0xFFFFFFFF))[0]
                            current_sts.append((s, t))

                        gpos += 8
                    if (total_regs % 2) == 1:
                        gpos += 8

                    if current_verts and state.tme and state.tex0:
                        dc = DrawCall(state, current_verts, current_uvs, current_sts,
                                      vsync_count, packet_idx, draw_seq)
                        draw_calls.append(dc)
                        draw_seq += 1

                elif flg == 2:  # IMAGE mode
                    gpos += nloop * 16

                if eop:
                    break

        elif tag == 1:  # VSync
            if pos + 1 > len(data):
                break
            pos += 1
            vsync_count += 1

        elif tag == 2:  # ReadFIFO2
            if pos + 4 > len(data):
                break
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4

        elif tag == 3:  # Registers
            if pos + 0x2000 > len(data):
                break
            pos += 0x2000
        else:
            print(f"Unknown tag 0x{tag:02X} at 0x{pos-1:X}")
            break

        packet_idx += 1

    print(f"\nParsed: {vsync_count} vsyncs, {draw_seq} textured draw calls")
    print(f"  GIF tags: {gif_tag_count}")
    print(f"  PRIM inline (PRE bit): {prim_inline_count}")
    print(f"  Packed vertices: {packed_vertex_count}")
    print(f"  REGLIST vertices: {reglist_vertex_count}")
    print(f"  A+D vertices: {ad_vertex_count}")
    print(f"  BITBLTBUF writes: {len(bitblt_writes)}")

    return draw_calls, bitblt_writes


def analyze_draws(draw_calls, bitblt_writes):
    # ===== 1. ALL UNIQUE TEX0 CONFIGS =====
    print("\n" + "=" * 90)
    print("ALL UNIQUE TEX0 CONFIGURATIONS (textured draws only)")
    print("=" * 90)
    tex0_counts = defaultdict(int)
    for dc in draw_calls:
        key = (dc.tbp0, dc.tbw, dc.psm, dc.tw, dc.th, dc.cbp, dc.cpsm, dc.csa)
        tex0_counts[key] += 1

    print(f"{'TBP0':>8} {'TBW':>4} {'PSM':>10} {'Size':>10} {'CBP':>8} {'CPSM':>10} {'CSA':>4} {'Draws':>6}")
    print("-" * 75)
    for key in sorted(tex0_counts.keys()):
        tbp0, tbw, psm, tw, th, cbp, cpsm, csa = key
        cnt = tex0_counts[key]
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        cpsm_name = PSM_NAMES.get(cpsm, f"0x{cpsm:02X}")
        marker = ""
        if psm == 0x14: marker += " [PSMT4]"
        if tbp0 == 0x2840: marker += " <-- 0x2840!"
        if tbp0 == 0x3000: marker += " <-- 0x3000!"
        print(f"0x{tbp0:04X} {tbw:4d} {psm_name:>10} {tw:4d}x{th:<4d} 0x{cbp:04X} {cpsm_name:>10} {csa:4d} {cnt:6d}{marker}")

    # ===== 2. ALL PSMT4 DRAWS WITH POSITIONS =====
    print("\n" + "=" * 90)
    print("ALL PSMT4 TEXTURED DRAWS WITH SCREEN POSITIONS")
    print("=" * 90)
    psmt4_draws = [dc for dc in draw_calls if dc.psm == 0x14]
    print(f"Total PSMT4 draws: {len(psmt4_draws)}")

    by_tbp0 = defaultdict(list)
    for dc in psmt4_draws:
        by_tbp0[dc.tbp0].append(dc)

    for tbp0 in sorted(by_tbp0.keys()):
        draws = by_tbp0[tbp0]
        print(f"\n--- TBP0=0x{tbp0:04X} TBW={draws[0].tbw} tex={draws[0].tw}x{draws[0].th} "
              f"CBP=0x{draws[0].cbp:04X} ({len(draws)} draws) ---")
        for dc in draws[:200]:
            ox, oy = dc.xyoffset
            if dc.vertices:
                coords = [((vx - ox) / 16.0, (vy - oy) / 16.0) for vx, vy, vz in dc.vertices]
                min_x = min(c[0] for c in coords)
                min_y = min(c[1] for c in coords)
                max_x = max(c[0] for c in coords)
                max_y = max(c[1] for c in coords)

                uv_str = ""
                if dc.uvs:
                    uv_coords = [(u / 16.0, v / 16.0) for u, v in dc.uvs]
                    uv_str = f" UV=({min(u for u,v in uv_coords):.1f},{min(v for u,v in uv_coords):.1f})-({max(u for u,v in uv_coords):.1f},{max(v for u,v in uv_coords):.1f})"
                elif dc.sts:
                    uv_str = f" ST=({min(s for s,t in dc.sts):.4f},{min(t for s,t in dc.sts):.4f})-({max(s for s,t in dc.sts):.4f},{max(t for s,t in dc.sts):.4f})"

                prim_name = PRIM_TYPES.get(dc.prim_type, str(dc.prim_type))
                print(f"  [{dc.seq:4d}] scr=({min_x:6.1f},{min_y:6.1f})-({max_x:6.1f},{max_y:6.1f}) "
                      f"{prim_name:>8} v={len(dc.vertices)} CSA={dc.csa}{uv_str}")

    # ===== 3. GRID REGION =====
    print("\n" + "=" * 90)
    print("KEYBOARD GRID REGION ANALYSIS (X=50-600, Y=100-500)")
    print("Small draws that could be character cells")
    print("=" * 90)

    grid_draws = []
    for dc in draw_calls:
        if not dc.vertices:
            continue
        ox, oy = dc.xyoffset
        coords = [((vx - ox) / 16.0, (vy - oy) / 16.0) for vx, vy, vz in dc.vertices]
        min_x = min(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_x = max(c[0] for c in coords)
        max_y = max(c[1] for c in coords)
        w = max_x - min_x
        h = max_y - min_y

        if 50 <= min_x <= 600 and 100 <= min_y <= 500 and w <= 40 and h <= 40 and w > 0 and h > 0:
            grid_draws.append((dc, min_x, min_y, max_x, max_y, w, h))

    print(f"Found {len(grid_draws)} small draws in grid region")

    # Group by Y
    rows = defaultdict(list)
    for dc, min_x, min_y, max_x, max_y, w, h in grid_draws:
        row_y = round(min_y / 4) * 4
        rows[row_y].append((dc, min_x, min_y, max_x, max_y, w, h))

    for row_y in sorted(rows.keys()):
        items = sorted(rows[row_y], key=lambda x: x[1])
        psm_types = set(PSM_NAMES.get(i[0].psm, f"0x{i[0].psm:02X}") for i in items)
        print(f"\n  Row Y~{row_y}: {len(items)} draws (PSM types: {psm_types})")
        for dc, min_x, min_y, max_x, max_y, w, h in items:
            psm_name = PSM_NAMES.get(dc.psm, f"0x{dc.psm:02X}")
            uv_str = ""
            if dc.uvs:
                uv_coords = [(u / 16.0, v / 16.0) for u, v in dc.uvs]
                uv_str = f" UV=({uv_coords[0][0]:.1f},{uv_coords[0][1]:.1f})"
                if len(uv_coords) > 1:
                    uv_str += f"..({uv_coords[-1][0]:.1f},{uv_coords[-1][1]:.1f})"
            elif dc.sts:
                uv_str = f" ST=({dc.sts[0][0]:.3f},{dc.sts[0][1]:.3f})"
            print(f"    X={min_x:6.1f}-{max_x:6.1f} [{w:.0f}x{h:.0f}] TBP0=0x{dc.tbp0:04X} {psm_name} "
                  f"CBP=0x{dc.cbp:04X} CSA={dc.csa}{uv_str}")

    # ===== 4. FULL DRAW SEQUENCE =====
    print("\n" + "=" * 90)
    print(f"FULL DRAW SEQUENCE (all {len(draw_calls)} draws)")
    print("=" * 90)
    for dc in draw_calls[:400]:
        psm_name = PSM_NAMES.get(dc.psm, f"0x{dc.psm:02X}")
        ox, oy = dc.xyoffset
        pos_str = "no-verts"
        if dc.vertices:
            coords = [((vx - ox) / 16.0, (vy - oy) / 16.0) for vx, vy, vz in dc.vertices]
            min_x = min(c[0] for c in coords)
            min_y = min(c[1] for c in coords)
            max_x = max(c[0] for c in coords)
            max_y = max(c[1] for c in coords)
            pos_str = f"({min_x:6.1f},{min_y:6.1f})-({max_x:6.1f},{max_y:6.1f})"

        uv_str = ""
        if dc.uvs:
            uv_coords = [(u / 16.0, v / 16.0) for u, v in dc.uvs]
            uv_str = f" UV({min(u for u,v in uv_coords):.0f},{min(v for u,v in uv_coords):.0f})-({max(u for u,v in uv_coords):.0f},{max(v for u,v in uv_coords):.0f})"

        prim_name = PRIM_TYPES.get(dc.prim_type, str(dc.prim_type))
        print(f"  [{dc.seq:4d}] vs{dc.vsync} TBP0=0x{dc.tbp0:04X} TBW={dc.tbw} {psm_name:>8} "
              f"{dc.tw}x{dc.th} CBP=0x{dc.cbp:04X} CSA={dc.csa:2d} "
              f"FBP=0x{dc.frame_fbp:03X} {prim_name:>8} v={len(dc.vertices):3d} {pos_str}{uv_str}")

    if len(draw_calls) > 400:
        print(f"  ... ({len(draw_calls) - 400} more)")

    # ===== 5. TBP0=0x2840 =====
    print("\n" + "=" * 90)
    print("TBP0=0x2840 ANALYSIS")
    print("=" * 90)
    tbp_2840 = [dc for dc in draw_calls if dc.tbp0 == 0x2840]
    if tbp_2840:
        print(f"Found {len(tbp_2840)} draws using TBP0=0x2840")
        for dc in tbp_2840:
            print(f"  seq={dc.seq} psm=0x{dc.psm:02X} {dc.tw}x{dc.th} tbw={dc.tbw}")
    else:
        print("NO draws use TBP0=0x2840")
        print("\nBITBLTBUF involving 0x2840:")
        found = False
        for bb in bitblt_writes:
            if bb['sbp'] == 0x2840 or bb['dbp'] == 0x2840:
                sn = PSM_NAMES.get(bb['spsm'], f"0x{bb['spsm']:02X}")
                dn = PSM_NAMES.get(bb['dpsm'], f"0x{bb['dpsm']:02X}")
                print(f"  SBP=0x{bb['sbp']:04X}({sn}) -> DBP=0x{bb['dbp']:04X}({dn})")
                found = True
        if not found:
            print("  None found")

    # ===== 6. BITBLTBUF =====
    print("\n" + "=" * 90)
    print("ALL VRAM COPIES (BITBLTBUF)")
    print("=" * 90)
    for i, bb in enumerate(bitblt_writes):
        sn = PSM_NAMES.get(bb['spsm'], f"0x{bb['spsm']:02X}")
        dn = PSM_NAMES.get(bb['dpsm'], f"0x{bb['dpsm']:02X}")
        print(f"  [{i:2d}] SBP=0x{bb['sbp']:04X}(tbw={bb['sbw']},{sn}) -> "
              f"DBP=0x{bb['dbp']:04X}(tbw={bb['dbw']},{dn}) vsync#{bb['vsync']}")


def main():
    draw_calls, bitblt_writes = parse_dump(GS_DUMP)
    analyze_draws(draw_calls, bitblt_writes)


if __name__ == '__main__':
    main()
