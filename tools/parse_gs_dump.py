"""
Parse a PCSX2 GS dump (.gs.zst) to extract UV coordinates for texture draws
using TBP0=0x2840 and 0x2A68 (R1188 font atlas texture pages).

The key insight: the game uses GIF REGLIST mode for vertex data (not PACKED).
Pattern per draw:
  1. Path3 PACKED A+D: set TEX0 (TBP0=0x2840/0x2A68, PSMT4, 256x256)
  2. Path3 PACKED A+D: set CLAMP
  3. Path3 REGLIST: 6 registers [PRIM, RGBAQ, UV, ???, UV, XYZ2] = 1 SPRITE primitive
  4. Path3 PACKED A+D: set FRAME

UV register (REGLIST 64-bit): U = bits 0-13 (12.4 fixed), V = bits 16-29 (12.4 fixed)
XYZ2 register (REGLIST 64-bit): X = bits 0-15 (12.4 fixed), Y = bits 16-31 (12.4 fixed)
"""

import struct
import zstandard as zstd
from collections import defaultdict

GS_DUMP_PATH = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602200912.gs.zst"

TARGET_TBP0 = {0x2840, 0x2A68}

REG_UV   = 0x03
REG_XYZF2 = 0x04
REG_XYZ2 = 0x05
REG_AD   = 0x0E

AD_TEX0_1 = 0x06
AD_TEX0_2 = 0x07

PSM_NAMES = {0: 'PSMCT32', 1: 'PSMCT24', 2: 'PSMCT16', 0x13: 'PSMT8',
             0x14: 'PSMT4', 0x24: 'PSMT8H', 0x2C: 'PSMT4HL', 0x36: 'PSMT4HH'}

# Packet stream segments (4 frames)
SEGMENTS = [
    (5431859, 7128631),
    (7136824, 8833596),
    (8841789, 10538561),
    (10546754, 12243526),
]


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
    }


def parse_segment(data, seg_start, seg_end):
    """Parse one frame segment for target TEX0 draws."""
    pos = seg_start
    current_tex0 = None
    draws = []

    while pos < seg_end:
        t = data[pos]
        if t == 0:  # Transfer
            if pos + 6 > seg_end:
                break
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000:
                break

            gif = data[pos + 6: pos + 6 + size]
            parse_gif(gif, current_tex0, draws, lambda t: t)

            # Update current_tex0 from this packet
            new_tex0 = extract_last_tex0(gif)
            if new_tex0 is not None:
                current_tex0 = new_tex0

            pos += 6 + size
        elif t in (1, 3):
            pos += 2
        elif t == 2:
            if pos + 5 > seg_end:
                break
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            pos += 5 + sz
        else:
            break

    return draws


def extract_last_tex0(gif):
    """Extract the last TEX0 value written in a GIF packet."""
    gp = 0
    last_tex0 = None
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
                        return last_tex0
                    qw_lo = struct.unpack_from('<Q', gif, gp)[0]
                    qw_hi = struct.unpack_from('<Q', gif, gp + 8)[0]
                    gp += 16
                    if reg_id == REG_AD:
                        ad = qw_hi & 0xFF
                        if ad in (AD_TEX0_1, AD_TEX0_2):
                            last_tex0 = parse_tex0(qw_lo)
                    elif reg_id in (0x06, 0x07):
                        last_tex0 = parse_tex0(qw_lo)
        elif flg == 1:
            tb = nloop * nreg * 8
            if tb % 16: tb += 16 - (tb % 16)
            gp += tb
        elif flg == 2:
            gp += nloop * 16

        if eop:
            break
    return last_tex0


def parse_gif(gif, current_tex0, draws, on_tex0_update):
    """Parse GIF data, collecting draws that use target TEX0."""
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

        if flg == 1:  # REGLIST
            regs = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
            has_uv = REG_UV in regs
            has_xy = REG_XYZ2 in regs or REG_XYZF2 in regs

            if has_uv and current_tex0 and current_tex0['tbp0'] in TARGET_TBP0:
                uvs = []
                xys = []
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
                        elif reg_id in (REG_XYZ2, REG_XYZF2):
                            x = (val & 0xFFFF) / 16.0
                            y = ((val >> 16) & 0xFFFF) / 16.0
                            xys.append((x, y))

                if uvs:
                    draws.append({
                        'tex0': dict(current_tex0),
                        'uvs': uvs,
                        'xys': xys,
                    })
            else:
                # Skip data
                tb = nloop * nreg * 8
                if tb % 16: tb += 16 - (tb % 16)
                gp += tb

        elif flg == 0:  # PACKED - just skip (TEX0 handled separately)
            gp += nloop * nreg * 16

        elif flg == 2:  # IMAGE
            gp += nloop * 16

        if eop:
            break


def main():
    print("Decompressing GS dump...")
    data = decompress_gs_dump(GS_DUMP_PATH)
    print(f"Decompressed: {len(data):,} bytes, 4 frame segments")

    # Parse all segments - use segment 1 as reference (all frames should be identical)
    all_draws = []
    for seg_i, (seg_start, seg_end) in enumerate(SEGMENTS):
        draws = parse_segment(data, seg_start, seg_end)
        print(f"  Frame {seg_i}: {len(draws)} draws with target TBP0")
        all_draws.extend(draws)

    # Deduplicate (same UV region across frames)
    unique = deduplicate(all_draws)
    print(f"\nTotal draws across 4 frames: {len(all_draws)}")
    print(f"Unique UV regions: {len(unique)}")

    # Separate by TBP0
    draws_2840 = [d for d in unique if d['tex0']['tbp0'] == 0x2840]
    draws_2a68 = [d for d in unique if d['tex0']['tbp0'] == 0x2A68]

    print(f"\n  TBP0=0x2840: {len(draws_2840)} unique draws")
    print(f"  TBP0=0x2A68: {len(draws_2a68)} unique draws")

    # Print results
    print_results(draws_2840, "TBP0=0x2840")
    print_results(draws_2a68, "TBP0=0x2A68")

    # Create a grid map showing which 16x16 cells are used
    print_grid_map(unique)


def deduplicate(draws):
    seen = set()
    unique = []
    for d in draws:
        uvs = tuple(sorted((round(u, 1), round(v, 1)) for u, v in d['uvs']))
        key = (d['tex0']['tbp0'], uvs)
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def print_results(draws, label):
    print(f"\n{'='*100}")
    print(f"DRAWS: {label}")
    print(f"{'='*100}")
    print(f"{'#':>3}  {'UV top-left':>14}  {'UV bot-right':>14}  {'Size':>8}  "
          f"{'Screen XY':>14}  {'Screen Size':>14}")
    print("-" * 80)

    for i, d in enumerate(draws):
        uvs = d['uvs']
        xys = d['xys']
        tex0 = d['tex0']

        if len(uvs) >= 2:
            us = [u for u, v in uvs]
            vs = [v for u, v in uvs]
            u_min, v_min = min(us), min(vs)
            u_max, v_max = max(us), max(vs)
            w = u_max - u_min
            h = v_max - v_min
        else:
            continue

        if xys:
            # For SPRITE: first XY = top-left screen pos
            sx = xys[0][0] - 2048.0
            sy = xys[0][1] - 2048.0
            if len(xys) >= 2:
                sx2 = xys[1][0] - 2048.0
                sy2 = xys[1][1] - 2048.0
                sw = sx2 - sx
                sh = sy2 - sy
                scr_pos = f"({sx:.0f},{sy:.0f})"
                scr_sz = f"{sw:.0f}x{sh:.0f}"
            else:
                scr_pos = f"({sx:.0f},{sy:.0f})"
                scr_sz = "N/A"
        else:
            scr_pos = "N/A"
            scr_sz = "N/A"

        print(f"{i:>3}  ({u_min:6.1f},{v_min:5.1f})  ({u_max:6.1f},{v_max:5.1f})  "
              f"{w:3.0f}x{h:<3.0f}  {scr_pos:>14}  {scr_sz:>14}")


def print_grid_map(draws):
    """Show a 16x16 grid map of which cells in the 256x256 texture are referenced."""
    print(f"\n{'='*100}")
    print("TEXTURE CELL USAGE MAP (256x256 texture, 16x16 cells)")
    print("Each cell = 16x16 pixels. '#' = used, '.' = unused")
    print(f"{'='*100}")

    for tbp0 in sorted(TARGET_TBP0):
        tbp0_draws = [d for d in draws if d['tex0']['tbp0'] == tbp0]
        if not tbp0_draws:
            continue

        # Create 16x16 grid (256/16 = 16 cells per axis)
        grid = [[False]*16 for _ in range(16)]
        cell_draws = {}  # (cx, cy) -> draw info

        for d in tbp0_draws:
            uvs = d['uvs']
            if len(uvs) < 2:
                continue
            us = [u for u, v in uvs]
            vs = [v for u, v in uvs]
            u_min, v_min = min(us), min(vs)

            # Which 16x16 cell does this come from?
            cx = int(u_min) // 16
            cy = int(v_min) // 16
            if 0 <= cx < 16 and 0 <= cy < 16:
                grid[cy][cx] = True
                w = max(us) - min(us)
                h = max(vs) - min(vs)
                cell_draws[(cx, cy)] = f"{w:.0f}x{h:.0f}"

        print(f"\nTBP0=0x{tbp0:04X}:")
        print("     " + "".join(f"{c:>3}" for c in range(16)))
        for row in range(16):
            cells = ""
            for col in range(16):
                if grid[row][col]:
                    cells += "  #"
                else:
                    cells += "  ."
            print(f"  {row:>2} {cells}")

        # List referenced cells with pixel coordinates
        print(f"\n  Referenced cells (pixel coords within 256x256):")
        for (cx, cy), size in sorted(cell_draws.items()):
            px_x = cx * 16
            px_y = cy * 16
            print(f"    cell({cx},{cy}) = pixel ({px_x},{px_y})-({px_x+16},{px_y+16})  draw size={size}")

    # Also handle non-16x16 draws from 0x2A68
    print(f"\n{'='*100}")
    print("NON-STANDARD SIZE DRAWS (not 16x16)")
    print(f"{'='*100}")
    for d in draws:
        uvs = d['uvs']
        if len(uvs) < 2:
            continue
        us = [u for u, v in uvs]
        vs = [v for u, v in uvs]
        w = max(us) - min(us)
        h = max(vs) - min(vs)
        if abs(w - 16) > 1 or abs(h - 16) > 1:
            u_min, v_min = min(us), min(vs)
            u_max, v_max = max(us), max(vs)
            scr = "N/A"
            if d['xys']:
                sx = d['xys'][0][0] - 2048
                sy = d['xys'][0][1] - 2048
                scr = f"({sx:.0f},{sy:.0f})"
            print(f"  TBP0=0x{d['tex0']['tbp0']:04X}  "
                  f"UV=({u_min:.1f},{v_min:.1f})-({u_max:.1f},{v_max:.1f})  "
                  f"size={w:.0f}x{h:.0f}  screen={scr}")


if __name__ == '__main__':
    main()
