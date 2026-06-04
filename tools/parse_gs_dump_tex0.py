#!/usr/bin/env python3
"""Parse a PCSX2 GS dump (.gs.zst) to find TEX0 values used in draw calls.

Focus: identify PSMT4 font atlas textures used for stat label rendering
on the chargen screen.

Strategy: Search for A+D GIF tags (NREG=1, REGS=0x0E) in the decompressed
data and extract all register writes including TEX0_1.
"""

import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

import zstandard as zstd

GS_DUMP = Path(r"C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps/Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260603181358.gs.zst")

PSM_NAMES = {
    0x00: "PSMCT32", 0x01: "PSMCT24", 0x02: "PSMCT16", 0x0A: "PSMCT16S",
    0x13: "PSMT8", 0x14: "PSMT4", 0x1B: "PSMT8H",
    0x24: "PSMT4HL", 0x2C: "PSMT4HH",
    0x30: "PSMZ32", 0x31: "PSMZ24", 0x32: "PSMZ16", 0x3A: "PSMZ16S",
}

REG_NAMES = {
    0x00: "PRIM", 0x01: "RGBAQ", 0x02: "ST", 0x03: "UV",
    0x04: "XYZF2", 0x05: "XYZ2", 0x06: "TEX0_1", 0x07: "TEX0_2",
    0x08: "CLAMP_1", 0x09: "CLAMP_2", 0x0A: "FOG",
    0x0C: "XYZF3", 0x0D: "XYZ3", 0x0E: "A+D", 0x0F: "NOP",
    0x14: "TEX1_1", 0x15: "TEX1_2", 0x16: "TEX2_1", 0x17: "TEX2_2",
    0x18: "XYOFFSET_1", 0x19: "XYOFFSET_2",
    0x1A: "PRMODECONT", 0x1B: "PRMODE", 0x22: "TEXCLUT",
    0x34: "SCANMSK", 0x3B: "MIPTBP1_1", 0x3C: "MIPTBP1_2",
    0x3D: "MIPTBP2_1", 0x3E: "MIPTBP2_2", 0x3F: "TEXA",
    0x40: "FOGCOL", 0x42: "TEXFLUSH",
    0x43: "SCISSOR_1", 0x44: "SCISSOR_2",
    0x45: "ALPHA_1", 0x46: "ALPHA_2", 0x47: "DIMX",
    0x48: "DTHE", 0x49: "COLCLAMP",
    0x4A: "TEST_1", 0x4B: "TEST_2",
    0x4C: "PABE", 0x4D: "FBA_1", 0x4E: "FBA_2",
    0x50: "BITBLTBUF", 0x51: "TRXPOS", 0x52: "TRXREG", 0x53: "TRXDIR",
    0x54: "HWREG", 0x60: "SIGNAL", 0x61: "FINISH", 0x62: "LABEL",
}

PRIM_TYPES = ['Point', 'Line', 'LineStrip', 'Tri', 'TriStrip', 'TriFan', 'Sprite']


def parse_tex0(val):
    return {
        'tbp0': val & 0x3FFF, 'tbw': (val >> 14) & 0x3F,
        'psm': (val >> 20) & 0x3F,
        'tw': 1 << ((val >> 26) & 0xF), 'th': 1 << ((val >> 30) & 0xF),
        'tcc': (val >> 34) & 1, 'tfx': (val >> 35) & 3,
        'cbp': (val >> 37) & 0x3FFF, 'cpsm': (val >> 51) & 0xF,
        'csm': (val >> 55) & 1, 'csa': (val >> 56) & 0x1F,
        'cld': (val >> 61) & 7, 'raw': val,
    }


def find_ad_blocks(data):
    """Find all A+D GIF tag blocks."""
    target_hi = struct.pack('<Q', 0x000000000000000E)
    blocks = []
    pos = 0
    while pos < len(data) - 16:
        idx = data.find(target_hi, pos)
        if idx == -1 or idx < 8:
            break
        lo = struct.unpack_from('<Q', data, idx - 8)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 58) & 3
        nreg = (lo >> 60) & 0xF
        if nreg == 0:
            nreg = 16
        if flg == 0 and nreg == 1 and 1 <= nloop <= 200:
            writes = []
            for i in range(nloop):
                off = idx + 8 + i * 16
                if off + 16 > len(data):
                    break
                val = struct.unpack_from('<Q', data, off)[0]
                addr = struct.unpack_from('<Q', data, off + 8)[0] & 0xFF
                writes.append((addr, val))
            blocks.append((idx - 8, nloop, writes))
            pos = idx + 8 + nloop * 16
        else:
            pos = idx + 8
    return blocks


def main():
    print(f"Reading: {GS_DUMP}")
    print(f"File size: {GS_DUMP.stat().st_size:,} bytes")

    dctx = zstd.ZstdDecompressor()
    with open(GS_DUMP, 'rb') as f:
        data = dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)
    print(f"Decompressed: {len(data):,} bytes")

    # Parse header
    hdr = struct.unpack_from('<9I', data, 8)
    serial_off = hdr[2]
    serial_size = hdr[3]
    serial = data[44 + serial_off:44 + serial_off + serial_size]
    crc = hdr[4]
    print(f"Serial: {serial.decode('ascii','ignore')}, CRC: 0x{crc:08X}")

    # Find all A+D blocks
    print("\nScanning for A+D GIF blocks...")
    ad_blocks = find_ad_blocks(data)
    print(f"Found {len(ad_blocks)} A+D blocks")

    # ===== TEX0 ANALYSIS =====
    tex0_by_key = defaultdict(int)
    tex0_details = {}
    for off, nloop, writes in ad_blocks:
        for addr, val in writes:
            if addr == 0x06:
                p = parse_tex0(val)
                key = (p['tbp0'], p['tbw'], p['psm'])
                tex0_by_key[key] += 1
                if key not in tex0_details:
                    tex0_details[key] = p

    print(f"\n{'='*80}")
    print("ALL TEX0_1 VALUES (unique, sorted by write count)")
    print(f"{'='*80}")
    print(f"{'TBP0':>8} {'TBW':>5} {'PSM':>12} {'Writes':>8} {'TexW':>6} {'TexH':>6} "
          f"{'CBP':>8} {'CPSM':>10} {'VRAM':>10}")
    print("-" * 90)
    for key in sorted(tex0_by_key, key=tex0_by_key.get, reverse=True):
        tbp0, tbw, psm = key
        cnt = tex0_by_key[key]
        p = tex0_details[key]
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        cpsm_name = PSM_NAMES.get(p['cpsm'], f"0x{p['cpsm']:02X}")
        vram = tbp0 * 256
        print(f"0x{tbp0:04X} {tbw:5d} {psm_name:>12} {cnt:8d} {p['tw']:6d} {p['th']:6d} "
              f"0x{p['cbp']:04X} {cpsm_name:>10} 0x{vram:06X}")

    # ===== PSMT4 DETAIL =====
    psmt4_keys = [k for k in tex0_by_key if k[2] == 0x14]
    print(f"\n{'='*80}")
    print("PSMT4 TEXTURES -- FONT ATLAS CANDIDATES")
    print(f"{'='*80}")
    for key in sorted(psmt4_keys, key=lambda k: tex0_by_key[k], reverse=True):
        tbp0, tbw, psm = key
        p = tex0_details[key]
        cnt = tex0_by_key[key]
        cpsm_name = PSM_NAMES.get(p['cpsm'], f"0x{p['cpsm']:02X}")
        vram = tbp0 * 256
        buf_w = tbw * 64
        print(f"  TBP0=0x{tbp0:04X} TBW={tbw}(bufw={buf_w}px) writes={cnt:4d} "
              f"tex={p['tw']}x{p['th']} CLUT@0x{p['cbp']:04X}({cpsm_name}) "
              f"CSA={p['csa']} VRAM=0x{vram:06X}")

    # ===== VRAM COPIES =====
    print(f"\n{'='*80}")
    print("VRAM COPIES (BITBLTBUF)")
    print(f"{'='*80}")
    copy_info = defaultdict(int)
    for off, nloop, writes in ad_blocks:
        for addr, val in writes:
            if addr == 0x50:
                sbp = val & 0x3FFF
                sbw = (val >> 16) & 0x3F
                spsm = (val >> 24) & 0x3F
                dbp = (val >> 32) & 0x3FFF
                dbw = (val >> 48) & 0x3F
                dpsm = (val >> 56) & 0x3F
                copy_info[(sbp, sbw, spsm, dbp, dbw, dpsm)] += 1
    for key, cnt in sorted(copy_info.items(), key=lambda x: x[1], reverse=True):
        sbp, sbw, spsm, dbp, dbw, dpsm = key
        sn = PSM_NAMES.get(spsm, f"0x{spsm:02X}")
        dn = PSM_NAMES.get(dpsm, f"0x{dpsm:02X}")
        print(f"  SRC=0x{sbp:04X}(tbw={sbw},{sn}) -> DST=0x{dbp:04X}(tbw={dbw},{dn})  x{cnt}")

    # ===== RENDERING SEQUENCE =====
    # Track TEX0 + PRIM + vertices in order through blocks
    print(f"\n{'='*80}")
    print("RENDERING SEQUENCE (TEX0 -> PRIM -> Vertices)")
    print("Shows each texture-change + draw-call sequence")
    print(f"{'='*80}")

    current_tex0 = None
    current_prim = None
    seq_num = 0
    tex0_sequence = []  # (seq, tex0_key, tex0_details, prim_info, vertex_count, block_offset)

    for bi, (off, nloop, writes) in enumerate(ad_blocks):
        local_verts = 0
        for addr, val in writes:
            if addr == 0x06:
                # If we had accumulated draws, emit them
                if current_tex0 and local_verts > 0:
                    tex0_sequence.append((seq_num, current_tex0, current_prim, local_verts, off))
                    seq_num += 1
                    local_verts = 0
                p = parse_tex0(val)
                current_tex0 = (p['tbp0'], p['tbw'], p['psm'], p['tw'], p['th'], p['cbp'])
            elif addr == 0x00:
                ptype = val & 7
                tme = (val >> 4) & 1
                abe = (val >> 6) & 1
                current_prim = (ptype, tme, abe)
            elif addr in (0x05, 0x0D):
                local_verts += 1
            elif addr == 0x50:
                # VRAM copy - emit as special
                sbp = val & 0x3FFF
                dbp = (val >> 32) & 0x3FFF
                tex0_sequence.append((seq_num, ('VRAMCOPY', sbp, dbp, 0, 0, 0), None, 0, off))
                seq_num += 1
        if current_tex0 and local_verts > 0:
            tex0_sequence.append((seq_num, current_tex0, current_prim, local_verts, off))
            seq_num += 1

    # Show first 80 events
    shown = 0
    for seq, tex0, prim, verts, boff in tex0_sequence[:80]:
        if tex0[0] == 'VRAMCOPY':
            _, sbp, dbp = tex0[0], tex0[1], tex0[2]
            print(f"  [{seq:3d}] VRAM COPY 0x{sbp:04X} -> 0x{dbp:04X}")
        else:
            tbp0, tbw, psm, tw, th, cbp = tex0
            psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
            prim_str = ""
            if prim:
                pt, tme, abe = prim
                pname = PRIM_TYPES[pt] if pt < len(PRIM_TYPES) else str(pt)
                prim_str = f" prim={pname} tme={tme}"
            marker = ""
            if psm == 0x14 and tbp0 == 0x3000:
                marker = " *** R1272 FONT ***"
            elif psm == 0x14:
                marker = " [PSMT4]"
            elif psm == 0x00 and tbp0 == 0x3000:
                marker = " *** CACHED SCREEN ***"
            print(f"  [{seq:3d}] TBP0=0x{tbp0:04X} TBW={tbw} {psm_name:>8} "
                  f"{tw}x{th} CBP=0x{cbp:04X} verts={verts}{prim_str}{marker}")
        shown += 1

    if len(tex0_sequence) > 80:
        print(f"  ... ({len(tex0_sequence) - 80} more events)")

    # ===== SUMMARY =====
    print(f"\n{'='*80}")
    print("SUMMARY: FONT ATLAS IDENTIFICATION")
    print(f"{'='*80}")

    print("\nR1272 main font atlas (known):")
    r1272_key = (0x3000, 4, 0x14)
    if r1272_key in tex0_by_key:
        p = tex0_details[r1272_key]
        print(f"  TBP0=0x3000 TBW=4 PSMT4 {p['tw']}x{p['th']} -> {tex0_by_key[r1272_key]} TEX0 writes")
    else:
        print("  NOT FOUND as exact key")

    # List ALL unique CBP values used with PSMT4 textures
    print("\nAll PSMT4 CLUT base pointers (CBP):")
    cbp_set = set()
    for off, nloop, writes in ad_blocks:
        for addr, val in writes:
            if addr == 0x06:
                psm = (val >> 20) & 0x3F
                if psm == 0x14:
                    cbp = (val >> 37) & 0x3FFF
                    tbp0 = val & 0x3FFF
                    cbp_set.add((tbp0, cbp))
    for tbp0, cbp in sorted(cbp_set):
        vram_cbp = cbp * 256
        print(f"  TBP0=0x{tbp0:04X} -> CBP=0x{cbp:04X} (VRAM 0x{vram_cbp:06X})")

    print("\nConclusion:")
    print("  The PSMT4 font atlas at TBP0=0x3000 TBW=4 256x512 is R1272.")
    print("  Other high-frequency PSMT4 textures:")
    for key in sorted(psmt4_keys, key=lambda k: tex0_by_key[k], reverse=True)[:5]:
        tbp0, tbw, psm = key
        p = tex0_details[key]
        cnt = tex0_by_key[key]
        print(f"    TBP0=0x{tbp0:04X} TBW={tbw} {p['tw']}x{p['th']} -> {cnt} writes")


if __name__ == '__main__':
    main()
