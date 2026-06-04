"""
Parse a PCSX2 GS dump (.gs.zst) to extract UV coordinates for texture draws
using TBP0=0x3327 and TBP0=0x319F (stat label texture pages).

Extended version: auto-discovers packet stream, extracts full TEX0 info,
handles XYZ3 (top-left) + XYZ2 (bottom-right) SPRITE vertices,
and cross-references screen positions with known stat label locations.

GS SPRITE draw pattern in REGLIST mode (6 registers, nloop=1):
  PRIM(0x00), RGBAQ(0x01), UV(0x03), XYZ3(0x0D), UV(0x03), XYZ2(0x05)
  - First UV = top-left texture coordinate
  - XYZ3 = top-left screen position (no drawing kick)
  - Second UV = bottom-right texture coordinate
  - XYZ2 = bottom-right screen position (triggers draw)

XYOFFSET for this game: OFX=1778, OFY=1841
  Screen X = GS_X - 1778
  Screen Y = GS_Y - 1841
"""

import struct
import sys
import zstandard as zstd
from collections import defaultdict

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

GS_DUMP_PATH = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602201903.gs.zst"

TARGET_TBP0 = {0x3327, 0x319F}

# GIF register IDs
REG_PRIM  = 0x00
REG_RGBAQ = 0x01
REG_UV    = 0x03
REG_XYZF2 = 0x04
REG_XYZ2  = 0x05
REG_XYZ3  = 0x0D  # Same as XYZ2 but no drawing kick
REG_AD    = 0x0E

# GS register addresses (used in A+D mode)
AD_TEX0_1 = 0x06
AD_TEX0_2 = 0x07

# GS XYOFFSET for this game (inferred from known label positions)
XYOFFSET_X = 1778.0
XYOFFSET_Y = 1841.0

PSM_NAMES = {0: 'PSMCT32', 1: 'PSMCT24', 2: 'PSMCT16', 0x13: 'PSMT8',
             0x14: 'PSMT4', 0x24: 'PSMT8H', 0x2C: 'PSMT4HL', 0x36: 'PSMT4HH'}

# Known stat label screen positions (approximate, from screenshot)
KNOWN_LABELS = [
    ("STR (力)", 30, 155),
    ("INT (知恵)", 30, 175),
    ("PIE (信仰心)", 30, 195),
    ("VIT (生命力)", 30, 215),
    ("AGI (素早さ)", 30, 235),
    ("LUC (運の強さ)", 30, 255),
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
        'raw': val64,
    }


def try_parse_chain(data, start, max_steps=50):
    """Try parsing a GS packet chain from a given offset. Returns step count."""
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
    """Find packet stream by scanning for valid GS packet chains.
    The dump has a large header (GS state + VRAM) before the packet stream."""
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

    # Fine-grained search around the best offset
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
        elif flg == 1:
            tb = nloop * nreg * 8
            if tb % 16: tb += 16 - (tb % 16)
            gp += tb
        elif flg == 2:
            gp += nloop * 16

        if eop:
            break
    return last_tex0


def parse_all_draws(data, seg_start, seg_end):
    """Parse the packet stream for target TEX0 draws.
    Tracks TEX0 changes inline. Handles XYZ3 for SPRITE top-left vertex."""
    pos = seg_start
    current_tex0 = [None]  # mutable for inline updates
    draws = []

    while pos < seg_end:
        t = data[pos]
        if t == 0:  # Transfer
            if pos + 6 > seg_end:
                break
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if path not in (1, 2, 3) or size > 10_000_000:
                pos += 6 + size
                continue

            gif = data[pos + 6: pos + 6 + size]
            parse_gif_packet(gif, current_tex0, draws)

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


def parse_gif_packet(gif, current_tex0_ref, draws):
    """Parse a single GIF packet. Updates current_tex0_ref[0] inline.
    Collects draws from REGLIST primitives using target TEX0.
    Properly handles XYZ3 (reg 0x0D) as top-left screen vertex."""
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

            if has_uv and local_tex0 and local_tex0['tbp0'] in TARGET_TBP0:
                uvs = []
                xys_tl = []  # XYZ3 = top-left (no kick)
                xys_br = []  # XYZ2 = bottom-right (with kick)
                rgbaq = None

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
                        elif reg_id == REG_RGBAQ:
                            rgbaq = val

                # Handle alignment padding
                total_bytes = nloop * nreg * 8
                if total_bytes % 16:
                    # Need to skip padding bytes to reach 16-byte alignment
                    pass

                if uvs:
                    draws.append({
                        'tex0': dict(local_tex0),
                        'uvs': uvs,
                        'xys_tl': xys_tl,
                        'xys_br': xys_br,
                        'rgbaq': rgbaq,
                    })
            else:
                # Skip REGLIST data
                tb = nloop * nreg * 8
                if tb % 16: tb += 16 - (tb % 16)
                gp += tb

        elif flg == 2:  # IMAGE
            gp += nloop * 16

        if eop:
            break


def deduplicate(draws):
    seen = set()
    unique = []
    for d in draws:
        uvs = tuple(sorted((round(u, 1), round(v, 1)) for u, v in d['uvs']))
        tl = tuple(sorted((round(x, 1), round(y, 1)) for x, y in d['xys_tl']))
        br = tuple(sorted((round(x, 1), round(y, 1)) for x, y in d['xys_br']))
        key = (d['tex0']['tbp0'], uvs, tl, br)
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def gs_to_screen(gs_x, gs_y):
    """Convert GS coordinates to screen coordinates using XYOFFSET."""
    return gs_x - XYOFFSET_X, gs_y - XYOFFSET_Y


def print_results(draws, label):
    print(f"\n{'='*130}")
    print(f"DRAWS: {label}")
    if draws:
        t = draws[0]['tex0']
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        print(f"TEX0: TBP0=0x{t['tbp0']:04X}, TBW={t['tbw']}, PSM={psm_name}, "
              f"size={t['tw']}x{t['th']}, raw=0x{t.get('raw',0):016X}")
    print(f"XYOFFSET: ({XYOFFSET_X:.0f}, {XYOFFSET_Y:.0f})")
    print(f"{'='*130}")
    print(f"{'#':>3}  {'UV TL':>14}  {'UV BR':>14}  {'UV Size':>8}  "
          f"{'Screen TL':>14}  {'Screen BR':>14}  {'Scr Size':>10}  {'RGBA':>12}  {'Near Label?'}")
    print("-" * 130)

    sorted_draws = sorted(draws, key=lambda d: (
        d['xys_tl'][0][1] if d['xys_tl'] else (d['xys_br'][0][1] if d['xys_br'] else 0),
        d['xys_tl'][0][0] if d['xys_tl'] else (d['xys_br'][0][0] if d['xys_br'] else 0),
    ))

    for i, d in enumerate(sorted_draws):
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

        # Screen positions
        scr_tl_str = "N/A"
        scr_br_str = "N/A"
        scr_sz_str = "N/A"
        sx_tl = sy_tl = None

        if d['xys_tl']:
            sx_tl, sy_tl = gs_to_screen(*d['xys_tl'][0])
            scr_tl_str = f"({sx_tl:.0f},{sy_tl:.0f})"

        if d['xys_br']:
            sx_br, sy_br = gs_to_screen(*d['xys_br'][0])
            scr_br_str = f"({sx_br:.0f},{sy_br:.0f})"
            if d['xys_tl']:
                sw = sx_br - sx_tl
                sh = sy_br - sy_tl
                scr_sz_str = f"{sw:.0f}x{sh:.0f}"

        # RGBA from RGBAQ
        rgba_str = ""
        if d.get('rgbaq') is not None:
            r = d['rgbaq'] & 0xFF
            g = (d['rgbaq'] >> 8) & 0xFF
            b = (d['rgbaq'] >> 16) & 0xFF
            a = (d['rgbaq'] >> 24) & 0xFF
            rgba_str = f"#{r:02X}{g:02X}{b:02X} a={a}"

        # Cross-reference with known labels
        near = ""
        if sx_tl is not None and sy_tl is not None:
            for lbl, lx, ly in KNOWN_LABELS:
                if abs(sx_tl - lx) < 30 and abs(sy_tl - ly) < 15:
                    near = f"<-- {lbl}"
                    break

        print(f"{i:>3}  ({u_tl:6.1f},{v_tl:5.1f})  ({u_br:6.1f},{v_br:5.1f})  "
              f"{uv_w:3.0f}x{uv_h:<3.0f}  {scr_tl_str:>14}  {scr_br_str:>14}  "
              f"{scr_sz_str:>10}  {rgba_str:>12}  {near}")


def collect_all_tex0(data, seg_start, seg_end):
    """Collect all unique TEX0 values from the packet stream."""
    all_tex0 = {}
    pos = seg_start

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
            tex0 = extract_last_tex0(gif)
            if tex0:
                tbp0 = tex0['tbp0']
                if tbp0 not in all_tex0:
                    all_tex0[tbp0] = tex0
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

    return all_tex0


def main():
    print("Decompressing GS dump...")
    data = decompress_gs_dump(GS_DUMP_PATH)
    print(f"Decompressed: {len(data):,} bytes")

    print("\nFinding packet stream...")
    seg_start, seg_end = find_packet_stream(data)
    print(f"Packet stream: {seg_start:,} - {seg_end:,} ({seg_end-seg_start:,} bytes)")

    # Show all TEX0 values
    print(f"\n{'='*130}")
    print("ALL UNIQUE TEX0 VALUES")
    print(f"{'='*130}")
    all_tex0 = collect_all_tex0(data, seg_start, seg_end)
    for tbp0 in sorted(all_tex0.keys()):
        t = all_tex0[tbp0]
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        marker = " <-- TARGET" if tbp0 in TARGET_TBP0 else ""
        print(f"  TBP0=0x{tbp0:04X}  TBW={t['tbw']:>2}  PSM={psm_name:<8}  "
              f"size={t['tw']:>4}x{t['th']:<4}  raw=0x{t.get('raw',0):016X}{marker}")

    # Parse draws
    print("\nParsing draws...")
    all_draws = parse_all_draws(data, seg_start, seg_end)
    unique = deduplicate(all_draws)
    print(f"Total raw draws: {len(all_draws)}")
    print(f"Unique draws: {len(unique)}")

    # Separate by TBP0
    draws_3327 = [d for d in unique if d['tex0']['tbp0'] == 0x3327]
    draws_319f = [d for d in unique if d['tex0']['tbp0'] == 0x319F]

    print(f"\n  TBP0=0x3327: {len(draws_3327)} unique draws")
    print(f"  TBP0=0x319F: {len(draws_319f)} unique draws")

    # Print detailed results
    print_results(draws_3327, "TBP0=0x3327")
    print_results(draws_319f, "TBP0=0x319F")

    # Cross-reference section
    print(f"\n{'='*130}")
    print("CROSS-REFERENCE: Draws near known stat label positions")
    print(f"{'='*130}")
    for lbl, lx, ly in KNOWN_LABELS:
        print(f"\n  {lbl} (expected near screen {lx},{ly}):")
        found = False
        for d in unique:
            if d['xys_tl']:
                sx, sy = gs_to_screen(*d['xys_tl'][0])
                if abs(sx - lx) < 50 and abs(sy - ly) < 15:
                    uvs = d['uvs']
                    if len(uvs) >= 2:
                        u_tl, v_tl = uvs[0]
                        u_br, v_br = uvs[1]
                    else:
                        continue
                    scr_br_str = "N/A"
                    if d['xys_br']:
                        sx2, sy2 = gs_to_screen(*d['xys_br'][0])
                        scr_br_str = f"({sx2:.0f},{sy2:.0f})"
                    print(f"    TBP0=0x{d['tex0']['tbp0']:04X}  "
                          f"UV=({u_tl:.1f},{v_tl:.1f})-({u_br:.1f},{v_br:.1f})  "
                          f"screen=({sx:.0f},{sy:.0f})-{scr_br_str}  "
                          f"size={u_br-u_tl:.0f}x{v_br-v_tl:.0f}")
                    found = True
        if not found:
            print(f"    (no draws found near this position)")

    # UV region summary sorted by texture position
    print(f"\n{'='*130}")
    print("UV REGION SUMMARY (sorted by texture V, then U)")
    print(f"{'='*130}")
    for tbp0_val in [0x3327, 0x319F]:
        tbp0_draws = [d for d in unique if d['tex0']['tbp0'] == tbp0_val]
        if not tbp0_draws:
            continue
        t = tbp0_draws[0]['tex0']
        psm_name = PSM_NAMES.get(t['psm'], f"0x{t['psm']:02X}")
        print(f"\nTBP0=0x{tbp0_val:04X}  TBW={t['tbw']}  PSM={psm_name}  "
              f"tex={t['tw']}x{t['th']}  ({len(tbp0_draws)} draws):")

        for i, d in enumerate(sorted(tbp0_draws, key=lambda d: (
                d['uvs'][0][1] if d['uvs'] else 0,
                d['uvs'][0][0] if d['uvs'] else 0))):
            uvs = d['uvs']
            if len(uvs) >= 2:
                u_tl, v_tl = uvs[0]
                u_br, v_br = uvs[1]
            else:
                continue

            scr_str = "N/A"
            scr_sz = ""
            if d['xys_tl']:
                sx, sy = gs_to_screen(*d['xys_tl'][0])
                scr_str = f"({sx:.0f},{sy:.0f})"
                if d['xys_br']:
                    sx2, sy2 = gs_to_screen(*d['xys_br'][0])
                    scr_sz = f" -> ({sx2:.0f},{sy2:.0f}) = {sx2-sx:.0f}x{sy2-sy:.0f}px"

            print(f"  [{i:>3}] UV ({u_tl:6.1f},{v_tl:5.1f})-({u_br:6.1f},{v_br:5.1f})  "
                  f"tex {u_br-u_tl:3.0f}x{v_br-v_tl:<3.0f}  "
                  f"screen {scr_str}{scr_sz}")


if __name__ == '__main__':
    main()
