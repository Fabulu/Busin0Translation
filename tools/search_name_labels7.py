#!/usr/bin/env python3
"""Search for name entry labels - phase 7.
Key insight: The name entry uses its OWN glyph ID system (IDs 1193+).
The tab labels are likely part of this same system, stored as these
high glyph IDs pointing into a UI font atlas.

The structs at 0x3C9730 etc have format:
  u16 zero, u16 glyph_id, u16 zero, u16 glyph_id, u16 flag(0/1), u16 glyph_id, [padding]

These are the GRID CELLS. The labels (tabs/buttons) would be separate
but similar structures.

Let's look at what comes AFTER the last grid data, and also look
at the data that PRECEDES the first pointer table.
Also, let's look for the actual font atlas that maps these 1193+ IDs.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Let's scan the region AFTER the kana paired tables end
# Last seen paired table entry was around 0x3CABFE
print("=== Region 0x3CAC00-0x3CAE00 as LE uint16 (non-zero) ===")
for off in range(0x3CAC00, 0x3CAE00, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# And what comes BEFORE the first pointer table at 0x3C94F0
# Let's check 0x3C9400-0x3C9500
print("\n=== Region 0x3C9400-0x3C9500 as LE uint16 (non-zero) ===")
for off in range(0x3C9400, 0x3C9500, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# And 0x3C9300-0x3C9400
print("\n=== Region 0x3C9300-0x3C9400 as LE uint16 (non-zero) ===")
for off in range(0x3C9300, 0x3C9400, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# What if the labels reference specific glyph IDs that are
# part of the 1193-1566 range? E.g. if glyph 1283 = 決定 label?
# Let's check: glyph 1283 appeared at 0x3CA962 in a paired entry
# In the name entry screen, these might be BUTTON glyphs
# rather than individual character glyphs.

# Let's also look for the grid layout descriptor
# There might be a struct like:
# { num_rows, num_cols, glyph_id_array_ptr, num_tabs, tab_array_ptr }
# Check what references our pointer table at VA 0x4C99B0
ptr_table_va = 0x4C99B0  # VA of the first pointer in the table
print("\n=== Looking for references to VA 0x%08X in data section ===" % ptr_table_va)
# Search for this VA as LE u32
target = struct.pack('<I', ptr_table_va)
pos = 0
while True:
    pos = exe.find(target, pos)
    if pos < 0:
        break
    print("  Found at file offset 0x%06X" % pos)
    # Show context
    for i in range(-4, 8):
        o = pos + i * 4
        if 0 <= o < len(exe) - 3:
            v = struct.unpack_from('<I', exe, o)[0]
            m = ' <--' if i == 0 else ''
            print("    0x%06X: 0x%08X (%d)%s" % (o, v, v, m))
    pos += 1

# Also search for the alphanumeric grid VA (file 0x3CA690 -> VA 0x4CA610)
alnum_va = 0x3CA690 - 0x80 + 0x100000
print("\n=== Looking for references to alphanumeric grid VA 0x%08X ===" % alnum_va)
target2 = struct.pack('<I', alnum_va)
pos = 0
while True:
    pos = exe.find(target2, pos)
    if pos < 0:
        break
    print("  Found at file offset 0x%06X" % pos)
    for i in range(-4, 8):
        o = pos + i * 4
        if 0 <= o < len(exe) - 3:
            v = struct.unpack_from('<I', exe, o)[0]
            m = ' <--' if i == 0 else ''
            print("    0x%06X: 0x%08X (%d)%s" % (o, v, v, m))
    pos += 1
