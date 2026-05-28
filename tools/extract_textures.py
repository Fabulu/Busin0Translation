#!/usr/bin/env python3
"""Extract PS2 CockpitImg textures from raw PACKDATA resources to PNG.

These are GS (Graphics Synthesizer) packets containing GIF tags followed by
A+D register writes and IMAGE data transfers. Pixel data is often split
across multiple IMAGE transfers (strips), and palette data may be in a
separate transfer or inline.
"""
import struct
import sys
import os

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

PSM_NAMES = {
    0x00: 'PSMCT32', 0x01: 'PSMCT24', 0x02: 'PSMCT16', 0x0a: 'PSMCT16S',
    0x13: 'PSMT8', 0x14: 'PSMT4', 0x1b: 'PSMT8H',
    0x24: 'PSMT4HL', 0x2c: 'PSMT4HH',
    0x30: 'PSMZ32', 0x31: 'PSMZ24', 0x32: 'PSMZ16', 0x3a: 'PSMZ16S',
}

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


def parse_gif_tag(lo, hi):
    """Parse a 128-bit GIF tag."""
    nloop = lo & 0x7FFF
    eop = (lo >> 15) & 1
    flg = (lo >> 46) & 3
    nreg = (lo >> 60) & 0xF
    if nreg == 0:
        nreg = 16
    pre = (lo >> 46) & 1
    # Extract register list from hi
    regs = []
    for r in range(nreg):
        regs.append((hi >> (r * 4)) & 0xF)
    return {
        'nloop': nloop, 'eop': eop, 'flg': flg, 'nreg': nreg,
        'pre': pre, 'regs': regs,
    }


def walk_gs_packet(tex, verbose=False):
    """Walk through the entire GS packet, parsing GIF tags and collecting
    register writes and IMAGE data blocks.

    Returns: (info_dict, list_of_transfers)
    Each transfer is a dict with keys like 'type', 'bitbltbuf', 'trxreg', 'trxdir',
    'data_offset', 'data_size', etc.
    """
    info = {}
    transfers = []  # List of IMAGE data transfers with their preceding register context
    current_regs = {}  # Track current GS register state

    i = 0
    max_qw = len(tex) // 16

    while i < max_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        hi = struct.unpack_from('<Q', tex, i * 16 + 8)[0]

        tag = parse_gif_tag(lo, hi)

        if tag['flg'] == 2:  # IMAGE mode
            data_start = (i + 1) * 16
            data_size = tag['nloop'] * 16
            if verbose:
                print(f"  QW[{i}] IMAGE: nloop={tag['nloop']}, data at {data_start}, size={data_size}")
            transfers.append({
                'type': 'image',
                'data_offset': data_start,
                'data_size': data_size,
                'regs': dict(current_regs),  # snapshot of register state
            })
            i += 1 + tag['nloop']

        elif tag['flg'] == 0:  # PACKED mode
            if verbose:
                print(f"  QW[{i}] PACKED: nloop={tag['nloop']}, nreg={tag['nreg']}, regs={tag['regs']}")

            # Check if this is an A+D block (register 0x0e)
            is_ad = (tag['nreg'] >= 1 and 0x0e in tag['regs']) or tag['nreg'] == 16

            if is_ad or tag['nreg'] == 16:
                # Read A+D register pairs
                for loop_i in range(tag['nloop']):
                    for reg_i in range(tag['nreg']):
                        qi = i + 1 + loop_i * tag['nreg'] + reg_i
                        if qi >= max_qw:
                            break
                        data_lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                        data_hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]

                        # For A+D: data_hi[7:0] = register address
                        reg_addr = data_hi & 0xFF
                        reg_name = GS_REG_NAMES.get(reg_addr, f'0x{reg_addr:02x}')
                        current_regs[reg_addr] = data_lo

                        if verbose and reg_addr in (0x50, 0x51, 0x52, 0x53, 0x06):
                            print(f"    [{qi}] {reg_name}: 0x{data_lo:016x}")

                        # Decode specific registers
                        if reg_addr == 0x50:  # BITBLTBUF
                            dpsm = (data_lo >> 44) & 0x3F
                            dbw = (data_lo >> 40) & 0x3F
                            dbp = (data_lo >> 32) & 0x3FFF
                            spsm = (data_lo >> 20) & 0x3F
                            sbw = (data_lo >> 16) & 0x3F
                            sbp = data_lo & 0x3FFF
                            info['dpsm'] = dpsm
                            info['dbw'] = dbw
                            info['dbp'] = dbp
                            if verbose:
                                print(f"      BITBLTBUF: DBP={dbp} DBW={dbw} DPSM={dpsm}({PSM_NAMES.get(dpsm,'?')})")

                        elif reg_addr == 0x52:  # TRXREG
                            rrw = data_lo & 0xFFF
                            rrh = (data_lo >> 32) & 0xFFF
                            info['trx_width'] = rrw
                            info['trx_height'] = rrh
                            if verbose:
                                print(f"      TRXREG: {rrw}x{rrh}")

                        elif reg_addr == 0x06:  # TEX0_1
                            tbp0 = data_lo & 0x3FFF
                            tbw = (data_lo >> 14) & 0x3F
                            psm = (data_lo >> 20) & 0x3F
                            tw = (data_lo >> 26) & 0xF
                            th = (data_lo >> 30) & 0xF
                            cbp = (data_lo >> 37) & 0x3FFF
                            cpsm = (data_lo >> 51) & 0xF
                            info['psm'] = psm
                            info['tex_w'] = 1 << tw
                            info['tex_h'] = 1 << th
                            info['cbp'] = cbp
                            info['cpsm'] = cpsm
                            info['tbw'] = tbw
                            if verbose:
                                print(f"      TEX0: PSM={psm}({PSM_NAMES.get(psm,'?')}) "
                                      f"{1<<tw}x{1<<th} CBP={cbp}")

                i += 1 + tag['nloop'] * tag['nreg']
            else:
                # Other PACKED mode - skip
                i += 1 + tag['nloop'] * tag['nreg']

        elif tag['flg'] == 1:  # REGLIST mode
            i += 1 + ((tag['nloop'] * tag['nreg'] + 1) // 2)
        else:
            i += 1

    return info, transfers


def unswizzle_clut_psmt8(palette_data):
    """Unswizzle PS2 CLUT for PSMT8 (256 colors).
    PS2 PSMT8 CLUT has entries 8-15 and 16-23 swapped within each 32-entry group."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r = palette_data[off]
            g = palette_data[off + 1]
            b = palette_data[off + 2]
            a = palette_data[off + 3]
            a = min(a * 2, 255)  # PS2 alpha 0-128 -> 0-255
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))

    # Swap entries 8-15 with 16-23 in each group of 32
    unswizzled = list(colors)
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            unswizzled[base + 8 + j], unswizzled[base + 16 + j] = \
                unswizzled[base + 16 + j], unswizzled[base + 8 + j]

    return unswizzled


def decode_psmt8_image(pixel_data, palette, width, height):
    """Decode a PSMT8 image given linear pixel data and a decoded palette."""
    img = Image.new('RGBA', (width, height))
    pixels_out = []
    for i in range(width * height):
        if i < len(pixel_data):
            idx = pixel_data[i]
            pixels_out.append(palette[idx])
        else:
            pixels_out.append((0, 0, 0, 0))
    img.putdata(pixels_out)
    return img


def process_file(filename, verbose=True):
    """Process a single raw texture file."""
    filepath = os.path.join(TEX_DIR, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    data = open(filepath, 'rb').read()
    print(f"\n{'='*60}")
    print(f"Processing: {filename} ({len(data)} bytes)")
    print(f"{'='*60}")

    # 16-byte sub-header
    sub_hdr = struct.unpack_from('<IIII', data, 0)
    payload_size = sub_hdr[1]
    print(f"Sub-header: type={sub_hdr[0]}, payload={payload_size}, offset={sub_hdr[2]}, pad={sub_hdr[3]}")

    tex = data[16:]

    # Walk the GS packet
    info, transfers = walk_gs_packet(tex, verbose=verbose)

    print(f"\nTexture info: {info}")
    print(f"Found {len(transfers)} IMAGE transfers")

    if not transfers:
        print("No IMAGE data found - trying alternate parse...")
        # Some files may not use IMAGE GIF tags but embed data differently
        # Try brute force: scan for pixel data patterns
        return try_bruteforce(tex, info, filename)

    # Determine texture format
    psm = info.get('psm', info.get('dpsm', 0x13))
    width = info.get('tex_w', info.get('trx_width', 512))
    height = info.get('tex_h', info.get('trx_height', 512))

    print(f"Format: PSM=0x{psm:02x} ({PSM_NAMES.get(psm, '?')}), {width}x{height}")

    if psm == 0x13:  # PSMT8
        return decode_psmt8_resource(tex, info, transfers, width, height, filename)
    elif psm == 0x14:  # PSMT4
        return decode_psmt4_resource(tex, info, transfers, width, height, filename)
    elif psm == 0x00:  # PSMCT32
        return decode_psmct32_resource(tex, info, transfers, width, height, filename)
    else:
        print(f"Unsupported PSM: 0x{psm:02x}")


def decode_psmt8_resource(tex, info, transfers, width, height, filename):
    """Decode a PSMT8 resource with potentially multiple IMAGE transfers."""
    pixel_count = width * height
    pal_size = 256 * 4

    # Concatenate all IMAGE transfer data
    all_data = bytearray()
    for t in transfers:
        chunk = tex[t['data_offset']:t['data_offset'] + t['data_size']]
        all_data.extend(chunk)

    print(f"Total IMAGE data: {len(all_data)} bytes")
    print(f"Need: {pixel_count} pixel bytes + {pal_size} palette bytes = {pixel_count + pal_size}")

    # The concatenated data should contain pixel data followed by palette,
    # or there may be separate transfers for each.
    # Also, there might be register writes between transfers that change
    # BITBLTBUF/TRXREG indicating pixel vs palette transfers.

    # Check if each transfer has BITBLTBUF info to distinguish pixel from palette
    pixel_transfers = []
    palette_transfers = []

    for t in transfers:
        regs = t.get('regs', {})
        if 0x50 in regs:  # BITBLTBUF
            bltbuf = regs[0x50]
            dpsm = (bltbuf >> 44) & 0x3F
            dbp = (bltbuf >> 32) & 0x3FFF
            if dpsm == 0x00:  # PSMCT32 transfer to CLUT area
                palette_transfers.append(t)
                print(f"  Transfer at {t['data_offset']}: PALETTE (PSMCT32, DBP={dbp})")
            elif dpsm == 0x13:  # PSMT8 pixel data
                pixel_transfers.append(t)
                print(f"  Transfer at {t['data_offset']}: PIXELS (PSMT8, DBP={dbp})")
            else:
                print(f"  Transfer at {t['data_offset']}: DPSM=0x{dpsm:02x} DBP={dbp}")
                # Could be palette in another format
                if t['data_size'] <= 1024:
                    palette_transfers.append(t)
                else:
                    pixel_transfers.append(t)
        else:
            # No BITBLTBUF info - guess based on size
            if t['data_size'] <= 1024:
                palette_transfers.append(t)
            else:
                pixel_transfers.append(t)

    if not pixel_transfers:
        pixel_transfers = transfers  # Use all as pixel data

    # Concatenate pixel data
    pixel_data = bytearray()
    for t in pixel_transfers:
        chunk = tex[t['data_offset']:t['data_offset'] + t['data_size']]
        pixel_data.extend(chunk)

    print(f"Pixel data: {len(pixel_data)} bytes (need {pixel_count})")

    # Get palette data
    palette_raw = None
    if palette_transfers:
        palette_raw = bytearray()
        for t in palette_transfers:
            chunk = tex[t['data_offset']:t['data_offset'] + t['data_size']]
            palette_raw.extend(chunk)
        print(f"Palette data from transfers: {len(palette_raw)} bytes")
    else:
        # Try palette right after pixel data in the concatenated stream
        if len(all_data) >= pixel_count + pal_size:
            palette_raw = all_data[pixel_count:pixel_count + pal_size]
            print(f"Palette from end of data: {len(palette_raw)} bytes")
        else:
            # Look for palette after the last IMAGE transfer
            last_t = transfers[-1]
            pal_start = last_t['data_offset'] + last_t['data_size']
            if pal_start + pal_size <= len(tex):
                palette_raw = tex[pal_start:pal_start + pal_size]
                print(f"Palette after last transfer: {len(palette_raw)} bytes")

    if palette_raw is None or len(palette_raw) < pal_size:
        print(f"Could not find palette data!")
        # Try with a grayscale palette as fallback
        palette = [(i, i, i, 255) for i in range(256)]
        print("Using grayscale palette as fallback")
    else:
        palette = unswizzle_clut_psmt8(palette_raw)

    # Truncate pixel data to what we need
    if len(pixel_data) > pixel_count:
        pixel_data = pixel_data[:pixel_count]

    img = decode_psmt8_image(pixel_data, palette, width, height)

    out_name = filename.replace('.raw', '.png')
    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"Saved: {out_path}")
    return img


def decode_psmt4_resource(tex, info, transfers, width, height, filename):
    """Decode a PSMT4 resource."""
    pixel_bytes = (width * height) // 2
    pal_size = 16 * 4

    all_data = bytearray()
    for t in transfers:
        chunk = tex[t['data_offset']:t['data_offset'] + t['data_size']]
        all_data.extend(chunk)

    pixel_data = all_data[:pixel_bytes]
    palette_data = all_data[pixel_bytes:pixel_bytes + pal_size]

    colors = []
    for i in range(16):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            a = min(a * 2, 255)
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))

    img = Image.new('RGBA', (width, height))
    pixels_out = []
    for i in range(width * height):
        byte_idx = i // 2
        if byte_idx < len(pixel_data):
            if i % 2 == 0:
                idx = pixel_data[byte_idx] & 0x0F
            else:
                idx = (pixel_data[byte_idx] >> 4) & 0x0F
            pixels_out.append(colors[idx])
        else:
            pixels_out.append((0, 0, 0, 0))
    img.putdata(pixels_out)

    out_name = filename.replace('.raw', '.png')
    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"Saved: {out_path}")
    return img


def decode_psmct32_resource(tex, info, transfers, width, height, filename):
    """Decode a PSMCT32 (32-bit RGBA) resource."""
    all_data = bytearray()
    for t in transfers:
        chunk = tex[t['data_offset']:t['data_offset'] + t['data_size']]
        all_data.extend(chunk)

    img = Image.new('RGBA', (width, height))
    pixels_out = []
    for i in range(width * height):
        off = i * 4
        if off + 3 < len(all_data):
            r, g, b, a = all_data[off], all_data[off+1], all_data[off+2], all_data[off+3]
            a = min(a * 2, 255)
            pixels_out.append((r, g, b, a))
        else:
            pixels_out.append((0, 0, 0, 0))
    img.putdata(pixels_out)

    out_name = filename.replace('.raw', '.png')
    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"Saved: {out_path}")
    return img


def try_bruteforce(tex, info, filename):
    """Try to decode texture by brute-force scanning for pixel data."""
    psm = info.get('psm', info.get('dpsm', 0x13))
    width = info.get('tex_w', info.get('trx_width', 512))
    height = info.get('tex_h', info.get('trx_height', 64))

    print(f"Brute force: PSM=0x{psm:02x}, {width}x{height}")

    if psm == 0x13:  # PSMT8
        pixel_count = width * height
        pal_size = 256 * 4

        # Scan for where actual pixel/palette data might be
        # Skip the GIF tag headers and find the raw data
        # Look for the data after all GIF tags
        # Try starting from different offsets

        # First, let's find all the data by scanning quadwords and extracting
        # non-header data
        # Actually let's re-parse more carefully
        # The PACKED GIF with NLOOP=5634 NREG=16 is suspicious - that's huge
        # Maybe it's actually the pixel data stored as PACKED A+D writes?

        # For R2119: total tex = 34800 bytes
        # After 16-byte sub-header, 34800 bytes of GS packet
        # Need 512*64 = 32768 pixel bytes + 1024 palette = 33792
        # That leaves 34800 - 33792 = 1008 bytes for headers

        # Let me scan through looking for BITBLTBUF/TRXREG/TRXDIR writes
        # then find where the IMAGE data actually starts

        # Re-walk more carefully
        i = 0
        max_qw = len(tex) // 16
        found_image_data = []

        while i < max_qw:
            lo = struct.unpack_from('<Q', tex, i * 16)[0]
            hi = struct.unpack_from('<Q', tex, i * 16 + 8)[0]

            nloop = lo & 0x7FFF
            flg = (lo >> 46) & 3
            nreg = (lo >> 60) & 0xF
            if nreg == 0:
                nreg = 16

            # Check if this QW could be a valid GIF tag
            # For IMAGE mode: FLG=2, NLOOP>0
            if flg == 2 and nloop > 0:
                data_start = (i + 1) * 16
                data_size = nloop * 16
                found_image_data.append((data_start, data_size))
                print(f"  Found IMAGE at QW[{i}]: offset={data_start}, size={data_size}")
                i += 1 + nloop
            elif flg == 0 and nloop > 0:
                # PACKED mode
                total_qw = nloop * nreg
                if total_qw > 100 and total_qw + i + 1 > max_qw:
                    # This "GIF tag" would go past the end of data
                    # Probably not actually a GIF tag - raw data?
                    print(f"  QW[{i}]: Suspicious PACKED tag (nloop={nloop}, nreg={nreg}, total={total_qw})")
                    print(f"    Would need {total_qw} QWs but only {max_qw - i - 1} remain")
                    # Just skip to next QW
                    i += 1
                else:
                    print(f"  QW[{i}]: PACKED nloop={nloop} nreg={nreg}")
                    # Parse A+D writes
                    for li in range(nloop):
                        for ri in range(nreg):
                            qi = i + 1 + li * nreg + ri
                            if qi < max_qw:
                                d_lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                                d_hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
                                reg = d_hi & 0xFF
                                if reg in (0x50, 0x51, 0x52, 0x53):
                                    rn = GS_REG_NAMES.get(reg, '?')
                                    print(f"    [{qi}] {rn}: 0x{d_lo:016x}")
                                    if reg == 0x52:
                                        w = d_lo & 0xFFF
                                        h = (d_lo >> 32) & 0xFFF
                                        print(f"      TRXREG: {w}x{h}")
                    i += 1 + total_qw
            else:
                i += 1

        if found_image_data:
            print(f"Found {len(found_image_data)} IMAGE blocks")
            all_pixels = bytearray()
            for offset, size in found_image_data:
                all_pixels.extend(tex[offset:offset+size])
            print(f"Total pixel data: {len(all_pixels)} bytes, need {pixel_count + pal_size}")

            if len(all_pixels) >= pixel_count + pal_size:
                pixels = all_pixels[:pixel_count]
                pal_raw = all_pixels[pixel_count:pixel_count + pal_size]
                palette = unswizzle_clut_psmt8(pal_raw)
                img = decode_psmt8_image(pixels, palette, width, height)
                out_path = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
                img.save(out_path)
                print(f"Saved: {out_path}")
                return img
            elif len(all_pixels) >= pixel_count:
                # Palette might be elsewhere
                pixels = all_pixels[:pixel_count]
                palette = [(i, i, i, 255) for i in range(256)]
                img = decode_psmt8_image(pixels, palette, width, height)
                out_path = os.path.join(TEX_DIR, filename.replace('.raw', '_grayscale.png'))
                img.save(out_path)
                print(f"Saved (grayscale): {out_path}")
                return img

    print("Brute force failed!")
    return None


if __name__ == '__main__':
    files = [
        'R2118_tavern_background.raw',
        'R2119_tavern_buttons_1.raw',
        'R2120_tavern_buttons_2.raw',
        'R2121_guild_background.raw',
        'R2122_guild_buttons.raw',
        'R2124_menu_overlay.raw',
    ]
    for f in files:
        process_file(f)
