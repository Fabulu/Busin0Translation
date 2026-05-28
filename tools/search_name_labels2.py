#!/usr/bin/env python3
"""Search for name entry screen labels - phase 2."""
import struct, json, sys

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Check ELF header
if exe[:4] == b'\x7fELF':
    e_entry = struct.unpack_from('<I', exe, 0x18)[0]
    ph_off = struct.unpack_from('<I', exe, 0x1C)[0]
    ph_num = struct.unpack_from('<H', exe, 0x2C)[0]
    print('ELF entry: 0x%08X' % e_entry)
    for i in range(min(ph_num, 4)):
        off = ph_off + i * 32
        p_type = struct.unpack_from('<I', exe, off)[0]
        p_offset = struct.unpack_from('<I', exe, off+4)[0]
        p_vaddr = struct.unpack_from('<I', exe, off+8)[0]
        p_filesz = struct.unpack_from('<I', exe, off+16)[0]
        print('  Seg %d: type=%d off=0x%X vaddr=0x%08X size=0x%X' %
              (i, p_type, p_offset, p_vaddr, p_filesz))

# The grid data is at 0x3C99B8. Let's check what MIPS code references
# addresses near here. The VA would be vaddr + (file_offset - p_offset)
# For typical PS2: vaddr=0x100000, p_offset=0 or small
# Let's compute the VA of the grid data
ph_off_val = struct.unpack_from('<I', exe, 0x1C)[0]
p_offset = struct.unpack_from('<I', exe, ph_off_val+4)[0]
p_vaddr = struct.unpack_from('<I', exe, ph_off_val+8)[0]
va_base = p_vaddr - p_offset

grid_va = va_base + 0x3C99B8
print('\nGrid VA = 0x%08X (file 0x3C99B8)' % grid_va)

# The data at 0x3C9800 (before grids) has structures with stride 0x20
# This looks like an array of structs. Let's interpret as LE instead of BE.
print('\n=== Region 0x3C9800-0x3C99C0 as LE uint16 ===')
for off in range(0x3C9800, 0x3C99C0, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    if off % 0x20 == 0:
        print('  ---')
    print('  0x%06X: %5d (0x%04X)  %s' % (off, v, v, ch))

# Also try LE for kana grids themselves
print('\n=== Region 0x3C99B8-0x3C9A18 as LE uint16 (first grid) ===')
for off in range(0x3C99B8, 0x3C9A18, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    ch = gmap.get(str(v), '[%d]' % v)
    print('  0x%06X: %5d (0x%04X)  %s' % (off, v, v, ch))

# Try searching with LE encoding
print('\n=== LE search for カナ (198, 213) ===')
pat = struct.pack('<HH', 198, 213)
pos = 0
while True:
    pos = exe.find(pat, pos)
    if pos < 0:
        break
    print('  Hit at 0x%06X' % pos)
    for i in range(-4, 8):
        o = pos + i * 2
        if 0 <= o < len(exe) - 1:
            v = struct.unpack_from('<H', exe, o)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            m = ' <--' if i == 0 else ''
            print('    0x%06X: %5d  %s%s' % (o, v, ch, m))
    pos += 2

# LE search for かな (117, 132)
print('\n=== LE search for かな (117, 132) ===')
pat = struct.pack('<HH', 117, 132)
pos = 0
while True:
    pos = exe.find(pat, pos)
    if pos < 0:
        break
    print('  Hit at 0x%06X' % pos)
    for i in range(-4, 8):
        o = pos + i * 2
        if 0 <= o < len(exe) - 1:
            v = struct.unpack_from('<H', exe, o)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            m = ' <--' if i == 0 else ''
            print('    0x%06X: %5d  %s%s' % (o, v, ch, m))
    pos += 2

# LE search for 男名 (518, 713)
print('\n=== LE search for 男名 (518, 713) ===')
pat = struct.pack('<HH', 518, 713)
pos = 0
while True:
    pos = exe.find(pat, pos)
    if pos < 0:
        break
    print('  Hit at 0x%06X' % pos)
    for i in range(-4, 8):
        o = pos + i * 2
        if 0 <= o < len(exe) - 1:
            v = struct.unpack_from('<H', exe, o)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            print('    0x%06X: %5d  %s' % (o, v, ch))
    pos += 2

# LE search for 女名 (418, 713)
print('\n=== LE search for 女名 (418, 713) ===')
pat = struct.pack('<HH', 418, 713)
pos = 0
while True:
    pos = exe.find(pat, pos)
    if pos < 0:
        break
    print('  Hit at 0x%06X' % pos)
    for i in range(-4, 8):
        o = pos + i * 2
        if 0 <= o < len(exe) - 1:
            v = struct.unpack_from('<H', exe, o)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            print('    0x%06X: %5d  %s' % (o, v, ch))
    pos += 2
