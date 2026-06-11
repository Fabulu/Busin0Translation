"""
Find all HOST-TO-LOCAL texture uploads (BITBLTBUF + TRXREG + TRXDIR)
targeting DBP in range 0x2800-0x2A00 in a PCSX2 GS dump.

GS dump format:
  - u32 state_size at offset 0
  - state_size bytes of state data
  - then packet stream:
    type 0 = transfer: u8 path, u32 size, then 'size' bytes of GIF data
    type 1 = vsync: u8 field
    type 2 = fifo: u32 size, then 'size' bytes
    type 3 = registers: u8 which_reg

GS registers for image transfer:
  BITBLTBUF (0x50): SBP[13:0], SBW[21:16], SPSM[29:24], DBP[45:32], DBW[53:48], DPSM[61:56]
  TRXREG (0x52): RRW[11:0], RRH[43:32]
  TRXDIR (0x53): XDIR[1:0] — 0=host-to-local, 1=local-to-host, 2=local-to-local
"""

import struct
import zstandard as zstd
import sys

GS_DUMP_PATH = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260605055713.gs.zst"

# Search range for DBP
DBP_MIN = 0x2700
DBP_MAX = 0x2C00

# GS register addresses
REG_BITBLTBUF = 0x50
REG_TRXREG   = 0x52
REG_TRXDIR   = 0x53
REG_AD       = 0x0E

PSM_NAMES = {0: 'PSMCT32', 1: 'PSMCT24', 2: 'PSMCT16', 0x13: 'PSMT8',
             0x14: 'PSMT4', 0x24: 'PSMT8H', 0x2C: 'PSMT4HL', 0x36: 'PSMT4HH'}


def decompress_gs_dump(path):
    print(f"Decompressing {path}...")
    with open(path, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(f.read(), max_output_size=1024 * 1024 * 1024)


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


def scan_gif_for_ad_writes(gif):
    """Yield all A+D register writes from a GIF packet."""
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
                        ad_reg = qw_hi & 0xFF
                        yield (ad_reg, qw_lo)
        elif flg == 1:  # REGLIST
            # Check for A+D in reglist too
            regs = [(tag_hi >> (i * 4)) & 0xF for i in range(nreg)]
            total_regs = nloop * nreg
            total_bytes = total_regs * 8
            if total_bytes % 16: total_bytes += 16 - (total_bytes % 16)

            reg_idx = 0
            rp = gp
            for i in range(total_regs):
                if rp + 8 > len(gif):
                    break
                val = struct.unpack_from('<Q', gif, rp)[0]
                rid = regs[i % nreg]
                rp += 8
                if rid == REG_AD:
                    ad_reg = (val >> 56) & 0xFF  # In REGLIST, AD packs differently
                    # Actually in REGLIST mode, each reg is 64 bits, AD is special
                    pass
            gp += total_bytes
        elif flg == 2:  # IMAGE
            gp += nloop * 16
        elif flg == 3:
            break

        if eop:
            break


def main():
    data = decompress_gs_dump(GS_DUMP_PATH)
    print(f"Decompressed size: {len(data)} bytes")

    # Read state size
    state_size = struct.unpack_from('<I', data, 0)[0]
    print(f"State size: {state_size}")

    # Packet stream starts after state
    pkt_start = 4 + state_size
    print(f"Packet stream starts at offset {pkt_start}")

    pos = pkt_start
    frame = 0

    # Track current BITBLTBUF and TRXREG state
    cur_bitbltbuf = None
    cur_trxreg = None

    uploads = []
    all_dbp_seen = set()

    while pos < len(data):
        t = data[pos]

        if t == 0:  # Transfer (GIF packet)
            if pos + 6 > len(data):
                break
            path = data[pos + 1]
            size = struct.unpack_from('<I', data, pos + 2)[0]
            if size > 50_000_000:
                print(f"  WARNING: huge packet size {size} at offset {pos}, stopping")
                break

            gif = data[pos + 6: pos + 6 + size]

            # Scan for BITBLTBUF, TRXREG, TRXDIR writes
            for ad_reg, val in scan_gif_for_ad_writes(gif):
                if ad_reg == REG_BITBLTBUF:
                    cur_bitbltbuf = parse_bitbltbuf(val)
                    all_dbp_seen.add(cur_bitbltbuf['dbp'])
                elif ad_reg == REG_TRXREG:
                    cur_trxreg = parse_trxreg(val)
                elif ad_reg == REG_TRXDIR:
                    xdir = val & 3
                    if xdir == 0 and cur_bitbltbuf and cur_trxreg:  # Host-to-local
                        dbp = cur_bitbltbuf['dbp']
                        if DBP_MIN <= dbp <= DBP_MAX:
                            uploads.append({
                                'frame': frame,
                                'offset': pos,
                                'bitbltbuf': dict(cur_bitbltbuf),
                                'trxreg': dict(cur_trxreg),
                            })
                    elif xdir == 0 and cur_bitbltbuf:
                        # Track all uploads even outside range for context
                        pass

            pos += 6 + size

        elif t == 1:  # Vsync
            frame += 1
            pos += 2

        elif t == 2:  # FIFO write (privileged registers)
            if pos + 5 > len(data):
                break
            sz = struct.unpack_from('<I', data, pos + 1)[0]
            pos += 5 + sz

        elif t == 3:  # Register transfer
            pos += 2

        else:
            print(f"  Unknown packet type {t} at offset {pos}, stopping")
            break

    print(f"\nTotal frames: {frame}")
    print(f"\n=== UPLOADS TARGETING DBP 0x{DBP_MIN:04X}-0x{DBP_MAX:04X} ===\n")

    if not uploads:
        print("NO uploads found in this range!")
        # Show nearby DBPs
        nearby = sorted([d for d in all_dbp_seen if 0x2000 <= d <= 0x3000])
        print(f"\nAll DBPs seen in range 0x2000-0x3000:")
        for d in nearby:
            print(f"  0x{d:04X}")
    else:
        for i, u in enumerate(uploads):
            bb = u['bitbltbuf']
            tr = u['trxreg']
            psm_name = PSM_NAMES.get(bb['dpsm'], f"0x{bb['dpsm']:02X}")
            print(f"Upload #{i}:")
            print(f"  Frame:    {u['frame']}")
            print(f"  Offset:   {u['offset']}")
            print(f"  DBP:      0x{bb['dbp']:04X}")
            print(f"  DBW:      {bb['dbw']}")
            print(f"  DPSM:     {psm_name}")
            print(f"  SBP:      0x{bb['sbp']:04X}")
            print(f"  Size:     {tr['rrw']}x{tr['rrh']}")
            print(f"  Is 256x256? {'YES' if tr['rrw']==256 and tr['rrh']==256 else 'NO'}")
            print()

    # Also show ALL unique DBPs for reference
    print(f"\n=== ALL UNIQUE DBPs SEEN (sorted) ===")
    for d in sorted(all_dbp_seen):
        print(f"  0x{d:04X}")


if __name__ == '__main__':
    main()
