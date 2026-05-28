#!/usr/bin/env python3
"""Search for name entry labels - phase 16.
Dump all newly-discovered data regions.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

regions = [
    (0x3C93D0, 0x3C9400, "preset name suffix/extra 0x3C93D0"),
    (0x3C9A28, 0x3C9B00, "tab data 0x3C9A28 (referenced by tab code)"),
    (0x3C9B00, 0x3C9C00, "tab data continued"),
    (0x3C9C00, 0x3C9D00, "grid control 0x3C9C00"),
    (0x3C9D00, 0x3C9E00, "grid control 0x3C9D00 (frequently referenced)"),
]

for start, end, label in regions:
    print("=== %s ===" % label)
    for off in range(start, end, 2):
        v = struct.unpack_from('<H', exe, off)[0]
        if v == 0:
            continue
        ch = gmap.get(str(v), '[%d]' % v)
        if v == 0xFFFF:
            ch = 'FFFF'
        print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))
    print()

# Also dump 0x3C9D48 and 0x3C9D60 regions
print("=== Region 0x3C9D40-0x3C9E00 ===")
for off in range(0x3C9D40, 0x3C9E00, 4):
    v = struct.unpack_from('<I', exe, off)[0]
    if v == 0:
        continue
    # Check if it looks like a VA
    if 0x004C0000 <= v <= 0x004D0000:
        foff = v - 0x100000 + 0x80
        print("  0x%06X: VA 0x%08X -> file 0x%06X" % (off, v, foff))
    else:
        v16a = v & 0xFFFF
        v16b = (v >> 16) & 0xFFFF
        ch_a = gmap.get(str(v16a), '[%d]' % v16a)
        ch_b = gmap.get(str(v16b), '[%d]' % v16b)
        print("  0x%06X: 0x%08X  (%d=%s, %d=%s)" % (off, v, v16a, ch_a, v16b, ch_b))

# Now look at 0x3C9A38 as pointer table (it's at the right offset for kana grid pointers)
print("\n=== 0x3C9A38 as LE uint32 pointer table ===")
for i in range(20):
    off = 0x3C9A38 + i*4
    v = struct.unpack_from('<I', exe, off)[0]
    if v == 0:
        print("  [%d] 0x%06X: 0 (end)" % (i, off))
        break
    if 0x004C0000 <= v <= 0x004D0000:
        foff = v - 0x100000 + 0x80
        print("  [%d] 0x%06X: VA 0x%08X -> file 0x%06X" % (i, off, v, foff))
    else:
        print("  [%d] 0x%06X: 0x%08X" % (i, off, v))
