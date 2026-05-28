#!/usr/bin/env python3
"""Extract pixel data from CockpitImg by stripping GIF tag headers.

The pixel data in these resources is wrapped in GIF packets:
- Initial PACKED GIF tag (nloop=1 nreg=16) sets up GS registers
- Then alternating: register-setup GIF tags + IMAGE GIF tags with pixel data
- The register setup between strips updates TRXPOS/TRXREG for the next strip

We need to:
1. Walk the GIF tag structure
2. Extract only the pixel data from IMAGE mode transfers
3. Also find the palette data
"""
import struct, sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def walk_gif_packets(tex, verbose=True):
    """Walk all GIF packets in the tex data and extract IMAGE data blocks."""
    max_qw = len(tex) // 16
    i = 0
    image_blocks = []
    register_info = {}

    while i < max_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        hi = struct.unpack_from('<Q', tex, i * 16 + 8)[0]

        nloop = lo & 0x7FFF
        eop = (lo >> 15) & 1
        prim_en = (lo >> 46) & 1  # Note: bit 46 is part of FLG in packed/reglist
        flg = (lo >> 46) & 3
        nreg = (lo >> 60) & 0xF
        if nreg == 0:
            nreg = 16

        if flg == 2 and nloop > 0:
            # IMAGE mode: pixel data follows
            data_start = (i + 1) * 16
            data_size = nloop * 16
            if verbose:
                print(f"  QW[{i}] IMAGE nloop={nloop} data@{data_start} size={data_size}")
            image_blocks.append((data_start, data_size))
            i += 1 + nloop

        elif flg == 0 and nloop > 0:
            # PACKED mode: register writes
            total_regs = nloop * nreg
            end_qw = i + 1 + total_regs

            # Check if this PACKED block makes sense (doesn't extend past data)
            if end_qw > max_qw:
                # Too large -- probably not a real GIF tag
                if verbose:
                    print(f"  QW[{i}] PACKED overflow nloop={nloop} nreg={nreg} (need {end_qw} QWs, have {max_qw})")
                i += 1
                continue

            if verbose:
                print(f"  QW[{i}] PACKED nloop={nloop} nreg={nreg} ({total_regs} writes)")

            # Parse A+D writes for register info
            for j in range(total_regs):
                qi = i + 1 + j
                if qi >= max_qw:
                    break
                d_lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                d_hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
                reg = d_hi & 0xFF

                if reg == 0x06:  # TEX0
                    psm = (d_lo >> 20) & 0x3F
                    tw = (d_lo >> 26) & 0xF
                    th = (d_lo >> 30) & 0xF
                    register_info['psm'] = psm
                    register_info['tex_w'] = 1 << tw
                    register_info['tex_h'] = 1 << th
                elif reg == 0x50:  # BITBLTBUF
                    dpsm = (d_lo >> 44) & 0x3F
                    register_info['dpsm'] = dpsm
                elif reg == 0x52:  # TRXREG
                    rrw = d_lo & 0xFFF
                    rrh = (d_lo >> 32) & 0xFFF
                    register_info['trx_w'] = rrw
                    register_info['trx_h'] = rrh

            i = end_qw

        elif flg == 1:
            # REGLIST mode
            total_regs = nloop * nreg
            qw_count = (total_regs + 1) // 2
            if verbose:
                print(f"  QW[{i}] REGLIST nloop={nloop} nreg={nreg}")
            i += 1 + qw_count

        else:
            # Unknown or zero -- could be raw data
            # Check if this QW and subsequent ones look like raw pixel data
            # by checking if they don't match any valid GIF tag pattern

            # Heuristic: if several consecutive QWs have inconsistent GIF tag fields,
            # treat the rest as raw data
            i += 1

    return image_blocks, register_info


def unswizzle_clut(palette_data):
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            colors.append((r, g, b, min(a * 2, 255)))
        else:
            colors.append((0, 0, 0, 0))
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            colors[base + 8 + j], colors[base + 16 + j] = \
                colors[base + 16 + j], colors[base + 8 + j]
    return colors


def decode_resource(filename, expected_w, expected_h):
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    tex = data[16:]  # skip sub-header

    print(f"\n{'='*60}")
    print(f"Processing {filename} ({len(data)} bytes)")

    image_blocks, reg_info = walk_gif_packets(tex, verbose=True)

    psm = reg_info.get('psm', 0x13)
    width = reg_info.get('tex_w', expected_w)
    height = reg_info.get('tex_h', expected_h)

    print(f"\nFormat: PSM=0x{psm:02x}, {width}x{height}")
    print(f"Found {len(image_blocks)} IMAGE blocks")

    if psm != 0x13:
        print("Not PSMT8, skipping")
        return

    pixel_count = width * height
    pal_size = 1024

    # Concatenate all IMAGE block data
    pixel_data = bytearray()
    for offset, size in image_blocks:
        chunk = tex[offset:offset + size]
        pixel_data.extend(chunk)

    print(f"Total IMAGE data: {len(pixel_data)} bytes (need {pixel_count} pixels + {pal_size} palette)")

    if len(pixel_data) < pixel_count:
        # Maybe we missed some data. Try adding remaining data after last GIF tag
        if image_blocks:
            last_end = image_blocks[-1][0] + image_blocks[-1][1]
            remaining = tex[last_end:]
            print(f"  Adding {len(remaining)} bytes from after last IMAGE block")
            pixel_data.extend(remaining)

    if len(pixel_data) < pixel_count:
        print(f"  Still short: {len(pixel_data)} < {pixel_count}")
        # Pad
        pixel_data.extend(b'\x00' * (pixel_count + pal_size - len(pixel_data)))

    # Extract palette (after pixel data in the IMAGE stream)
    px = pixel_data[:pixel_count]
    pal_raw = pixel_data[pixel_count:pixel_count + pal_size]

    if len(pal_raw) < pal_size:
        print(f"  Palette short: {len(pal_raw)} < {pal_size}, trying end of file")
        pal_raw = tex[-(pal_size):]

    palette = unswizzle_clut(pal_raw)

    img = Image.new('RGBA', (width, height))
    img.putdata([palette[px[j]] for j in range(pixel_count)])
    out_path = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out_path)
    print(f"Saved: {out_path}")


if __name__ == '__main__':
    decode_resource('R2121_guild_background.raw', 512, 512)
    decode_resource('R2122_guild_buttons.raw', 512, 64)
    decode_resource('R2118_tavern_background.raw', 512, 512)
    print("\nDone!")
