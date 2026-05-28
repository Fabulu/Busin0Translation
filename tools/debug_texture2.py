#!/usr/bin/env python3
"""Detailed debug of R2119 and R2118 GS packet structure."""
import struct
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def dump_qws(tex, start_qw, count):
    """Dump quadwords."""
    for i in range(start_qw, min(start_qw + count, len(tex) // 16)):
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        hi = struct.unpack_from('<Q', tex, i * 16 + 8)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3
        nreg = (lo >> 60) & 0xF or 16
        eop = (lo >> 15) & 1
        b = tex[i*16:i*16+16]
        print(f"  QW[{i:5d}] {lo:016x} {hi:016x}  "
              f"(GIF: nloop={nloop} flg={flg} nreg={nreg} eop={eop}) "
              f"bytes: {b.hex()}")


def analyze_r2119():
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    total_qw = len(tex) // 16
    print(f"R2119: {len(tex)} bytes, {total_qw} QWs")

    # Show the first PACKED block (QW 0-16)
    print("\nFirst PACKED block (setup registers):")
    dump_qws(tex, 0, 20)

    # What's between QW[17] and QW[792]?
    # We know QW[0] PACKED nloop=1 nreg=16 -> uses QW 1..16
    # Then QW[17] should be the next GIF tag
    print("\nQW[17] and surroundings:")
    dump_qws(tex, 17, 5)

    # Check if QW[17] could be a GIF tag
    lo17 = struct.unpack_from('<Q', tex, 17 * 16)[0]
    nloop17 = lo17 & 0x7FFF
    flg17 = (lo17 >> 46) & 3
    print(f"\nQW[17] as GIF: nloop={nloop17}, flg={flg17}")

    # Maybe the data layout is different. Let me look at what's at QW[17]:
    # The first PACKED block writes 16 registers as A+D pairs
    # But wait - NREG=16 means all 16 registers come from the REGS field
    # The REGS field (hi word of QW[0]) = 0x0000000000000000
    # So all 16 regs are register 0 (PRIM)?! That doesn't make sense.

    # Actually, looking back at R2118, the PACKED at QW[0] has:
    # lo = 0x0000000200000001 -> nloop=1, nreg=16 (0 means 16)
    # hi = 0x0000000000000000 -> all regs are 0

    # But the actual data QWs have register addresses in their hi bytes:
    # QW[5]: data=TEX0 hi=0x06 (TEX0_1)
    # This means it's actually A+D mode where each QW has the register in its hi byte!

    # So it's NOT PACKED with reg list, it's PACKED with A+D where:
    # FLG=0, NREG could be anything, but the data is A+D pairs.
    # Actually NREG=16 and regs=[0,0,0,...0] means each packed datum uses reg 0x00
    # But that can't be right since QW[1] through QW[16] have different regs in hi.

    # OH WAIT. I think this might actually be a DMA/VIF wrapper, not a GIF packet.
    # Let me look at this as VIF codes instead.

    # VIF unpack codes:
    # Or maybe it's just a custom header, not standard GIF.

    # Let me just look at the raw data starting at different offsets
    # and try to make sense of the 34800 bytes

    # Method: find where the actual pixel data starts by looking for
    # a transition from structured data to pixel-like data

    print("\n--- Scanning for data transitions ---")
    prev_entropy = 0
    for qi in range(0, total_qw, 16):
        block = tex[qi*16:(qi+16)*16]
        if len(block) < 256:
            break
        unique = len(set(block))
        if abs(unique - prev_entropy) > 20 or qi < 32:
            print(f"  QW[{qi:5d}] offset={qi*16:6d}: unique_bytes={unique:3d}/256")
        prev_entropy = unique

    # Just dump some key QWs to understand the structure
    print("\n--- QWs around offset 272 (QW 17) ---")
    dump_qws(tex, 15, 8)

    print("\n--- QWs around QW 790 ---")
    dump_qws(tex, 788, 8)

    # Actually let me try a different approach:
    # look for BITBLTBUF (0x50), TRXPOS (0x51), TRXREG (0x52), TRXDIR (0x53)
    # These are written before each IMAGE transfer
    print("\n--- Scanning for GS transfer registers ---")
    for qi in range(total_qw):
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
        reg = hi & 0xFF
        if reg in (0x50, 0x51, 0x52, 0x53):
            names = {0x50: 'BITBLTBUF', 0x51: 'TRXPOS', 0x52: 'TRXREG', 0x53: 'TRXDIR'}
            extra = ""
            if reg == 0x52:
                w = lo & 0xFFF
                h = (lo >> 32) & 0xFFF
                extra = f" ({w}x{h})"
            elif reg == 0x50:
                dpsm = (lo >> 44) & 0x3F
                dbp = (lo >> 32) & 0x3FFF
                dbw = (lo >> 40) & 0x3F
                psm_names = {0:'PSMCT32',0x13:'PSMT8',0x14:'PSMT4'}
                extra = f" (DBP={dbp} DBW={dbw} DPSM=0x{dpsm:02x}={psm_names.get(dpsm,'?')})"
            print(f"  QW[{qi:5d}] {names[reg]}: 0x{lo:016x}{extra}")


def analyze_r2118_gap():
    """Look at the gap between IMAGE blocks 8 and 9 in R2118."""
    data = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex = data[16:]

    print("\nR2118: QWs around the gap (QW 5044-5048):")
    dump_qws(tex, 5043, 8)

    # Also check what TRXREG/BITBLTBUF values are set in the header
    print("\n--- R2118 GS transfer registers ---")
    total_qw = len(tex) // 16
    for qi in range(min(20, total_qw)):
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
        reg = hi & 0xFF
        if reg in (0x50, 0x51, 0x52, 0x53, 0x06):
            names = {0x50: 'BITBLTBUF', 0x51: 'TRXPOS', 0x52: 'TRXREG', 0x53: 'TRXDIR', 0x06: 'TEX0_1'}
            extra = ""
            if reg == 0x52:
                w = lo & 0xFFF
                h = (lo >> 32) & 0xFFF
                extra = f" ({w}x{h})"
            elif reg == 0x50:
                dpsm = (lo >> 44) & 0x3F
                dbp = (lo >> 32) & 0x3FFF
                dbw = (lo >> 40) & 0x3F
                extra = f" (DBP={dbp} DBW={dbw} DPSM=0x{dpsm:02x})"
            print(f"  QW[{qi:5d}] {names[reg]}: 0x{lo:016x}{extra}")


if __name__ == '__main__':
    analyze_r2119()
    analyze_r2118_gap()
