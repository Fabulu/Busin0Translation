"""
Parse GS dump to find exactly how stat labels (HP, Str, Int, Pie, Vit, Agi, Lck)
are rendered. Captures ALL draws at screen Y positions matching stat labels,
regardless of TBP0.

Stat screen Y positions (approximate from screenshot):
  HP ~y=103, Str ~y=129, Int ~y=155, Pie ~y=181, Vit ~y=207, Agi ~y=233, Lck ~y=259
"""

import struct
import sys
import zstandard as zstd

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

GS_DUMP_PATH = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602231607.gs.zst"

# GIF register IDs
REG_PRIM  = 0x00
REG_RGBAQ = 0x01
REG_UV    = 0x03
REG_XYZF2 = 0x04
REG_XYZ2  = 0x05
REG_XYZ3  = 0x0D
REG_AD    = 0x0E

AD_TEX0_1 = 0x06
AD_TEX0_2 = 0x07

PSM_NAMES = {0: 'PSMCT32', 1: 'PSMCT24', 2: 'PSMCT16', 0x13: 'PSMT8',
             0x14: 'PSMT4', 0x24: 'PSMT8H', 0x2C: 'PSMT4HL', 0x36: 'PSMT4HH'}

# Known stat label Y positions (screen coords) and search tolerance
STAT_LABELS = [
    ("HP",  103),
    ("Str", 129),
    ("Int", 155),
    ("Pie", 181),
    ("Vit", 207),
    ("Agi", 233),
    ("Lck", 259),
]
Y_TOLERANCE = 15
# X range for stat labels (left side of screen)
X_MIN = 0
X_MAX = 200


def decompress_gs_dump(path):
    with open(path, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)


def parse_tex0(val64):
    return {
        'tbp0': val64 & 0x3FFF,
        'tbw': (val64 >> 14) & 0x3F,
        'psm': (val64 >> 20) & 0x3F,
        'tw': 1 << ((val64 >> 26) & 0xF),
        'th': 1 << ((val64 >> 30) & 0xF),
        'raw': val64,
    }


def try_parse_chain(data, start, max_steps=50):
    pos = start
    steps = 0
    while pos < len(data) and steps < max_steps:
        t = data[pos]
        if t == 0:
            if pos + 6 > len(data): return steps
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000 or size == 0: return steps
            pos += 6 + size
            steps += 1
        elif t == 1:
            pos += 2; steps += 1
        elif t == 2:
            if pos + 5 > len(data): return steps
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            if sz > 10_000_000: return steps
            pos += 5 + sz; steps += 1
        elif t == 3:
            pos += 2; steps += 1
        else:
            return steps
    return steps


def find_packet_stream(data):
    print("  Scanning for packet stream start...")
    best_off = 0
    best_cl = 0
    for off in range(0, len(data), 10000):
        cl = try_parse_chain(data, off, 50)
        if cl > best_cl:
            best_cl = cl
            best_off = off

    if best_cl < 10:
        print(f"  WARNING: No valid packet chain found (best={best_cl} steps)")
        return 0, len(data)

    lo = max(best_off - 10000, 0)
    final_off = best_off
    final_cl = best_cl
    for off in range(lo, best_off + 1):
        cl = try_parse_chain(data, off, 100)
        if cl > final_cl:
            final_cl = cl
            final_off = off

    print(f"  Packet stream starts at offset {final_off} (0x{final_off:X}), chain={final_cl}")
    return final_off, len(data)


def parse_all_draws_unfiltered(data, seg_start, seg_end):
    """Parse ALL draws from the packet stream, capturing TEX0 + UV + screen pos."""
    pos = seg_start
    current_tex0 = [None]
    draws = []
    draw_count = 0

    while pos < seg_end:
        t = data[pos]
        if t == 0:
            if pos + 6 > seg_end:
                break
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000:
                pos += 6 + size
                continue

            gif = data[pos + 6: pos + 6 + size]
            parse_gif_all(gif, current_tex0, draws)

            pos += 6 + size
        elif t in (1, 3):
            pos += 2
        elif t == 2:
            if pos + 5 > seg_end:
                break
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            pos += 5 + sz
        else:
            pos += 1

    return draws


def parse_gif_all(gif, current_tex0_ref, draws):
    """Parse GIF packet, collecting ALL draws with UV and screen position."""
    gp = 0

    while gp + 16 <= len(gif):
        tag_lo = struct.unpack_from('<Q', gif, gp)[0]
        tag_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
        nloop = tag_lo & 0x7FFF
        flg = (tag_lo >> 58) & 0x3
        nreg = (tag_lo >> 60) & 0xF
        if nreg == 0: nreg = 16
        eop = (tag_lo >> 15) & 1
        gp += 16

        if flg == 0:  # PACKED
            regs = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
            for _ in range(nloop):
                for reg_id in regs:
                    if gp + 16 > len(gif):
                        return
                    qw_lo = struct.unpack_from('<Q', gif, gp)[0]
                    qw_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
                    gp += 16
                    if reg_id == REG_AD:
                        ad = qw_hi & 0xFF
                        if ad in (AD_TEX0_1, AD_TEX0_2):
                            current_tex0_ref[0] = parse_tex0(qw_lo)

        elif flg == 1:  # REGLIST
            regs = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
            has_uv = REG_UV in regs
            has_xy = (REG_XYZ2 in regs or REG_XYZF2 in regs or REG_XYZ3 in regs)
            local_tex0 = current_tex0_ref[0]

            if has_uv and has_xy and local_tex0:
                uvs = []
                xys_tl = []
                xys_br = []

                for li in range(nloop):
                    for reg_id in regs:
                        if gp + 8 > len(gif):
                            break
                        val = struct.unpack_from('<Q', gif, gp)[0]
                        gp += 8

                        if reg_id == REG_UV:
                            u = (val & 0x3FFF) / 16.0
                            v = ((val >> 16) & 0x3FFF) / 16.0
                            uvs.append((u, v))
                        elif reg_id == REG_XYZ3:
                            x = (val & 0xFFFF) / 16.0
                            y = ((val >> 16) & 0xFFFF) / 16.0
                            xys_tl.append((x, y))
                        elif reg_id in (REG_XYZ2, REG_XYZF2):
                            x = (val & 0xFFFF) / 16.0
                            y = ((val >> 16) & 0xFFFF) / 16.0
                            xys_br.append((x, y))

                # Align to 16 bytes
                total_bytes = nloop * nreg * 8
                # gp already advanced

                if uvs:
                    draws.append({
                        'tex0': dict(local_tex0),
                        'uvs': uvs,
                        'xys_tl': xys_tl,
                        'xys_br': xys_br,
                    })
            else:
                tb = nloop * nreg * 8
                if tb % 16: tb += 16 - (tb % 16)
                gp += tb

        elif flg == 2:  # IMAGE
            gp += nloop * 16

        if eop:
            break


def find_xyoffset(data, seg_start, seg_end):
    """Try to find XYOFFSET register writes (reg addr 0x18/0x19) in the dump."""
    pos = seg_start
    offsets = []

    while pos < seg_end:
        t = data[pos]
        if t == 0:
            if pos + 6 > seg_end: break
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000:
                pos += 6 + size
                continue
            gif = data[pos + 6: pos + 6 + size]

            # Scan for XYOFFSET in A+D writes
            gp = 0
            while gp + 16 <= len(gif):
                tag_lo = struct.unpack_from('<Q', gif, gp)[0]
                tag_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
                nloop = tag_lo & 0x7FFF
                flg = (tag_lo >> 58) & 0x3
                nreg = (tag_lo >> 60) & 0xF
                if nreg == 0: nreg = 16
                eop = (tag_lo >> 15) & 1
                gp += 16

                if flg == 0:  # PACKED
                    regs_list = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
                    for _ in range(nloop):
                        for reg_id in regs_list:
                            if gp + 16 > len(gif): break
                            qw_lo = struct.unpack_from('<Q', gif, gp)[0]
                            qw_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
                            gp += 16
                            if reg_id == REG_AD:
                                ad = qw_hi & 0xFF
                                if ad in (0x18, 0x19):  # XYOFFSET_1, XYOFFSET_2
                                    ofx = (qw_lo & 0xFFFF) / 16.0
                                    ofy = ((qw_lo >> 32) & 0xFFFF) / 16.0
                                    offsets.append((ad, ofx, ofy))
                elif flg == 1:
                    tb = nloop * nreg * 8
                    if tb % 16: tb += 16 - (tb % 16)
                    gp += tb
                elif flg == 2:
                    gp += nloop * 16
                if eop: break

            pos += 6 + size
        elif t in (1, 3):
            pos += 2
        elif t == 2:
            if pos + 5 > seg_end: break
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            pos += 5 + sz
        else:
            pos += 1

    return offsets


def main():
    print("Decompressing GS dump...")
    data = decompress_gs_dump(GS_DUMP_PATH)
    print(f"Decompressed: {len(data):,} bytes")

    print("\nFinding packet stream...")
    seg_start, seg_end = find_packet_stream(data)

    # Find XYOFFSET
    print("\nSearching for XYOFFSET registers...")
    offsets = find_xyoffset(data, seg_start, seg_end)
    unique_offsets = list(set(offsets))
    for ad, ofx, ofy in sorted(unique_offsets):
        reg_name = "XYOFFSET_1" if ad == 0x18 else "XYOFFSET_2"
        print(f"  {reg_name}: OFX={ofx:.1f}, OFY={ofy:.1f}")

    # Use first XYOFFSET found, or default
    if unique_offsets:
        _, XYOFF_X, XYOFF_Y = unique_offsets[0]
    else:
        XYOFF_X, XYOFF_Y = 1778.0, 1841.0
        print(f"  No XYOFFSET found, using default ({XYOFF_X}, {XYOFF_Y})")

    # Parse ALL draws
    print("\nParsing ALL draws (unfiltered)...")
    all_draws = parse_all_draws_unfiltered(data, seg_start, seg_end)
    print(f"Total raw draws: {len(all_draws)}")

    # Collect all unique TEX0 values
    all_tbp0 = {}
    for d in all_draws:
        tbp0 = d['tex0']['tbp0']
        if tbp0 not in all_tbp0:
            all_tbp0[tbp0] = d['tex0']

    print(f"\nAll unique TEX0 values ({len(all_tbp0)}):")
    for tbp0 in sorted(all_tbp0.keys()):
        t = all_tbp0[tbp0]
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        known = ""
        if tbp0 == 0x2840:
            known = " <-- R1188 font atlas"
        elif tbp0 == 0x2A68:
            known = " <-- R1188 page 2"
        print(f"  TBP0=0x{tbp0:04X}  TBW={t['tbw']:>2}  PSM={psm_name:<8}  "
              f"size={t['tw']:>4}x{t['th']:<4}{known}")

    # Filter draws to stat label screen Y positions
    print(f"\n{'='*130}")
    print("DRAWS AT STAT LABEL SCREEN POSITIONS")
    print(f"XYOFFSET: ({XYOFF_X:.1f}, {XYOFF_Y:.1f})")
    print(f"{'='*130}")

    stat_draws = []
    for d in all_draws:
        # Get screen Y from either XYZ3 (top-left) or XYZ2
        sy = None
        sx = None
        if d['xys_tl']:
            sx = d['xys_tl'][0][0] - XYOFF_X
            sy = d['xys_tl'][0][1] - XYOFF_Y
        elif d['xys_br']:
            sx = d['xys_br'][0][0] - XYOFF_X
            sy = d['xys_br'][0][1] - XYOFF_Y

        if sx is None or sy is None:
            continue

        # Check if this draw is near any stat label Y position
        for label, target_y in STAT_LABELS:
            if abs(sy - target_y) < Y_TOLERANCE and X_MIN <= sx <= X_MAX:
                stat_draws.append((d, sx, sy, label, target_y))
                break

    print(f"\nFound {len(stat_draws)} draws near stat label positions")

    # Sort by screen Y then X
    stat_draws.sort(key=lambda x: (x[2], x[1]))

    print(f"\n{'#':>3}  {'Label':>6}  {'TBP0':>8}  {'TBW':>4}  {'PSM':>8}  {'TexSize':>8}  "
          f"{'UV TL':>14}  {'UV BR':>14}  {'UV Size':>8}  "
          f"{'Screen TL':>14}  {'Screen BR':>14}  {'Scr Size':>10}")
    print("-" * 150)

    for i, (d, sx, sy, label, target_y) in enumerate(stat_draws):
        t = d['tex0']
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        uvs = d['uvs']

        if len(uvs) >= 2:
            u_tl, v_tl = uvs[0]
            u_br, v_br = uvs[1]
            uv_w = u_br - u_tl
            uv_h = v_br - v_tl
        elif len(uvs) == 1:
            u_tl, v_tl = uvs[0]
            u_br, v_br = u_tl, v_tl
            uv_w = uv_h = 0
        else:
            continue

        scr_tl = f"({sx:.0f},{sy:.0f})"
        scr_br = "N/A"
        scr_sz = "N/A"
        if d['xys_br']:
            sx2 = d['xys_br'][0][0] - XYOFF_X
            sy2 = d['xys_br'][0][1] - XYOFF_Y
            scr_br = f"({sx2:.0f},{sy2:.0f})"
            if d['xys_tl']:
                scr_sz = f"{sx2-sx:.0f}x{sy2-sy:.0f}"

        print(f"{i:>3}  {label:>6}  0x{t['tbp0']:04X}  {t['tbw']:>4}  {psm_name:>8}  "
              f"{t['tw']}x{t['th']:<4}  ({u_tl:6.1f},{v_tl:5.1f})  ({u_br:6.1f},{v_br:5.1f})  "
              f"{uv_w:3.0f}x{uv_h:<3.0f}  {scr_tl:>14}  {scr_br:>14}  {scr_sz:>10}")

    # Summary: group by TBP0
    print(f"\n{'='*130}")
    print("SUMMARY: TBP0 usage for stat labels")
    print(f"{'='*130}")

    tbp0_groups = {}
    for d, sx, sy, label, target_y in stat_draws:
        tbp0 = d['tex0']['tbp0']
        if tbp0 not in tbp0_groups:
            tbp0_groups[tbp0] = []
        tbp0_groups[tbp0].append((d, sx, sy, label))

    for tbp0 in sorted(tbp0_groups.keys()):
        items = tbp0_groups[tbp0]
        t = items[0][0]['tex0']
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        known = ""
        if tbp0 == 0x2840:
            known = " (R1188 font atlas)"
        elif tbp0 == 0x2A68:
            known = " (R1188 page 2)"
        print(f"\n  TBP0=0x{tbp0:04X}  TBW={t['tbw']}  PSM={psm_name}  "
              f"tex={t['tw']}x{t['th']}{known}  ({len(items)} draws)")
        for d, sx, sy, label in sorted(items, key=lambda x: x[2]):
            uvs = d['uvs']
            if len(uvs) >= 2:
                u_tl, v_tl = uvs[0]
                u_br, v_br = uvs[1]
                print(f"    {label:>6}  screen=({sx:.0f},{sy:.0f})  "
                      f"UV=({u_tl:.1f},{v_tl:.1f})-({u_br:.1f},{v_br:.1f})  "
                      f"size={u_br-u_tl:.0f}x{v_br-v_tl:.0f}")

    # Also dump ALL draws in the Y range 90-270 regardless of X (broader search)
    print(f"\n{'='*130}")
    print("BROADER SEARCH: ALL draws with screen Y in [90, 270] (any X)")
    print(f"{'='*130}")

    broad_draws = []
    for d in all_draws:
        sy = None
        sx = None
        if d['xys_tl']:
            sx = d['xys_tl'][0][0] - XYOFF_X
            sy = d['xys_tl'][0][1] - XYOFF_Y
        elif d['xys_br']:
            sx = d['xys_br'][0][0] - XYOFF_X
            sy = d['xys_br'][0][1] - XYOFF_Y

        if sy is not None and 90 <= sy <= 270 and -100 <= sx <= 300:
            broad_draws.append((d, sx, sy))

    # Deduplicate
    seen = set()
    unique_broad = []
    for d, sx, sy in broad_draws:
        uvs = tuple((round(u,1), round(v,1)) for u, v in d['uvs'])
        key = (d['tex0']['tbp0'], uvs, round(sx), round(sy))
        if key not in seen:
            seen.add(key)
            unique_broad.append((d, sx, sy))

    unique_broad.sort(key=lambda x: (x[2], x[1]))

    print(f"Found {len(unique_broad)} unique draws")
    print(f"\n{'#':>3}  {'TBP0':>8}  {'PSM':>8}  {'TexSize':>8}  "
          f"{'UV TL':>14}  {'UV BR':>14}  {'UV Size':>8}  {'Screen pos':>14}")
    print("-" * 100)

    for i, (d, sx, sy) in enumerate(unique_broad):
        t = d['tex0']
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        uvs = d['uvs']
        if len(uvs) >= 2:
            u_tl, v_tl = uvs[0]
            u_br, v_br = uvs[1]
            uv_w = u_br - u_tl
            uv_h = v_br - v_tl
        else:
            continue

        # Check if near a stat label
        near = ""
        for label, target_y in STAT_LABELS:
            if abs(sy - target_y) < 8:
                near = f" <-- {label}?"
                break

        print(f"{i:>3}  0x{t['tbp0']:04X}  {psm_name:>8}  {t['tw']}x{t['th']:<4}  "
              f"({u_tl:6.1f},{v_tl:5.1f})  ({u_br:6.1f},{v_br:5.1f})  "
              f"{uv_w:3.0f}x{uv_h:<3.0f}  ({sx:.0f},{sy:.0f}){near}")


if __name__ == '__main__':
    main()
