#!/usr/bin/env python3
"""Compare TBP0=0x2840 keyboard atlas between chargen stat screen and name entry screen GS dumps.

For each dump:
1. Extract initial VRAM state
2. Deswizzle TBP0=0x2840 as PSMT4 256x256 (bw_psmt4=256, dbw_ct32=128)
3. Extract cells 38 (F) and 45 (M)
4. Count non-transparent pixels
5. Count draws from TBP0=0x2840
"""

import struct
import sys
import os
from collections import defaultdict

import zstandard as zstd

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import _psmt4_nibble_addr, _psmct32_word_addr

NAME_ENTRY_DUMP = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605055713.gs.zst"
CHARGEN_DUMP = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260603181358.gs.zst"

OUT_DIR = os.path.join(BASE, "debug_vram", "compare_2840")

PSM_NAMES = {
    0x00: "PSMCT32", 0x01: "PSMCT24", 0x02: "PSMCT16", 0x0A: "PSMCT16S",
    0x13: "PSMT8", 0x14: "PSMT4", 0x1B: "PSMT8H",
    0x24: "PSMT4HL", 0x2C: "PSMT4HH",
}
PRIM_TYPES = {0: "POINT", 1: "LINE", 2: "LINE_STRIP", 3: "TRI",
              4: "TRI_STRIP", 5: "TRI_FAN", 6: "SPRITE"}


def decompress_gs_dump(path):
    print(f"  Decompressing {os.path.basename(path)}...")
    with open(path, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(f.read(), max_output_size=1024 * 1024 * 1024)


def parse_gs_dump_header(data):
    """Parse GS dump header, return (state_data, packets_start_offset).

    GS dump format (PCSX2):
    - 4 bytes: fake CRC
    - 4 bytes: header_total_size (includes the 9 ints below)
    - 9 x 4 bytes: state_version, state_size, ...
    - state_size bytes: GS state (registers + VRAM)
    - 0x2000 bytes: internal registers
    - then packet stream
    """
    pos = 0
    fake_crc = struct.unpack_from("<I", data, pos)[0]; pos += 4
    header_total_size = struct.unpack_from("<I", data, pos)[0]; pos += 4
    hdr = struct.unpack_from("<9I", data, pos)
    state_version, state_size = hdr[0], hdr[1]

    data_start = 8 + header_total_size
    # State includes VRAM (4MB) + registers
    packets_start = data_start + state_size + 0x2000

    print(f"    Header total: {header_total_size}, state_version: {state_version}, state_size: {state_size}")
    print(f"    Data start: {data_start}, packets start: {packets_start}")

    return data_start, state_size, packets_start


def extract_initial_vram(data, data_start, state_size):
    """Extract the initial VRAM snapshot from the GS state.

    The state contains: GS registers (509 bytes or so), then 4MB VRAM.
    But actually in GS dumps, the state is laid out differently.
    Let's check the actual structure.
    """
    # In PCSX2 GS dumps, the state block contains registers + VRAM
    # VRAM is 4MB = 4194304 bytes
    # The registers come first, then VRAM fills the rest
    VRAM_SIZE = 4 * 1024 * 1024

    # State starts at data_start, is state_size bytes
    state_data = data[data_start:data_start + state_size]

    # VRAM is at the END of the state block (last 4MB)
    if state_size >= VRAM_SIZE:
        vram_offset = state_size - VRAM_SIZE
        vram = state_data[vram_offset:vram_offset + VRAM_SIZE]
        print(f"    VRAM extracted: {len(vram)} bytes (offset {vram_offset} in state)")
        return vram
    else:
        print(f"    WARNING: state_size {state_size} < VRAM_SIZE {VRAM_SIZE}")
        return state_data


def read_psmt4_from_vram(vram, tbp0, tex_w, tex_h, bw_psmt4):
    """Read PSMT4 texture from linear VRAM at TBP0."""
    base_byte = tbp0 * 256
    base_nibble = base_byte * 2
    out = bytearray(tex_w * tex_h)
    for y in range(tex_h):
        for x in range(tex_w):
            nib_offset = _psmt4_nibble_addr(x, y, bw_psmt4)
            nib_addr = base_nibble + nib_offset
            byte_addr = nib_addr // 2
            if byte_addr < len(vram):
                byte_val = vram[byte_addr]
                if nib_addr & 1:
                    out[y * tex_w + x] = (byte_val >> 4) & 0xF
                else:
                    out[y * tex_w + x] = byte_val & 0xF
    return out


def extract_cell(pixels, tex_w, cell_col, cell_row, cell_size=16):
    """Extract a cell_size x cell_size cell from a pixel array."""
    cell = bytearray(cell_size * cell_size)
    x0 = cell_col * cell_size
    y0 = cell_row * cell_size
    for cy in range(cell_size):
        for cx in range(cell_size):
            cell[cy * cell_size + cx] = pixels[(y0 + cy) * tex_w + (x0 + cx)]
    return cell


def save_grayscale(pixels, w, h, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img = Image.new('L', (w, h))
    img.putdata([min(p, 15) * 17 for p in pixels[:w * h]])
    img.save(path)


def parse_tex0(val):
    return {
        'tbp0': val & 0x3FFF, 'tbw': (val >> 14) & 0x3F,
        'psm': (val >> 20) & 0x3F,
        'tw': 1 << ((val >> 26) & 0xF), 'th': 1 << ((val >> 30) & 0xF),
        'cbp': (val >> 37) & 0x3FFF, 'cpsm': (val >> 51) & 0xF,
        'csa': (val >> 56) & 0x1F, 'cld': (val >> 61) & 7,
    }


def parse_bitbltbuf(val64):
    return {
        'sbp': val64 & 0x3FFF,
        'sbw': (val64 >> 16) & 0x3F,
        'spsm': (val64 >> 24) & 0x3F,
        'dbp': (val64 >> 32) & 0x3FFF,
        'dbw': (val64 >> 48) & 0x3F,
        'dpsm': (val64 >> 56) & 0x3F,
    }


def parse_trxreg(val64):
    return {
        'rrw': val64 & 0xFFF,
        'rrh': (val64 >> 32) & 0xFFF,
    }


REG_AD = 0x0E
REG_BITBLTBUF = 0x50
REG_TRXREG = 0x52
REG_TRXDIR = 0x53


def count_draws_and_uploads(data, packets_start, max_vsyncs=4):
    """Parse packet stream and count draws from TBP0=0x2840 and uploads to DBP=0x2840 area."""

    cur_tex0 = None
    cur_xyoffset = (0, 0)
    cur_bitbltbuf = None
    cur_trxreg = None

    draws_2840 = []
    all_tex0_counts = defaultdict(int)
    uploads = []

    pos = packets_start
    vsync_count = 0

    while pos < len(data) and vsync_count < max_vsyncs:
        if pos >= len(data):
            break
        tag = data[pos]; pos += 1

        if tag == 0:  # Transfer (GIF packet)
            if pos + 5 > len(data): break
            path_idx = data[pos]; pos += 1
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            if size > 100_000_000 or pos + size > len(data): break
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
                                elif reg_addr == 0x18:
                                    cur_xyoffset = (plo & 0xFFFF, (plo >> 32) & 0xFFFF)
                                elif reg_addr == REG_BITBLTBUF:
                                    cur_bitbltbuf = parse_bitbltbuf(plo)
                                elif reg_addr == REG_TRXREG:
                                    cur_trxreg = parse_trxreg(plo)
                                elif reg_addr == REG_TRXDIR:
                                    xdir = plo & 3
                                    if xdir == 0 and cur_bitbltbuf and cur_trxreg:
                                        uploads.append({
                                            'vsync': vsync_count,
                                            'bitbltbuf': dict(cur_bitbltbuf),
                                            'trxreg': dict(cur_trxreg),
                                        })
                                elif reg_addr in (0x04, 0x05, 0x0C, 0x0D):
                                    x = plo & 0xFFFF; y = (plo >> 16) & 0xFFFF
                                    verts.append((x, y))
                                elif reg_addr == 0x03:
                                    u = plo & 0x3FFF; v = (plo >> 16) & 0x3FFF
                                    uvs.append((u, v))
                            elif reg_id == 0x05:  # XYZ2
                                x = plo & 0xFFFF; y = (plo >> 32) & 0xFFFF
                                verts.append((x, y))
                            elif reg_id == 0x04:  # XYZF2
                                x = plo & 0xFFFF; y = (plo >> 32) & 0xFFFF
                                verts.append((x, y))
                            elif reg_id == 0x03:  # UV
                                u = plo & 0x3FFF; v = (plo >> 32) & 0x3FFF
                                uvs.append((u, v))
                            elif reg_id == 0x00:  # PRIM
                                prim_type = plo & 0x7
                                tme = (plo >> 4) & 1
                            gpos += 16

                    if verts and cur_tex0 and tme:
                        tbp0 = cur_tex0['tbp0']
                        all_tex0_counts[tbp0] += 1
                        if tbp0 == 0x2840:
                            draws_2840.append({
                                'vsync': vsync_count,
                                'tex0': dict(cur_tex0),
                                'prim': prim_type,
                                'verts': verts, 'uvs': uvs,
                                'xyoff': cur_xyoffset,
                                'flg': 'PACKED',
                            })

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
                        tbp0 = cur_tex0['tbp0']
                        all_tex0_counts[tbp0] += 1
                        if tbp0 == 0x2840:
                            draws_2840.append({
                                'vsync': vsync_count,
                                'tex0': dict(cur_tex0),
                                'prim': prim_type, 'tme': tme,
                                'verts': verts, 'uvs': uvs,
                                'xyoff': cur_xyoffset,
                                'flg': 'REGLIST',
                            })

                elif flg == 2:  # IMAGE
                    gpos += nloop * 16

                if eop: break

        elif tag == 1:  # Vsync
            if pos + 1 > len(data): break
            pos += 1
            vsync_count += 1

        elif tag == 2:  # FIFO
            if pos + 4 > len(data): break
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            if pos + size > len(data): break
            pos += size

        elif tag == 3:  # Registers
            if pos + 0x2000 > len(data): break
            pos += 0x2000

        else:
            break

    return draws_2840, uploads, all_tex0_counts, vsync_count


def analyze_draws_2840(draws, label):
    """Analyze TBP0=0x2840 draws for cell indices and F/M presence."""
    print(f"\n  Total draws from TBP0=0x2840: {len(draws)}")

    cell_usage = defaultdict(int)
    cell_positions = {}

    for d in draws:
        if len(d['uvs']) >= 2:
            u0 = d['uvs'][0][0] / 16.0
            v0 = d['uvs'][0][1] / 16.0
            cell_col = int(round(u0)) // 16
            cell_row = int(round(v0)) // 16
            cell_idx = cell_row * 16 + cell_col
            cell_usage[(cell_col, cell_row)] += 1

            ox, oy = d['xyoff']
            if len(d['verts']) >= 2:
                sx = (d['verts'][0][0] - ox) / 16.0
                sy = (d['verts'][0][1] - oy) / 16.0
                cell_positions[(cell_col, cell_row)] = (sx, sy)

    # Check for cells 38 (F) and 45 (M)
    # Cell 38: col=6, row=2 (38 = 2*16 + 6)
    # Cell 45: col=13, row=2 (45 = 2*16 + 13)
    cell_38 = cell_usage.get((6, 2), 0)
    cell_45 = cell_usage.get((13, 2), 0)

    print(f"  Cell 38 (F) at (6,2): {cell_38} draws")
    print(f"  Cell 45 (M) at (13,2): {cell_45} draws")

    # Print cell usage grid
    print(f"\n  Atlas cell usage grid (16x16):")
    print("       ", end="")
    for c in range(16):
        print(f"{c:3d}", end="")
    print()
    for r in range(16):
        print(f"    {r:2d}:", end="")
        for c in range(16):
            cnt = cell_usage.get((c, r), 0)
            if c == 6 and r == 2:
                print(f" F{'!' if cnt > 0 else '.'}", end="")
            elif c == 13 and r == 2:
                print(f" M{'!' if cnt > 0 else '.'}", end="")
            elif cnt > 0:
                print(f"{cnt:3d}", end="")
            else:
                print("  .", end="")
        print()

    # Group by screen row
    rows = defaultdict(list)
    for (cc, cr), cnt in cell_usage.items():
        pos = cell_positions.get((cc, cr))
        if pos:
            row_y = round(pos[1] / 10) * 10
            rows[row_y].append((pos[0], cc, cr, cc + cr * 16))

    print(f"\n  Keyboard grid by screen row:")
    for ry in sorted(rows.keys()):
        items = sorted(rows[ry])
        cells_str = ", ".join([f"({cc},{cr})={idx}" for _, cc, cr, idx in items])
        print(f"    Y~{ry}: {len(items)} cells: {cells_str}")

    return cell_usage


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=" * 80)
    print("COMPARE TBP0=0x2840 BETWEEN CHARGEN STAT AND NAME ENTRY GS DUMPS")
    print("=" * 80)

    dumps = {
        'chargen': CHARGEN_DUMP,
        'nameentry': NAME_ENTRY_DUMP,
    }

    vram_data = {}
    atlas_pixels = {}

    for label, path in dumps.items():
        print(f"\n{'='*80}")
        print(f"  DUMP: {label}")
        print(f"{'='*80}")

        data = decompress_gs_dump(path)
        print(f"    Decompressed size: {len(data):,} bytes")

        data_start, state_size, packets_start = parse_gs_dump_header(data)

        # Extract initial VRAM
        vram = extract_initial_vram(data, data_start, state_size)
        vram_data[label] = vram

        # Deswizzle TBP0=0x2840 as PSMT4 256x256 bw=256
        print(f"\n  Deswizzling TBP0=0x2840 as PSMT4 256x256 bw=256...")
        px = read_psmt4_from_vram(vram, 0x2840, 256, 256, 256)
        atlas_pixels[label] = px

        nz = sum(1 for p in px if p != 0)
        print(f"    Total non-zero pixels: {nz} / {256*256} ({nz*100/(256*256):.1f}%)")

        # Save full atlas
        save_grayscale(px, 256, 256, os.path.join(OUT_DIR, f"{label}_atlas_2840.png"))
        print(f"    Saved: {label}_atlas_2840.png")

        # Extract cells 38 (F) and 45 (M)
        # Cell 38: col=6, row=2
        cell_38 = extract_cell(px, 256, 6, 2, 16)
        cell_45 = extract_cell(px, 256, 13, 2, 16)

        nz_38 = sum(1 for p in cell_38 if p != 0)
        nz_45 = sum(1 for p in cell_45 if p != 0)
        print(f"\n    Cell 38 (F) at (col=6, row=2): {nz_38} non-transparent pixels / 256")
        print(f"    Cell 45 (M) at (col=13, row=2): {nz_45} non-transparent pixels / 256")

        # Save individual cells (scaled up 8x for visibility)
        for cell_name, cell_data, cell_idx in [("cell38_F", cell_38, 38), ("cell45_M", cell_45, 45)]:
            img = Image.new('L', (16, 16))
            img.putdata([min(p, 15) * 17 for p in cell_data])
            img_big = img.resize((128, 128), Image.Resampling.NEAREST)
            img_big.save(os.path.join(OUT_DIR, f"{label}_{cell_name}.png"))
            print(f"    Saved: {label}_{cell_name}.png")

        # Also print pixel data for cells
        print(f"\n    Cell 38 (F) pixel data (hex nibbles, 16 rows):")
        for r in range(16):
            row_data = cell_38[r*16:(r+1)*16]
            hex_str = ''.join(f'{p:X}' for p in row_data)
            print(f"      {hex_str}")

        print(f"\n    Cell 45 (M) pixel data (hex nibbles, 16 rows):")
        for r in range(16):
            row_data = cell_45[r*16:(r+1)*16]
            hex_str = ''.join(f'{p:X}' for p in row_data)
            print(f"      {hex_str}")

        # Also check a few nearby cells for context
        print(f"\n    Nearby cell non-zero counts:")
        for idx in range(33, 59):  # A through Z
            col = idx % 16
            row = idx // 16
            cell = extract_cell(px, 256, col, row, 16)
            nz_c = sum(1 for p in cell if p != 0)
            letter = chr(ord('A') + idx - 33)
            marker = " <<<" if idx in (38, 45) else ""
            print(f"      Cell {idx:3d} ({col:2d},{row:2d}) = '{letter}': {nz_c:3d} non-zero{marker}")

        # Count draws
        print(f"\n  Parsing draw calls...")
        draws, uploads, tex0_counts, vsync_total = count_draws_and_uploads(data, packets_start)
        print(f"    Vsyncs parsed: {vsync_total}")

        # Show uploads targeting 0x2840 area
        uploads_2840 = [u for u in uploads if 0x2800 <= u['bitbltbuf']['dbp'] <= 0x2900]
        print(f"\n    Uploads targeting DBP 0x2800-0x2900: {len(uploads_2840)}")
        for u in uploads_2840:
            bb = u['bitbltbuf']
            tr = u['trxreg']
            psm = PSM_NAMES.get(bb['dpsm'], f"0x{bb['dpsm']:02X}")
            print(f"      Vsync {u['vsync']}: DBP=0x{bb['dbp']:04X} DBW={bb['dbw']} {psm} {tr['rrw']}x{tr['rrh']}")

        # Analyze draw cells
        print(f"\n    Draw analysis:")
        analyze_draws_2840(draws, label)

        # Show all TBP0 values used
        print(f"\n    All TBP0 values used in draws:")
        for tbp0 in sorted(tex0_counts.keys()):
            cnt = tex0_counts[tbp0]
            marker = " <<<" if tbp0 == 0x2840 else ""
            print(f"      TBP0=0x{tbp0:04X}: {cnt} draws{marker}")

    # ===== COMPARE BETWEEN DUMPS =====
    print(f"\n{'='*80}")
    print("COMPARISON BETWEEN CHARGEN AND NAME ENTRY")
    print(f"{'='*80}")

    px_cg = atlas_pixels['chargen']
    px_ne = atlas_pixels['nameentry']

    # Overall comparison
    total = 256 * 256
    matches = sum(1 for i in range(total) if px_cg[i] == px_ne[i])
    print(f"\n  Full atlas comparison: {matches}/{total} pixels match ({matches*100/total:.1f}%)")

    # Cell-by-cell comparison
    print(f"\n  Cell-by-cell comparison (16x16 cells, 256 pixels each):")
    diff_cells = []
    for row in range(16):
        for col in range(16):
            cell_cg = extract_cell(px_cg, 256, col, row, 16)
            cell_ne = extract_cell(px_ne, 256, col, row, 16)
            cell_matches = sum(1 for i in range(256) if cell_cg[i] == cell_ne[i])
            if cell_matches < 256:
                idx = row * 16 + col
                nz_cg = sum(1 for p in cell_cg if p != 0)
                nz_ne = sum(1 for p in cell_ne if p != 0)
                diff_cells.append((col, row, idx, cell_matches, nz_cg, nz_ne))

    if diff_cells:
        print(f"    {len(diff_cells)} cells differ:")
        for col, row, idx, m, nz_cg, nz_ne in diff_cells:
            marker = ""
            if idx == 38: marker = " [F]"
            elif idx == 45: marker = " [M]"
            print(f"      Cell ({col:2d},{row:2d}) idx={idx:3d}: {m}/256 match, "
                  f"chargen {nz_cg} nz, nameentry {nz_ne} nz{marker}")
    else:
        print(f"    ALL cells are IDENTICAL between the two dumps!")

    # Specific cells 38 and 45
    cell_38_cg = extract_cell(px_cg, 256, 6, 2, 16)
    cell_38_ne = extract_cell(px_ne, 256, 6, 2, 16)
    cell_45_cg = extract_cell(px_cg, 256, 13, 2, 16)
    cell_45_ne = extract_cell(px_ne, 256, 13, 2, 16)

    m38 = sum(1 for i in range(256) if cell_38_cg[i] == cell_38_ne[i])
    m45 = sum(1 for i in range(256) if cell_45_cg[i] == cell_45_ne[i])
    print(f"\n  Cell 38 (F): {m38}/256 pixels identical between dumps")
    print(f"  Cell 45 (M): {m45}/256 pixels identical between dumps")

    # Raw VRAM comparison at TBP0=0x2840 region
    base_byte = 0x2840 * 256
    region_size = 0x100 * 256  # ~256 pages worth
    if base_byte + region_size <= len(vram_data['chargen']):
        raw_cg = vram_data['chargen'][base_byte:base_byte + region_size]
        raw_ne = vram_data['nameentry'][base_byte:base_byte + region_size]
        raw_match = sum(1 for i in range(len(raw_cg)) if raw_cg[i] == raw_ne[i])
        print(f"\n  Raw VRAM at 0x{base_byte:06X} - 0x{base_byte+region_size:06X}:")
        print(f"    {raw_match}/{len(raw_cg)} bytes match ({raw_match*100/len(raw_cg):.1f}%)")

    print(f"\n  Done! Images saved to: {OUT_DIR}")


if __name__ == '__main__':
    main()
