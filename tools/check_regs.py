#!/usr/bin/env python3
"""Check all register values in the 192-byte header."""
import struct
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

GS_REG_NAMES = {
    0x00: 'PRIM', 0x01: 'RGBAQ', 0x02: 'ST', 0x03: 'UV',
    0x04: 'XYZF2', 0x05: 'XYZ2', 0x06: 'TEX0_1', 0x07: 'TEX0_2',
    0x08: 'CLAMP_1', 0x09: 'CLAMP_2', 0x0e: 'A+D',
    0x14: 'TEX1_1', 0x15: 'TEX1_2',
    0x34: 'MIPTBP1_1', 0x3c: 'MIPTBP2_1',
    0x40: 'SCISSOR_1', 0x42: 'ALPHA_1', 0x47: 'PRMODECONT',
    0x4c: 'TEXFLUSH',
    0x50: 'BITBLTBUF', 0x51: 'TRXPOS', 0x52: 'TRXREG', 0x53: 'TRXDIR',
}


def analyze_header(filename):
    data = open(os.path.join(TEX_DIR, filename), 'rb').read()
    tex = data[16:]
    print(f"\n{filename}:")

    # QW[0] is GIF tag
    lo0 = struct.unpack_from('<Q', tex, 0)[0]
    hi0 = struct.unpack_from('<Q', tex, 8)[0]
    nloop = lo0 & 0x7FFF
    nreg = (lo0 >> 60) & 0xF or 16
    flg = (lo0 >> 46) & 3
    print(f"  GIF tag: NLOOP={nloop} NREG={nreg} FLG={flg}")
    print(f"  REGS field: {hi0:016x}")

    # The REGS field tells us which registers are being written
    # For PACKED mode with NREG registers:
    regs_list = []
    for r in range(nreg):
        reg_id = (hi0 >> (r * 4)) & 0xF
        regs_list.append(reg_id)
    print(f"  Register list: {[f'0x{r:x}' for r in regs_list]}")

    # Now decode each register write
    for qi in range(1, 12):  # QW[1] through QW[11]
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]

        # In PACKED mode, the register ID comes from REGS field
        # For A+D (reg 0x0e): data=lo, addr=hi&0xFF
        # But if the REGS says specific registers, the addressing is different

        # Actually, for PACKED mode, each register uses the ID from REGS:
        # Loop i, register j: the register ID is regs_list[j]
        # The data format depends on the register type

        # But we also have the hi byte which might be A+D
        reg_from_hi = hi & 0xFF
        name_hi = GS_REG_NAMES.get(reg_from_hi, f'0x{reg_from_hi:02x}')

        # Which position in the NREG cycle?
        pos_in_cycle = (qi - 1) % nreg
        reg_from_regs = regs_list[pos_in_cycle] if pos_in_cycle < len(regs_list) else 0
        name_regs = GS_REG_NAMES.get(reg_from_regs, f'0x{reg_from_regs:02x}')

        print(f"  QW[{qi:2d}]: lo={lo:016x} hi={hi:016x}")
        print(f"           A+D reg={name_hi}(0x{reg_from_hi:02x}), REGS pos={pos_in_cycle} reg={name_regs}(0x{reg_from_regs:x})")

        # Decode if it's a known register
        if reg_from_hi == 0x06:  # TEX0
            tbp0 = lo & 0x3FFF
            tbw = (lo >> 14) & 0x3F
            psm = (lo >> 20) & 0x3F
            tw = (lo >> 26) & 0xF
            th = (lo >> 30) & 0xF
            tcc = (lo >> 34) & 1
            tfx = (lo >> 35) & 3
            cbp = (lo >> 37) & 0x3FFF
            cpsm = (lo >> 51) & 0xF
            csm = (lo >> 55) & 1
            csa = (lo >> 56) & 0x1F
            cld = (lo >> 61) & 7
            print(f"           TEX0: TBP0={tbp0} TBW={tbw}({tbw*64}px) PSM=0x{psm:02x} "
                  f"TW={tw}({1<<tw}) TH={th}({1<<th}) TCC={tcc} TFX={tfx}")
            print(f"           TEX0: CBP={cbp} CPSM=0x{cpsm:x} CSM={csm} CSA={csa} CLD={cld}")

        elif reg_from_hi == 0x50:  # BITBLTBUF
            sbp = lo & 0x3FFF
            sbw = (lo >> 16) & 0x3F
            spsm = (lo >> 20) & 0x3F
            dbp = (lo >> 32) & 0x3FFF
            dbw = (lo >> 40) & 0x3F
            dpsm = (lo >> 44) & 0x3F
            print(f"           BITBLTBUF: SBP={sbp} SBW={sbw} SPSM=0x{spsm:02x} "
                  f"DBP={dbp} DBW={dbw} DPSM=0x{dpsm:02x}")

        elif reg_from_hi == 0x51:  # TRXPOS
            ssax = lo & 0x7FF
            ssay = (lo >> 16) & 0x7FF
            dsax = (lo >> 32) & 0x7FF
            dsay = (lo >> 48) & 0x7FF
            print(f"           TRXPOS: SSAX={ssax} SSAY={ssay} DSAX={dsax} DSAY={dsay}")

        elif reg_from_hi == 0x52:  # TRXREG
            rrw = lo & 0xFFF
            rrh = (lo >> 32) & 0xFFF
            print(f"           TRXREG: {rrw}x{rrh}")

        elif reg_from_hi == 0x53:  # TRXDIR
            xdir = lo & 3
            names = {0: 'host->local', 1: 'local->host', 2: 'local->local', 3: 'deactivated'}
            print(f"           TRXDIR: {names.get(xdir, '?')} ({xdir})")

        elif reg_from_hi == 0x08:  # CLAMP
            wms = lo & 3
            wmt = (lo >> 2) & 3
            minu = (lo >> 4) & 0x3FF
            maxu = (lo >> 14) & 0x3FF
            minv = (lo >> 24) & 0x3FF
            maxv = (lo >> 34) & 0x3FF
            clamp_names = {0: 'REPEAT', 1: 'CLAMP', 2: 'REGION_CLAMP', 3: 'REGION_REPEAT'}
            print(f"           CLAMP: WMS={clamp_names.get(wms,'?')} WMT={clamp_names.get(wmt,'?')} "
                  f"MINU={minu} MAXU={maxu} MINV={minv} MAXV={maxv}")


for f in ['R2118_tavern_background.raw', 'R2119_tavern_buttons_1.raw',
          'R2120_tavern_buttons_2.raw']:
    analyze_header(f)
