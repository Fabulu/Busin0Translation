#!/usr/bin/env python3
"""
Parse R2100 sub-block VIF/GIF headers AND CLUT tails to find VRAM upload params.

The 0x4C0 header contains CLUT palette uploads (10 palettes via GIF IMAGE mode).
The actual BITBLTBUF/TRXPOS/TRXREG for the pixel data transfer might be in the
CLUT tail (640 bytes after pixel data), or encoded in the header differently.

This script does a thorough hex scan of the ENTIRE sub-block (header + pixels + tail)
looking specifically for BITBLTBUF writes, and also properly parses VIF DIRECT packets.
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
SUB_SIZE = 34624
HDR_SIZE = 0x4C0
PIXEL_SIZE = 32768
TAIL_SIZE = 640


def parse_gs_reg(reg, data):
    """Parse a GS register write."""
    val = struct.unpack('<Q', data)[0]

    if reg == 0x50:  # BITBLTBUF
        sbp = val & 0x3FFF
        sbw = (val >> 16) & 0x3F
        spsm = (val >> 24) & 0x3F
        dbp = (val >> 32) & 0x3FFF
        dbw = (val >> 48) & 0x3F
        dpsm = (val >> 56) & 0x3F
        psm_names = {0: "PSMCT32", 1: "PSMCT24", 2: "PSMCT16",
                     0x13: "PSMT8", 0x14: "PSMT4", 0x30: "PSMZ32"}
        return (f"BITBLTBUF: SBP=0x{sbp:04X} SBW={sbw} SPSM={psm_names.get(spsm, hex(spsm))} "
                f"DBP=0x{dbp:04X} DBW={dbw} DPSM={psm_names.get(dpsm, hex(dpsm))}")
    elif reg == 0x51:  # TRXPOS
        ssax = val & 0x7FF
        ssay = (val >> 16) & 0x7FF
        dsax = (val >> 32) & 0x7FF
        dsay = (val >> 48) & 0x7FF
        return f"TRXPOS: Src=({ssax},{ssay}) Dst=({dsax},{dsay})"
    elif reg == 0x52:  # TRXREG
        rrw = val & 0xFFF
        rrh = (val >> 32) & 0xFFF
        return f"TRXREG: {rrw}x{rrh}"
    elif reg == 0x53:  # TRXDIR
        xdir = val & 0x3
        names = {0: "host->local", 1: "local->host", 2: "local->local"}
        return f"TRXDIR: {names.get(xdir, str(xdir))}"
    elif reg == 0x06:  # TEX0_1
        tbp0 = val & 0x3FFF
        tbw = (val >> 14) & 0x3F
        psm = (val >> 20) & 0x3F
        tw = (val >> 26) & 0xF
        th = (val >> 30) & 0xF
        psm_names = {0: "PSMCT32", 0x13: "PSMT8", 0x14: "PSMT4"}
        return (f"TEX0_1: TBP0=0x{tbp0:04X} TBW={tbw} PSM={psm_names.get(psm, hex(psm))} "
                f"TW=2^{tw}={1<<tw} TH=2^{th}={1<<th}")
    else:
        return f"REG 0x{reg:02X}: 0x{val:016X}"


def scan_vif_direct(data, base_label=""):
    """Parse VIF commands, find DIRECT packets, then parse GIF inside them."""
    pos = 0
    size = len(data)
    results = []

    while pos < size - 4:
        cmd_word = struct.unpack_from('<I', data, pos)[0]

        # VIF command format: [CMD:7][NUM:8][IMMEDIATE:16] in bits 31..0
        # But actually it's: byte3=CMD, byte2=NUM, byte1:byte0=IMMEDIATE
        vif_cmd = (cmd_word >> 24) & 0x7F
        vif_num = (cmd_word >> 16) & 0xFF
        vif_imm = cmd_word & 0xFFFF

        if vif_cmd == 0x50:  # DIRECT
            # DIRECT: sends vif_imm quadwords directly to GIF
            qwc = vif_imm
            gif_start = pos + 4
            gif_size = qwc * 16

            if gif_start + gif_size <= size:
                # Parse GIF tag at gif_start
                gif_tag = struct.unpack_from('<QQ', data, gif_start)
                nloop = gif_tag[0] & 0x7FFF
                eop = (gif_tag[0] >> 15) & 1
                flg = (gif_tag[0] >> 58) & 3
                nreg = (gif_tag[0] >> 60) & 0xF
                if nreg == 0:
                    nreg = 16

                flg_names = {0: "PACKED", 1: "REGLIST", 2: "IMAGE", 3: "DISABLED"}
                results.append(f"  {base_label}+0x{pos:04X}: VIF DIRECT qwc={qwc}")
                results.append(f"    GIF tag: NLOOP={nloop}, EOP={eop}, FLG={flg_names.get(flg,'?')}, NREG={nreg}")

                if flg == 0:  # PACKED (A+D)
                    # REGS descriptor in gif_tag[1]
                    regs = gif_tag[1]
                    results.append(f"    REGS: 0x{regs:016X}")

                    ad_start = gif_start + 16  # after GIF tag
                    for i in range(nloop):
                        for r in range(nreg):
                            entry_off = ad_start + (i * nreg + r) * 16
                            if entry_off + 16 > size:
                                break
                            reg_from_desc = (regs >> (r * 4)) & 0xF

                            if reg_from_desc == 0x0E:  # A+D
                                d = data[entry_off:entry_off + 8]
                                a = struct.unpack_from('<Q', data, entry_off + 8)[0]
                                reg_addr = a & 0xFF
                                parsed = parse_gs_reg(reg_addr, d)
                                results.append(f"    [{i}] {parsed}")
                            else:
                                d = data[entry_off:entry_off + 16]
                                results.append(f"    [{i}][r{r}] REG={reg_from_desc}: {d.hex()}")

                elif flg == 2:  # IMAGE
                    results.append(f"    IMAGE data: {nloop} quadwords = {nloop*16} bytes")

            pos = gif_start + gif_size
            continue

        elif vif_cmd == 0x01:  # STCYCL
            results.append(f"  {base_label}+0x{pos:04X}: VIF STCYCL wl={vif_imm>>8} cl={vif_imm&0xFF}")
            pos += 4
        elif vif_cmd == 0x00:  # NOP
            pos += 4
        elif vif_cmd >= 0x60:  # UNPACK
            # UNPACK Vn-m: transfers data to VU memory, skip for our purposes
            pos += 4  # simplified; real UNPACK has variable-length data
        else:
            pos += 4

    return results


def main():
    print("=== R2100 VRAM Upload Analysis v2 ===\n")

    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
        so, sc, tc = struct.unpack_from("<III", toc_data, R2100_TOC_INDEX * 12)
        f.seek(so * SECTOR)
        r2100 = f.read(sc * SECTOR)

    # Parse descriptor table
    sub_entries = []
    for i in range(NUM_SUBS):
        sub_idx, sub_size, data_off, pad = struct.unpack_from("<IIII", r2100, i * 16)
        sub_entries.append((sub_idx, sub_size, data_off))

    # Check if all headers are identical first
    headers = []
    tails = []
    for blk in range(NUM_SUBS):
        _, _, data_off = sub_entries[blk]
        headers.append(bytes(r2100[data_off:data_off + HDR_SIZE]))
        tail_off = data_off + HDR_SIZE + PIXEL_SIZE
        tails.append(bytes(r2100[tail_off:tail_off + TAIL_SIZE]))

    print(f"Headers identical: {all(h == headers[0] for h in headers[1:])}")
    print(f"Tails identical: {all(t == tails[0] for t in tails[1:])}")

    # Full hex dump of the tail (640 bytes) - this might contain the transfer setup
    print(f"\n=== TAIL (CLUT) region - {TAIL_SIZE} bytes ===")
    tail = tails[0]
    for row in range(0, TAIL_SIZE, 16):
        hex_str = ' '.join(f'{tail[row+j]:02X}' for j in range(min(16, TAIL_SIZE-row)))
        ascii_str = ''.join(chr(tail[row+j]) if 32 <= tail[row+j] < 127 else '.'
                           for j in range(min(16, TAIL_SIZE-row)))
        print(f"  {row:04X}: {hex_str}  {ascii_str}")

    # Now let's do a brute-force scan of the ENTIRE sub-block for the byte pattern
    # that would indicate BITBLTBUF. In A+D mode, we'd see register 0x50 at offset+8.
    # But in REGLIST mode or raw GIF, it could be elsewhere.

    print(f"\n=== Brute-force scan for GS register 0x50 (BITBLTBUF) ===")
    sub_data = r2100[sub_entries[0][2]:sub_entries[0][2] + SUB_SIZE]

    for off in range(0, len(sub_data) - 16):
        # Look for byte 0x50 followed by 7 zero bytes (A+D register address format)
        if (sub_data[off] == 0x50 and
            all(sub_data[off+j] == 0 for j in range(1, 8))):
            # The 8 bytes BEFORE this would be the data
            if off >= 8:
                data = sub_data[off-8:off]
                parsed = parse_gs_reg(0x50, data)
                print(f"  Found at sub+0x{off:04X}: {parsed}")
                print(f"    Data bytes: {data.hex()}")

    print(f"\n=== Brute-force scan for GS register 0x51 (TRXPOS) ===")
    for off in range(0, len(sub_data) - 16):
        if (sub_data[off] == 0x51 and
            all(sub_data[off+j] == 0 for j in range(1, 8))):
            if off >= 8:
                data = sub_data[off-8:off]
                parsed = parse_gs_reg(0x51, data)
                print(f"  Found at sub+0x{off:04X}: {parsed}")

    print(f"\n=== Brute-force scan for GS register 0x52 (TRXREG) ===")
    for off in range(0, len(sub_data) - 16):
        if (sub_data[off] == 0x52 and
            all(sub_data[off+j] == 0 for j in range(1, 8))):
            if off >= 8:
                data = sub_data[off-8:off]
                parsed = parse_gs_reg(0x52, data)
                print(f"  Found at sub+0x{off:04X}: {parsed}")

    print(f"\n=== Brute-force scan for GS register 0x53 (TRXDIR) ===")
    for off in range(0, len(sub_data) - 16):
        if (sub_data[off] == 0x53 and
            all(sub_data[off+j] == 0 for j in range(1, 8))):
            if off >= 8:
                data = sub_data[off-8:off]
                parsed = parse_gs_reg(0x53, data)
                print(f"  Found at sub+0x{off:04X}: {parsed}")

    # Also parse TEX0_1 from the header - the scanner found these
    print(f"\n=== TEX0_1 analysis (from header) ===")
    # TEX0_1 at header offset 0x50: data = 00 00 41 21 06 00 00 20
    tex0_data = bytes.fromhex("0000412106000020")
    parsed = parse_gs_reg(0x06, tex0_data)
    print(f"  {parsed}")

    # Parse VIF structure of header properly
    print(f"\n=== VIF/GIF parse of header ===")
    vif_results = scan_vif_direct(bytes(headers[0]), "HDR")
    for line in vif_results:
        print(line)

    print(f"\n=== VIF/GIF parse of tail ===")
    vif_results = scan_vif_direct(bytes(tails[0]), "TAIL")
    for line in vif_results:
        print(line)

    # The CLUT tail has 10 palettes. Let's see if there's a VIF DIRECT wrapping
    # BITBLTBUF+TRXPOS+TRXREG+TRXDIR before the palette data.
    # Each palette is 16 colors * 4 bytes = 64 bytes.
    # 10 palettes = 640 bytes = TAIL_SIZE. So the tail is pure palette data, no headers.

    # The header must contain the pixel transfer setup too.
    # Let me look at the header structure more carefully.
    # The repeated block at 0x50-step pattern suggests palette uploads.

    # Let's look at the LAST part of the header (after the palette region)
    print(f"\n=== Header bytes 0x330-0x4C0 ===")
    hdr = headers[0]
    for row in range(0x330, HDR_SIZE, 16):
        end = min(row + 16, HDR_SIZE)
        hex_str = ' '.join(f'{hdr[row+j]:02X}' for j in range(end - row))
        print(f"  {row:04X}: {hex_str}")

    # Key insight: the header might NOT contain BITBLTBUF at all.
    # The game's DMA engine might set up the transfer registers from the EXE code,
    # then use DIRECT/IMAGE to send raw pixel data. The header only contains
    # palette uploads (CLUT data via GIF IMAGE mode).

    # Let's check: does the game use EXE code to configure the GS transfer?
    # We should look for BITBLTBUF in the full R2100 resource
    print(f"\n=== Full R2100 scan for BITBLTBUF (0x50 register) ===")
    for off in range(0, len(r2100) - 16):
        if (r2100[off] == 0x50 and
            all(r2100[off+j] == 0 for j in range(1, 8))):
            if off >= 8:
                data = bytes(r2100[off-8:off])
                parsed = parse_gs_reg(0x50, data)
                print(f"  R2100+0x{off:04X}: {parsed}")

    print(f"\n=== Full R2100 scan for TRXREG (0x52 register) ===")
    for off in range(0, len(r2100) - 16):
        if (r2100[off] == 0x52 and
            all(r2100[off+j] == 0 for j in range(1, 8))):
            if off >= 8:
                data = bytes(r2100[off-8:off])
                parsed = parse_gs_reg(0x52, data)
                print(f"  R2100+0x{off:04X}: {parsed}")


if __name__ == "__main__":
    main()
