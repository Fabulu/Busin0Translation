#!/usr/bin/env python3
"""Find the pixel/palette boundary by tracking register writes between IMAGE blocks."""
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

    # Walk through, tracking all gaps and IMAGE blocks
    i = 17
    segments = []  # (type, qw_start, qw_end_exclusive, description)

    while i < total_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3

        if flg == 2 and 0 < nloop <= 800:
            segments.append(('IMAGE', i, i + 1 + nloop, f'nloop={nloop}'))
            i += 1 + nloop
        else:
            # Non-IMAGE QW - collect until we find next IMAGE
            gap_start = i
            while i < total_qw:
                lo2 = struct.unpack_from('<Q', tex, i * 16)[0]
                flg2 = (lo2 >> 46) & 3
                nloop2 = lo2 & 0x7FFF
                if flg2 == 2 and 0 < nloop2 <= 800:
                    break
                i += 1

            # Decode register writes in the gap
            gap_desc = f'gap QWs {gap_start}-{i-1}'
            for qi in range(gap_start, min(i, total_qw)):
                d_lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                d_hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
                reg = d_hi & 0xFF
                reg_names = {0x50: 'BITBLTBUF', 0x51: 'TRXPOS', 0x52: 'TRXREG', 0x53: 'TRXDIR', 0x06: 'TEX0'}
                if reg in reg_names:
                    extra = ""
                    if reg == 0x50:
                        dpsm = (d_lo >> 44) & 0x3F
                        dbp = (d_lo >> 32) & 0x3FFF
                        dbw = (d_lo >> 40) & 0x3F
                        extra = f" DBP={dbp} DBW={dbw} DPSM=0x{dpsm:02x}"
                    elif reg == 0x52:
                        w = d_lo & 0xFFF
                        h = (d_lo >> 32) & 0xFFF
                        extra = f" {w}x{h}"
                    elif reg == 0x53:
                        d = d_lo & 3
                        extra = f" dir={d}"
                    gap_desc += f'\n    QW[{qi}] {reg_names[reg]}: 0x{d_lo:016x}{extra}'
                else:
                    gap_desc += f'\n    QW[{qi}] reg=0x{reg:02x}: 0x{d_lo:016x}'

            segments.append(('GAP', gap_start, i, gap_desc))

    # Print segments and track cumulative data sizes
    print("Segments:")
    cum_data = 0
    pixel_count = 512 * 512  # 262144
    pal_size = 1024

    pixel_data = bytearray()
    palette_data = bytearray()
    collecting_palette = False

    for seg_type, seg_start, seg_end, desc in segments:
        if seg_type == 'IMAGE':
            nloop = int(desc.split('=')[1])
            data_start = (seg_start + 1) * 16
            data_size = nloop * 16
            data_size = min(data_size, len(tex) - data_start)

            marker = ""
            if cum_data < pixel_count and cum_data + data_size >= pixel_count:
                marker = " <-- PIXEL/PALETTE BOUNDARY"
                # Split this block
                pixel_bytes = pixel_count - cum_data
                pal_bytes = data_size - pixel_bytes
                marker += f" (pixel:{pixel_bytes}, pal:{pal_bytes})"

            print(f"  IMAGE at QW[{seg_start}]: {data_size} bytes, cumulative={cum_data}..{cum_data+data_size}{marker}")

            if not collecting_palette:
                needed = pixel_count - len(pixel_data)
                if needed > 0:
                    take = min(needed, data_size)
                    pixel_data.extend(tex[data_start:data_start + take])
                    if take < data_size:
                        collecting_palette = True
                        palette_data.extend(tex[data_start + take:data_start + data_size])
                else:
                    collecting_palette = True
                    palette_data.extend(tex[data_start:data_start + data_size])
            else:
                palette_data.extend(tex[data_start:data_start + data_size])

            cum_data += data_size
        else:
            print(f"  {desc}")

    print(f"\nTotal IMAGE data: {cum_data}")
    print(f"Pixel data collected: {len(pixel_data)} (need {pixel_count})")
    print(f"Palette data collected: {len(palette_data)} (need {pal_size})")

    # Check palette
    print(f"\nPalette first 16 colors:")
    for ci in range(min(16, len(palette_data) // 4)):
        r, g, b, a = palette_data[ci*4], palette_data[ci*4+1], palette_data[ci*4+2], palette_data[ci*4+3]
        print(f"  [{ci:3d}] R={r:3d} G={g:3d} B={b:3d} A={a:3d}")

    # The palette data might actually be in the GAP or after all IMAGE blocks
    # Let me also try: maybe the gaps contain register writes that change
    # BITBLTBUF to palette format, meaning the IMAGE data after the gap IS palette data

    # Also try: maybe the palette is uploaded as PSMCT32 (not PSMT8) to a different DBP
    # In that case, the BITBLTBUF in the gap would show DPSM=0x00 (PSMCT32)

    # For now, render with what we have
    if len(pixel_data) >= pixel_count:
        # Try 1: palette from collected data
        if len(palette_data) >= pal_size:
            palette = unswizzle_clut_psmt8(palette_data[:pal_size])
            img = Image.new('RGBA', (512, 512))
            pix_out = [palette[pixel_data[i]] for i in range(pixel_count)]
            img.putdata(pix_out)
            out_path = os.path.join(TEX_DIR, 'R2118_split.png')
            img.save(out_path)
            print(f"\nSaved: {out_path}")

        # Try 2: grayscale (to verify pixel data correctness)
        palette_gray = [(i, i, i, 255) for i in range(256)]
        img_gray = Image.new('RGBA', (512, 512))
        pix_gray = [palette_gray[pixel_data[i]] for i in range(pixel_count)]
        img_gray.putdata(pix_gray)
        out_path_gray = os.path.join(TEX_DIR, 'R2118_gray.png')
        img_gray.save(out_path_gray)
        print(f"Saved (grayscale): {out_path_gray}")

    # ===== Also do R2119 with grayscale to check pixel data =====
    print("\n=== R2119 grayscale check ===")
    data2 = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex2 = data2[16:]
    w, h = 512, 64
    pc2 = w * h
    pixels2 = tex2[192:192 + pc2]

    palette_gray2 = [(i, i, i, 255) for i in range(256)]
    img_gray2 = Image.new('RGBA', (w, h))
    pix_gray2 = [palette_gray2[pixels2[i]] for i in range(pc2)]
    img_gray2.putdata(pix_gray2)
    out_path2 = os.path.join(TEX_DIR, 'R2119_gray.png')
    img_gray2.save(out_path2)
    print(f"Saved: {out_path2}")


if __name__ == '__main__':
    main()
