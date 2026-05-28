#!/usr/bin/env python3
"""Search for name entry screen labels in the PS2 EXE."""
import struct, json, sys

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Reverse map: char -> glyph ID
rev = {}
for gid, ch in gmap.items():
    rev[ch] = int(gid)

# Target labels
targets = ['カ','ナ','か','な','英','数','記','号','決','定','男','名','女']
print("=== Glyph IDs for target characters ===")
for ch in targets:
    if ch in rev:
        print("  %s = %d (0x%04X)" % (ch, rev[ch], rev[ch]))
    else:
        print("  %s = NOT IN MAP" % ch)

# Search for カナ (198, 213) as BE uint16 pair
print("\n=== Searching for カナ (198, 213) as BE uint16 ===")
pat = struct.pack('>HH', 198, 213)
pos = 0
while True:
    pos = exe.find(pat, pos)
    if pos < 0:
        break
    print("  Hit at 0x%06X" % pos)
    # Context: 16 words centered on hit
    for i in range(-8, 8):
        off = pos + i * 2
        if 0 <= off < len(exe) - 1:
            v = struct.unpack_from('>H', exe, off)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            marker = " <--" if i == 0 else ""
            print("    0x%06X: %5d  %s%s" % (off, v, ch, marker))
    pos += 2

# Search for かな (117, 132) as BE uint16 pair
print("\n=== Searching for かな (117, 132) as BE uint16 ===")
pat2 = struct.pack('>HH', 117, 132)
pos = 0
while True:
    pos = exe.find(pat2, pos)
    if pos < 0:
        break
    print("  Hit at 0x%06X" % pos)
    for i in range(-4, 8):
        off = pos + i * 2
        if 0 <= off < len(exe) - 1:
            v = struct.unpack_from('>H', exe, off)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            marker = " <--" if i == 0 else ""
            print("    0x%06X: %5d  %s%s" % (off, v, ch, marker))
    pos += 2

# Search for 決 (737) followed by anything within 4 bytes
print("\n=== Searching for 決 (737) as BE uint16 ===")
pat3 = struct.pack('>H', 737)
pos = 0
count = 0
while count < 20:
    pos = exe.find(pat3, pos)
    if pos < 0:
        break
    # Check if even-aligned
    v_next = struct.unpack_from('>H', exe, pos + 2)[0] if pos + 3 < len(exe) else 0
    ch_next = gmap.get(str(v_next), '[%d]' % v_next)
    print("  0x%06X: 決 + %s(%d)" % (pos, ch_next, v_next))
    pos += 2
    count += 1

# Search for 男名 (518, 713) as BE uint16
print("\n=== Searching for 男名 (518, 713) as BE uint16 ===")
pat4 = struct.pack('>HH', 518, 713)
pos = 0
while True:
    pos = exe.find(pat4, pos)
    if pos < 0:
        break
    print("  Hit at 0x%06X" % pos)
    for i in range(-4, 8):
        off = pos + i * 2
        if 0 <= off < len(exe) - 1:
            v = struct.unpack_from('>H', exe, off)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            print("    0x%06X: %5d  %s" % (off, v, ch))
    pos += 2

# Search for 女名 (418, 713) as BE uint16
print("\n=== Searching for 女名 (418, 713) as BE uint16 ===")
pat5 = struct.pack('>HH', 418, 713)
pos = 0
while True:
    pos = exe.find(pat5, pos)
    if pos < 0:
        break
    print("  Hit at 0x%06X" % pos)
    for i in range(-4, 8):
        off = pos + i * 2
        if 0 <= off < len(exe) - 1:
            v = struct.unpack_from('>H', exe, off)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            print("    0x%06X: %5d  %s" % (off, v, ch))
    pos += 2

# Broader search: dump the region around the known kana grids
# The grids start at 0x3C99B8. Look backwards for labels.
print("\n=== Dump 0x3C9800-0x3C99C0 (before kana grids) ===")
for off in range(0x3C9800, 0x3C99C0, 2):
    v = struct.unpack_from('>H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# Also try: the labels might be stored as Shift-JIS strings, not glyph IDs
print("\n=== Searching for SJIS カナ near 0x3C9000-0x3CB000 ===")
sjis_kana = 'カナ'.encode('shift_jis')
sjis_kana2 = 'かな'.encode('shift_jis')
sjis_eisu = '英数'.encode('shift_jis')
sjis_kigo = '記号'.encode('shift_jis')
sjis_kettei = '決定'.encode('shift_jis')
sjis_otoko = '男名'.encode('shift_jis')
sjis_onna = '女名'.encode('shift_jis')

for label, pat in [('カナ', sjis_kana), ('かな', sjis_kana2), ('英数', sjis_eisu),
                    ('記号', sjis_kigo), ('決定', sjis_kettei), ('男名', sjis_otoko), ('女名', sjis_onna)]:
    pos = 0
    hits = []
    while True:
        pos = exe.find(pat, pos)
        if pos < 0:
            break
        hits.append(pos)
        pos += 1
    if hits:
        print("  %s SJIS: %s" % (label, ', '.join('0x%06X' % h for h in hits)))
    else:
        print("  %s SJIS: not found" % label)
