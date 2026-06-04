"""
Parse PCSX2 GS dump (.gs.zst) - correct format based on PCSX2 source.

File format:
  [0xFFFFFFFF/4] [header_total_size/4] [GSDumpHeader/36] [serial/n] [screenshot/n]
  [state_data/state_size] [GSPrivRegSet/0x2000]
  Then packets:
    Transfer: [0/1] [path_index/1] [size/4] [gif_data/size]
    VSync:    [1/1] [field/1]
    ReadFIFO: [2/1] [size/4]
    Regs:     [3/1] [GSPrivRegSet/0x2000]

GSDumpHeader (36 bytes, packed):
  u32 state_version
  u32 state_size
  u32 serial_offset
  u32 serial_size
  u32 crc
  u32 screenshot_width
  u32 screenshot_height
  u32 screenshot_offset
  u32 screenshot_size
"""

import struct
import zstandard as zstd
from collections import defaultdict

GS_DUMP = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602231607.gs.zst"

PSM_NAMES = {
    0x00: "PSMCT32", 0x01: "PSMCT24", 0x02: "PSMCT16",
    0x0A: "PSMCT16S", 0x13: "PSMT8", 0x14: "PSMT4",
    0x1B: "PSMT8H", 0x24: "PSMT4HL", 0x2C: "PSMT4HH",
    0x30: "PSMZ32", 0x31: "PSMZ24", 0x32: "PSMZ16", 0x3A: "PSMZ16S",
}

PRIM_TYPES = {0: "POINT", 1: "LINE", 2: "LINE_STRIP", 3: "TRI",
              4: "TRI_STRIP", 5: "TRI_FAN", 6: "SPRITE"}

def main():
    with open(GS_DUMP, "rb") as f:
        raw = f.read()
    dctx = zstd.ZstdDecompressor()
    data = dctx.decompress(raw, max_output_size=200 * 1024 * 1024)
    print(f"Decompressed: {len(data)} bytes")

    # === PARSE HEADER ===
    pos = 0
    fake_crc = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    assert fake_crc == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got 0x{fake_crc:08X}"

    header_total_size = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    print(f"Header total size: {header_total_size} (0x{header_total_size:X})")

    # GSDumpHeader (36 bytes)
    hdr = struct.unpack_from("<9I", data, pos)
    state_version, state_size, serial_offset, serial_size, crc, \
        ss_width, ss_height, ss_offset, ss_size = hdr
    pos += 36

    print(f"State version: {state_version}")
    print(f"State size: {state_size} (0x{state_size:X})")
    print(f"Serial offset: {serial_offset}, size: {serial_size}")
    print(f"CRC: 0x{crc:08X}")
    print(f"Screenshot: {ss_width}x{ss_height}, offset={ss_offset}, size={ss_size}")

    # Serial string
    serial_abs = 8 + serial_offset  # 8 = fake_crc(4) + header_total_size(4)
    serial = data[serial_abs:serial_abs + serial_size].decode("ascii", errors="replace")
    print(f"Serial: {serial}")

    # Skip to after header + state + regs
    # After the 4+4 bytes (fake_crc + header_total_size), we have:
    #   header_total_size bytes of (GSDumpHeader + serial + screenshot)
    #   state_size bytes of state data
    #   0x2000 bytes of GSPrivRegSet
    data_start = 8 + header_total_size  # end of header block
    state_start = data_start
    state_end = state_start + state_size
    regs_start = state_end
    regs_end = regs_start + 0x2000
    packets_start = regs_end

    print(f"\nState data: 0x{state_start:X} - 0x{state_end:X}")
    print(f"GSPrivRegSet: 0x{regs_start:X} - 0x{regs_end:X}")
    print(f"Packets start: 0x{packets_start:X}")
    print(f"Remaining: {len(data) - packets_start} bytes")

    # === PARSE INITIAL GSPrivRegSet ===
    print("\n" + "=" * 70)
    print("INITIAL GSPrivRegSet (at dump capture point)")
    print("=" * 70)
    parse_priv_regs(data, regs_start)

    # === PARSE PACKETS ===
    pos = packets_start
    transfer_count = 0
    vsync_count = 0
    readfifo_count = 0
    regs_count = 0
    unknown_count = 0

    # Collect register writes from GIF transfers
    frame_writes = []
    zbuf_writes = []
    tex0_writes = []
    bitblt_writes = []
    trxpos_writes = []
    trxreg_writes = []
    trxdir_writes = []
    prim_writes = []
    xyoffset_writes = []
    scissor_writes = []

    # Current render state tracking
    current_frame = None
    current_tex0 = None

    packet_idx = 0
    while pos < len(data):
        tag = data[pos]
        pos += 1

        if tag == 0:  # Transfer
            if pos + 5 > len(data):
                break
            path = data[pos]
            pos += 1
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            if pos + size > len(data):
                print(f"  WARNING: Transfer truncated at packet #{packet_idx}")
                break

            gif_data = data[pos:pos + size]
            pos += size
            transfer_count += 1

            # Parse GIF packets
            parse_gif(gif_data, path, vsync_count, packet_idx,
                      frame_writes, zbuf_writes, tex0_writes,
                      bitblt_writes, trxpos_writes, trxreg_writes, trxdir_writes,
                      prim_writes, xyoffset_writes, scissor_writes)

        elif tag == 1:  # VSync
            if pos + 1 > len(data):
                break
            field = data[pos]
            pos += 1
            vsync_count += 1

        elif tag == 2:  # ReadFIFO2
            if pos + 4 > len(data):
                break
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            readfifo_count += 1

        elif tag == 3:  # Registers (GSPrivRegSet)
            if pos + 0x2000 > len(data):
                break
            regs_count += 1
            # Parse the register set for FRAME values
            parse_priv_regs_for_frame(data, pos, vsync_count, frame_writes)
            pos += 0x2000

        else:
            unknown_count += 1
            print(f"  Unknown tag 0x{tag:02X} at offset 0x{pos - 1:X}, packet #{packet_idx}")
            break

        packet_idx += 1

    print(f"\nParsed {packet_idx} packets:")
    print(f"  Transfers: {transfer_count}")
    print(f"  VSyncs: {vsync_count}")
    print(f"  ReadFIFOs: {readfifo_count}")
    print(f"  Regs: {regs_count}")
    if unknown_count:
        print(f"  Unknown: {unknown_count}")

    # === REPORT FRAME WRITES ===
    print("\n" + "=" * 70)
    print(f"ALL FRAME REGISTER WRITES ({len(frame_writes)} total)")
    print("=" * 70)
    unique_frames = defaultdict(list)
    for entry in frame_writes:
        offset, fbp, fbw, psm, fbmsk, rname, vsync, pkt, src = entry
        key = (fbp, fbw, psm, fbmsk, rname, src)
        unique_frames[key].append((vsync, pkt))

    print(f"{'FBP':>6} {'BP/64':>7} {'FBW':>5} {'PSM':>12} {'FBMSK':>10} {'Reg':>8} {'Count':>6} Source")
    print("-" * 85)
    for (fbp, fbw, psm, fbmsk, rname, src), occurrences in sorted(unique_frames.items()):
        bp64 = fbp * 32
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        marker = ""
        if bp64 == 0x1800:
            marker = " <<<< 0x1800!"
        elif bp64 == 0x3000:
            marker = " <<<< 0x3000!"
        print(f"0x{fbp:04X} 0x{bp64:05X}   {fbw:3d} {psm_name:>12} 0x{fbmsk:08X} {rname:>8} {len(occurrences):>6} {src}{marker}")

    # === REPORT TEX0 WRITES ===
    print("\n" + "=" * 70)
    print(f"ALL UNIQUE TEX0 WRITES ({len(tex0_writes)} total)")
    print("=" * 70)
    unique_tex0 = defaultdict(int)
    for _, tbp0, tbw, psm, tw, th, rname, vsync, pkt in tex0_writes:
        key = (tbp0, tbw, psm, tw, th, rname)
        unique_tex0[key] += 1

    for (tbp0, tbw, psm, tw, th, rname), count in sorted(unique_tex0.items()):
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        marker = ""
        if tbp0 == 0x1800:
            marker = " <<<< 0x1800!"
        if tbp0 == 0x3000:
            marker = " <<<< 0x3000!"
        print(f"  TBP0=0x{tbp0:04X} TBW={tbw:>2} PSM={psm_name:>10} {1 << tw:>4}x{1 << th:<4} ({rname}) x{count}{marker}")

    # === REPORT BITBLTBUF + TRANSFERS ===
    print("\n" + "=" * 70)
    print(f"ALL BITBLTBUF WRITES ({len(bitblt_writes)} total)")
    print("=" * 70)
    for i, (_, sbp, sbw, spsm, dbp, dbw, dpsm, vsync, pkt) in enumerate(bitblt_writes):
        spsm_name = PSM_NAMES.get(spsm, f"0x{spsm:02X}")
        dpsm_name = PSM_NAMES.get(dpsm, f"0x{dpsm:02X}")
        marker = ""
        if sbp == 0x1800 or dbp == 0x1800:
            marker += " <<<< 0x1800!"
        if sbp == 0x3000 or dbp == 0x3000:
            marker += " <<<< 0x3000!"
        print(f"  [{i}] vsync#{vsync} pkt#{pkt}: SBP=0x{sbp:04X}({spsm_name}) SBW={sbw} -> DBP=0x{dbp:04X}({dpsm_name}) DBW={dbw}{marker}")

        # Find matching TRXPOS/TRXREG/TRXDIR
        for _, rd, vs2, pk2 in trxpos_writes:
            if vs2 == vsync and pk2 >= pkt and pk2 <= pkt + 2:
                ssax = rd & 0x7FF
                ssay = (rd >> 16) & 0x7FF
                dsax = (rd >> 32) & 0x7FF
                dsay = (rd >> 48) & 0x7FF
                print(f"      TRXPOS: SSAX={ssax} SSAY={ssay} DSAX={dsax} DSAY={dsay}")
                break
        for _, rd, vs2, pk2 in trxreg_writes:
            if vs2 == vsync and pk2 >= pkt and pk2 <= pkt + 2:
                rrw = rd & 0xFFF
                rrh = (rd >> 32) & 0xFFF
                print(f"      TRXREG: {rrw}x{rrh}")
                break
        for _, rd, vs2, pk2 in trxdir_writes:
            if vs2 == vsync and pk2 >= pkt and pk2 <= pkt + 2:
                xdir = rd & 0x3
                dirs = {0: "host->local", 1: "local->host", 2: "local->local", 3: "deactivated"}
                print(f"      TRXDIR: {dirs.get(xdir, str(xdir))}")
                break

    # === KEY ANALYSIS ===
    print("\n" + "=" * 70)
    print("KEY ANALYSIS: What renders to VRAM 0x1800?")
    print("FRAME.FBP = 0xC0 => BP/64 = 0x1800")
    print("FRAME.FBP = 0x180 => BP/64 = 0x3000")
    print("=" * 70)

    found = False
    for entry in frame_writes:
        _, fbp, fbw, psm, fbmsk, rname, vsync, pkt, src = entry
        bp64 = fbp * 32
        if bp64 in (0x1800, 0x3000):
            found = True
            psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
            print(f"  FOUND: {rname} FBP=0x{fbp:03X} (BP/64=0x{bp64:05X}) FBW={fbw} PSM={psm_name} "
                  f"FBMSK=0x{fbmsk:08X} vsync#{vsync} pkt#{pkt} src={src}")

    if not found:
        print("  NO FRAME writes target 0x1800 or 0x3000 in GIF transfers!")
        print()
        print("  Checking host->local transfers to DBP=0x1800:")
        for i, (_, sbp, sbw, spsm, dbp, dbw, dpsm, vsync, pkt) in enumerate(bitblt_writes):
            if dbp == 0x1800:
                dpsm_name = PSM_NAMES.get(dpsm, f"0x{dpsm:02X}")
                print(f"    FOUND: host->local to DBP=0x1800 PSM={dpsm_name} vsync#{vsync} pkt#{pkt}")

    # === TIMELINE around 0x1800/0x3000 operations ===
    print("\n" + "=" * 70)
    print("TIMELINE: All render state changes around VRAM copies involving 0x1800/0x3000")
    print("=" * 70)

    # Build unified timeline
    events = []
    for entry in frame_writes:
        _, fbp, fbw, psm, fbmsk, rname, vsync, pkt, src = entry
        events.append((vsync, pkt, "FRAME", entry))
    for entry in tex0_writes:
        _, tbp0, tbw, psm, tw, th, rname, vsync, pkt = entry
        events.append((vsync, pkt, "TEX0", entry))
    for i, entry in enumerate(bitblt_writes):
        _, sbp, sbw, spsm, dbp, dbw, dpsm, vsync, pkt = entry
        events.append((vsync, pkt, "BITBLTBUF", entry))
    for entry in trxdir_writes:
        _, rd, vsync, pkt = entry
        events.append((vsync, pkt, "TRXDIR", entry))
    for entry in prim_writes:
        _, ptype, tme, vsync, pkt = entry
        events.append((vsync, pkt, "PRIM", entry))

    events.sort()

    # Find the BITBLTBUF that copies 0x1800->0x3000 and show surrounding context
    target_vsync = None
    target_pkt = None
    for vsync_n, pkt_n, etype, entry in events:
        if etype == "BITBLTBUF":
            _, sbp, sbw, spsm, dbp, dbw, dpsm, vs, pk = entry
            if sbp == 0x1800 and dbp == 0x3000:
                target_vsync = vs
                target_pkt = pk
                break

    if target_vsync is not None:
        print(f"\nVRAM copy 0x1800->0x3000 found at vsync#{target_vsync} pkt#{target_pkt}")
        print("Showing all events in same vsync frame:\n")
        for vsync_n, pkt_n, etype, entry in events:
            if vsync_n == target_vsync:
                if etype == "FRAME":
                    _, fbp, fbw, psm, fbmsk, rname, vs, pk, src = entry
                    psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
                    print(f"  pkt#{pk:>4} FRAME {rname}: FBP=0x{fbp:03X}(BP/64=0x{fbp * 32:05X}) FBW={fbw} PSM={psm_name} FBMSK=0x{fbmsk:08X} [{src}]")
                elif etype == "TEX0":
                    _, tbp0, tbw, psm, tw, th, rname, vs, pk = entry
                    psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
                    print(f"  pkt#{pk:>4} TEX0  {rname}: TBP0=0x{tbp0:04X} TBW={tbw} PSM={psm_name} {1 << tw}x{1 << th}")
                elif etype == "BITBLTBUF":
                    _, sbp, sbw, spsm, dbp, dbw, dpsm, vs, pk = entry
                    sn = PSM_NAMES.get(spsm, f"0x{spsm:02X}")
                    dn = PSM_NAMES.get(dpsm, f"0x{dpsm:02X}")
                    marker = " ****" if (sbp == 0x1800 or dbp == 0x1800 or sbp == 0x3000 or dbp == 0x3000) else ""
                    print(f"  pkt#{pk:>4} BITBLTBUF: SBP=0x{sbp:04X}({sn}) -> DBP=0x{dbp:04X}({dn}){marker}")
                elif etype == "TRXDIR":
                    _, rd, vs, pk = entry
                    xdir = rd & 0x3
                    dirs = {0: "host->local", 1: "local->host", 2: "local->local", 3: "deactivated"}
                    print(f"  pkt#{pk:>4} TRXDIR: {dirs.get(xdir, str(xdir))}")
                elif etype == "PRIM":
                    _, ptype, tme, vs, pk = entry
                    pname = PRIM_TYPES.get(ptype, str(ptype))
                    print(f"  pkt#{pk:>4} PRIM: {pname} TME={tme}")


def parse_priv_regs(data, offset):
    """Parse GSPrivRegSet (0x2000 bytes) for display registers."""
    # GSPrivRegSet layout (from GSRegs.h):
    # The privileged registers are memory-mapped at specific offsets.
    # Key registers:
    #   PMODE at 0x00, SMODE1 at 0x10, SMODE2 at 0x20,
    #   DISPFB1 at 0x70, DISPLAY1 at 0x80,
    #   DISPFB2 at 0x90, DISPLAY2 at 0xA0,
    #   EXTBUF at 0xB0, EXTDATA at 0xC0, EXTWRITE at 0xD0,
    #   BGCOLOR at 0xE0,
    #   CSR at 0x1000, IMR at 0x1010,
    #   BUSDIR at 0x1040, SIGLBLID at 0x1080

    # DISPFB1 (0x70): frame buffer setting for display circuit 1
    dispfb1 = struct.unpack_from("<Q", data, offset + 0x70)[0]
    fbp1 = dispfb1 & 0x1FF
    fbw1 = (dispfb1 >> 9) & 0x3F
    psm1 = (dispfb1 >> 15) & 0x1F
    dbx1 = (dispfb1 >> 32) & 0x7FF
    dby1 = (dispfb1 >> 43) & 0x7FF

    dispfb2 = struct.unpack_from("<Q", data, offset + 0x90)[0]
    fbp2 = dispfb2 & 0x1FF
    fbw2 = (dispfb2 >> 9) & 0x3F
    psm2 = (dispfb2 >> 15) & 0x1F
    dbx2 = (dispfb2 >> 32) & 0x7FF
    dby2 = (dispfb2 >> 43) & 0x7FF

    print(f"  DISPFB1: FBP=0x{fbp1:03X}(BP/64=0x{fbp1 * 32:05X}) FBW={fbw1} PSM={PSM_NAMES.get(psm1, hex(psm1))} DBX={dbx1} DBY={dby1}")
    print(f"  DISPFB2: FBP=0x{fbp2:03X}(BP/64=0x{fbp2 * 32:05X}) FBW={fbw2} PSM={PSM_NAMES.get(psm2, hex(psm2))} DBX={dbx2} DBY={dby2}")

    # Also dump raw hex of first 256 bytes for reference
    print("  Raw privileged registers (first 0x100):")
    for i in range(0, 0x100, 16):
        hex_str = " ".join(f"{data[offset + i + j]:02X}" for j in range(16))
        print(f"    0x{i:04X}: {hex_str}")


def parse_priv_regs_for_frame(data, offset, vsync_count, frame_writes):
    """Extract FRAME-like info from GSPrivRegSet registers block (tag=3)."""
    # The tag=3 Regs block is the full GSPrivRegSet, not GS drawing registers.
    # It contains DISPFB which tells us the display framebuffer, not the render target.
    # We note the display FB for reference.
    dispfb1 = struct.unpack_from("<Q", data, offset + 0x70)[0]
    fbp1 = dispfb1 & 0x1FF
    fbw1 = (dispfb1 >> 9) & 0x3F
    psm1 = (dispfb1 >> 15) & 0x1F
    frame_writes.append((offset, fbp1, fbw1, psm1, 0, "DISPFB1", vsync_count, -1, "PrivRegs"))

    dispfb2 = struct.unpack_from("<Q", data, offset + 0x90)[0]
    fbp2 = dispfb2 & 0x1FF
    fbw2 = (dispfb2 >> 9) & 0x3F
    psm2 = (dispfb2 >> 15) & 0x1F
    frame_writes.append((offset, fbp2, fbw2, psm2, 0, "DISPFB2", vsync_count, -1, "PrivRegs"))


def parse_gif(gif_data, path, vsync_count, packet_idx,
              frame_writes, zbuf_writes, tex0_writes,
              bitblt_writes, trxpos_writes, trxreg_writes, trxdir_writes,
              prim_writes, xyoffset_writes, scissor_writes):
    """Parse GIF transfer data for A+D register writes."""
    tpos = 0
    while tpos + 16 <= len(gif_data):
        lo = struct.unpack_from("<Q", gif_data, tpos)[0]
        hi = struct.unpack_from("<Q", gif_data, tpos + 8)[0]

        nloop = lo & 0x7FFF
        eop = (lo >> 15) & 1
        flg = (lo >> 58) & 3
        nreg = (lo >> 60) & 0xF
        if nreg == 0:
            nreg = 16

        tpos += 16  # skip GIFtag

        if flg == 0:  # PACKED mode
            for loop in range(nloop):
                for r in range(nreg):
                    if tpos + 16 > len(gif_data):
                        return
                    reg_id = (hi >> (r * 4)) & 0xF

                    if reg_id == 0x0E:  # A+D
                        reg_data = struct.unpack_from("<Q", gif_data, tpos)[0]
                        reg_addr = struct.unpack_from("<Q", gif_data, tpos + 8)[0] & 0xFF

                        process_register(reg_addr, reg_data, vsync_count, packet_idx, tpos,
                                         frame_writes, zbuf_writes, tex0_writes,
                                         bitblt_writes, trxpos_writes, trxreg_writes, trxdir_writes,
                                         prim_writes, xyoffset_writes, scissor_writes)

                    elif reg_id == 0x00:  # PRIM (direct, not via A+D)
                        reg_data = struct.unpack_from("<Q", gif_data, tpos)[0]
                        ptype = reg_data & 0x7
                        tme = (reg_data >> 4) & 1
                        prim_writes.append((tpos, ptype, tme, vsync_count, packet_idx))

                    tpos += 16

        elif flg == 1:  # REGLIST mode
            total_regs = nloop * nreg
            for i in range(total_regs):
                if tpos + 8 > len(gif_data):
                    return
                reg_id = (hi >> ((i % nreg) * 4)) & 0xF
                # REGLIST uses 8-byte entries, but reg_id is only 4 bits
                # FRAME (0x4C) can't be addressed with 4 bits, only A+D (0xE) can carry it
                tpos += 8
            if (total_regs % 2) == 1:
                tpos += 8  # align to 16 bytes

        elif flg == 2:  # IMAGE mode
            tpos += nloop * 16

        else:
            break

        if eop:
            break


def process_register(addr, reg_data, vsync_count, packet_idx, tpos,
                     frame_writes, zbuf_writes, tex0_writes,
                     bitblt_writes, trxpos_writes, trxreg_writes, trxdir_writes,
                     prim_writes, xyoffset_writes, scissor_writes):
    """Process a single A+D register write."""
    if addr in (0x4C, 0x4D):  # FRAME_1/2
        fbp = reg_data & 0x1FF
        fbw = (reg_data >> 16) & 0x3F
        psm = (reg_data >> 24) & 0x3F
        fbmsk = (reg_data >> 32) & 0xFFFFFFFF
        rname = "FRAME_1" if addr == 0x4C else "FRAME_2"
        frame_writes.append((tpos, fbp, fbw, psm, fbmsk, rname, vsync_count, packet_idx, "GIF"))

    elif addr in (0x4E, 0x4F):  # ZBUF_1/2
        zbp = reg_data & 0x1FF
        psm = (reg_data >> 24) & 0xF
        zmsk = (reg_data >> 32) & 0x1
        rname = "ZBUF_1" if addr == 0x4E else "ZBUF_2"
        zbuf_writes.append((tpos, zbp, psm, zmsk, rname, vsync_count, packet_idx))

    elif addr in (0x06, 0x07):  # TEX0_1/2
        tbp0 = reg_data & 0x3FFF
        tbw = (reg_data >> 14) & 0x3F
        psm = (reg_data >> 20) & 0x3F
        tw = (reg_data >> 26) & 0xF
        th = (reg_data >> 30) & 0xF
        rname = "TEX0_1" if addr == 0x06 else "TEX0_2"
        tex0_writes.append((tpos, tbp0, tbw, psm, tw, th, rname, vsync_count, packet_idx))

    elif addr == 0x50:  # BITBLTBUF
        sbp = reg_data & 0x3FFF
        sbw = (reg_data >> 16) & 0x3F
        spsm = (reg_data >> 24) & 0x3F
        dbp = (reg_data >> 32) & 0x3FFF
        dbw = (reg_data >> 48) & 0x3F
        dpsm = (reg_data >> 56) & 0x3F
        bitblt_writes.append((tpos, sbp, sbw, spsm, dbp, dbw, dpsm, vsync_count, packet_idx))

    elif addr == 0x51:  # TRXPOS
        trxpos_writes.append((tpos, reg_data, vsync_count, packet_idx))

    elif addr == 0x52:  # TRXREG
        trxreg_writes.append((tpos, reg_data, vsync_count, packet_idx))

    elif addr == 0x53:  # TRXDIR
        trxdir_writes.append((tpos, reg_data, vsync_count, packet_idx))

    elif addr == 0x00:  # PRIM
        ptype = reg_data & 0x7
        tme = (reg_data >> 4) & 1
        prim_writes.append((tpos, ptype, tme, vsync_count, packet_idx))

    elif addr == 0x18:  # XYOFFSET_1
        xyoffset_writes.append((tpos, reg_data, vsync_count, packet_idx))

    elif addr == 0x40:  # SCISSOR_1
        scissor_writes.append((tpos, reg_data, vsync_count, packet_idx))


if __name__ == "__main__":
    main()
