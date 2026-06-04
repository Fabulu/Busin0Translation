"""
Parse GS dump detail: show ALL register writes around the FRAME->0x1800 and the SPRITE draws.
Focus on vsync#1 packets 1080-1095 to understand what gets rendered to 0x1800.
"""
import struct
import zstandard as zstd

GS_DUMP = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602231607.gs.zst"

PSM_NAMES = {
    0x00: "PSMCT32", 0x01: "PSMCT24", 0x02: "PSMCT16",
    0x0A: "PSMCT16S", 0x13: "PSMT8", 0x14: "PSMT4",
    0x1B: "PSMT8H", 0x24: "PSMT4HL", 0x2C: "PSMT4HH",
    0x30: "PSMZ32", 0x31: "PSMZ24", 0x32: "PSMZ16", 0x3A: "PSMZ16S",
}

REG_NAMES = {
    0x00: "PRIM", 0x01: "RGBAQ", 0x02: "ST", 0x03: "UV", 0x04: "XYZF2",
    0x05: "XYZ2", 0x06: "TEX0_1", 0x07: "TEX0_2", 0x08: "CLAMP_1",
    0x09: "CLAMP_2", 0x0A: "FOG", 0x0C: "XYZF3", 0x0D: "XYZ3",
    0x0E: "A+D", 0x0F: "NOP",
    0x14: "TEX1_1", 0x15: "TEX1_2", 0x16: "TEX2_1", 0x17: "TEX2_2",
    0x18: "XYOFFSET_1", 0x19: "XYOFFSET_2",
    0x1A: "PRMODECONT", 0x1B: "PRMODE",
    0x1C: "TEXCLUT", 0x22: "SCANMSK",
    0x34: "MIPTBP1_1", 0x35: "MIPTBP1_2",
    0x36: "MIPTBP2_1", 0x37: "MIPTBP2_2",
    0x3B: "TEXA", 0x3D: "FOGCOL",
    0x3F: "TEXFLUSH", 0x40: "SCISSOR_1", 0x41: "SCISSOR_2",
    0x42: "ALPHA_1", 0x43: "ALPHA_2",
    0x44: "DIMX", 0x45: "DTHE", 0x46: "COLCLAMP",
    0x47: "TEST_1", 0x48: "TEST_2",
    0x49: "PABE", 0x4A: "FBA_1", 0x4B: "FBA_2",
    0x4C: "FRAME_1", 0x4D: "FRAME_2",
    0x4E: "ZBUF_1", 0x4F: "ZBUF_2",
    0x50: "BITBLTBUF", 0x51: "TRXPOS", 0x52: "TRXREG", 0x53: "TRXDIR",
    0x60: "SIGNAL", 0x61: "FINISH", 0x62: "LABEL",
}

PRIM_TYPES = {0: "POINT", 1: "LINE", 2: "LINE_STRIP", 3: "TRI",
              4: "TRI_STRIP", 5: "TRI_FAN", 6: "SPRITE"}


def format_register(addr, reg_data):
    """Format a register write for display."""
    name = REG_NAMES.get(addr, f"REG_0x{addr:02X}")
    detail = ""

    if addr == 0x00:  # PRIM
        ptype = reg_data & 0x7
        iip = (reg_data >> 3) & 1
        tme = (reg_data >> 4) & 1
        fge = (reg_data >> 5) & 1
        abe = (reg_data >> 6) & 1
        aa1 = (reg_data >> 7) & 1
        fst = (reg_data >> 8) & 1
        detail = f" type={PRIM_TYPES.get(ptype, str(ptype))} IIP={iip} TME={tme} FGE={fge} ABE={abe} AA1={aa1} FST={fst}"

    elif addr == 0x01:  # RGBAQ
        r = reg_data & 0xFF
        g = (reg_data >> 8) & 0xFF
        b = (reg_data >> 16) & 0xFF
        a = (reg_data >> 24) & 0xFF
        q_bits = (reg_data >> 32) & 0xFFFFFFFF
        detail = f" R={r} G={g} B={b} A={a} Q=0x{q_bits:08X}"

    elif addr in (0x04, 0x0C):  # XYZF2/XYZF3
        x = reg_data & 0xFFFF
        y = (reg_data >> 16) & 0xFFFF
        z = (reg_data >> 32) & 0xFFFFFF
        f = (reg_data >> 56) & 0xFF
        detail = f" X={x / 16:.1f} Y={y / 16:.1f} Z={z} F={f}"

    elif addr in (0x05, 0x0D):  # XYZ2/XYZ3
        x = reg_data & 0xFFFF
        y = (reg_data >> 16) & 0xFFFF
        z = (reg_data >> 32) & 0xFFFFFFFF
        detail = f" X={x / 16:.1f} Y={y / 16:.1f} Z=0x{z:08X}"

    elif addr in (0x06, 0x07):  # TEX0
        tbp0 = reg_data & 0x3FFF
        tbw = (reg_data >> 14) & 0x3F
        psm = (reg_data >> 20) & 0x3F
        tw = (reg_data >> 26) & 0xF
        th = (reg_data >> 30) & 0xF
        tcc = (reg_data >> 34) & 1
        tfx = (reg_data >> 35) & 3
        cbp = (reg_data >> 37) & 0x3FFF
        cpsm = (reg_data >> 51) & 0xF
        csm = (reg_data >> 55) & 1
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        detail = f" TBP0=0x{tbp0:04X} TBW={tbw} PSM={psm_name} {1 << tw}x{1 << th} TCC={tcc} TFX={tfx} CBP=0x{cbp:04X}"

    elif addr == 0x18:  # XYOFFSET_1
        ofx = reg_data & 0xFFFF
        ofy = (reg_data >> 32) & 0xFFFF
        detail = f" OFX={ofx / 16:.1f} OFY={ofy / 16:.1f}"

    elif addr == 0x40:  # SCISSOR_1
        scax0 = reg_data & 0x7FF
        scax1 = (reg_data >> 16) & 0x7FF
        scay0 = (reg_data >> 32) & 0x7FF
        scay1 = (reg_data >> 48) & 0x7FF
        detail = f" X=[{scax0},{scax1}] Y=[{scay0},{scay1}]"

    elif addr == 0x42:  # ALPHA_1
        a_a = reg_data & 3
        b_a = (reg_data >> 2) & 3
        c_a = (reg_data >> 4) & 3
        d_a = (reg_data >> 6) & 3
        fix = (reg_data >> 32) & 0xFF
        detail = f" A={a_a} B={b_a} C={c_a} D={d_a} FIX={fix}"

    elif addr == 0x47:  # TEST_1
        ate = reg_data & 1
        atst = (reg_data >> 1) & 7
        aref = (reg_data >> 4) & 0xFF
        afail = (reg_data >> 12) & 3
        date = (reg_data >> 14) & 1
        datm = (reg_data >> 15) & 1
        zte = (reg_data >> 16) & 1
        ztst = (reg_data >> 17) & 3
        detail = f" ATE={ate} ATST={atst} AREF=0x{aref:02X} AFAIL={afail} DATE={date} ZTE={zte} ZTST={ztst}"

    elif addr in (0x4C, 0x4D):  # FRAME
        fbp = reg_data & 0x1FF
        fbw = (reg_data >> 16) & 0x3F
        psm = (reg_data >> 24) & 0x3F
        fbmsk = (reg_data >> 32) & 0xFFFFFFFF
        bp64 = fbp * 32
        psm_name = PSM_NAMES.get(psm, f"0x{psm:02X}")
        marker = ""
        if bp64 == 0x1800:
            marker = " <<<< 0x1800!"
        detail = f" FBP=0x{fbp:03X}(BP/64=0x{bp64:05X}) FBW={fbw} PSM={psm_name} FBMSK=0x{fbmsk:08X}{marker}"

    elif addr in (0x4E, 0x4F):  # ZBUF
        zbp = reg_data & 0x1FF
        psm = (reg_data >> 24) & 0xF
        zmsk = (reg_data >> 32) & 0x1
        detail = f" ZBP=0x{zbp:03X}(BP/64=0x{zbp * 32:05X}) PSM=0x{psm:X} ZMSK={zmsk}"

    elif addr == 0x50:  # BITBLTBUF
        sbp = reg_data & 0x3FFF
        sbw = (reg_data >> 16) & 0x3F
        spsm = (reg_data >> 24) & 0x3F
        dbp = (reg_data >> 32) & 0x3FFF
        dbw = (reg_data >> 48) & 0x3F
        dpsm = (reg_data >> 56) & 0x3F
        detail = f" SBP=0x{sbp:04X} SBW={sbw} SPSM={PSM_NAMES.get(spsm, hex(spsm))} -> DBP=0x{dbp:04X} DBW={dbw} DPSM={PSM_NAMES.get(dpsm, hex(dpsm))}"

    elif addr == 0x51:  # TRXPOS
        ssax = reg_data & 0x7FF
        ssay = (reg_data >> 16) & 0x7FF
        dsax = (reg_data >> 32) & 0x7FF
        dsay = (reg_data >> 48) & 0x7FF
        detail = f" SS=({ssax},{ssay}) DS=({dsax},{dsay})"

    elif addr == 0x52:  # TRXREG
        rrw = reg_data & 0xFFF
        rrh = (reg_data >> 32) & 0xFFF
        detail = f" {rrw}x{rrh}"

    elif addr == 0x53:  # TRXDIR
        xdir = reg_data & 0x3
        dirs = {0: "host->local", 1: "local->host", 2: "local->local", 3: "deactivated"}
        detail = f" {dirs.get(xdir, str(xdir))}"

    elif addr == 0x02:  # ST
        s_bits = reg_data & 0xFFFFFFFF
        t_bits = (reg_data >> 32) & 0xFFFFFFFF
        s = struct.unpack("<f", struct.pack("<I", s_bits))[0]
        t = struct.unpack("<f", struct.pack("<I", t_bits))[0]
        detail = f" S={s:.4f} T={t:.4f}"

    elif addr == 0x03:  # UV
        u = reg_data & 0x3FFF
        v = (reg_data >> 16) & 0x3FFF
        detail = f" U={u / 16:.1f} V={v / 16:.1f}"

    return f"{name}{detail}"


def parse_gif_detail(gif_data, path, packet_idx):
    """Parse and print ALL register writes in a GIF transfer."""
    lines = []
    tpos = 0
    while tpos + 16 <= len(gif_data):
        lo = struct.unpack_from("<Q", gif_data, tpos)[0]
        hi = struct.unpack_from("<Q", gif_data, tpos + 8)[0]

        nloop = lo & 0x7FFF
        eop = (lo >> 15) & 1
        pre = (lo >> 46) & 1
        prim = (lo >> 47) & 0x7FF
        flg = (lo >> 58) & 3
        nreg = (lo >> 60) & 0xF
        if nreg == 0:
            nreg = 16

        flg_names = {0: "PACKED", 1: "REGLIST", 2: "IMAGE", 3: "INVALID"}
        reg_desc = []
        for r in range(nreg):
            rid = (hi >> (r * 4)) & 0xF
            reg_desc.append(REG_NAMES.get(rid, f"0x{rid:X}"))

        lines.append(f"    GIFtag: NLOOP={nloop} EOP={eop} FLG={flg_names[flg]} NREG={nreg} PRE={pre} REGS=[{','.join(reg_desc)}]")
        if pre:
            ptype = prim & 7
            tme = (prim >> 4) & 1
            lines.append(f"    GIFtag PRIM: type={PRIM_TYPES.get(ptype, str(ptype))} TME={tme}")

        tpos += 16

        if flg == 0:  # PACKED
            for loop in range(nloop):
                for r in range(nreg):
                    if tpos + 16 > len(gif_data):
                        return lines
                    reg_id = (hi >> (r * 4)) & 0xF
                    reg_data = struct.unpack_from("<Q", gif_data, tpos)[0]

                    if reg_id == 0x0E:  # A+D
                        reg_addr = struct.unpack_from("<Q", gif_data, tpos + 8)[0] & 0xFF
                        lines.append(f"      A+D: {format_register(reg_addr, reg_data)}")
                    elif reg_id == 0x00:  # PRIM direct
                        lines.append(f"      {format_register(0x00, reg_data)}")
                    elif reg_id == 0x01:  # RGBAQ
                        lines.append(f"      {format_register(0x01, reg_data)}")
                    elif reg_id == 0x02:  # ST
                        lines.append(f"      {format_register(0x02, reg_data)}")
                    elif reg_id == 0x03:  # UV
                        lines.append(f"      {format_register(0x03, reg_data)}")
                    elif reg_id in (0x04, 0x0C):  # XYZF2/3
                        lines.append(f"      {format_register(reg_id, reg_data)}")
                    elif reg_id in (0x05, 0x0D):  # XYZ2/3
                        lines.append(f"      {format_register(reg_id, reg_data)}")
                    else:
                        rname = REG_NAMES.get(reg_id, f"0x{reg_id:X}")
                        lines.append(f"      {rname}: 0x{reg_data:016X}")

                    tpos += 16

        elif flg == 1:  # REGLIST
            total = nloop * nreg
            for i in range(total):
                if tpos + 8 > len(gif_data):
                    return lines
                tpos += 8
            if (total % 2) == 1:
                tpos += 8

        elif flg == 2:  # IMAGE
            img_size = nloop * 16
            lines.append(f"    IMAGE data: {img_size} bytes")
            tpos += img_size

        if eop:
            break

    return lines


def main():
    with open(GS_DUMP, "rb") as f:
        raw = f.read()
    dctx = zstd.ZstdDecompressor()
    data = dctx.decompress(raw, max_output_size=200 * 1024 * 1024)

    header_total_size = struct.unpack_from("<I", data, 4)[0]
    hdr = struct.unpack_from("<9I", data, 8)
    state_size = hdr[1]
    packets_start = 8 + header_total_size + state_size + 0x2000

    pos = packets_start
    packet_idx = 0
    vsync_count = 0

    # We want to show detail for vsync#1 packets around the FRAME write (pkt#1085)
    # and the VRAM copy (pkt#1929)
    target_ranges = [
        (1, 1083, 1095),   # FRAME write + SPRITE draws
        (1, 1925, 1935),   # VRAM copy region
    ]

    while pos < len(data):
        tag = data[pos]
        pos += 1

        if tag == 0:  # Transfer
            path = data[pos]; pos += 1
            size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            gif_data = data[pos:pos + size]; pos += size

            show = False
            for tv, tstart, tend in target_ranges:
                if vsync_count == tv and tstart <= packet_idx <= tend:
                    show = True
                    break

            if show:
                print(f"\n{'='*70}")
                print(f"PKT #{packet_idx} (vsync#{vsync_count}): TRANSFER path={path} size={size}")
                print(f"{'='*70}")
                lines = parse_gif_detail(gif_data, path, packet_idx)
                for line in lines:
                    print(line)

            packet_idx += 1

        elif tag == 1:
            pos += 1
            vsync_count += 1
            packet_idx += 1

        elif tag == 2:
            pos += 4
            packet_idx += 1

        elif tag == 3:
            pos += 0x2000
            packet_idx += 1

        else:
            break


if __name__ == "__main__":
    main()
