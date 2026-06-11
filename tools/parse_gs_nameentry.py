#!/usr/bin/env python3
"""Parse PCSX2 GS dump from NAME ENTRY screen.

Focus: Find ALL textured draws (especially PSMT4 font draws) in the keyboard
grid region, identify draw positions for F and M characters, and check
whether they are drawn or skipped.

Key questions:
1. What TBP0/TBW/CBP is used for keyboard character draws?
2. Are F and M drawn or are there gaps?
3. What texture data sits at TBP0=0x2840?
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


class DrawCall:
    """Represents a single textured draw call."""
    def __init__(self):
        self.tex0_raw = 0
        self.tbp0 = 0
        self.tbw = 0
        self.psm = 0
        self.tw = 0
        self.th = 0
        self.cbp = 0
        self.cpsm = 0
        self.csa = 0
        self.cld = 0
        self.prim_type = -1
        self.tme = 0  # texture mapping enable
        self.vertices = []  # list of (x, y, z) screen coords (fixed point >> 4)
        self.uvs = []  # list of (u, v) tex coords
        self.sts = []  # list of (s, t) tex coords
        self.frame_fbp = 0
        self.frame_fbw = 0
        self.xyoffset = (0, 0)
        self.vsync = 0
        self.packet_idx = 0
        self.seq = 0


def parse_dump(path):
    """Parse GS dump and return list of DrawCall objects."""
    print(f"Reading: {path}")
    print(f"File size: {path.stat().st_size:,} bytes")

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
    print(f"Packets start: 0x{packets_start:X}")

    # Parse packets
    pos = packets_start
    vsync_count = 0
    packet_idx = 0

    # Current render state
    cur_tex0_raw = 0
    cur_tbp0 = 0
    cur_tbw = 0
    cur_psm = 0
    cur_tw = 0
    cur_th = 0
    cur_cbp = 0
    cur_cpsm = 0
    cur_csa = 0
    cur_cld = 0
    cur_prim_type = 6  # default sprite
    cur_tme = 0
    cur_frame_fbp = 0
    cur_frame_fbw = 0
    cur_xyoffset = (0, 0)

    draw_calls = []
    bitblt_writes = []
    all_tex0 = []

    # Accumulate vertices for current draw
    current_verts = []
    current_uvs = []
    current_sts = []
    draw_seq = 0

    def flush_draw():
        nonlocal current_verts, current_uvs, current_sts, draw_seq
        if current_verts and cur_tme:
            dc = DrawCall()
            dc.tex0_raw = cur_tex0_raw
            dc.tbp0 = cur_tbp0
            dc.tbw = cur_tbw
            dc.psm = cur_psm
            dc.tw = cur_tw
            dc.th = cur_th
            dc.cbp = cur_cbp
            dc.cpsm = cur_cpsm
            dc.csa = cur_csa
            dc.cld = cur_cld
            dc.prim_type = cur_prim_type
            dc.tme = cur_tme
            dc.vertices = list(current_verts)
            dc.uvs = list(current_uvs)
            dc.sts = list(current_sts)
            dc.frame_fbp = cur_frame_fbp
            dc.frame_fbw = cur_frame_fbw
            dc.xyoffset = cur_xyoffset
            dc.vsync = vsync_count
            dc.packet_idx = packet_idx
            dc.seq = draw_seq
            draw_calls.append(dc)
            draw_seq += 1
        current_verts = []
        current_uvs = []
        current_sts = []

    def process_register(addr, reg_data):
        nonlocal cur_tex0_raw, cur_tbp0, cur_tbw, cur_psm, cur_tw, cur_th
        nonlocal cur_cbp, cur_cpsm, cur_csa, cur_cld
        nonlocal cur_prim_type, cur_tme
        nonlocal cur_frame_fbp, cur_frame_fbw, cur_xyoffset
        nonlocal current_verts, current_uvs, current_sts

        if addr in (0x06, 0x07):  # TEX0_1/2
            flush_draw()
            cur_tex0_raw = reg_data
            cur_tbp0 = reg_data & 0x3FFF
            cur_tbw = (reg_data >> 14) & 0x3F
            cur_psm = (reg_data >> 20) & 0x3F
            cur_tw = 1 << ((reg_data >> 26) & 0xF)
            cur_th = 1 << ((reg_data >> 30) & 0xF)
            tcc = (reg_data >> 34) & 1
            tfx = (reg_data >> 35) & 3
            cur_cbp = (reg_data >> 37) & 0x3FFF
            cur_cpsm = (reg_data >> 51) & 0xF
            csm = (reg_data >> 55) & 1
            cur_csa = (reg_data >> 56) & 0x1F
            cur_cld = (reg_data >> 61) & 7
            all_tex0.append({
                'tbp0': cur_tbp0, 'tbw': cur_tbw, 'psm': cur_psm,
                'tw': cur_tw, 'th': cur_th, 'cbp': cur_cbp,
                'cpsm': cur_cpsm, 'csa': cur_csa, 'cld': cur_cld,
                'vsync': vsync_count, 'packet': packet_idx,
            })

        elif addr == 0x00:  # PRIM
            flush_draw()
            cur_prim_type = reg_data & 0x7
            cur_tme = (reg_data >> 4) & 1

        elif addr in (0x4C, 0x4D):  # FRAME_1/2
            cur_frame_fbp = reg_data & 0x1FF
            cur_frame_fbw = (reg_data >> 16) & 0x3F

        elif addr == 0x18:  # XYOFFSET_1
            ox = reg_data & 0xFFFF
            oy = (reg_data >> 32) & 0xFFFF
            cur_xyoffset = (ox, oy)

        elif addr == 0x04:  # XYZF2 (with fog)
            x = reg_data & 0xFFFF
            y = (reg_data >> 16) & 0xFFFF
            z = (reg_data >> 32) & 0xFFFFFF
            current_verts.append((x, y, z))

        elif addr == 0x05:  # XYZ2
            x = reg_data & 0xFFFF
            y = (reg_data >> 16) & 0xFFFF
            z = (reg_data >> 32) & 0xFFFFFFFF
            current_verts.append((x, y, z))

        elif addr == 0x0C:  # XYZF3
            x = reg_data & 0xFFFF
            y = (reg_data >> 16) & 0xFFFF
            z = (reg_data >> 32) & 0xFFFFFF
            current_verts.append((x, y, z))

        elif addr == 0x0D:  # XYZ3
            x = reg_data & 0xFFFF
            y = (reg_data >> 16) & 0xFFFF
            z = (reg_data >> 32) & 0xFFFFFFFF
            current_verts.append((x, y, z))

        elif addr == 0x03:  # UV
            u = reg_data & 0x3FFF
            v = (reg_data >> 16) & 0x3FFF
            current_uvs.append((u, v))

        elif addr == 0x02:  # ST
            s_bits = reg_data & 0xFFFFFFFF
            t_bits = (reg_data >> 32) & 0xFFFFFFFF
            s = struct.unpack('<f', struct.pack('<I', s_bits))[0]
            t = struct.unpack('<f', struct.pack('<I', t_bits))[0]
            current_sts.append((s, t))

        elif addr == 0x50:  # BITBLTBUF
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

            # Parse GIF
            tpos = 0
            while tpos + 16 <= len(gif_data):
                lo = struct.unpack_from("<Q", gif_data, tpos)[0]
                hi = struct.unpack_from("<Q", gif_data, tpos + 8)[0]
                nloop = lo & 0x7FFF
                eop = (lo >> 15) & 1
                flg = (lo >> 58) & 3
                nreg = (lo >> 60) & 0xF
                if nreg == 0:
                    nreg = 16
                tpos += 16

                if flg == 0:  # PACKED
                    for loop in range(nloop):
                        for r in range(nreg):
                            if tpos + 16 > len(gif_data):
                                break
                            reg_id = (hi >> (r * 4)) & 0xF
                            if reg_id == 0x0E:  # A+D
                                rd = struct.unpack_from("<Q", gif_data, tpos)[0]
                                ra = struct.unpack_from("<Q", gif_data, tpos + 8)[0] & 0xFF
                                process_register(ra, rd)
                            elif reg_id == 0x00:  # PRIM (packed)
                                rd = struct.unpack_from("<Q", gif_data, tpos)[0]
                                flush_draw()
                                cur_prim_type = rd & 0x7
                                cur_tme = (rd >> 4) & 1
                            elif reg_id == 0x04:  # XYZF2 (packed format is different!)
                                # Packed XYZF2: bits [79:64]=X, [95:80]=Y, [103:96]=Z, [111:104]=F
                                # But stored as 128-bit: lo=first 64 bits, hi=second 64 bits
                                plo = struct.unpack_from("<Q", gif_data, tpos)[0]
                                phi = struct.unpack_from("<Q", gif_data, tpos + 8)[0]
                                x = plo & 0xFFFF
                                y = (plo >> 16) & 0xFFFF  # actually bits [31:16] are Y...
                                # Wait - packed format for XYZF2:
                                # Data[31:0] = X (unsigned), Data[47:32] = Y (unsigned)... no
                                # Actually in PACKED mode, the register data layout differs.
                                # For XYZF2 packed: X=bits[15:0], Y=bits[31:16], Z=bits[55:32], F=bits[111:104]
                                # But packed uses full 128-bit quadword
                                # Let me just use lo bits for x,y as 16-bit values
                                # Packed XYZF2: X=[15:0], Y=[47:32], Z=[75:48], F=[111:100]
                                # lo = bits 0-63:  X in [15:0], pad [31:16]?, Y in [47:32]
                                x = plo & 0xFFFF
                                y = (plo >> 32) & 0xFFFF
                                z = (phi >> 4) & 0xFFFFFF  # approximate
                                current_verts.append((x, y, z))
                            elif reg_id == 0x05:  # XYZ2 (packed)
                                plo = struct.unpack_from("<Q", gif_data, tpos)[0]
                                phi = struct.unpack_from("<Q", gif_data, tpos + 8)[0]
                                x = plo & 0xFFFF
                                y = (plo >> 32) & 0xFFFF
                                z = phi & 0xFFFFFFFF
                                current_verts.append((x, y, z))
                            elif reg_id == 0x03:  # UV (packed)
                                plo = struct.unpack_from("<Q", gif_data, tpos)[0]
                                u = plo & 0x3FFF
                                v = (plo >> 32) & 0x3FFF  # packed: V in [47:32]
                                current_uvs.append((u, v))
                            elif reg_id == 0x02:  # ST (packed)
                                plo = struct.unpack_from("<Q", gif_data, tpos)[0]
                                phi = struct.unpack_from("<Q", gif_data, tpos + 8)[0]
                                s = struct.unpack('<f', struct.pack('<I', plo & 0xFFFFFFFF))[0]
                                t = struct.unpack('<f', struct.pack('<I', (plo >> 32) & 0xFFFFFFFF))[0]
                                current_sts.append((s, t))
                            tpos += 16
                elif flg == 1:  # REGLIST
                    total_regs = nloop * nreg
                    for i in range(total_regs):
                        if tpos + 8 > len(gif_data):
                            break
                        reg_id = (hi >> ((i % nreg) * 4)) & 0xF
                        rd = struct.unpack_from("<Q", gif_data, tpos)[0]
                        # In REGLIST mode, the data IS the register value (8 bytes)
                        if reg_id == 0x0E:  # A+D — doesn't exist in REGLIST
                            pass
                        elif reg_id == 0x05:  # XYZ2
                            x = rd & 0xFFFF
                            y = (rd >> 16) & 0xFFFF
                            z = (rd >> 32) & 0xFFFFFFFF
                            current_verts.append((x, y, z))
                        elif reg_id == 0x04:  # XYZF2
                            x = rd & 0xFFFF
                            y = (rd >> 16) & 0xFFFF
                            z = (rd >> 32) & 0xFFFFFF
                            current_verts.append((x, y, z))
                        elif reg_id == 0x03:  # UV
                            u = rd & 0x3FFF
                            v = (rd >> 16) & 0x3FFF
                            current_uvs.append((u, v))
                        elif reg_id == 0x02:  # ST
                            s = struct.unpack('<f', struct.pack('<I', rd & 0xFFFFFFFF))[0]
                            t = struct.unpack('<f', struct.pack('<I', (rd >> 32) & 0xFFFFFFFF))[0]
                            current_sts.append((s, t))
                        tpos += 8
                    if (total_regs % 2) == 1:
                        tpos += 8
                elif flg == 2:  # IMAGE
                    tpos += nloop * 16
                else:
                    break

                if eop:
                    break

        elif tag == 1:  # VSync
            flush_draw()
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

    flush_draw()

    print(f"\nParsed: {vsync_count} vsyncs, {len(draw_calls)} textured draw calls")
    print(f"  BITBLTBUF writes: {len(bitblt_writes)}")
    print(f"  TEX0 changes: {len(all_tex0)}")

    return draw_calls, bitblt_writes, all_tex0


def analyze_draws(draw_calls, bitblt_writes, all_tex0):
    """Analyze draw calls for name entry keyboard grid."""

    # ===== 1. ALL UNIQUE TEX0 CONFIGURATIONS =====
    print("\n" + "=" * 90)
    print("ALL UNIQUE TEX0 CONFIGURATIONS")
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
        if tbp0 == 0x2840:
            marker = " <-- TBP0=0x2840!"
        if psm == 0x14:
            marker += " [PSMT4]"
        print(f"0x{tbp0:04X} {tbw:4d} {psm_name:>10} {tw:4d}x{th:<4d} 0x{cbp:04X} {cpsm_name:>10} {csa:4d} {cnt:6d}{marker}")

    # ===== 2. PSMT4 DRAW DETAILS WITH SCREEN POSITIONS =====
    print("\n" + "=" * 90)
    print("ALL PSMT4 TEXTURED DRAWS WITH SCREEN POSITIONS")
    print("(Screen coords = vertex_val/16 - xyoffset/16)")
    print("=" * 90)

    psmt4_draws = [dc for dc in draw_calls if dc.psm == 0x14]
    print(f"Total PSMT4 draws: {len(psmt4_draws)}")

    # Group by TBP0
    by_tbp0 = defaultdict(list)
    for dc in psmt4_draws:
        by_tbp0[dc.tbp0].append(dc)

    for tbp0 in sorted(by_tbp0.keys()):
        draws = by_tbp0[tbp0]
        print(f"\n--- TBP0=0x{tbp0:04X} TBW={draws[0].tbw} ({len(draws)} draws) ---")
        for dc in draws[:150]:  # limit output
            ox, oy = dc.xyoffset
            if dc.vertices:
                coords = []
                for vx, vy, vz in dc.vertices:
                    sx = (vx - ox) / 16.0
                    sy = (vy - oy) / 16.0
                    coords.append((sx, sy))
                min_x = min(c[0] for c in coords)
                min_y = min(c[1] for c in coords)
                max_x = max(c[0] for c in coords)
                max_y = max(c[1] for c in coords)

                uv_str = ""
                if dc.uvs:
                    uv_coords = [(u/16.0, v/16.0) for u, v in dc.uvs]
                    uv_min_u = min(c[0] for c in uv_coords)
                    uv_min_v = min(c[1] for c in uv_coords)
                    uv_max_u = max(c[0] for c in uv_coords)
                    uv_max_v = max(c[1] for c in uv_coords)
                    uv_str = f" UV=({uv_min_u:.1f},{uv_min_v:.1f})-({uv_max_u:.1f},{uv_max_v:.1f})"
                elif dc.sts:
                    s_min = min(s for s, t in dc.sts)
                    t_min = min(t for s, t in dc.sts)
                    s_max = max(s for s, t in dc.sts)
                    t_max = max(t for s, t in dc.sts)
                    uv_str = f" ST=({s_min:.4f},{t_min:.4f})-({s_max:.4f},{t_max:.4f})"

                prim_name = PRIM_TYPES.get(dc.prim_type, str(dc.prim_type))
                print(f"  [{dc.seq:4d}] scr=({min_x:6.1f},{min_y:6.1f})-({max_x:6.1f},{max_y:6.1f}) "
                      f"{prim_name:>8} verts={len(dc.vertices)}"
                      f" CBP=0x{dc.cbp:04X} CSA={dc.csa}{uv_str}")
            else:
                print(f"  [{dc.seq:4d}] (no vertices)")

    # ===== 3. KEYBOARD GRID REGION ANALYSIS =====
    # The keyboard grid is approximately X=100-600, Y=200-500 on screen
    print("\n" + "=" * 90)
    print("KEYBOARD GRID REGION (X=50-600, Y=150-500)")
    print("Looking for regularly-spaced small draws (character cells)")
    print("=" * 90)

    grid_draws = []
    for dc in draw_calls:
        if not dc.vertices:
            continue
        ox, oy = dc.xyoffset
        coords = [(((vx - ox) / 16.0), ((vy - oy) / 16.0)) for vx, vy, vz in dc.vertices]
        min_x = min(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_x = max(c[0] for c in coords)
        max_y = max(c[1] for c in coords)

        # Filter for grid region and small-ish draws
        if 50 <= min_x <= 600 and 150 <= min_y <= 500:
            w = max_x - min_x
            h = max_y - min_y
            if w <= 100 and h <= 100:  # character cells are small
                grid_draws.append((dc, min_x, min_y, max_x, max_y, w, h))

    print(f"Found {len(grid_draws)} small draws in grid region")
    for dc, min_x, min_y, max_x, max_y, w, h in sorted(grid_draws, key=lambda x: (x[2], x[1])):
        psm_name = PSM_NAMES.get(dc.psm, f"0x{dc.psm:02X}")
        uv_str = ""
        if dc.uvs:
            uv_coords = [(u/16.0, v/16.0) for u, v in dc.uvs]
            uv_min_u = min(c[0] for c in uv_coords)
            uv_min_v = min(c[1] for c in uv_coords)
            uv_max_u = max(c[0] for c in uv_coords)
            uv_max_v = max(c[1] for c in uv_coords)
            uv_str = f" UV=({uv_min_u:.1f},{uv_min_v:.1f})-({uv_max_u:.1f},{uv_max_v:.1f})"
        elif dc.sts:
            s_min = min(s for s, t in dc.sts)
            t_min = min(t for s, t in dc.sts)
            s_max = max(s for s, t in dc.sts)
            t_max = max(t for s, t in dc.sts)
            uv_str = f" ST=({s_min:.4f},{t_min:.4f})-({s_max:.4f},{t_max:.4f})"

        print(f"  [{dc.seq:4d}] ({min_x:6.1f},{min_y:6.1f})-({max_x:6.1f},{max_y:6.1f}) "
              f"[{w:.0f}x{h:.0f}] TBP0=0x{dc.tbp0:04X} {psm_name:>8} "
              f"CBP=0x{dc.cbp:04X} CSA={dc.csa}{uv_str}")

    # ===== 4. LOOK FOR REGULARLY SPACED ROWS =====
    print("\n" + "=" * 90)
    print("GRID PATTERN DETECTION")
    print("Group draws by Y position (rows)")
    print("=" * 90)

    # Group grid draws by Y (round to nearest 2 pixels)
    rows = defaultdict(list)
    for dc, min_x, min_y, max_x, max_y, w, h in grid_draws:
        row_y = round(min_y / 2) * 2  # round to nearest even
        rows[row_y].append((dc, min_x, min_y, max_x, max_y))

    for row_y in sorted(rows.keys()):
        items = sorted(rows[row_y], key=lambda x: x[1])  # sort by X
        print(f"\n  Row Y~{row_y}: {len(items)} draws")
        for dc, min_x, min_y, max_x, max_y in items:
            psm_name = PSM_NAMES.get(dc.psm, f"0x{dc.psm:02X}")
            uv_str = ""
            if dc.uvs:
                uv_coords = [(u/16.0, v/16.0) for u, v in dc.uvs]
                uv_str = f" UV=({uv_coords[0][0]:.1f},{uv_coords[0][1]:.1f})"
                if len(uv_coords) > 1:
                    uv_str += f"-({uv_coords[-1][0]:.1f},{uv_coords[-1][1]:.1f})"
            elif dc.sts:
                uv_str = f" ST=({dc.sts[0][0]:.4f},{dc.sts[0][1]:.4f})"
            print(f"    X={min_x:6.1f}-{max_x:6.1f} TBP0=0x{dc.tbp0:04X} {psm_name} "
                  f"CBP=0x{dc.cbp:04X} CSA={dc.csa}{uv_str}")

    # ===== 5. TBP0=0x2840 ANALYSIS =====
    print("\n" + "=" * 90)
    print("TBP0=0x2840 ANALYSIS")
    print("=" * 90)
    tbp_2840 = [dc for dc in draw_calls if dc.tbp0 == 0x2840]
    if tbp_2840:
        print(f"Found {len(tbp_2840)} draws using TBP0=0x2840")
        for dc in tbp_2840:
            psm_name = PSM_NAMES.get(dc.psm, f"0x{dc.psm:02X}")
            ox, oy = dc.xyoffset
            if dc.vertices:
                coords = [((vx - ox) / 16.0, (vy - oy) / 16.0) for vx, vy, vz in dc.vertices]
                min_x = min(c[0] for c in coords)
                min_y = min(c[1] for c in coords)
                max_x = max(c[0] for c in coords)
                max_y = max(c[1] for c in coords)
                print(f"  [{dc.seq:4d}] scr=({min_x:.1f},{min_y:.1f})-({max_x:.1f},{max_y:.1f}) "
                      f"{psm_name} {dc.tw}x{dc.th} TBW={dc.tbw} CBP=0x{dc.cbp:04X}")
    else:
        print("NO draws use TBP0=0x2840")
        # Check BITBLTBUF for 0x2840
        print("\nChecking BITBLTBUF for 0x2840:")
        for bb in bitblt_writes:
            if bb['sbp'] == 0x2840 or bb['dbp'] == 0x2840:
                sn = PSM_NAMES.get(bb['spsm'], f"0x{bb['spsm']:02X}")
                dn = PSM_NAMES.get(bb['dpsm'], f"0x{bb['dpsm']:02X}")
                print(f"  SBP=0x{bb['sbp']:04X}({sn}) -> DBP=0x{bb['dbp']:04X}({dn})")

    # ===== 6. ALL BITBLTBUF WRITES =====
    print("\n" + "=" * 90)
    print("ALL VRAM COPIES (BITBLTBUF)")
    print("=" * 90)
    for i, bb in enumerate(bitblt_writes):
        sn = PSM_NAMES.get(bb['spsm'], f"0x{bb['spsm']:02X}")
        dn = PSM_NAMES.get(bb['dpsm'], f"0x{bb['dpsm']:02X}")
        marker = ""
        if bb['dbp'] in (0x2840, 0x3000, 0x1800):
            marker = f" <-- DBP=0x{bb['dbp']:04X}!"
        print(f"  [{i}] SBP=0x{bb['sbp']:04X}(tbw={bb['sbw']},{sn}) -> "
              f"DBP=0x{bb['dbp']:04X}(tbw={bb['dbw']},{dn}) vsync#{bb['vsync']}{marker}")

    # ===== 7. DRAW CALL SEQUENCE (ALL) =====
    print("\n" + "=" * 90)
    print("FULL DRAW SEQUENCE (first 200)")
    print("=" * 90)
    for dc in draw_calls[:200]:
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
        prim_name = PRIM_TYPES.get(dc.prim_type, str(dc.prim_type))
        print(f"  [{dc.seq:4d}] TBP0=0x{dc.tbp0:04X} TBW={dc.tbw} {psm_name:>8} "
              f"{dc.tw}x{dc.th} CBP=0x{dc.cbp:04X} CSA={dc.csa:2d} "
              f"{prim_name:>8} v={len(dc.vertices):3d} {pos_str}")

    if len(draw_calls) > 200:
        print(f"  ... ({len(draw_calls) - 200} more)")


def main():
    draw_calls, bitblt_writes, all_tex0 = parse_dump(GS_DUMP)
    analyze_draws(draw_calls, bitblt_writes, all_tex0)


if __name__ == '__main__':
    main()
