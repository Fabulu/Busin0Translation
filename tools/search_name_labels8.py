#!/usr/bin/env python3
"""Search for name entry labels - phase 8.
BREAKTHROUGH: Found preset names at 0x3C93B0:
  エミーリア (Emilia) and リュート (Lute)
These are LE uint16 glyph IDs from msg_glyph_map, padded with 0xFFFF.

The tab labels (カナ, かな, etc.) should use the SAME format nearby.
Let's decode the entire region around this systematically.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Decode the region 0x3C9200-0x3C93E0 showing glyph text
print("=== Region 0x3C9200-0x3C93E0 decoded as LE uint16 glyph sequences ===")
for off in range(0x3C9200, 0x3C93E0, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# Also look even earlier: 0x3C9000-0x3C9200
print("\n=== Region 0x3C9000-0x3C9200 decoded as LE uint16 (non-zero) ===")
for off in range(0x3C9000, 0x3C9200, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# And 0x3C8E00-0x3C9000
print("\n=== Region 0x3C8E00-0x3C9000 decoded as LE uint16 (non-zero, recognized glyphs only) ===")
for off in range(0x3C8E00, 0x3C9000, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0 or v == 0xFFFF:
        continue
    if str(v) in gmap:
        ch = gmap[str(v)]
        print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))
