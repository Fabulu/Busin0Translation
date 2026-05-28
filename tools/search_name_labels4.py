#!/usr/bin/env python3
"""Search for name entry labels - phase 4.
The 0x3C99B8 pointer table points to structs with glyph IDs 1193-1214.
These appear to be the kana character cells (not the grid directly).
The tab labels might be elsewhere.

New approach:
1. Search for Shift-JIS strings throughout the entire EXE
2. Look for the name entry related code/data patterns
3. Check if there are pre-rendered texture references
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# What's the max glyph ID in the map?
max_gid = max(int(k) for k in gmap.keys())
print("Max glyph ID in map: %d" % max_gid)
print("Glyph IDs 1193-1214 are beyond the map (%d entries)" % len(gmap))

# Search for Shift-JIS strings containing our target labels
# Search entire EXE for these SJIS sequences
import codecs

targets_sjis = [
    ('カナ', 'カナ'.encode('shift_jis')),
    ('かな', 'かな'.encode('shift_jis')),
    ('英数', '英数'.encode('shift_jis')),
    ('記号', '記号'.encode('shift_jis')),
    ('決定', '決定'.encode('shift_jis')),
    ('男名', '男名'.encode('shift_jis')),
    ('女名', '女名'.encode('shift_jis')),
    ('名前', '名前'.encode('shift_jis')),
]

print("\n=== Full EXE SJIS search ===")
for label, pat in targets_sjis:
    print("  %s (SJIS %s):" % (label, pat.hex()))
    pos = 0
    while True:
        pos = exe.find(pat, pos)
        if pos < 0:
            break
        # Show context
        ctx_start = max(0, pos - 8)
        ctx_end = min(len(exe), pos + len(pat) + 8)
        ctx = exe[ctx_start:ctx_end]
        print("    0x%06X: %s" % (pos, ctx.hex()))
        # Try to decode surrounding as SJIS
        try:
            s = exe[ctx_start:ctx_end].decode('shift_jis', errors='replace')
            print("    decoded: %s" % s)
        except:
            pass
        pos += 1

# Also search for individual kanji as SJIS
print("\n=== Individual kanji SJIS search ===")
for ch in ['決', '定', '英', '号']:
    try:
        sjis = ch.encode('shift_jis')
        hits = []
        pos = 0
        while len(hits) < 5:
            pos = exe.find(sjis, pos)
            if pos < 0:
                break
            hits.append(pos)
            pos += 1
        if hits:
            print("  %s (%s): %s%s" % (ch, sjis.hex(),
                  ', '.join('0x%06X' % h for h in hits),
                  '...' if len(hits) >= 5 else ''))
        else:
            print("  %s (%s): not found" % (ch, sjis.hex()))
    except:
        print("  %s: encode error" % ch)

# Now let's look at the ACTUAL kana grid data more carefully
# The earlier dump showed glyphs 33-37 (A-E) at 0x3CA6D1 (BE)
# which is 0x3CA6D0 as LE: 0x0021 = 33
# Let's look at that region with different struct interpretation
print("\n=== Region 0x3CA680-0x3CA780 raw hex ===")
for off in range(0x3CA680, 0x3CA780, 16):
    raw = exe[off:off+16]
    print("  0x%06X: %s" % (off, raw.hex()))

# Decode 0x3CA680-0x3CA780 as LE uint16 glyph IDs
print("\n=== Region 0x3CA680-0x3CA780 as LE uint16 glyphs ===")
for off in range(0x3CA680, 0x3CA780, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0 or v == 0xFFFF:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    print("  0x%06X: %5d  %s" % (off, v, ch))
