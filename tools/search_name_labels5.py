#!/usr/bin/env python3
"""Search for name entry labels - phase 5.
Key findings so far:
- Kana grids at 0x3C99B8 are pointer tables -> structs with glyph IDs 1193+
- Alphanumeric grid at 0x3CA690 has glyph IDs 0-55 as LE uint16
- No SJIS strings found for ANY tab labels (カナ, かな, 英数, 記号, 決定, 男名, 女名)
- Labels must be pre-rendered textures OR generated from glyph IDs in code

Let's:
1. Dump the full region around the grids to find ALL tables
2. Check what immediately follows the alphanumeric grid
3. Look for small glyph-ID arrays that could be the labels
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Reverse map
rev = {}
for gid, ch in gmap.items():
    rev[ch] = int(gid)

# Let's dump the full structure from 0x3CA680 onwards
print("=== Full dump 0x3CA680-0x3CA900 as LE uint16 ===")
for off in range(0x3CA680, 0x3CA900, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0:
        ch = '_'
    elif v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# Also check: where does each grid table start?
# Look for more pointer arrays
print("\n=== Looking for pointer arrays (4-byte aligned LE u32 in VA range 0x004C0000-0x004D0000) ===")
for off in range(0x3C9500, 0x3CA800, 4):
    v = struct.unpack_from('<I', exe, off)[0]
    if 0x004C0000 <= v <= 0x004D0000:
        foff = v - 0x100000 + 0x80
        print("  0x%06X: VA=0x%08X -> file=0x%06X" % (off, v, foff))
