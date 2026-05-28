#!/usr/bin/env python3
"""Carefully extract R2118 and R2119 pixel data."""
import struct
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def unswizzle_clut_psmt8(palette_data):
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            a = min(a * 2, 255)
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))
    unswizzled = list(colors)
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            unswizzled[base + 8 + j], unswizzled[base + 16 + j] = \
                unswizzled[base + 16 + j], unswizzled[base + 8 + j]
    return unswizzled


def analyze_r2118():
    """Analyze R2118 structure in detail."""
    data = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex = data[16:]
    total_qw = len(tex) // 16

    print(f"R2118: {len(tex)} bytes = {total_qw} QWs")

    # Walk through QWs, carefully tracking position
    i = 0
    pixel_groups = []  # List of (group_label, [(offset, size), ...])
    current_group = []
    current_label = "pre-header"
    reg_state = {}

    while i < total_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        hi = struct.unpack_from('<Q', tex, i * 16 + 8)[0]

        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3
        eop = (lo >> 15) & 1
        nreg = (lo >> 60) & 0xF or 16

        if flg == 2 and 0 < nloop <= 1024:
            # IMAGE mode - collect pixel data
            data_start = (i + 1) * 16
            data_size = min(nloop * 16, len(tex) - data_start)
            current_group.append((data_start, data_size))
            i += 1 + nloop
            if eop:
                pass  # Continue collecting

        elif flg == 0 and 0 < nloop and nreg > 0:
            total_data = nloop * nreg
            end = i + 1 + total_data

            if end > total_qw:
                # Overflows - not a real GIF tag, part of pixel data
                # But could be a register write group between two IMAGE sections
                # Check if this looks like register data (hi bytes are known regs)
                next_hi = struct.unpack_from('<Q', tex, (i+1) * 16 + 8)[0] if i+1 < total_qw else 0
                next_reg = next_hi & 0xFF

                if next_reg in (0x50, 0x51, 0x52, 0x53, 0x06, 0x0e, 0x4c):
                    # Looks like a real register write section
                    # Parse just a few QWs as A+D
                    print(f"QW[{i}]: Mid-stream register writes (overflows)")
                    # Save current group and start new one
                    if current_group:
                        pixel_groups.append((current_label, current_group))
                        current_group = []
                        current_label = f"group_after_QW{i}"

                    # Try to find next IMAGE tag manually
                    for j in range(i + 1, min(i + 20, total_qw)):
                        lo_j = struct.unpack_from('<Q', tex, j * 16)[0]
                        flg_j = (lo_j >> 46) & 3
                        nloop_j = lo_j & 0x7FFF
                        if flg_j == 2 and 0 < nloop_j <= 1024:
                            print(f"  Next IMAGE at QW[{j}]")
                            i = j
                            break
                        # Check for A+D register writes
                        hi_j = struct.unpack_from('<Q', tex, j * 16 + 8)[0]
                        reg_j = hi_j & 0xFF
                        if reg_j in (0x50, 0x51, 0x52, 0x53):
                            rn = {0x50:'BITBLTBUF', 0x51:'TRXPOS', 0x52:'TRXREG', 0x53:'TRXDIR'}[reg_j]
                            extra = ""
                            if reg_j == 0x52:
                                w = lo_j & 0xFFF
                                h = (lo_j >> 32) & 0xFFF
                                extra = f" ({w}x{h})"
                            elif reg_j == 0x50:
                                dpsm = (lo_j >> 44) & 0x3F
                                dbp = (lo_j >> 32) & 0x3FFF
                                extra = f" (DBP={dbp} DPSM=0x{dpsm:02x})"
                            print(f"  QW[{j}] {rn}: 0x{lo_j:016x}{extra}")
                    else:
                        print(f"  No more IMAGE tags found")
                        break
                else:
                    # Not register writes - raw data
                    print(f"QW[{i}]: Treating as raw data until end (overflow, reg=0x{next_reg:02x})")
                    remaining = len(tex) - i * 16
                    current_group.append((i * 16, remaining))
                    break
            else:
                # Valid PACKED block - register writes
                if i == 0:
                    print(f"QW[{i}]: Header PACKED block, {nloop} loops, {nreg} regs")
                else:
                    print(f"QW[{i}]: PACKED block, {nloop} loops, {nreg} regs")
                    # Save current group
                    if current_group:
                        pixel_groups.append((current_label, current_group))
                        current_group = []
                        current_label = f"group_after_QW{i}"

                # Parse register writes
                for li in range(nloop):
                    for ri in range(nreg):
                        qi = i + 1 + li * nreg + ri
                        if qi < total_qw:
                            d_lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                            d_hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
                            reg = d_hi & 0xFF
                            if reg in (0x50, 0x52, 0x53):
                                rn = {0x50:'BITBLTBUF', 0x52:'TRXREG', 0x53:'TRXDIR'}[reg]
                                extra = ""
                                if reg == 0x52:
                                    w = d_lo & 0xFFF
                                    h = (d_lo >> 32) & 0xFFF
                                    extra = f" ({w}x{h})"
                                elif reg == 0x50:
                                    dpsm = (d_lo >> 44) & 0x3F
                                    dbp = (d_lo >> 32) & 0x3FFF
                                    extra = f" (DBP={dbp} DPSM=0x{dpsm:02x})"
                                print(f"  [{qi}] {rn}: 0x{d_lo:016x}{extra}")
                                reg_state[reg] = d_lo

                i = end
        else:
            i += 1

    if current_group:
        pixel_groups.append((current_label, current_group))

    # Print groups
    print(f"\n{len(pixel_groups)} pixel groups:")
    for label, blocks in pixel_groups:
        total_bytes = sum(s for _, s in blocks)
        print(f"  {label}: {len(blocks)} blocks, {total_bytes} bytes")

    # Concatenate all groups
    all_pixels = bytearray()
    for label, blocks in pixel_groups:
        for offset, size in blocks:
            all_pixels.extend(tex[offset:offset + size])

    return all_pixels


def analyze_r2119():
    """Analyze R2119 structure in detail."""
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    total_qw = len(tex) // 16

    print(f"\nR2119: {len(tex)} bytes = {total_qw} QWs")

    # The header is QW[0-16] (17 QWs = 272 bytes)
    # Let me check what register writes are in the header
    for qi in range(17):
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
        reg = hi & 0xFF
        if reg in (0x50, 0x51, 0x52, 0x53, 0x06):
            rn = {0x50:'BITBLTBUF', 0x51:'TRXPOS', 0x52:'TRXREG', 0x53:'TRXDIR', 0x06:'TEX0_1'}[reg]
            extra = ""
            if reg == 0x52:
                w = lo & 0xFFF
                h = (lo >> 32) & 0xFFF
                extra = f" ({w}x{h})"
            elif reg == 0x50:
                dpsm = (lo >> 44) & 0x3F
                dbp = (lo >> 32) & 0x3FFF
                extra = f" (DBP={dbp} DPSM=0x{dpsm:02x})"
            elif reg == 0x06:
                psm = (lo >> 20) & 0x3F
                tw = (lo >> 26) & 0xF
                th = (lo >> 30) & 0xF
                extra = f" (PSM=0x{psm:02x} {1<<tw}x{1<<th})"
            print(f"  QW[{qi}] {rn}: 0x{lo:016x}{extra}")

    # Check: does the header contain TRXREG (transfer dimensions)?
    # Without TRXREG, the pixel upload dimensions might be different from TEX0 dimensions

    # Now look at the data after QW[16]
    # We know QW[12-16] are 0xFF (part of pixel data)
    # But those are within the "PACKED" block data...
    # Wait: QW[0] says PACKED nloop=1 nreg=16
    # That means 1 loop of 16 registers = QW[1] through QW[16]
    # So QW[12-16] are register writes where both data and reg happen to be 0xFF

    # After the PACKED block: QW[17] should be the next GIF tag
    # But QW[17] is all 0xFF which is not a valid GIF tag for our purposes

    # So maybe the structure is:
    # QW[0]: GIF tag (PACKED, 1 loop, 16 regs)
    # QW[1-16]: 16 A+D register writes (though QW[12-16] = 0xFF which is reg 0xFF = invalid)
    # QW[17]: Next GIF tag? But it's 0xFF...

    # Maybe the actual pixel data starts at a different offset
    # Let me check if there's a TRXDIR=0 (host->local) followed by an IMAGE tag
    # TRXDIR at QW[9]: lo=4 -> host->local transfer

    # Actually, maybe the issue is that this ISN'T a GIF packet at all!
    # Maybe it's a VIF/DMA structure or just raw data with a custom header.

    # Let me try: header is just 12 QWs (192 bytes), not 17
    # Because QW[12] starts with 0xFF which is clearly pixel data

    # Wait, let me look at this more carefully.
    # QW[9] has hi=0x0000000000000000 and lo=0x0000000000000004
    # If this is A+D: reg=0x00, data=4
    # QW[10]: hi=0, lo=0 -> reg=0x00, data=0
    # QW[11]: hi=0, lo=0 -> reg=0x00, data=0

    # These last few "register writes" set PRIM to 4, 0, 0 which is odd

    # Then QW[12-16] are 0xFFFF...
    # If these are register writes: reg=0xFF (unknown), data=0xFFFF...
    # These are garbage register writes, or padding

    # Actually, I think the format might be:
    # 16 bytes sub-header
    # Variable-size GS packet header (registers)
    # Pixel data
    # Palette data

    # The GS packet header ends when we hit the first non-register QW
    # QW[12] = 0xFFFFFFFF... is clearly not a register write

    # So the data structure for R2119 might be:
    # QW[0]: GIF tag
    # QW[1-11]: Register writes (A+D pairs, some with reg=0 = PRIM)
    # QW[12] onward: This is supposed to be an IMAGE GIF tag followed by pixel data!

    # Maybe QW[11] or QW[10] is supposed to be the IMAGE GIF tag?
    # QW[11]: lo=0, hi=0 -> nloop=0, flg=0 -> invalid
    # What if QW[9] lo=4 is a TRXDIR write, and QW[10] is an IMAGE GIF tag?
    # QW[10]: lo=0, hi=0 -> nloop=0 -> no data. Invalid.

    # THEORY: The GIF tag at QW[0] says NLOOP=1, meaning 1 iteration of 16 regs.
    # After that (QW[17]) should be the next GIF tag.
    # But QW[17] is 0xFF which would be: nloop=32767, flg=3 -> invalid

    # Unless... the NREG/NLOOP interpretation is wrong and this is actually:
    # QW[0] = DMA tag or VIF code, not a GIF tag

    # VIF CODE format: cmd(7:0), num(15:8), immediate(31:16)
    # For VIF UNPACK: cmd = 0x60-0x7F

    # DMA tag: QWC(15:0), unused(25:16), ID(30:28), ADDR(63:32)
    # lo = 0x0000000200000001: QWC=1, ID=(lo>>28)&7 = 0, ADDR=2
    # That doesn't make much sense either.

    # Let me try yet another theory: maybe the header is exactly 272 bytes (17 QWs)
    # and the data at QW[12-16] is part of the register block (padding/unused regs)
    # Then pixel data starts at QW[17] = offset 272
    # And the pixel data IS 0xFFFF... for the first few rows (white/transparent background)

    # For 512x64 PSMT8:
    # pixel data = 32768 bytes at offset 272
    # palette = 1024 bytes at offset 272 + 32768 = 33040
    # Total = 34064
    # File tex = 34800 bytes
    # Remaining = 34800 - 34064 = 736 bytes (unused/padding at end?)

    # But earlier we got recognizable Japanese text with offset 192 (QW[12])
    # Let me compare both offsets

    w, h = 512, 64
    pixel_count = w * h
    pal_size = 1024

    results = {}

    for start_offset in [192, 272]:
        pixels = tex[start_offset:start_offset + pixel_count]
        pal_raw = tex[start_offset + pixel_count:start_offset + pixel_count + pal_size]
        palette = unswizzle_clut_psmt8(pal_raw)

        img = Image.new('RGBA', (w, h))
        pix_out = [palette[pixels[i]] for i in range(pixel_count)]
        img.putdata(pix_out)

        out_path = os.path.join(TEX_DIR, f'R2119_start{start_offset}.png')
        img.save(out_path)
        print(f"  Saved: {out_path}")
        results[start_offset] = out_path

    # Also try: the data between IMAGE transfers in R2118 follows a pattern
    # Each group of IMAGE transfers is preceded by a register write section
    # that includes BITBLTBUF/TRXPOS/TRXREG/TRXDIR

    # For R2119, maybe the pixel data is also uploaded in strips,
    # but the strip boundaries happen to align with the data

    # Let me check if the pixel data at offset 192 shows striping
    # (i.e., some rows are wrong due to GIF tag contamination)

    # Look at pixel values at specific positions
    pixels192 = tex[192:192 + pixel_count]
    print(f"\n  Pixel row 0 (first 32 bytes): {pixels192[:32].hex()}")
    print(f"  Pixel row 1: {pixels192[512:544].hex()}")
    print(f"  Pixel row 5: {pixels192[5*512:5*512+32].hex()}")

    return results


def main():
    all_pixels = analyze_r2118()

    pixel_count = 512 * 512
    pal_size = 1024

    print(f"\nTotal pixel data: {len(all_pixels)}")
    print(f"Need: {pixel_count} pixels + {pal_size} palette = {pixel_count + pal_size}")

    if len(all_pixels) >= pixel_count + pal_size:
        pixels = all_pixels[:pixel_count]
        pal_raw = all_pixels[pixel_count:pixel_count + pal_size]
        palette = unswizzle_clut_psmt8(pal_raw)

        img = Image.new('RGBA', (512, 512))
        pix_out = [palette[pixels[i]] for i in range(pixel_count)]
        img.putdata(pix_out)
        out_path = os.path.join(TEX_DIR, 'R2118_clean.png')
        img.save(out_path)
        print(f"Saved: {out_path}")

    analyze_r2119()


if __name__ == '__main__':
    main()
