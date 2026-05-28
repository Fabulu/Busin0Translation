#!/usr/bin/env python3
"""PS2 PSMT8 unswizzle using the PCSX2/ps2dev algorithm.

Based on the GS pixel address calculation from PCSX2.
The key insight is that for PSMT8, the GS uses a specific page/block/column
addressing scheme. When data is uploaded via IMAGE (TRXDIR=0), the GS takes
linear data and swizzles it into its internal format. But if the raw file
contains data already in GS-internal format, we need to reverse the swizzle.

However, if the game uploads linear data via IMAGE mode, the raw file data
IS linear and no unswizzle is needed for display.

The distortion we see might be from a different cause - let's investigate.
"""
import os
import struct
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


def read_texture_params(tex):
    """Read texture parameters from the 192-byte header."""
    # The header contains register writes. Let me find TEX0 data.
    for qi in range(12):
        lo = struct.unpack_from('<Q', tex, qi * 16)[0]
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
        reg = hi & 0xFF
        if reg == 0x06:  # TEX0
            psm = (lo >> 20) & 0x3F
            tw = (lo >> 26) & 0xF
            th = (lo >> 30) & 0xF
            tbw = (lo >> 14) & 0x3F  # in 64-pixel units
            return {
                'psm': psm,
                'width': 1 << tw,
                'height': 1 << th,
                'tbw': tbw * 64,  # buffer width in pixels
            }
    return None


def main():
    # First, let's really understand R2119 by looking at the actual pixel patterns
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    pixel_count = w * h
    pal_size = 1024

    params = read_texture_params(tex)
    print(f"R2119 params: {params}")

    pixel_data = tex[192:192 + pixel_count]
    pal_data = tex[192 + pixel_count:192 + pixel_count + pal_size]
    palette = unswizzle_clut_psmt8(pal_data)

    # Let me look at a region where I know there should be text
    # and check for horizontal displacement between rows

    # Find first non-FF pixel to locate the text area
    text_start_y = 0
    for y in range(h):
        for x in range(w):
            if pixel_data[y * w + x] != 0xFF:
                text_start_y = y
                break
        if text_start_y > 0:
            break

    print(f"First non-white pixel at y={text_start_y}")

    # Show a few rows around the text
    for y in range(max(0, text_start_y - 2), min(h, text_start_y + 10)):
        row = pixel_data[y * w:(y + 1) * w]
        # Find first and last non-FF positions
        first_non_ff = -1
        last_non_ff = -1
        for x in range(w):
            if row[x] != 0xFF:
                if first_non_ff < 0:
                    first_non_ff = x
                last_non_ff = x
        if first_non_ff >= 0:
            print(f"  Row {y:2d}: first_non_ff={first_non_ff}, last_non_ff={last_non_ff}, "
                  f"pixels[{first_non_ff}..{min(first_non_ff+20,w)}]: "
                  f"{row[first_non_ff:first_non_ff+20].hex()}")
        else:
            print(f"  Row {y:2d}: all 0xFF")

    # KEY INSIGHT: Let me check if the buffer width (TBW) differs from texture width
    # TBW from TEX0 register tells us the actual memory layout width
    # If TBW > width, there's padding between rows

    tbw = params.get('tbw', w) if params else w
    print(f"\nBuffer width (TBW): {tbw}, Texture width: {w}")

    if tbw != w:
        # Try decoding with TBW as stride
        print(f"Decoding with stride={tbw} instead of {w}")
        output = bytearray(w * h)
        for y in range(h):
            src_off = y * tbw
            for x in range(w):
                if src_off + x < len(pixel_data):
                    output[y * w + x] = pixel_data[src_off + x]
        img = Image.new('RGBA', (w, h))
        pix_out = [palette[output[i]] for i in range(w * h)]
        img.putdata(pix_out)
        out_path = os.path.join(TEX_DIR, f'R2119_tbw{tbw}.png')
        img.save(out_path)
        print(f"Saved: {out_path}")

    # Also for R2118
    print("\n" + "="*60)
    data2 = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex2 = data2[16:]
    params2 = read_texture_params(tex2)
    print(f"R2118 params: {params2}")

    w2, h2 = 512, 512
    pixel_count2 = w2 * h2
    pixel_data2 = tex2[192:192 + pixel_count2]
    pal_data2 = tex2[192 + pixel_count2:192 + pixel_count2 + pal_size]
    palette2 = unswizzle_clut_psmt8(pal_data2)

    tbw2 = params2.get('tbw', w2) if params2 else w2
    print(f"Buffer width (TBW): {tbw2}, Texture width: {w2}")

    if tbw2 != w2:
        print(f"Decoding with stride={tbw2}")
        actual_data_needed = tbw2 * h2
        all_data = tex2[192:192 + actual_data_needed]
        print(f"Need {actual_data_needed} bytes for {tbw2}x{h2}, have {len(all_data)}")

        output2 = bytearray(w2 * h2)
        for y in range(h2):
            src_off = y * tbw2
            for x in range(w2):
                if src_off + x < len(all_data):
                    output2[y * w2 + x] = all_data[src_off + x]
        img2 = Image.new('RGBA', (w2, h2))
        pix_out2 = [palette2[output2[i]] for i in range(w2 * h2)]
        img2.putdata(pix_out2)
        out_path2 = os.path.join(TEX_DIR, f'R2118_tbw{tbw2}.png')
        img2.save(out_path2)
        print(f"Saved: {out_path2}")

    # Now let me also check: what if the header is NOT 192 bytes but something else?
    # The sub-header says payload = 263360 bytes starting at offset 16
    # So meaningful data: bytes 16 to 16+263360-1 = bytes 16..263375

    # What if the "header" isn't a fixed 192 bytes but has a variable size?
    # The first QW[0] is a GIF tag with NLOOP=1 NREG=16 (register writes QW[1-16])
    # After that, QW[17] should be the next GIF tag.

    # In R2118: QW[17] lo = (from earlier debug) -> parsed as IMAGE nloop=642 flg=2
    # But we showed that this might just be pixel data that happens to parse as IMAGE

    # Actually wait - the initial bytes of pixel data for R2118 are 0x82828282...
    # And QW[12-16] are also 0x82828282... So pixel data starts at QW[12].

    # For the GIF tag at QW[0] NLOOP=1 NREG=16:
    # This means 1 loop of 16 packed-mode register writes
    # QW[1-16] are the register data
    # But QW[12-16] = 0xFFFF... (R2119) or 0x8282... (R2118)
    # These register writes go to register 0xFF or 0x82 which don't exist
    # They're effectively NOPs

    # So the GIF header is 17 QWs (272 bytes) but the last 5 QWs (QW[12-16])
    # are "register writes" that happen to contain pixel data values
    # After the header at QW[17], what follows?

    # If QW[17] IS actually a real GIF IMAGE tag (and not just pixel data):
    # QW[17] lo=0x8282828282828282 -> flg=2 (IMAGE), nloop=642
    # nloop=642 -> 642 QWs = 10272 bytes of pixel data
    # Then QW[660] next tag, etc.

    # ALTERNATE THEORY: The GIF IMAGE tags are real!
    # The pixel data is uploaded via multiple GIF IMAGE transfers.
    # Each transfer uploads a strip of the texture.
    # The strips fill the GS buffer at positions defined by TRXPOS.
    # The GS buffer has width TBW (in 64-pixel units from BITBLTBUF).

    # BUT the TRXPOS/TRXREG are set in the header (QW[0-16]) once
    # and then all IMAGE transfers use the same settings.
    # Each IMAGE transfer appends to the GS buffer continuously.

    # If TBW=512 (8 * 64), the IMAGE data fills the buffer left-to-right,
    # top-to-bottom, 512 pixels per row. That would be linear layout!

    # Let me check: sub-header payload = 263360
    # Subtract header: 263360 - 272 = 263088 (data after header)
    # But GIF tag overhead: how many IMAGE tags are there?
    # If 26 IMAGE tags: 26 * 16 = 416 bytes of tags
    # Pixel data = 263088 - 416 = 262672 bytes
    # But we need 262144 + 1024 = 263168 bytes
    # 262672 < 263168 -> not enough!

    # With header=192: 263360 - 192 = 263168 -> exact for pixel+palette
    # With header=272: 263360 - 272 = 263088 -> not enough even without GIF tags
    # With header=272 and NO GIF tags: 263088 >= 263168? NO, 263088 < 263168

    # So the header MUST be 192 bytes for the math to work.
    # This means QW[12-16] are part of the pixel data, not part of the header!
    # And there are NO GIF IMAGE tags in the pixel data.

    # The "GIF tags" I was finding were just pixel data that happened to
    # match the IMAGE tag pattern.

    # CONCLUSION: The data layout is:
    # 16 bytes: sub-header (type, payload_size, offset, pad)
    # 192 bytes: GS config (12 QWs of register data)
    # 262144 bytes: raw linear pixel data (PSMT8, 512x512 or 512x64)
    # 1024 bytes: raw palette data (256 RGBA entries)
    # remainder: padding to file size

    # And the pixel data is ALREADY LINEAR (not GS-swizzled).
    # The visual distortion must be from something else.

    # Let me verify by checking if the linear decode of R2119 is correct
    # The pixels at rows 10-19 are all 0xFF (white/transparent)
    # The text should be around rows 20-50 or so

    # Let me find exact text location
    for y in range(h):
        row = pixel_data[y * w:(y + 1) * w]
        non_ff = sum(1 for b in row if b != 0xFF)
        if non_ff > 10:
            print(f"R2119 row {y}: {non_ff} non-white pixels")

    # The image at R2119_noswizzle.png actually looks correct!
    # The "distortion" I was seeing was just from viewing it at small scale.
    # Let me save a clean version with proper naming.

    img_clean = Image.new('RGBA', (w, h))
    pix_clean = [palette[pixel_data[i]] for i in range(w * h)]
    img_clean.putdata(pix_clean)
    out_clean = os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.png')
    img_clean.save(out_clean)
    print(f"\nFinal R2119: {out_clean}")

    # R2118 - the linear version had wider banding which means the issue is
    # likely the buffer width / stride
    # Let me see if TBW differs from 512

    # From the header, TBW = 8 * 64 = 512. So stride = width. Linear should work.
    # But the linear R2118 had visible banding...

    # Let me check if the banding in R2118 is just from the palette
    # Maybe some palette entries are wrong

    print(f"\nR2118 palette check:")
    for i in range(16):
        print(f"  [{i:3d}] = {palette2[i]}")

    # Also save the pixel values histogram
    from collections import Counter
    hist = Counter(pixel_data2[:pixel_count2])
    top_10 = hist.most_common(10)
    print(f"\nR2118 top 10 pixel values:")
    for val, count in top_10:
        print(f"  0x{val:02x}: {count:6d} ({100*count/pixel_count2:.1f}%) -> color {palette2[val]}")


if __name__ == '__main__':
    main()
