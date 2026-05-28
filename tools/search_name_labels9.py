#!/usr/bin/env python3
"""Search for name entry labels - phase 9.
The tab labels might use the same glyph-ID-sequence format as the
preset names (エミーリア at 0x3C93B0). But we couldn't find カナ as
a pair because some chars (英, 号, 定) aren't in the glyph map.

Alternative theory: The labels are NOT stored as glyph sequences at all.
They might be pre-rendered into a texture atlas that's part of the
name entry screen's graphics resources.

Let's check:
1. Search the ENTIRE EXE for ANY occurrence of カ (198) followed by ナ (213)
   with potential padding bytes between them
2. Look for the code that draws the name entry tabs
3. Check if there's a resource reference for the name entry screen
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Search for カ(198) with ナ(213) within 16 bytes, any alignment
print("=== Searching for カ(198) near ナ(213) in LE uint16, any stride ===")
for off in range(0x80, len(exe) - 20, 2):
    v1 = struct.unpack_from('<H', exe, off)[0]
    if v1 != 198:
        continue
    # Check next 8 uint16 values for 213
    for d in range(1, 9):
        if off + d*2 + 1 >= len(exe):
            break
        v2 = struct.unpack_from('<H', exe, off + d*2)[0]
        if v2 == 213:
            # Check context to see if it looks like glyph data
            context = []
            for i in range(-2, 10):
                o = off + i*2
                if 0 <= o < len(exe) - 1:
                    v = struct.unpack_from('<H', exe, o)[0]
                    ch = gmap.get(str(v), '[%d]' % v)
                    context.append('%s(%d)' % (ch, v))
            print("  0x%06X: カ at +0, ナ at +%d: %s" % (off, d*2, ' '.join(context)))
            break

# Also search for 男(518) near 名(713)
print("\n=== Searching for 男(518) near 名(713) within 16 bytes ===")
for off in range(0x80, len(exe) - 20, 2):
    v1 = struct.unpack_from('<H', exe, off)[0]
    if v1 != 518:
        continue
    for d in range(1, 9):
        if off + d*2 + 1 >= len(exe):
            break
        v2 = struct.unpack_from('<H', exe, off + d*2)[0]
        if v2 == 713:
            context = []
            for i in range(-2, 10):
                o = off + i*2
                if 0 <= o < len(exe) - 1:
                    v = struct.unpack_from('<H', exe, o)[0]
                    ch = gmap.get(str(v), '[%d]' % v)
                    context.append('%s(%d)' % (ch, v))
            print("  0x%06X: 男 at +0, 名 at +%d: %s" % (off, d*2, ' '.join(context)))
            break

# Search for 女(418) near 名(713)
print("\n=== Searching for 女(418) near 名(713) within 16 bytes ===")
for off in range(0x80, len(exe) - 20, 2):
    v1 = struct.unpack_from('<H', exe, off)[0]
    if v1 != 418:
        continue
    for d in range(1, 9):
        if off + d*2 + 1 >= len(exe):
            break
        v2 = struct.unpack_from('<H', exe, off + d*2)[0]
        if v2 == 713:
            context = []
            for i in range(-2, 10):
                o = off + i*2
                if 0 <= o < len(exe) - 1:
                    v = struct.unpack_from('<H', exe, o)[0]
                    ch = gmap.get(str(v), '[%d]' % v)
                    context.append('%s(%d)' % (ch, v))
            print("  0x%06X: 女 at +0, 名 at +%d: %s" % (off, d*2, ' '.join(context)))
            break

# Search for 決(737) near 記(801) - these would be on the same screen
print("\n=== Searching for 決(737) near 記(801) within 100 bytes ===")
for off in range(0x80, len(exe) - 200, 2):
    v1 = struct.unpack_from('<H', exe, off)[0]
    if v1 != 737:
        continue
    for d in range(1, 51):
        if off + d*2 + 1 >= len(exe):
            break
        v2 = struct.unpack_from('<H', exe, off + d*2)[0]
        if v2 == 801:
            print("  0x%06X: 決 at +0, 記 at +%d" % (off, d*2))
            break
