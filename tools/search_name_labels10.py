#!/usr/bin/env python3
"""Search for name entry labels - phase 10.
CONFIRMED: Labels are NOT glyph-ID-based text anywhere in the EXE.
They must be pre-rendered texture images.

Let's check:
1. The pointer tables at 0x3C9600 had values paired with 47 (0x002F)
   and 0x3C9314 had values paired with 76 (0x004C).
   These look like (offset, page/bank) pairs pointing into a texture.
   If page 47 and 76 are texture pages, the labels are baked into those textures.

2. Let's check the struct at 0x3C99B0 more carefully. The 20 pointers at
   0x3C99B8 point to 0x20-byte structs containing glyph IDs 1193-1214.
   These IDs are from a DIFFERENT font system (not msg_glyph_map).

3. The table at 0x3CA770: {0, 2, 1, FFFF, 4, FFFF, 5, 6, 7, 8, 9, 10}
   This is likely an INDEX table mapping tab positions to mode IDs.

4. Let's look at the alphanumeric grid at 0x3CA690 more carefully.
   Glyph IDs 0-55 are sequential - this might be a DIFFERENT font system too,
   where 0=space, 1-5=symbols, 6-31=more symbols, 32=space, 33=A, etc.
   This matches ASCII-0x20 mapping! So 33='A', 34='B', etc.

5. The real question: where are the LABEL TEXTURES?
   Let's look for texture coordinate data or sprite definitions
   near the grid data.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# The alphanumeric grid uses IDs 0-55 which map perfectly to ASCII:
# 0=space/null, 1=!, 2=", ... 33=A, 34=B, ... 55=W
# This is glyph_id = ASCII_code - 0x20 (the standard printable ASCII offset)
# So this is a simple ASCII-based system for the name entry.

# The symbol/alphanumeric grid at 0x3CA690:
print("=== Alphanumeric grid decoded as ASCII-0x20 ===")
for off in range(0x3CA690, 0x3CA770, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 60:
        ch = '<blank>'
    elif v == 0:
        ch = '<null>'
    elif 0 <= v <= 94:
        ch = chr(v + 0x20)
    else:
        ch = '[%d]' % v
    if off % 24 == 0x3CA690 % 24:
        print()
    print("  0x%06X: %3d  %s" % (off, v, ch), end='')
print()

# Now let's look at the INDEX table at 0x3CA770 in context
# The data at 0x3CA770-0x3CA790 was:
# 0, 2, 1, FFFF, 4, FFFF, 5, 6, 7, 8, 9, 10
# These might be: tab/button definitions
# Let's reinterpret as 32-bit LE values
print("\n=== Region 0x3CA770-0x3CA7A0 as LE uint32 ===")
for off in range(0x3CA770, 0x3CA7A0, 4):
    v = struct.unpack_from('<I', exe, off)[0]
    print("  0x%06X: 0x%08X (%d)" % (off, v, v))

# Let's look at the surrounding area for any texture/sprite descriptors
# A PS2 sprite descriptor might contain: x, y, width, height, texture_page, u, v
# These would typically be small values (<512)
print("\n=== Looking at 0x3CAE00-0x3CB000 for sprite data ===")
for off in range(0x3CAE00, 0x3CB000, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '')
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# Let's also look at what data comes after the last kana table
# The paired glyph tables end around 0x3CADE0
print("\n=== Region 0x3CAE00-0x3CB200 raw hex ===")
for off in range(0x3CAE00, 0x3CB200, 32):
    raw = exe[off:off+32]
    # Check if non-zero
    if raw == b'\x00' * 32:
        continue
    print("  0x%06X: %s" % (off, raw.hex()))
