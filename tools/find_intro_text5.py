#!/usr/bin/env python3
"""Check if R1193 uses a different glyph numbering than msg_glyph_map."""
import struct
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir("C:/Programmieren/wizardrytranslation")

gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# R1193 M0: first sentence should be
# かつて三十年もの長きにわたってドゥーハン王国を血と恐怖に陥れた戦乱があった。
# Actual glyphs:
m0 = [117, 129, 130, 337, 1186, 684, 146, 136, 404, 118, 133, 155, 127, 191, 130, 257, 217, 193, 136, 551, 156, 1200, 131, 1060, 153, 127, 734, 788, 158, 112, 191, 127, 63]

# Expected text chars:
text = "かつて三十年もの長きにわたってベノアの？を？と？？に？れた戦乱があった。"

# Map:
# か=117 ✓, つ=129 ✓, て=130 ✓
# 三=337 but 337 maps to 中, not 三. So either map is wrong or glyph is different
# Let me check: does gm have 三?
rev = {}
for gid, ch in gm.items():
    rev.setdefault(ch, []).append(int(gid))

# Show the glyph ID to character mapping for the IDs in M0
print("=== R1193 M0 glyphs decoded ===")
expected = list("かつて三十年もの長きにわたってベノアの？を？と？？に？れた戦乱があった。")
for i, g in enumerate(m0):
    ch = gm.get(str(g), f'?({g})')
    exp = expected[i] if i < len(expected) else '?'
    match = '✓' if ch == exp else f'≠ expected {exp}'
    print(f"  [{i:2d}] glyph {g:5d} -> {ch:4s}  {match}")

# Check: what about the full text using R1193 M2?
print("\n=== Full intro text (R1193 M2) ===")
data = open('extracted/packdata_raw/1193_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 24)[0]
sec2 = data[sec2_off:]

# Skip to M2 (past M0 FFFF and M1 FFFF)
pos = 0
for skip in range(2):
    while pos < len(sec2) - 1:
        val = struct.unpack_from('>H', sec2, pos)[0]
        pos += 2
        if val == 0xFFFF:
            break

# Now read M2
gs2 = []
while pos < len(sec2) - 1:
    val = struct.unpack_from('>H', sec2, pos)[0]
    pos += 2
    if val == 0xFFFF:
        break
    gs2.append(val)

# Expected full intro (approx):
# かつて三十年もの長きにわたってドゥーハン王国を血と恐怖に陥れた戦乱があった。
# 王国の人口を２／３までに減少させたその悲惨な戦争はバンクォーの戦役と人々に記憶される。
# ...

text2 = ''
for g in gs2:
    if g == 0xFFFE:
        text2 += '\n'
    elif g >= 0xFFC0:
        text2 += f'[{g:04X}]'
    else:
        ch = gm.get(str(g))
        if ch:
            text2 += ch
        else:
            text2 += f'({g})'
print(text2[:2000])

# Now: the key question. Is 337 actually 三 (not 中)?
# Or are there two different glyph tables?
print("\n=== Glyph 337 analysis ===")
print(f"  msg_glyph_map says: {gm.get('337', 'not in map')}")

# Also check the partial map
gm_partial = json.load(open('data/glyph_map_partial.json', encoding='utf-8'))
print(f"  glyph_map_partial says: {gm_partial.get('337', 'not in map')}")

# Check what glyph_map_template says
gm_template = json.load(open('data/glyph_map_template.json', encoding='utf-8'))
print(f"  glyph_map_template says: {gm_template.get('337', 'not in map')}")
