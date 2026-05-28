#!/usr/bin/env python3
"""Search for name entry labels - phase 11.
The kana char structs have format: 0, glyph_id, 0, glyph_id, flag, 0, glyph_id, 0
(8 bytes per entry, at 0x20 stride).

These glyph IDs (1193+) reference a DEDICATED name-entry font.
The font glyphs themselves must be stored as texture data somewhere.

The pointer tables at:
- 0x3C9314: pairs with value 76 (0x4C) -> VA page references
- 0x3C93A0: pairs with value 47 (0x2F) -> different VA page
- 0x3C9400: pairs with value 47 (0x2F)
- 0x3C9600: pairs with value 47 (0x2F)

These (low16, high16) = 32-bit VA addresses pointing to font glyph
bitmap data in memory. The glyphs are rendered from these bitmaps.

For the TAB LABELS, they would be larger bitmaps (multi-character labels
rendered as single sprites). Let's look for:
1. References with unusual sizes (larger than single glyphs)
2. The actual code that renders the tab labels
3. Any string table or label definition table

Let's search for the pointer to the mode index table (0x3CA770).
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# VA of the mode index table at file 0x3CA770
mode_table_va = 0x3CA770 - 0x80 + 0x100000  # = 0x4CA6F0
print("Mode index table VA: 0x%08X" % mode_table_va)

# Search for this VA as LE uint32 in the EXE
target = struct.pack('<I', mode_table_va)
pos = 0
print("Searching for references to mode table VA...")
while True:
    pos = exe.find(target, pos)
    if pos < 0:
        break
    print("  Found at 0x%06X" % pos)
    # Dump context as uint32
    for i in range(-8, 8):
        o = pos + i*4
        if 0 <= o < len(exe) - 3:
            v = struct.unpack_from('<I', exe, o)[0]
            m = ' <--' if i == 0 else ''
            print("    0x%06X: 0x%08X%s" % (o, v, m))
    pos += 1

# Also search for the alphanumeric grid table VA (0x3CA690 -> VA)
alnum_va = 0x3CA690 - 0x80 + 0x100000
print("\nAlphanumeric grid VA: 0x%08X" % alnum_va)
target2 = struct.pack('<I', alnum_va)
pos = 0
while True:
    pos = exe.find(target2, pos)
    if pos < 0:
        break
    print("  Found at 0x%06X" % pos)
    for i in range(-8, 8):
        o = pos + i*4
        if 0 <= o < len(exe) - 3:
            v = struct.unpack_from('<I', exe, o)[0]
            m = ' <--' if i == 0 else ''
            print("    0x%06X: 0x%08X%s" % (o, v, m))
    pos += 1

# Search for the preset name VA (エミーリア at 0x3C93B0 -> VA)
name_va = 0x3C93B0 - 0x80 + 0x100000
print("\nPreset name VA: 0x%08X" % name_va)
target3 = struct.pack('<I', name_va)
pos = 0
while True:
    pos = exe.find(target3, pos)
    if pos < 0:
        break
    print("  Found at 0x%06X" % pos)
    for i in range(-8, 8):
        o = pos + i*4
        if 0 <= o < len(exe) - 3:
            v = struct.unpack_from('<I', exe, o)[0]
            m = ' <--' if i == 0 else ''
            print("    0x%06X: 0x%08X%s" % (o, v, m))
    pos += 1

# Search for the first glyph struct pointer table VA
struct_ptrs_va = 0x3C99B0 - 0x80 + 0x100000
print("\nGlyph struct pointer table VA: 0x%08X" % struct_ptrs_va)
target4 = struct.pack('<I', struct_ptrs_va)
pos = 0
while True:
    pos = exe.find(target4, pos)
    if pos < 0:
        break
    print("  Found at 0x%06X" % pos)
    for i in range(-8, 8):
        o = pos + i*4
        if 0 <= o < len(exe) - 3:
            v = struct.unpack_from('<I', exe, o)[0]
            m = ' <--' if i == 0 else ''
            print("    0x%06X: 0x%08X%s" % (o, v, m))
    pos += 1

# Search VA of kana grid entry 0 (VA=0x4C96B0, first ptr in the table at 0x3C99B8)
print("\nSearching for VA 0x004C96B0 (first kana grid entry)...")
target5 = struct.pack('<I', 0x004C96B0)
pos = 0
while True:
    pos = exe.find(target5, pos)
    if pos < 0:
        break
    if pos != 0x3C99B8:  # Skip the pointer table itself
        print("  Found at 0x%06X" % pos)
    pos += 1
