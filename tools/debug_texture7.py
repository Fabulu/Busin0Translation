#!/usr/bin/env python3
"""Precise IMAGE transfer extraction for R2118."""
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


def main():
    data = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex = data[16:]
    total_qw = len(tex) // 16

    # The structure from debug_texture.py was:
    # QW[0]: PACKED header (17 QWs: 0-16)
    # QW[17]: IMAGE nloop=642 -> QW[18..659]
    # QW[660]: IMAGE nloop=642 -> QW[661..1302]
    # QW[1303]: IMAGE nloop=642
    # QW[1946]: IMAGE nloop=642
    # QW[2589]: IMAGE nloop=642
    # QW[3232]: IMAGE nloop=642
    # QW[3875]: IMAGE nloop=525
    # QW[4401]: IMAGE nloop=642 -> QW[4402..5043]
    # QW[5044]: BAD PACKED -> actually register writes + IMAGE continues
    # QW[5047]: nloop=642 but parsed as IMAGE with flg=2
    #   Wait, from debug: QW[5047] lo=8282828282828282 hi=0282828229828282
    #   flg = (lo >> 46) & 3 = (0x8282828282828282 >> 46) & 3
    #   Let me compute: 0x8282828282828282 = ...
    #   bit 46 and 47: let's compute
    #   0x8282828282828282 in binary: 1000001010000010...
    #   >> 46: that's shifting right by 46 bits
    #   0x8282828282828282 / 2^46 = 0x20A0A
    #   & 3 = 2  -> FLG=2 (IMAGE)!
    #   nloop = lo & 0x7FFF = 0x8282 & 0x7FFF = 0x0282 = 642
    #   So QW[5047] accidentally has flg=2 and nloop=642 just from pixel data!

    # This means QW[5047] is NOT a real GIF tag, it's pixel data that
    # happens to parse as IMAGE with nloop=642. The actual pixel data
    # is continuous from QW[18] onward (after stripping only the initial
    # and real GIF tags).

    # So the real structure is:
    # QW[0-16]: Header registers (272 bytes)
    # QW[17]: Real GIF tag (IMAGE, nloop=642)
    # QW[18-659]: Pixel data (642*16 = 10272 bytes)
    # QW[660]: Real GIF tag (IMAGE, nloop=642)
    # QW[661-1302]: Pixel data
    # ... etc
    # The question is: how many real GIF tags are there?

    # From the first 8 IMAGE tags, each is at:
    # 17, 660, 1303, 1946, 2589, 3232, 3875, 4401
    # Gaps: 660-17=643, 1303-660=643, etc. -> each IMAGE = 1 tag + 642 data QWs = 643 QWs

    # But QW[3875] has nloop=525 (not 642), so:
    # QW[3875+1+525] = QW[4401] -> 3875+526 = 4401. Correct!

    # After QW[4401] IMAGE nloop=642: data ends at QW[5043]
    # QW[5044] should be the next tag.

    # Let me check: what is QW[5044]?
    # From debug: lo=0182117f397c1602 hi=66822f8201820082
    # nloop = 0x1602 & 0x7FFF = 0x1602 = 5634 -> clearly pixel data, not a tag
    # This means QW[5044] is pixel data that was treated as a GIF tag

    # But wait, in the IMAGE transfer at QW[4401]:
    # nloop=642, data = QW[4402..5043] = 642 QWs
    # Then QW[5044] SHOULD be the next GIF tag.
    # But it's pixel data bytes... That means the GIF tag parser in PS2 firmware
    # finishes the 642-QW IMAGE, then reads QW[5044] as the next GIF tag.

    # QW[5044] lo=0182117f397c1602: nloop=5634, flg=0 (PACKED)
    # That's wrong for the PS2 - it would try to read 90144 QWs.
    # Unless the EOP bit on the previous tag stops it.

    # Let me check the EOP on each IMAGE tag:
    image_qws = [17, 660, 1303, 1946, 2589, 3232, 3875, 4401]
    for qi in image_qws:
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        nloop = lo & 0x7FFF
        eop = (lo >> 15) & 1
        flg = (lo >> 46) & 3
        print(f"  QW[{qi}]: nloop={nloop}, flg={flg}, EOP={eop}")

    # If EOP=1 on the tag at QW[4401], then the GIF packet ends there.
    # The PS2 would stop processing GIF after that.
    # Then what's at QW[5044]? A NEW GIF packet (started by VIF/DMA).

    # So the overall structure might be:
    # DMA packet 1: GIF tag + registers + GIF tag + IMAGE data + ... + GIF tag + IMAGE (EOP)
    # DMA packet 2: GIF tag + registers + GIF tag + IMAGE data + ...

    # Each IMAGE tag has EOP=1, so each IMAGE transfer is a complete GIF packet.
    # Between IMAGE packets, there are DMA/VIF headers that I'm not seeing.

    # Wait, EOP=1 means the GIF tag is the last in this GIF packet.
    # But between GIF packets there could be DMA/VIF wrapper data.

    # Actually, for standard PS2 GIF: after an EOP, the next GIF packet starts
    # at the next QW boundary. There's no additional header unless it's DMA/VIF.

    # Let me re-examine: maybe the structure is cleaner than I think.
    # The initial PACKED block (QW 0) has EOP=0, meaning more GIF follows.
    # Then each IMAGE tag has EOP=1.

    # Wait: first PACKED at QW[0]: lo=0x0000000200000001
    # EOP = (lo >> 15) & 1 = 0
    # So EOP=0 means more GIF data follows. But NLOOP=1, NREG=16, so
    # it processes QW[1-16] then continues to QW[17].

    # QW[17] IMAGE nloop=642 EOP=1: processes QW[18-659], then EOP stops GIF.
    # So the GIF packet is: QW[0-16] (PACKED) + QW[17-659] (IMAGE). Done.

    # Then QW[660] is a NEW GIF packet (started by DMA/VIF).
    # QW[660] IMAGE nloop=642 EOP=1: this is a standalone IMAGE GIF packet.
    # So QW[660] is both the GIF tag and the entire packet.

    # This means between QW[659] and QW[660] there SHOULD be DMA/VIF wrapper.
    # But QW[660] immediately follows QW[659].

    # Unless the DMA chain links them back-to-back. In that case:
    # DMA chunk 1: QW[0-659] (first PACKED + first IMAGE)
    # DMA chunk 2: QW[660-1302] (second IMAGE)
    # etc.

    # In this case, there are NO extra bytes between IMAGE blocks!
    # The GIF tags at QW[17, 660, 1303, ...] are the only overhead.

    # But after QW[5043] (end of 8th IMAGE at QW[4401]):
    # QW[5044] starts a new DMA chunk. What's in it?

    # From the debug, QW[5044-5046] look like register writes for a new transfer:
    # QW[5045]: hi ends with 0x65 = 101, but 0x65 is not a standard GS register

    # Actually, from debug_texture2:
    # QW[5045] = 1c82608282821f82 13007900000e8265
    # hi & 0xFF = 0x65 -> not a standard register
    # But hi has bytes: 65 82 0e 00 00 79 00 13
    # Hmm, if we look at QW[5045] differently:
    # As bytes: 82 1f 82 82 82 60 82 1c  65 82 0e 00 00 79 00 13

    # I wonder if QW[5044-5046] are actually:
    # QW[5044]: a DMA tag
    # QW[5045]: a VIF unpack code + data
    # QW[5046]: more VIF/GIF data

    # OR: they are a short PACKED GIF block with register writes
    # QW[5044] as GIF tag: nloop=5634 which is too big... BUT
    # What if we split this differently?

    # Let me try: QW[5044] = DMA tag
    # DMA tag format: lo = QWC[15:0] | pad[25:16] | ID[30:28] | IRQ[31] | ADDR[63:32]
    # lo = 0x0182117f397c1602
    # QWC = 0x1602 = 5634
    # ID = (lo >> 28) & 7 = (0x0182117f397c1602 >> 28) & 7 = (0x182117f39) & 7 = 1
    # ADDR = lo >> 32 = 0x0182117f
    # That could be a DMA tag: transfer 5634 QWs from address 0x0182117f. Plausible.

    # If QW[5044] is a DMA tag, then QW[5045] starts VIF codes,
    # and QW[5046-5047] might be VIF DIRECT commands wrapping GIF data.

    # Actually, for PS2 GIF via PATH 3 (VIF->GIF):
    # VIF DIRECT command: VIFcode(32) | data(QWs)
    # VIF DIRECT: cmd=0x50, IMM=size_in_QWs

    # Let me check QW[5045-5046] as VIF codes
    # But this is getting very deep. Let me try a different approach entirely.

    # APPROACH: The file contains the exact GS upload data.
    # The PS2 game uploads the texture in strips.
    # Between strip groups, there are register writes that set BITBLTBUF/TRXPOS/TRXREG.
    #
    # The first group (QW 17-5043) uploads the pixel data.
    # The second group (after some register writes) uploads the palette.
    #
    # Let me see: at QW[5044-5046], 3 QWs of non-IMAGE data, then IMAGE continues.
    # The register writes at QW[5045] might set up BITBLTBUF for palette upload.

    # But 3 QWs doesn't seem like enough for a full register write block.
    # A PACKED block needs at least 1 GIF tag + data QWs.

    # Let me just try: the break between pixel and palette data is at the
    # exact pixel count boundary (262144 bytes of IMAGE data).

    # Collect ALL data (stripping only the initial GIF tags for known IMAGE blocks):
    all_image_data = bytearray()
    image_info = []

    i = 17  # Start after header
    while i < total_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3

        # Only treat as IMAGE if nloop is reasonable (< 1024)
        # This avoids treating pixel data as GIF tags
        if flg == 2 and 0 < nloop <= 800:
            data_start = (i + 1) * 16
            data_size = nloop * 16
            data_size = min(data_size, len(tex) - data_start)
            all_image_data.extend(tex[data_start:data_start + data_size])
            image_info.append((i, nloop, data_start, data_size))
            i += 1 + nloop
        else:
            # Check next few QWs for IMAGE
            found_next = False
            for j in range(i + 1, min(i + 10, total_qw)):
                lo_j = struct.unpack_from('<Q', tex, j * 16)[0]
                nloop_j = lo_j & 0x7FFF
                flg_j = (lo_j >> 46) & 3
                if flg_j == 2 and 0 < nloop_j <= 800:
                    # Skip QWs between as non-pixel data (register writes)
                    print(f"  Skipping QWs {i}-{j-1} (non-IMAGE)")
                    i = j
                    found_next = True
                    break

            if not found_next:
                # Rest might be IMAGE data without tags
                # Or we might be past all the data
                remaining = len(tex) - i * 16
                if remaining > 1024:  # More than just padding
                    print(f"  Collecting remaining {remaining} bytes from QW[{i}]")
                    all_image_data.extend(tex[i * 16:])
                break

    print(f"Collected {len(all_image_data)} bytes of IMAGE data from {len(image_info)} blocks")
    for qi, nl, ds, dsz in image_info:
        print(f"  QW[{qi}]: nloop={nl}, data_start={ds}, size={dsz}")

    pixel_count = 512 * 512  # 262144
    pal_size = 1024

    print(f"\nNeed {pixel_count} + {pal_size} = {pixel_count + pal_size}")
    print(f"Have {len(all_image_data)} bytes")
    print(f"Extra: {len(all_image_data) - (pixel_count + pal_size)} bytes")

    if len(all_image_data) >= pixel_count + pal_size:
        # The palette should be at exactly pixel_count offset
        pixels = all_image_data[:pixel_count]
        pal_raw = all_image_data[pixel_count:pixel_count + pal_size]

        # Check if palette data looks right
        print(f"\nPalette check (first 16 colors):")
        for ci in range(16):
            r, g, b, a = pal_raw[ci*4], pal_raw[ci*4+1], pal_raw[ci*4+2], pal_raw[ci*4+3]
            print(f"  [{ci:3d}] R={r:3d} G={g:3d} B={b:3d} A={a:3d}")

        palette = unswizzle_clut_psmt8(pal_raw)

        img = Image.new('RGBA', (512, 512))
        pix_out = [palette[pixels[i]] for i in range(pixel_count)]
        img.putdata(pix_out)
        out_path = os.path.join(TEX_DIR, 'R2118_precise.png')
        img.save(out_path)
        print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
