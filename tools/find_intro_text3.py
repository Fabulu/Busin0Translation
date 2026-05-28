#!/usr/bin/env python3
"""Find intro text by cross-referencing R1193 data with known glyph patterns."""
import struct
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir("C:/Programmieren/wizardrytranslation")

gm = json.load(open('data/glyph_map_partial.json', encoding='utf-8'))

# R1193 M0 glyphs (from earlier analysis)
m0_glyphs = [117, 129, 130, 337, 1186, 684, 146, 136, 404, 118, 133, 155, 127, 191, 130, 257, 217, 193, 136, 551, 156, 1200, 131, 771, 772, 133, 1060, 153, 127, 734, 788, 158, 112, 191, 127, 63, 332, 133, 254, 238, 200, 271, 93, 136, 734, 396, 131, 648, 173, 153, 152, 146, 136, 171, 112, 152, 63, 203, 238, 243, 93, 212, 136, 475, 158, 253, 269, 93, 218, 238, 490, 136, 156, 117, 117, 161, 1121, 145, 462, 191, 130, 118, 127, 136, 158, 62, 126, 146, 126, 146, 136, 1178, 627, 171, 112, 191, 127, 158, 92]

# Decode with partial map
print("=== R1193 M0 decoded with partial map ===")
text = ''
for g in m0_glyphs:
    ch = gm.get(str(g))
    if ch:
        text += ch
    elif g >= 0xFFC0:
        text += f'[{g:04X}]'
    elif g == 0xFFFE:
        text += '\n'
    else:
        text += f'({g})'
print(text)

# Show which glyphs are mapped vs unmapped
print("\n=== Mapping analysis ===")
mapped = sum(1 for g in m0_glyphs if str(g) in gm)
unmapped = [g for g in m0_glyphs if str(g) not in gm and g < 0xFFC0]
print(f"Mapped: {mapped}/{len(m0_glyphs)}")
print(f"Unmapped glyph IDs: {sorted(set(unmapped))}")

# The intro text: かつて三十年もの長きにわたってドゥーハン王国を血と恐怖に陥れた戦乱があった。
# Characters and their expected glyph IDs if we can find them
# か = 376, き = 377
# But R1193 M0 doesn't contain 376 or 377!
# This means R1193 M0 is NOT the intro narration
print(f"\n376 (ka) in M0? {376 in m0_glyphs}")
print(f"377 (ki) in M0? {377 in m0_glyphs}")

# Let's try another approach: look at the msg_glyph_map
print("\n=== msg_glyph_map.json ===")
msg_gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
print(f"Entries: {len(msg_gm)}")
if isinstance(msg_gm, dict):
    # Check structure
    first_key = next(iter(msg_gm))
    print(f"First key: {first_key}, value type: {type(msg_gm[first_key])}")
    # Show a few entries
    for i, (k, v) in enumerate(msg_gm.items()):
        if i >= 10:
            break
        print(f"  {k}: {v}")

# Check katakana map too
print("\n=== katakana_mapping.json ===")
kat = json.load(open('data/katakana_mapping.json', encoding='utf-8'))
print(f"Type: {type(kat)}")
if isinstance(kat, dict):
    for i, (k, v) in enumerate(kat.items()):
        if i >= 10:
            break
        print(f"  {k}: {v}")
elif isinstance(kat, list):
    print(f"Length: {len(kat)}")
    for i in range(min(10, len(kat))):
        print(f"  [{i}]: {kat[i]}")
