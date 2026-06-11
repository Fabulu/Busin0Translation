#!/usr/bin/env python3
"""
Parse R2100 sub-block VIF/GIF DMA headers to determine VRAM upload destinations.

Each sub-block has a 0x4C0 byte header containing VIF commands that wrap
GIF A+D packets writing to GS registers. We look for:
  - BITBLTBUF (0x50): destination base pointer (DBP) and buffer width (DBW)
  - TRXPOS (0x51): destination X,Y coordinates
  - TRXREG (0x52): transfer width and height
  - TRXDIR (0x53): transfer direction
"""

import struct
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIG_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")

SECTOR = 2048
R2100_TOC_INDEX = 2100
TOC_ENTRIES = 2883
NUM_SUBS = 4
SUB_SIZE = 34624       # 0x8740
HDR_SIZE = 0x4C0       # 1216 bytes VIF/GIF header per sub-block

# GS register addresses
GS_REGS = {
    0x00: "PRIM",
    0x01: "RGBAQ",
    0x04: "XYZF2",
    0x05: "XYZ2",
    0x06: "TEX0_1",
    0x07: "TEX0_2",
    0x08: "CLAMP_1",
    0x09: "CLAMP_2",
    0x14: "TEX1_1",
    0x16: "TEX2_1",
    0x34: "MIPTBP1_1",
    0x36: "MIPTBP2_1",
    0x3F: "TEXFLUSH",
    0x40: "SCISSOR_1",
    0x42: "ALPHA_1",
    0x45: "DTHE",
    0x46: "COLCLAMP",
    0x47: "TEST_1",
    0x4C: "FRAME_1",
    0x4E: "ZBUF_1",
    0x50: "BITBLTBUF",
    0x51: "TRXPOS",
    0x52: "TRXREG",
    0x53: "TRXDIR",
    0x60: "SIGNAL",
    0x61: "FINISH",
    0x62: "LABEL",
}

# VIF opcodes (upper 7 bits of cmd byte)
VIF_CMDS = {
    0x00: "NOP",
    0x01: "STCYCL",
    0x04: "ITOP",
    0x05: "STMOD",
    0x10: "FLUSHE",
    0x11: "FLUSH",
    0x13: "FLUSHA",
    0x14: "MSCAL",
    0x15: "MSCALF",
    0x17: "MSCNT",
    0x20: "STMASK",
    0x30: "STROW",
    0x31: "STCOL",
    0x50: "DIRECT",
    0x51: "DIRECTHL",
}


def parse_bitbltbuf(data64):
    """Parse BITBLTBUF register value (64-bit)."""
    val = struct.unpack('<Q', data64)[0]
    sbp = val & 0x3FFF            # bits 0-13: source base pointer
    sbw = (val >> 16) & 0x3F      # bits 16-21: source buffer width
    spsm = (val >> 24) & 0x3F     # bits 24-29: source pixel storage format
    dbp = (val >> 32) & 0x3FFF    # bits 32-45: dest base pointer
    dbw = (val >> 48) & 0x3F      # bits 48-53: dest buffer width
    dpsm = (val >> 56) & 0x3F     # bits 56-61: dest pixel storage format

    psm_names = {0: "PSMCT32", 1: "PSMCT24", 2: "PSMCT16", 10: "PSMCT16S",
                 0x13: "PSMT8", 0x14: "PSMT4", 0x1B: "PSMT8H", 0x24: "PSMT4HL",
                 0x2C: "PSMT4HH", 0x30: "PSMZ32", 0x31: "PSMZ24", 0x32: "PSMZ16",
                 0x3A: "PSMZ16S"}

    return {
        'sbp': sbp, 'sbw': sbw, 'spsm': spsm,
        'dbp': dbp, 'dbw': dbw, 'dpsm': dpsm,
        'dbp_hex': f"0x{dbp:04X}",
        'dpsm_name': psm_names.get(dpsm, f"0x{dpsm:02X}"),
        'spsm_name': psm_names.get(spsm, f"0x{spsm:02X}"),
        'dbp_vram_addr': dbp * 64,  # in 32-bit words -> byte address = dbp * 256
    }


def parse_trxpos(data64):
    """Parse TRXPOS register value (64-bit)."""
    val = struct.unpack('<Q', data64)[0]
    ssax = val & 0x7FF            # bits 0-10: source upper-left X
    ssay = (val >> 16) & 0x7FF    # bits 16-26: source upper-left Y
    dsax = (val >> 32) & 0x7FF    # bits 32-42: dest upper-left X
    dsay = (val >> 48) & 0x7FF    # bits 48-58: dest upper-left Y
    dir_val = (val >> 59) & 0x3   # bits 59-60: pixel transmission order
    return {'ssax': ssax, 'ssay': ssay, 'dsax': dsax, 'dsay': dsay, 'dir': dir_val}


def parse_trxreg(data64):
    """Parse TRXREG register value (64-bit)."""
    val = struct.unpack('<Q', data64)[0]
    rrw = val & 0xFFF             # bits 0-11: transfer width
    rrh = (val >> 32) & 0xFFF     # bits 32-43: transfer height
    return {'width': rrw, 'height': rrh}


def parse_trxdir(data64):
    """Parse TRXDIR register value (64-bit)."""
    val = struct.unpack('<Q', data64)[0]
    xdir = val & 0x3
    dir_names = {0: "host->local", 1: "local->host", 2: "local->local", 3: "disabled"}
    return {'dir': xdir, 'dir_name': dir_names.get(xdir, f"unknown({xdir})")}


def scan_for_gif_ad_packets(header_data):
    """Scan header for GIF A+D register writes.

    GIF A+D format: each entry is 16 bytes = 8 bytes data + 8 bytes register addr.
    The register address is in the low byte of the second quadword.

    We look for GIF tags first, then parse the A+D entries that follow.
    """
    results = []
    size = len(header_data)

    # Strategy: scan for known GS register patterns in the header
    # In A+D mode, every 16 bytes: [8 bytes data][8 bytes where low byte = register]
    # Look for BITBLTBUF (0x50), TRXPOS (0x51), TRXREG (0x52), TRXDIR (0x53)

    for off in range(0, size - 16, 4):  # scan at 4-byte alignment
        # Check if bytes at off+8 look like a GS register address
        if off + 16 > size:
            break

        reg_byte = header_data[off + 8]
        # Check that bytes 9-15 are zero (register address is just low byte)
        rest = header_data[off + 9:off + 16]

        if reg_byte in GS_REGS and all(b == 0 for b in rest):
            data = header_data[off:off + 8]
            reg_name = GS_REGS[reg_byte]

            entry = {
                'offset': off,
                'reg': reg_byte,
                'reg_name': reg_name,
                'data_hex': data.hex(),
                'data': data,
            }

            if reg_byte == 0x50:  # BITBLTBUF
                entry['parsed'] = parse_bitbltbuf(data)
            elif reg_byte == 0x51:  # TRXPOS
                entry['parsed'] = parse_trxpos(data)
            elif reg_byte == 0x52:  # TRXREG
                entry['parsed'] = parse_trxreg(data)
            elif reg_byte == 0x53:  # TRXDIR
                entry['parsed'] = parse_trxdir(data)

            results.append(entry)

    return results


def main():
    print("=== R2100 VRAM Upload Header Analysis ===\n")

    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
        so, sc, tc = struct.unpack_from("<III", toc_data, R2100_TOC_INDEX * 12)
        byte_off = so * SECTOR
        byte_size = sc * SECTOR

        print(f"R2100 TOC: sector_offset=0x{so:X}, sector_count={sc}, type={tc}")
        print(f"  Byte offset: 0x{byte_off:X}, size: {byte_size}\n")

        f.seek(byte_off)
        r2100 = f.read(byte_size)

    # Parse descriptor table
    sub_entries = []
    for i in range(NUM_SUBS):
        sub_idx, sub_size, data_off, pad = struct.unpack_from("<IIII", r2100, i * 16)
        sub_entries.append((sub_idx, sub_size, data_off))
        print(f"Sub {i}: index={sub_idx}, size=0x{sub_size:X}, offset=0x{data_off:X}")

    print(f"\n{'='*70}")

    # Parse each sub-block's header
    all_uploads = []
    for blk in range(NUM_SUBS):
        sub_idx, sub_size, data_off = sub_entries[blk]
        header = r2100[data_off:data_off + HDR_SIZE]

        print(f"\n--- Sub-block {blk} header (0x{HDR_SIZE:X} bytes at R2100+0x{data_off:X}) ---")

        # Hex dump first 256 bytes for context
        print(f"\n  First 256 bytes hex dump:")
        for row in range(0, min(256, HDR_SIZE), 16):
            hex_str = ' '.join(f'{header[row+j]:02X}' for j in range(16) if row+j < HDR_SIZE)
            print(f"    {row:04X}: {hex_str}")

        # Scan for GIF A+D register writes
        entries = scan_for_gif_ad_packets(header)

        print(f"\n  GS register writes found: {len(entries)}")

        upload_info = {}
        for e in entries:
            print(f"    @0x{e['offset']:04X}: {e['reg_name']:12s} (0x{e['reg']:02X}) = {e['data_hex']}")
            if 'parsed' in e:
                p = e['parsed']
                if e['reg'] == 0x50:
                    print(f"             DBP=0x{p['dbp']:04X} (VRAM word 0x{p['dbp']*64:06X}), DBW={p['dbw']}, DPSM={p['dpsm_name']}")
                    print(f"             SBP=0x{p['sbp']:04X}, SBW={p['sbw']}, SPSM={p['spsm_name']}")
                    upload_info['bitbltbuf'] = p
                elif e['reg'] == 0x51:
                    print(f"             Src=({p['ssax']},{p['ssay']}) Dst=({p['dsax']},{p['dsay']}) Dir={p['dir']}")
                    upload_info['trxpos'] = p
                elif e['reg'] == 0x52:
                    print(f"             Width={p['width']}, Height={p['height']}")
                    upload_info['trxreg'] = p
                elif e['reg'] == 0x53:
                    print(f"             Direction: {p['dir_name']}")
                    upload_info['trxdir'] = p

        all_uploads.append(upload_info)

    # Summary comparison
    print(f"\n{'='*70}")
    print("SUMMARY: VRAM Upload Destinations")
    print(f"{'='*70}\n")

    for blk in range(NUM_SUBS):
        info = all_uploads[blk]
        bb = info.get('bitbltbuf', {})
        tp = info.get('trxpos', {})
        tr = info.get('trxreg', {})
        td = info.get('trxdir', {})

        dbp = bb.get('dbp', '?')
        dbw = bb.get('dbw', '?')
        dpsm = bb.get('dpsm_name', '?')
        dx = tp.get('dsax', '?')
        dy = tp.get('dsay', '?')
        tw = tr.get('width', '?')
        th = tr.get('height', '?')

        if isinstance(dbp, int):
            print(f"  Sub {blk}: DBP=0x{dbp:04X} (TBP0=0x{dbp:04X}), DBW={dbw}, DPSM={dpsm}")
        else:
            print(f"  Sub {blk}: DBP={dbp}, DBW={dbw}, DPSM={dpsm}")
        print(f"          Dest=({dx},{dy}), Size=({tw}x{th}), Dir={td.get('dir_name', '?')}")

    # Check for overlap
    print(f"\n{'='*70}")
    print("OVERLAP ANALYSIS")
    print(f"{'='*70}\n")

    dbps = set()
    for blk in range(NUM_SUBS):
        bb = all_uploads[blk].get('bitbltbuf', {})
        dbp = bb.get('dbp')
        if dbp is not None:
            dbps.add(dbp)

    if len(dbps) == 1:
        print("*** ALL 4 SUB-BLOCKS UPLOAD TO THE SAME VRAM BASE! ***")
        print(f"    DBP = 0x{list(dbps)[0]:04X}")
        print()
        print("This means later sub-block uploads OVERWRITE earlier ones.")
        print("Any cells at the same pixel coordinates across sub-blocks will conflict.")

        # Check overlap with F/M cells in sub0
        # F = cell 38 in sub0: row=2, col=6 -> pixel (96,32)-(111,47)
        # M = cell 45 in sub0: row=2, col=13 -> pixel (208,32)-(223,47)
        print()
        print("F/M cells in sub0:")
        print("  F (cell 38): row=2, col=6 -> pixels (96,32)-(111,47)")
        print("  M (cell 45): row=2, col=13 -> pixels (208,32)-(223,47)")

        # Check which STAT_PATCHES or GENDER_PATCHES overlap these coordinates
        from patch_r2100 import STAT_PATCHES, GENDER_PATCHES

        f_row, f_col = 2, 6
        m_row, m_col = 2, 13

        print()
        print("Checking sub1/sub2 patches at F/M positions...")
        for (sb, r, c), text in {**STAT_PATCHES, **GENDER_PATCHES}.items():
            if sb > 0 and ((r == f_row and c == f_col) or (r == m_row and c == m_col)):
                label = text if isinstance(text, str) else str(text)
                which = "F" if c == f_col else "M"
                print(f"  CONFLICT: Sub{sb} ({r},{c}) = '{label}' overlaps sub0's {which} cell!")

        print()
        print("Checking: do sub1/sub2 headers specify different TRXPOS (dest offset)?")
        for blk in range(NUM_SUBS):
            tp = all_uploads[blk].get('trxpos', {})
            dx = tp.get('dsax', '?')
            dy = tp.get('dsay', '?')
            if dx != 0 or dy != 0:
                print(f"  Sub {blk}: TRXPOS dest = ({dx},{dy}) -- OFFSET, not (0,0)!")
            else:
                print(f"  Sub {blk}: TRXPOS dest = ({dx},{dy}) -- same origin")

    elif len(dbps) == NUM_SUBS:
        print("All 4 sub-blocks upload to DIFFERENT VRAM bases. No overlap.")
        for blk in range(NUM_SUBS):
            bb = all_uploads[blk].get('bitbltbuf', {})
            print(f"  Sub {blk}: DBP=0x{bb.get('dbp', 0):04X}")
    else:
        print(f"Mixed: {len(dbps)} unique DBP values among {NUM_SUBS} sub-blocks.")
        for blk in range(NUM_SUBS):
            bb = all_uploads[blk].get('bitbltbuf', {})
            print(f"  Sub {blk}: DBP=0x{bb.get('dbp', 0):04X}")

    # Also check if headers are identical across sub-blocks
    print(f"\n{'='*70}")
    print("HEADER COMPARISON")
    print(f"{'='*70}\n")

    headers = []
    for blk in range(NUM_SUBS):
        _, _, data_off = sub_entries[blk]
        headers.append(r2100[data_off:data_off + HDR_SIZE])

    if all(h == headers[0] for h in headers[1:]):
        print("ALL 4 headers are BYTE-IDENTICAL.")
        print("This confirms all sub-blocks upload to the exact same VRAM location.")
    else:
        print("Headers DIFFER between sub-blocks.")
        for i in range(1, NUM_SUBS):
            diffs = []
            for j in range(HDR_SIZE):
                if headers[i][j] != headers[0][j]:
                    diffs.append(j)
            if diffs:
                print(f"  Sub 0 vs Sub {i}: {len(diffs)} byte differences at offsets: {diffs[:20]}...")
            else:
                print(f"  Sub 0 vs Sub {i}: identical")


if __name__ == "__main__":
    main()
