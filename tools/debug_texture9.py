#!/usr/bin/env python3
"""Try treating the entire data after header as raw pixels + palette."""
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


def make_image(pixel_data, palette, width, height, out_path):
    pixel_count = width * height
    img = Image.new('RGBA', (width, height))
    pix_out = []
    for i in range(pixel_count):
        if i < len(pixel_data):
            pix_out.append(palette[pixel_data[i]])
        else:
            pix_out.append((0, 0, 0, 0))
    img.putdata(pix_out)
    img.save(out_path)
    print(f"  Saved: {out_path}")
    return img


def main():
    # ===== R2118 =====
    data = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex = data[16:]
    pixel_count = 512 * 512  # 262144
    pal_size = 1024

    # Theory 1: Everything from QW[17] (offset 272) is raw pixel+palette
    # Total from offset 272: 264176 - 272 = 263904 bytes
    # Need: 262144 + 1024 = 263168
    # Extra: 263904 - 263168 = 736 bytes -> might be padding at end

    print("R2118 - Theory 1: Raw data from offset 272")
    raw_data = tex[272:]
    print(f"  Raw data: {len(raw_data)} bytes")
    pixels = raw_data[:pixel_count]
    pal_raw = raw_data[pixel_count:pixel_count + pal_size]
    print(f"  Palette first 4 colors: {[pal_raw[i*4:i*4+4].hex() for i in range(4)]}")
    palette = unswizzle_clut_psmt8(pal_raw)
    make_image(pixels, palette, 512, 512,
               os.path.join(TEX_DIR, 'R2118_raw272.png'))

    # Theory 2: Everything from QW[12] (offset 192) is raw pixel+palette
    # (header is only 12 QWs since QW[12] might be pixel data)
    # Total from offset 192: 264176 - 192 = 263984 bytes
    # Need: 262144 + 1024 = 263168
    # Extra: 263984 - 263168 = 816 bytes

    print("\nR2118 - Theory 2: Raw data from offset 192")
    raw_data2 = tex[192:]
    pixels2 = raw_data2[:pixel_count]
    pal_raw2 = raw_data2[pixel_count:pixel_count + pal_size]
    print(f"  Palette first 4 colors: {[pal_raw2[i*4:i*4+4].hex() for i in range(4)]}")
    palette2 = unswizzle_clut_psmt8(pal_raw2)
    make_image(pixels2, palette2, 512, 512,
               os.path.join(TEX_DIR, 'R2118_raw192.png'))

    # Theory 3: Header includes first GIF tag at QW[0-16] (272 bytes)
    # Then a GIF tag at QW[17] (16 bytes) - IMAGE tag with nloop=642
    # Then pixel data from QW[18] (offset 288)
    # This means offset 288 onward is raw pixel data
    # But wait - every 10272+16 bytes there's another GIF tag
    # If we DON'T strip them, pixels would be at 288 continuously

    # Actually, let me check: what if the data is NOT a GIF packet
    # but rather the whole thing is a custom format where:
    # offset 0-15: sub-header
    # offset 16-287: texture metadata (registers/config)
    # offset 288: raw pixel data (262144 bytes)
    # offset 288+262144 = 262432: palette (1024 bytes)
    # offset 263456: padding to 264192

    print("\nR2118 - Theory 3: Raw data from offset 288")
    raw_data3 = tex[288:]
    pixels3 = raw_data3[:pixel_count]
    pal_raw3 = raw_data3[pixel_count:pixel_count + pal_size]
    print(f"  Palette first 4 colors: {[pal_raw3[i*4:i*4+4].hex() for i in range(4)]}")
    palette3 = unswizzle_clut_psmt8(pal_raw3)
    make_image(pixels3, palette3, 512, 512,
               os.path.join(TEX_DIR, 'R2118_raw288.png'))

    # Check: how big is the header actually?
    # Sub-header field 1 = payload_size = 263360
    # Sub-header field 2 = offset = 16
    # So payload starts at offset 16 and is 263360 bytes
    # 16 + 263360 = 263376
    # But total file is 264192 -> 264192 - 263376 = 816 bytes after payload?
    # Wait: sub-header is at offset 0 of file, payload at offset 16
    # Payload = 263360 bytes -> file should be 16 + 263360 = 263376 bytes
    # But file is 264192 bytes -> 264192 - 263376 = 816 bytes of padding
    # OR: sub-header says payload is 263360, but the resource is 264192
    # The resource might be padded to a sector boundary

    # payload_size = 263360
    # This includes the GS packet header + pixel data + palette
    # So the actual useful data is bytes 16..16+263360-1 = bytes 16..263375

    print(f"\nPayload boundaries: offset 16 to {16+263360-1} ({263360} bytes)")
    print(f"File size: {len(data)}")
    print(f"Tex size: {len(tex)}")

    # The payload is 263360 bytes of GS data
    # If the first 272 bytes (17 QWs) are header registers:
    # Pixel+palette = 263360 - 272 = 263088
    # But need 263168... that's 80 bytes short!

    # If the first 192 bytes (12 QWs) are header:
    # Pixel+palette = 263360 - 192 = 263168  <-- EXACT MATCH!

    print(f"\nPayload - 192 = {263360 - 192} (needs {pixel_count + pal_size})")
    print(f"Payload - 272 = {263360 - 272}")

    # So the header is 192 bytes (12 QWs), NOT 272 bytes!
    # QW[0-11] = header (192 bytes)
    # QW[12] onward = pixel data (262144 bytes) + palette (1024 bytes)
    # Total payload data = 263168 bytes

    # But QW[12-16] in R2118 = 0x82828282... which is pixel data
    # And QW[0-11] contains the GIF tag + register writes

    # Let me verify: QW[0] GIF tag says NLOOP=1, NREG=16
    # So it uses QW[1-16] as 16 register writes
    # That's 17 QWs (272 bytes) total for the header

    # But 263360 - 272 = 263088, and we need 263168. Off by 80 bytes.
    # That's 5 QWs. Maybe some of QW[12-16] are both header AND data?

    # Actually wait: maybe the header is QW[0] + some PACKED data,
    # followed by a separate GIF tag for IMAGE mode that covers the rest.
    # QW[0] PACKED nloop=1 nreg=16 -> uses QW[1-16]
    # But within those 16 QWs, some might be padding/zero that don't matter

    # Let me look at QW[9-16] again:
    for qi in range(9, 17):
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
        b = tex[qi*16:qi*16+16].hex()
        print(f"  QW[{qi}]: lo={lo:016x} hi={hi:016x} bytes={b}")

    # OK so QW[9] = 4, QW[10-11] = 0, QW[12-16] = 0xFF
    # The register writes at QW[9-11] set PRIM etc.
    # QW[12-16] write to register 0xFF which doesn't exist
    # These are "wasted" register writes - the GIF engine just ignores them

    # So the PACKED block at QW[0] processes QW[1-16] as register writes
    # After that, QW[17] is the next GIF tag, which happens to be an IMAGE tag

    # The correct pixel data layout is:
    # QW[17] = IMAGE GIF tag (nloop=642)
    # QW[18-659] = 642 QWs of pixel data
    # QW[660] = IMAGE GIF tag (nloop=642)
    # QW[661-1302] = pixel data
    # etc.

    # But this gives us the "stripped" version which has banding.
    # The banding suggests my stripping is correct but maybe the
    # pixel data is read COLUMN-WISE or in some other order.

    # WAIT: Let me look at this differently.
    # Each IMAGE transfer of 642 QWs = 10272 bytes.
    # If the texture is 512 pixels wide at 8bpp = 512 bytes per row.
    # 10272 / 512 = 20.0625 rows per strip. That's not an even number!
    # 10272 / 512 = 20 rows + 32 bytes leftover.
    # So each strip is NOT an exact number of rows.
    # This means the data MUST be continuous (the 32 extra bytes
    # are the start of the next row, continued in the next strip).

    # If the strips are continuous, then removing the GIF tags should give
    # correct continuous pixel data. But we see banding...
    # The banding is because every 10272 bytes, there's a 16-byte gap
    # where the GIF tag was. But we're removing those tags!

    # Unless... we're NOT removing them. Let me check.
    # In the current code, I collect data from (qw+1)*16 for nloop*16 bytes.
    # That correctly skips the GIF tag QW.

    # So the collected data should be continuous 262144+1264 bytes.
    # And the palette starts at byte 262144 of that stream.
    # But the palette was all zeros!

    # Hmm, let me check the LAST IMAGE block's data
    # QW[15980] IMAGE nloop=642 (from debug_texture7)
    # Wait, from the latest output it was nloop=530 (8480/16=530)

    # Actually from debug_texture8: QW[15980] nloop = 8480/16 = 530
    # Data size = 8480 bytes
    # cumulative before = 254928
    # 262144 - 254928 = 7216 bytes of pixel remaining
    # So palette starts at byte 7216 within this last IMAGE block
    # Palette data = 8480 - 7216 = 1264 bytes (more than 1024 needed)

    # But the palette was all zeros. Let me check the raw bytes
    # at that position in the actual file.

    # QW[15980]: data starts at (15980+1)*16 = 255696
    # Pixel/palette boundary at: 255696 + 7216 = 262912
    print(f"\nPalette should be at offset {255696 + 7216} in tex data")
    print(f"Palette bytes: {tex[262912:262912+64].hex()}")

    # Alternative: maybe the pixel data layout uses the header size of 192 bytes
    # so pixel start = 192, pixel end = 192 + 262144 = 262336
    # palette at 262336 for 1024 bytes
    print(f"\nWith 192-byte header:")
    print(f"  Palette at {192+262144} = {192+262144}")
    print(f"  Palette bytes: {tex[262336:262336+64].hex()}")

    # Try with offset 192 (12 QW header)
    print("\n=== FINAL ATTEMPT: 192-byte header, raw data ===")
    pixel_start = 192
    pixels_final = tex[pixel_start:pixel_start + pixel_count]
    pal_start = pixel_start + pixel_count
    pal_raw_final = tex[pal_start:pal_start + pal_size]
    print(f"  Palette at offset {pal_start}:")
    print(f"  First 64 bytes: {pal_raw_final[:64].hex()}")
    palette_final = unswizzle_clut_psmt8(pal_raw_final)
    make_image(pixels_final, palette_final, 512, 512,
               os.path.join(TEX_DIR, 'R2118_final192.png'))

    # And grayscale
    palette_gray = [(i, i, i, 255) for i in range(256)]
    make_image(pixels_final, palette_gray, 512, 512,
               os.path.join(TEX_DIR, 'R2118_gray192.png'))


if __name__ == '__main__':
    main()
