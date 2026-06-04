#!/usr/bin/env python3
"""
Zoom into the bottom rows of the EXE font atlas to identify the special characters.
Also check for ISOs from previous wipe tests.
"""
import os, sys, struct, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4, make_rgba_image_4bit

try:
    from PIL import Image
except ImportError:
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
exe_data = open(EXE_PATH, 'rb').read()

# Deswizzle
font_raw = exe_data[0x3D6C10:0x3D6C10 + 8192]
pixels = deswizzle_psmt4(font_raw, 128, 128, bw_psmt4=128, dbw_ct32=64)

# PS2 palette from the EXE
pal_data = exe_data[0x3D8C10:0x3D8C10 + 64]  # first palette (16 colors, 4 bytes each as PS2 RGB555)
palette = bytearray(64)
for i in range(16):
    off = i * 4
    val = struct.unpack_from('<H', pal_data, off)[0]
    r = (val & 0x1F) << 3
    g = ((val >> 5) & 0x1F) << 3
    b = ((val >> 10) & 0x1F) << 3
    a = 128 if val != 0 else 0
    palette[i*4] = r; palette[i*4+1] = g; palette[i*4+2] = b; palette[i*4+3] = a

img = make_rgba_image_4bit(pixels, palette, 128, 128)

# Extract just the bottom rows (rows 48-63 approximately - the last character row)
# The font appears to use 8-pixel tall rows
# Row 0 (y=0-7): !"#$%&'()*+,-./
# Row 1 (y=8-15): 0123456789:;<=>?
# Row 2 (y=16-23): @ABCDEFGHIJKLMNO
# Row 3 (y=24-31): PQRSTUVWXYZ[\]^_
# Row 4 (y=32-39): `abcdefghijklmno
# Row 5 (y=40-47): pqrstuvwxyz{|}
# Row 6 (y=48-55): special chars
# Row 7+ (y=56+): blank

# Zoom into row 6 (y=48-63, the special chars row)
bottom = img.crop((0, 48, 128, 64))
bottom_zoom = bottom.resize((128 * 8, 16 * 8), Image.NEAREST)
out1 = os.path.join(TEX_DIR, "EXE_font_row6_special_8x.png")
bottom_zoom.save(out1)
print(f"Saved special row zoom: {out1}")

# Also save rows 6-7 together
bottom2 = img.crop((0, 48, 128, 72))
bottom2_zoom = bottom2.resize((128 * 8, 24 * 8), Image.NEAREST)
out2 = os.path.join(TEX_DIR, "EXE_font_rows6_7_8x.png")
bottom2_zoom.save(out2)
print(f"Saved rows 6-7 zoom: {out2}")

# Zoom into each individual glyph in row 6
# Glyphs appear to be 8x8 pixels, 16 per row
print("\nRow 6 glyph pixel values (each 8x8):")
for glyph_idx in range(16):
    gx = glyph_idx * 8
    gy = 48
    glyph_pixels = []
    for y in range(gy, gy + 8):
        row = []
        for x in range(gx, gx + 8):
            row.append(pixels[y * 128 + x])
        glyph_pixels.append(row)

    # Check if glyph has any non-zero pixels
    has_content = any(p > 0 for row in glyph_pixels for p in row)
    if has_content:
        print(f"  Glyph {glyph_idx} (x={gx}-{gx+7}):")
        for row in glyph_pixels:
            print(f"    {''.join(f'{p:X}' for p in row)}")

# Also check below row 6 for any more content
print("\n\nChecking rows 56-127 for any non-zero content:")
for y in range(56, 128):
    row_sum = sum(pixels[y * 128 + x] for x in range(128))
    if row_sum > 0:
        print(f"  Row {y}: sum={row_sum}")

# ---- Check for test ISOs ----
print("\n\n=== Checking for previous test ISOs ===")
import datetime
for pattern in ["build/BUSIN0_EN_*.iso", "build/*.iso"]:
    isos = glob.glob(os.path.join(BASE, pattern))
    for iso in sorted(isos):
        size = os.path.getsize(iso)
        mtime = os.path.getmtime(iso)
        dt = datetime.datetime.fromtimestamp(mtime)

        # Check if the EXE section has zeroed font data
        # The EXE is at a specific location in the ISO
        # Let's just report the file info
        print(f"  {os.path.basename(iso)}: {size:,} bytes, modified {dt}")

# ---- Check the current patched EXE in build dir ----
patched_exe = os.path.join(BASE, "build", "SLPM_653.78")
if os.path.exists(patched_exe):
    pdata = open(patched_exe, 'rb').read()
    pfont = pdata[0x3D6C10:0x3D6C10 + 8192]
    nz = sum(1 for b in pfont if b != 0)
    print(f"\n  Build EXE font at 0x3D6C10: {nz} non-zero bytes out of 8192")
    if nz == 0:
        print("  *** FONT DATA IS ALL ZEROS IN BUILD EXE! ***")
else:
    print(f"\n  No patched EXE found at {patched_exe}")

print("\n=== Done ===")
