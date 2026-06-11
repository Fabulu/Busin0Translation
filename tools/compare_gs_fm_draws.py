#!/usr/bin/env python3
"""Compare GS dumps across sessions to find F/M keyboard draw differences.

For each dump/save state:
1. Check if it's from a name entry screen (has TBP0=0x2840 keyboard draws)
2. If yes: parse draw calls and check if cells 38 (F) and 45 (M) are present
3. Compare across dumps
"""

import struct
import zipfile
from collections import defaultdict
from pathlib import Path

try:
    import zstandard as zstd
except ImportError:
    zstd = None

SNAPS_DIR = Path(r"C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps")
RAM_DIR = Path(r"C:/Programmieren/wizardrytranslation/RAMdumps")

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


def parse_gs_data(data, label=""):
    """Parse GS dump binary data, return list of draws with tex0/verts/uvs."""
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
    cur_frame_fbp = 0
    all_draws = []
    draw_seq = 0

    pos = packets_start
    vsync_count = 0

    while pos < len(data) and vsync_count < 2:
        if pos >= len(data):
            break
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

    return all_draws


def analyze_keyboard_draws(all_draws):
    """Analyze keyboard-related draws, return cell info."""
    kbd_draws = [d for d in all_draws if d['tex0']['tbp0'] == 0x2840]
    if not kbd_draws:
        return None

    grid_positions = []
    for d in kbd_draws:
        ox, oy = d['xyoff']
        if len(d['verts']) >= 2 and len(d['uvs']) >= 2:
            x0 = (d['verts'][0][0] - ox) / 16.0
            y0 = (d['verts'][0][1] - oy) / 16.0
            u0 = d['uvs'][0][0] / 16.0
            v0 = d['uvs'][0][1] / 16.0

            cell_col = int(round(u0)) // 16
            cell_row = int(round(v0)) // 16
            cell_idx = cell_row * 16 + cell_col

            grid_positions.append({
                'seq': d['seq'], 'sx': x0, 'sy': y0,
                'cell_col': cell_col, 'cell_row': cell_row,
                'cell_idx': cell_idx,
            })

    cell_indices = set(gp['cell_idx'] for gp in grid_positions)

    # Check for F (cell 38) and M (cell 45)
    has_F = 38 in cell_indices
    has_M = 45 in cell_indices

    # Group by screen row
    rows = defaultdict(list)
    for gp in grid_positions:
        row = round(gp['sy'] / 10) * 10
        rows[row].append(gp)

    # All unique TBP0 configs
    tex0_set = set()
    for d in kbd_draws:
        t = d['tex0']
        tex0_set.add((t['tbp0'], t['tbw'], t['psm'], t['tw'], t['th'], t['cbp']))

    return {
        'total_kbd_draws': len(kbd_draws),
        'total_unique_cells': len(cell_indices),
        'cell_indices': sorted(cell_indices),
        'has_F': has_F,
        'has_M': has_M,
        'grid_positions': grid_positions,
        'rows': {k: len(v) for k, v in rows.items()},
        'tex0_configs': tex0_set,
    }


def analyze_all_tex0(all_draws):
    """Get summary of all texture configs used."""
    tex0_counts = defaultdict(int)
    for d in all_draws:
        t = d['tex0']
        key = (t['tbp0'], t['tbw'], t['psm'], t['tw'], t['th'], t['cbp'])
        tex0_counts[key] += 1
    return tex0_counts


def load_gs_dump_zst(path):
    """Load and decompress a .gs.zst file."""
    dctx = zstd.ZstdDecompressor()
    with open(path, 'rb') as f:
        return dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)


def load_gs_from_savestate(p2s_path):
    """Extract GS.bin from a PCSX2 save state (.p2s = zip)."""
    try:
        with zipfile.ZipFile(p2s_path, 'r') as zf:
            names = zf.namelist()
            # Look for GS register state - not a full GS dump though
            # .p2s files contain eeMemory.bin, GS.bin, etc.
            if 'GS.bin' in names:
                return zf.read('GS.bin'), names
            # Some versions use different naming
            gs_files = [n for n in names if 'GS' in n.upper() and n.endswith('.bin')]
            if gs_files:
                return zf.read(gs_files[0]), names
    except Exception as e:
        return None, str(e)
    return None, "No GS.bin found"


def try_parse_gs_bin_as_dump(gs_data):
    """Try to parse GS.bin from save state as a GS dump.

    Save state GS.bin has a different format from GS dumps.
    It contains raw GS register state + VRAM snapshot.
    We can extract VRAM and check for texture data at specific addresses.
    """
    # GS.bin from save states is typically: registers + VRAM (4MB)
    # VRAM is 4MB = 4194304 bytes
    # The register state size varies

    # Try to find VRAM by looking for the expected size
    vram_size = 4 * 1024 * 1024  # 4MB

    if len(gs_data) < vram_size:
        return None

    # VRAM might be at the end of the file
    # Or it could start after a register header
    # Common GS.bin layouts: header + registers + VRAM

    # For PCSX2, GS.bin internal state includes VRAM at a known offset
    # The exact offset depends on the GS plugin version

    return {
        'total_size': len(gs_data),
        'has_vram': len(gs_data) >= vram_size,
    }


def check_vram_for_fm_cells(gs_data):
    """Check VRAM content at positions where F and M cells should be.

    TBP0=0x2840 in PSMT4 format, TBW=4
    Cell 38 = F: col=6, row=2 -> pixel position (96, 32) in 256x256
    Cell 45 = M: col=13, row=2 -> pixel position (208, 32) in 256x256

    In VRAM, TBP0=0x2840 means base pointer at block 0x2840
    Each block = 256 bytes in VRAM
    So byte offset = 0x2840 * 256 = 0x284000

    For PSMT4 at TBW=4 (64-pixel-wide pages), the layout is complex
    due to PS2 swizzling. But we can still check if the data is non-zero.
    """
    vram_offset_candidates = []

    # VRAM is typically at the end of GS.bin
    vram_size = 4 * 1024 * 1024
    if len(gs_data) >= vram_size:
        # Try VRAM at end
        vram_start = len(gs_data) - vram_size
        vram_offset_candidates.append(vram_start)

    # TBP0=0x2840 -> byte offset in VRAM
    # Each "block" is 256 bytes (page = 8192 bytes, 32 blocks per page)
    tbp_byte_offset = 0x2840 * 256  # = 0x284000 = 2,637,824

    results = {}
    for vram_start in vram_offset_candidates:
        vram = gs_data[vram_start:vram_start + vram_size]

        # Check if offset is within VRAM
        if tbp_byte_offset + 4096 <= vram_size:
            region = vram[tbp_byte_offset:tbp_byte_offset + 4096]
            non_zero = sum(1 for b in region if b != 0)
            results['tbp0_region_nonzero'] = non_zero
            results['tbp0_region_total'] = len(region)

            # Check broader region
            broader = vram[tbp_byte_offset:tbp_byte_offset + 32768]
            results['tbp0_broad_nonzero'] = sum(1 for b in broader if b != 0)
        else:
            results['tbp0_region_nonzero'] = -1
            results['note'] = 'TBP offset exceeds VRAM size'

    return results


def main():
    print("=" * 90)
    print("GS DUMP COMPARISON: F/M KEYBOARD DRAW ANALYSIS")
    print("=" * 90)

    # ===== Process .gs.zst dumps =====
    gs_dumps = sorted(SNAPS_DIR.glob("*.gs.zst"))
    print(f"\nFound {len(gs_dumps)} GS dumps in snaps folder")

    results = []

    for gs_path in gs_dumps:
        # Extract timestamp from filename
        name = gs_path.stem  # e.g. "Busin 0 - ...20260605055713.gs"
        timestamp = name.split("_")[-1].replace(".gs", "")
        short_name = f"GS-{timestamp}"

        print(f"\n{'=' * 70}")
        print(f"PROCESSING: {short_name}")
        print(f"  File: {gs_path.name}")

        try:
            data = load_gs_dump_zst(gs_path)
            print(f"  Decompressed: {len(data):,} bytes")

            all_draws = parse_gs_data(data, short_name)
            print(f"  Total draws: {len(all_draws)}")

            # Check all TEX0 configs
            tex0_counts = analyze_all_tex0(all_draws)

            # Is this a name entry screen?
            has_2840 = any(k[0] == 0x2840 for k in tex0_counts)

            if has_2840:
                print(f"  ** HAS TBP0=0x2840 draws (name entry keyboard!) **")
                kbd_info = analyze_keyboard_draws(all_draws)
                if kbd_info:
                    print(f"  Keyboard draws: {kbd_info['total_kbd_draws']}")
                    print(f"  Unique cells: {kbd_info['total_unique_cells']}")
                    print(f"  Cell 38 (F): {'PRESENT' if kbd_info['has_F'] else 'MISSING'}")
                    print(f"  Cell 45 (M): {'PRESENT' if kbd_info['has_M'] else 'MISSING'}")
                    print(f"  Cell indices: {kbd_info['cell_indices']}")
                    print(f"  Screen rows: {kbd_info['rows']}")

                    # Show the row detail for rows containing F/M positions
                    for gp in kbd_info['grid_positions']:
                        row_y = round(gp['sy'] / 10) * 10
                        if row_y in (150, 170):  # rows where F and M should be
                            letter = chr(ord('A') + gp['cell_idx'] - 33) if 33 <= gp['cell_idx'] <= 58 else f"#{gp['cell_idx']}"
                            print(f"    Y~{row_y} X={gp['sx']:.0f} cell={gp['cell_idx']} ({letter})")

                    results.append({
                        'name': short_name,
                        'type': 'gs_dump',
                        'has_keyboard': True,
                        'has_F': kbd_info['has_F'],
                        'has_M': kbd_info['has_M'],
                        'total_kbd_draws': kbd_info['total_kbd_draws'],
                        'cell_indices': kbd_info['cell_indices'],
                    })
                else:
                    results.append({'name': short_name, 'type': 'gs_dump',
                                   'has_keyboard': True, 'has_F': False, 'has_M': False,
                                   'note': 'kbd parse failed'})
            else:
                # List what TBP0 values ARE present
                tbp0_list = sorted(set(k[0] for k in tex0_counts))
                print(f"  No TBP0=0x2840 (not name entry screen)")
                print(f"  TBP0 values present: {[f'0x{t:04X}' for t in tbp0_list[:20]]}")
                results.append({'name': short_name, 'type': 'gs_dump',
                               'has_keyboard': False, 'tbp0_list': tbp0_list})

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            results.append({'name': short_name, 'type': 'gs_dump', 'error': str(e)})

    # ===== Process save states =====
    print(f"\n\n{'=' * 90}")
    print("SAVE STATE ANALYSIS")
    print("=" * 90)

    # Name-entry related save states
    nameentry_states = [
        'NameEntryEuropean.p2s', 'NameEntryHiraganamode.p2s',
        'NameEntryRandomCrap.p2s', 'NameEntryV1.p2s',
        'Nameentrystate.p2s', 'bustednameentry.p2s', 'bustednameentryv3.p2s',
        'genderselectv3.p2s', 'latinalphabetv3.p2s',
    ]

    for ss_name in nameentry_states:
        ss_path = RAM_DIR / ss_name
        if not ss_path.exists():
            continue

        print(f"\n{'=' * 70}")
        print(f"SAVE STATE: {ss_name}")

        try:
            gs_data, names = load_gs_from_savestate(ss_path)
            if gs_data is None:
                print(f"  No GS.bin found. Contents: {names}")
                continue

            print(f"  GS.bin size: {len(gs_data):,} bytes")
            if isinstance(names, list):
                print(f"  Archive contents: {names}")

            # Save state GS.bin is NOT a GS dump - it's register state + VRAM
            # Check VRAM for texture data at TBP0=0x2840
            vram_info = check_vram_for_fm_cells(gs_data)
            if vram_info:
                print(f"  VRAM check at TBP0=0x2840:")
                for k, v in vram_info.items():
                    print(f"    {k}: {v}")

            # Also try parsing as GS dump (won't work for save states, but safe to try)
            try:
                all_draws = parse_gs_data(gs_data, ss_name)
                if all_draws:
                    print(f"  (Parsed as GS dump: {len(all_draws)} draws)")
                    kbd_draws = [d for d in all_draws if d['tex0']['tbp0'] == 0x2840]
                    if kbd_draws:
                        print(f"  ** Found {len(kbd_draws)} keyboard draws! **")
            except:
                pass

            # Check EE memory for version markers
            with zipfile.ZipFile(ss_path, 'r') as zf:
                if 'eeMemory.bin' in zf.namelist():
                    ee_data = zf.read('eeMemory.bin')
                    # Look for version string patterns
                    for marker in [b'BUSIN0_EN_v', b'v9.', b'v19', b'v22', b'v27', b'v32', b'v35']:
                        idx = ee_data.find(marker)
                        if idx >= 0:
                            context = ee_data[max(0,idx-4):idx+20]
                            print(f"  EE RAM version marker at 0x{idx:X}: {context}")
                            break

                    # Check for the name entry keyboard table in EE RAM
                    # The game must have a table that maps grid positions to cell indices
                    # Look for the sequence of cell indices near cells 33-42
                    # (which would be bytes 33,34,35,36,37,38,39,40,41,42 = !,",#,$,%,&,',(,),*)

                    # Search for the keyboard character table
                    # In the Japanese original, this would be hiragana cell indices
                    # In the patched version, it should be 33-90 for A-Z, a-z

                    # Look for sequential bytes 33,34,35,36,37 (or 38,39 nearby)
                    target_seq = bytes([33, 34, 35, 36, 37])  # A,B,C,D,E
                    idx = 0
                    found_tables = []
                    while idx < len(ee_data) - 20:
                        idx = ee_data.find(target_seq, idx)
                        if idx < 0:
                            break
                        # Check what comes after - is 38 (F) there or is it skipped?
                        context = ee_data[idx:idx+30]
                        # Check if this looks like a keyboard table
                        if len(context) >= 10:
                            vals = list(context[:15])
                            # Is this sequential?
                            if vals[5] == 38:  # F is present!
                                found_tables.append(('F_PRESENT', idx, vals))
                            elif vals[5] == 39:  # F is skipped, jumps to G
                                found_tables.append(('F_SKIPPED', idx, vals))
                            else:
                                found_tables.append(('OTHER', idx, vals))
                        idx += 1

                    if found_tables:
                        print(f"  Keyboard table candidates in EE RAM: {len(found_tables)}")
                        for status, addr, vals in found_tables[:5]:
                            print(f"    0x{addr:08X}: {status} - {vals}")

                    # Also search for 2-byte (16-bit) cell index tables
                    # The game might use 16-bit or 32-bit indices
                    target_16 = struct.pack("<5H", 33, 34, 35, 36, 37)
                    idx = 0
                    found_16bit = []
                    while idx < len(ee_data) - 40:
                        idx = ee_data.find(target_16, idx)
                        if idx < 0:
                            break
                        # Check next value
                        next_val = struct.unpack_from("<H", ee_data, idx + 10)[0]
                        if next_val == 38:
                            found_16bit.append(('F_PRESENT_16', idx, next_val))
                        elif next_val == 39:
                            found_16bit.append(('F_SKIPPED_16', idx, next_val))
                        else:
                            found_16bit.append(('OTHER_16', idx, next_val))
                        idx += 2

                    if found_16bit:
                        print(f"  16-bit table candidates: {len(found_16bit)}")
                        for status, addr, nv in found_16bit[:5]:
                            context_bytes = ee_data[idx-2:idx+30] if idx > 2 else ee_data[:30]
                            print(f"    0x{addr:08X}: {status} (next val={nv})")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()

    # ===== Check standalone GS.bin files in RAMdumps =====
    print(f"\n\n{'=' * 90}")
    print("STANDALONE GS.bin FILES")
    print("=" * 90)

    for gs_bin in sorted(RAM_DIR.glob("GS*.bin")):
        print(f"\n  {gs_bin.name}: {gs_bin.stat().st_size:,} bytes")
        gs_data = gs_bin.read_bytes()

        # Try as GS dump
        try:
            all_draws = parse_gs_data(gs_data, gs_bin.name)
            if all_draws:
                print(f"    Parsed as GS dump: {len(all_draws)} draws")
                kbd_draws = [d for d in all_draws if d['tex0']['tbp0'] == 0x2840]
                if kbd_draws:
                    kbd_info = analyze_keyboard_draws(all_draws)
                    if kbd_info:
                        print(f"    ** KEYBOARD DRAWS FOUND! **")
                        print(f"    Cell 38 (F): {'PRESENT' if kbd_info['has_F'] else 'MISSING'}")
                        print(f"    Cell 45 (M): {'PRESENT' if kbd_info['has_M'] else 'MISSING'}")
                        print(f"    Cells: {kbd_info['cell_indices']}")
        except:
            pass

        # Check VRAM
        vram_info = check_vram_for_fm_cells(gs_data)
        if vram_info:
            for k, v in vram_info.items():
                print(f"    VRAM {k}: {v}")

    # ===== FINAL COMPARISON =====
    print(f"\n\n{'=' * 90}")
    print("FINAL COMPARISON TABLE")
    print("=" * 90)
    print(f"{'Name':<30} {'Keyboard?':>10} {'Cell38(F)':>10} {'Cell45(M)':>10} {'#Draws':>8} {'Notes':<30}")
    print("-" * 100)

    for r in results:
        name = r.get('name', '?')
        has_kbd = 'YES' if r.get('has_keyboard') else 'no'
        has_f = 'YES!' if r.get('has_F') else ('MISSING' if r.get('has_keyboard') else '-')
        has_m = 'YES!' if r.get('has_M') else ('MISSING' if r.get('has_keyboard') else '-')
        ndraws = str(r.get('total_kbd_draws', '-'))
        notes = r.get('note', r.get('error', ''))
        if not r.get('has_keyboard') and 'tbp0_list' in r:
            notes = f"TBP0s: {len(r['tbp0_list'])} configs"
        print(f"{name:<30} {has_kbd:>10} {has_f:>10} {has_m:>10} {ndraws:>8} {notes:<30}")

    # ===== CELL INDEX DIFF between dumps =====
    kbd_results = [r for r in results if r.get('has_keyboard') and 'cell_indices' in r]
    if len(kbd_results) >= 2:
        print(f"\n\n{'=' * 90}")
        print("CELL INDEX COMPARISON BETWEEN KEYBOARD DUMPS")
        print("=" * 90)

        for i, r1 in enumerate(kbd_results):
            for r2 in kbd_results[i+1:]:
                s1 = set(r1['cell_indices'])
                s2 = set(r2['cell_indices'])
                only1 = s1 - s2
                only2 = s2 - s1
                common = s1 & s2

                print(f"\n  {r1['name']} vs {r2['name']}:")
                print(f"    Common cells: {len(common)}")
                if only1:
                    print(f"    Only in {r1['name']}: {sorted(only1)}")
                if only2:
                    print(f"    Only in {r2['name']}: {sorted(only2)}")
                if not only1 and not only2:
                    print(f"    IDENTICAL cell sets!")


if __name__ == '__main__':
    main()
